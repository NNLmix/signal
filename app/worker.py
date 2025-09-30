import asyncio, hashlib
from typing import Dict, List
import aiohttp
import logging
from datetime import datetime
from dateutil import tz

from .config import settings
from .services.binance import BinanceClient
from .services.redis_queue import RedisClient
from .services.supabase import SupabaseClient
from .services.strategies import STRATEGIES
from .services.indicators import atr
from .telegram import send_signal_message

log = logging.getLogger("worker")

NY_TZ = tz.gettz("America/New_York")
UA_TZ = tz.gettz("Europe/Kyiv")

def _fmt_entry_time(ts_ms: int | None) -> str:
    if not ts_ms:
        return "—"
    dt_utc = datetime.utcfromtimestamp(ts_ms/1000).replace(tzinfo=tz.UTC)
    dt_ny  = dt_utc.astimezone(NY_TZ)
    dt_ua  = dt_utc.astimezone(UA_TZ)
    return f"{dt_ny:%H:%M} NY | {dt_ua:%H:%M} Kyiv ({dt_ua:%d %b})"

def _dedup_key(symbol: str, strat_name: str, side: str, candle_close_ms: int | None) -> str:
    base = f"{symbol}|{strat_name}|{side}|{candle_close_ms or ''}"
    return "sig:" + hashlib.sha1(base.encode()).hexdigest()

async def run_worker(stop_event: asyncio.Event):
    redis = RedisClient()
    pairs: List[str] = getattr(settings, "PAIRS", ["BTCUSDT"])

    async with aiohttp.ClientSession() as session:
        binance = BinanceClient('https://fapi.binance.com', session)
        supa = SupabaseClient(session)
        keepalive_task = asyncio.create_task(_keepalive_loop(session, stop_event))
        try:
            while not stop_event.is_set():
                for strat in STRATEGIES:
                    tf = getattr(strat, "timeframe", "5m")
                    for symbol in pairs:
                        try:
                            kl = await binance.get_klines(symbol, tf, limit=300)
                            if not kl or len(kl) < 3:
                                continue
                            signals = strat.run(kl, symbol) or []

                            # Precompute ATR for fallback SL/TP
                            atr_vals = atr(kl, period=14)
                            last_atr = atr_vals[-1] if atr_vals and atr_vals[-1] is not None else None
                            last_close = float(kl[-1][4])
                            last_close_ms = int(kl[-1][6])

                            for sig in signals:
                                side = sig.get("side")
                                if side not in ("LONG", "SHORT"):
                                    continue

                                entry = sig.get("entry", last_close)
                                sl = sig.get("sl")
                                tp = sig.get("tp")

                                if sl is None or tp is None:
                                    if last_atr:
                                        mult_sl = getattr(settings, "ATR_SL_MULT", 1.0)
                                        mult_tp = getattr(settings, "ATR_TP_MULT", 2.0)
                                        if side == "LONG":
                                            sl = entry - mult_sl * last_atr
                                            tp = entry + mult_tp * last_atr
                                        else:
                                            sl = entry + mult_sl * last_atr
                                            tp = entry - mult_tp * last_atr
                                    else:
                                        # fallback static 0.5% / 1%
                                        if side == "LONG":
                                            sl = entry * 0.995
                                            tp = entry * 1.01
                                        else:
                                            sl = entry * 1.005
                                            tp = entry * 0.99

                                entry_time_ms = sig.get("entry_time_ms", last_close_ms)

                                # Dedup per symbol/strategy/side/candle
                                key = _dedup_key(sig.get("symbol", symbol), getattr(strat, "name", "unknown"), side, entry_time_ms)
                                fresh = await redis.try_set(key, getattr(settings, "DEDUP_TTL_SEC", 3600))
                                if not fresh:
                                    continue

                                # Persist
                                await supa.insert_signal({
                                    "symbol": sig.get("symbol", symbol),
                                    "side": side,
                                    "reason": sig.get("reason", ""),
                                    "strategy": getattr(strat, "name", ""),
                                    "timeframe": tf,
                                    "entry": entry,
                                    "sl": sl,
                                    "tp": tp,
                                    "entry_time_ms": entry_time_ms,
                                })

                                # Message text
                                rr = abs((tp - entry) / (entry - sl)) if (entry != sl) else 0.0
                                side_emoji = "🟢 LONG" if side == "LONG" else "🔴 SHORT"
                                lines = [
                                    f"<b>{side_emoji} {sig.get('symbol', symbol)}</b>",
                                    f"⏱ Entry time: { _fmt_entry_time(entry_time_ms) }",
                                    f"📈 Entry: <b>{entry:.4f}</b>",
                                    f"🎯 TP: {tp:.4f}   🛡 SL: {sl:.4f}   R:R <b>{rr:.2f}</b>",
                                    f"🧠 {getattr(strat, 'name', '')} · {tf}",
                                ]
                                rsn = sig.get("reason")
                                if rsn:
                                    lines.append(f"📝 {rsn}")
                                await send_signal_message("\n".join(lines))

                        except Exception as e:
                            log.exception("strategy_loop_error", extra={"strategy": getattr(strat, "name", ""), "symbol": symbol})

                await asyncio.sleep(getattr(settings, "POLL_INTERVAL_SEC", 5.0))
        finally:
            keepalive_task.cancel()
            with contextlib.suppress(Exception):
                await keepalive_task
import contextlib
async def _keepalive_loop(session: aiohttp.ClientSession, stop_event: asyncio.Event):
    # Self-ping health endpoint to prevent idling
    if not (getattr(settings, 'PUBLIC_URL', None) or getattr(settings, 'KOYEB_APP_URL', None)):
        return
    base = (settings.PUBLIC_URL or settings.KOYEB_APP_URL).rstrip('/')
    url = f"{base}/healthz"
    while not stop_event.is_set():
        try:
            async with session.get(url, timeout=5) as r:
                _ = await r.text()
        except Exception:
            pass
        await asyncio.sleep(getattr(settings, "KEEPALIVE_SEC", 60))

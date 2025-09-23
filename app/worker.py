import asyncio, hashlib
from typing import Dict, List
import aiohttp
import logging
from .config import settings
from .services.binance import BinanceClient
from .services.redis_queue import RedisClient
from .services.supabase import SupabaseClient
from .services.strategies import STRATEGIES
from .services.indicators import atr
from .telegram import send_signal_message

log = logging.getLogger("worker")

async def run_worker(stop_event: asyncio.Event):
    redis = RedisClient()
    async with aiohttp.ClientSession() as session:
        supa = SupabaseClient(session)
        binance = BinanceClient(settings.BINANCE_BASE, session)
        await binance.sync_time()

        # Preload klines for each symbol/timeframe once
        kline_cache: Dict[str, Dict[str, List[list]]] = {s: {} for s in settings.PAIRS}

        # Warm-up klines
        for symbol in settings.PAIRS:
            for strat in STRATEGIES:
                try:
                    kline_cache[symbol][strat.timeframe] = await binance.klines(symbol, strat.timeframe, limit=200)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    log.error("warmup_error", extra={"symbol": symbol, "tf": strat.timeframe, "err": str(e)})

        # Two background tasks: 1) keepalive pings 2) main per-second loop
        keepalive_task = asyncio.create_task(_keepalive_loop(session, stop_event))
        try:
            while not stop_event.is_set():
                loop_start = asyncio.get_event_loop().time()

                for symbol in settings.PAIRS:
                    for strat in STRATEGIES:
                        try:
                            # Refresh last candle cheaply: request small limit
                            kl = await binance.klines(symbol, strat.timeframe, limit=200)
                            kline_cache[symbol][strat.timeframe] = kl

                            signals = strat.run(kl, symbol)
                            if not signals:
                                continue

                            # Precompute ATR for SL/TP
                            atr_vals = atr(kl, period=14)
                            last_atr = atr_vals[-1] if atr_vals and atr_vals[-1] is not None else None
                            last_close = float(kl[-1][4])

                            for sig in signals:
                                # Attach entry/SL/TP
                                if last_atr:
                                    if sig["side"] == "LONG":
                                        sl = last_close - settings.ATR_SL_MULT * last_atr
                                        tp = last_close + settings.ATR_TP_MULT * last_atr
                                    else:
                                        sl = last_close + settings.ATR_SL_MULT * last_atr
                                        tp = last_close - settings.ATR_TP_MULT * last_atr
                                else:
                                    # Fallback fixed 0.5% / 1%
                                    if sig["side"] == "LONG":
                                        sl = last_close * 0.995
                                        tp = last_close * 1.01
                                    else:
                                        sl = last_close * 1.005
                                        tp = last_close * 0.99

                                text = format_signal_text(sig, last_close, sl, tp, strat.name, strat.timeframe)
                                dedup_key = make_dedup_key(sig, strat.name, last_close, sl, tp)
                                fresh = await redis.dedup_try_set(dedup_key, settings.DEDUP_TTL_SEC)
                                log.info('dedup_check', extra={'key': dedup_key, 'fresh': bool(fresh)})
                                if not fresh:
                                    continue

                                await supa.insert_signal({
                                    "symbol": sig["symbol"],
                                    "side": sig["side"],
                                    "reason": sig["reason"],
                                    "strategy": strat.name,
                                    "entry": last_close,
                                    "sl": sl,
                                    "tp": tp,
                                    "timeframe": strat.timeframe,
                                })
                                await send_signal_message(text)
                        except Exception as e:
                            log.error("loop_error", extra={"symbol": symbol, "strategy": strat.name, "err": str(e)})
                        await asyncio.sleep(0.05)  # tiny pacing between calls

                # Maintain ~1s cadence per full sweep (subject to rate limits)
                elapsed = asyncio.get_event_loop().time() - loop_start
                sleep_left = max(0, 1.0 - elapsed)
                await asyncio.sleep(sleep_left)
        finally:
            keepalive_task.cancel()
            with contextlib.suppress(Exception):
                await keepalive_task

def make_dedup_key(sig: dict, strategy: str, entry: float, sl: float, tp: float) -> str:
    payload = f"{sig['symbol']}|{strategy}|{sig['side']}|{sig.get('reason','')}|{entry:.4f}|{sl:.4f}|{tp:.4f}"
    return "dedup:signal:" + hashlib.sha1(payload.encode()).hexdigest()

def format_signal_text(sig: dict, entry: float, sl: float, tp: float, strategy: str, timeframe: str) -> str:
    return (
        f"<b>{sig['symbol']}</b> - <b>{sig['side']}</b>\n"
        f"TF: <code>{timeframe}</code> | Strategy: <code>{strategy}</code>\n"
        f"Entry: <code>{entry:.4f}</code>\n"
        f"SL: <code>{sl:.4f}</code> | TP: <code>{tp:.4f}</code>\n"
        f"Reason: {sig.get('reason','')}"
    )

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
        await asyncio.sleep(settings.KEEPALIVE_SEC)

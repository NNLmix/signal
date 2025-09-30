
import math, time, logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import aiohttp

from ..config import settings
from .binance import BinanceClient

log = logging.getLogger("backtest")

def _now_ms() -> int:
    return int(time.time() * 1000)

def _months_ago_ms(n: int) -> int:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=30*n)
    return int(dt.timestamp() * 1000)

async def _fetch_klines_3m(session: aiohttp.ClientSession, symbol: str, interval: str, months: int=3) -> List[List[Any]]:
    base = (getattr(settings, "BINANCE_BASE", "https://fapi.binance.com") or "https://fapi.binance.com").rstrip("/")
    url = f"{base}/fapi/v1/klines"
    end = _now_ms()
    start = _months_ago_ms(months)
    limit = 1000
    out: List[List[Any]] = []
    # Идём назад блоками по endTime
    current_end = end
    to_break = 20_000  # защита
    while current_end > start and to_break > 0:
        params = {"symbol": symbol, "interval": interval, "limit": limit, "endTime": current_end}
        timeout = getattr(settings, "REQUEST_TIMEOUT", 10)
        async with session.get(url, params=params, timeout=timeout) as r:
            r.raise_for_status()
            batch = await r.json()
        if not batch:
            break
        out[0:0] = batch  # prepend
        first_open = batch[0][0]
        if first_open <= start:
            break
        # следующий заход — до начала текущего батча
        current_end = first_open - 1
        to_break -= 1
    # фильтрация по диапазону
    out = [c for c in out if start <= c[0] <= end]
    return out

def _default_tp_sl(side: str, entry: float) -> (float, float):
    # примитив: 1% TP / 0.5% SL
    if side == "LONG":
        return (entry * 1.01, entry * 0.995)
    else:
        return (entry * 0.99, entry * 1.005)

def _hit(side: str, entry: float, tp: float, sl: float, subsequent: List[List[Any]]) -> Optional[str]:
    for c in subsequent:
        high = float(c[2]); low = float(c[3])
        tp_hit = high >= tp if side == "LONG" else low <= tp
        sl_hit = low <= sl if side == "LONG" else high >= sl
        if tp_hit and sl_hit:
            return "SL"
        if tp_hit:
            return "TP"
        if sl_hit:
            return "SL"
    return None

async def backtest_strategy(strategy, symbol: str, interval: str, months: int=3) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        kl = await _fetch_klines_3m(session, symbol, interval, months=months)
    if len(kl) < 200:
        return {"symbol": symbol, "trades": 0, "wins": 0, "winrate": 0.0}

    trades=0; wins=0
    # Бежим по истории и на каждом шаге используем текущую реализацию run(...)
    warm = 100
    for i in range(warm, len(kl)-1):
        window = kl[:i+1]
        signals = strategy.run(window, symbol) or []
        if not signals:
            continue
        # берем только первый сигнал на свече
        sig = signals[0]
        side = sig.get("side")
        if side not in ("LONG","SHORT"):
            continue
        entry = float(sig.get("entry") or window[-1][4])
        tp = float(sig.get("tp") or _default_tp_sl(side, entry)[0])
        sl = float(sig.get("sl") or _default_tp_sl(side, entry)[1])
        outcome = _hit(side, entry, tp, sl, kl[i+1:])
        if outcome:
            trades += 1
            if outcome == "TP":
                wins += 1
    winrate = (wins/trades*100.0) if trades else 0.0
    return {"symbol": symbol, "trades": trades, "wins": wins, "winrate": round(winrate,2)}

async def run_backtest(strategy_name: str, strategy, pairs: List[str], interval: str, months: int=3) -> Dict[str, Any]:
    per = {}
    total_tr=0; total_w=0
    for sym in pairs:
        try:
            r = await backtest_strategy(strategy, sym, interval, months=months)
            per[sym]=r
            total_tr += r["trades"]; total_w += r["wins"]
        except Exception as e:
            log.exception("backtest_error", extra={"symbol": sym, "error": str(e)})
    winrate = (total_w/total_tr*100.0) if total_tr else 0.0
    return {"strategy": strategy_name, "interval": interval, "trades": total_tr, "wins": total_w, "winrate": round(winrate,2), "per_symbol": per}

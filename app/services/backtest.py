
import time, logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
import aiohttp

from app.config import settings

log = logging.getLogger("backtest")

def _now_ms(): return int(time.time()*1000)
def _months_ago_ms(n): return int((datetime.now(tz=timezone.utc)-timedelta(days=30*n)).timestamp()*1000)

async def _fetch_klines(symbol: str, interval: str, months: int=3) -> List[List[Any]]:
    base = (getattr(settings, "BINANCE_BASE", "https://fapi.binance.com") or "https://fapi.binance.com").rstrip("/")
    url = f"{base}/fapi/v1/klines"
    end = _now_ms(); start = _months_ago_ms(months)
    out: List[List[Any]] = []
    limit = 1000
    async with aiohttp.ClientSession() as session:
        current_end = end
        guard = 20000
        while current_end > start and guard > 0:
            timeout = getattr(settings, "REQUEST_TIMEOUT", 10)
            params = {"symbol": symbol, "interval": interval, "limit": limit, "endTime": current_end}
            async with session.get(url, params=params, timeout=timeout) as r:
                r.raise_for_status()
                batch = await r.json()
            if not batch:
                break
            out[0:0] = batch
            first_open = batch[0][0]
            if first_open <= start: break
            current_end = first_open - 1
            guard -= 1
    return [c for c in out if start <= c[0] <= end]

def _default_tp_sl(side: str, entry: float):
    return ((entry*1.01, entry*0.995) if side=="LONG" else (entry*0.99, entry*1.005))

def _hit(side: str, entry: float, tp: float, sl: float, subsequent: List[List[Any]]):
    for c in subsequent:
        h = float(c[2]); l = float(c[3])
        tp_hit = h>=tp if side=="LONG" else l<=tp
        sl_hit = l<=sl if side=="LONG" else h>=sl
        if tp_hit and sl_hit: return "SL"
        if tp_hit: return "TP"
        if sl_hit: return "SL"
    return None

async def backtest_strategy(strategy, symbol: str, interval: str, months: int=3) -> Dict[str, Any]:
    kl = await _fetch_klines(symbol, interval, months)
    if len(kl) < 200:
        return {"symbol": symbol, "trades": 0, "wins": 0, "winrate": 0.0}
    trades=wins=0
    warm=100
    for i in range(warm, len(kl)-1):
        window = kl[:i+1]
        signals = strategy.run(window, symbol) or []
        if not signals: continue
        sig = signals[0]
        side = sig.get("side")
        if side not in ("LONG","SHORT"): continue
        entry = float(sig.get("entry") or window[-1][4])
        tp = float(sig.get("tp") or _default_tp_sl(side, entry)[0])
        sl = float(sig.get("sl") or _default_tp_sl(side, entry)[1])
        outcome = _hit(side, entry, tp, sl, kl[i+1:])
        if outcome:
            trades += 1
            if outcome=="TP": wins += 1
    winrate = (wins/trades*100.0) if trades else 0.0
    return {"symbol": symbol, "trades": trades, "wins": wins, "winrate": round(winrate,2)}

async def run_backtest(strategy_name: str, strategy, pairs: List[str], interval: str, months: int=3) -> Dict[str, Any]:
    per={}; T=W=0
    for sym in pairs:
        try:
            r = await backtest_strategy(strategy, sym, interval, months=months)
            per[sym]=r; T+=r["trades"]; W+=r["wins"]
        except Exception as e:
            log.exception("backtest_error", extra={"symbol": sym, "error": str(e)})
    winrate = (W/T*100.0) if T else 0.0
    return {"strategy": strategy_name, "interval": interval, "trades": T, "wins": W, "winrate": round(winrate,2), "per_symbol": per}

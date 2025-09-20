from typing import List, Dict, Any
from ..indicators import close_prices, ema

class Strategy:
    name = "trend_pullback_5m"
    timeframe = "5m"

    def run(self, klines: List[List[Any]], symbol: str) -> List[Dict[str, Any]]:
        closes = close_prices(klines)
        ema50 = ema(closes, 50)
        ema200 = ema(closes, 200)
        if len(closes) < 3 or len(ema50) < 3 or len(ema200) < 3:
            return []
        c0, c1 = closes[-1], closes[-2]
        e50_0, e50_1 = ema50[-1], ema50[-2]
        e200_0, e200_1 = ema200[-1], ema200[-2]
        out = []
        # Simple: bullish trend + pullback close above EMA50
        if e50_1 is not None and e200_1 is not None and e50_1 > e200_1 and c1 < e50_1 and c0 > e50_0:
            out.append({"side": "LONG", "reason": "PullbackAboveEMA50", "symbol": symbol})
        # Bearish mirror
        if e50_1 is not None and e200_1 is not None and e50_1 < e200_1 and c1 > e50_1 and c0 < e50_0:
            out.append({"side": "SHORT", "reason": "PullbackBelowEMA50", "symbol": symbol})
        return out

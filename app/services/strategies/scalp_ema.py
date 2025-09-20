from typing import List, Dict, Any
from ..indicators import close_prices, ema

class Strategy:
    name = "scalp_ema_cross_5m"
    timeframe = "5m"

    def run(self, klines: List[List[Any]], symbol: str) -> List[Dict[str, Any]]:
        closes = close_prices(klines)
        fast = ema(closes, 9)
        slow = ema(closes, 21)

        signals = []
        # Basic cross: fast crossing slow on the last bar
        if len(fast) >= 2 and len(slow) >= 2:
            f1, f0 = fast[-2], fast[-1]
            s1, s0 = slow[-2], slow[-1]
            if f1 is not None and s1 is not None and f0 is not None and s0 is not None:
                if f1 <= s1 and f0 > s0:
                    signals.append({"side": "LONG", "reason": "EMA9>EMA21", "symbol": symbol})
                if f1 >= s1 and f0 < s0:
                    signals.append({"side": "SHORT", "reason": "EMA9<EMA21", "symbol": symbol})
        return signals

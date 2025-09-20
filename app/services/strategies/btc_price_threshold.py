from typing import List, Dict, Any
from ..indicators import close_prices
from ...config import settings

class Strategy:
    name = "btc_price_gt_threshold"
    timeframe = "1m"  # frequent checks

    # once-per-process flag
    _sent_once: bool = False

    def run(self, klines: List[List[Any]], symbol: str) -> List[Dict[str, Any]]:
        if not settings.TEST_SIGNAL_ENABLED:
            return []
        if symbol != "BTCUSDT":
            return []
        closes = close_prices(klines)
        if len(closes) < 2:
            return []
        prev_close, last_close = closes[-2], closes[-1]
        thr = settings.TEST_SIGNAL_PRICE

        # only when price crosses above threshold (no spam)
        crossed_up = prev_close <= thr and last_close > thr

        if settings.TEST_SIGNAL_ONCE and self._sent_once:
            return []
        if crossed_up:
            if settings.TEST_SIGNAL_ONCE:
                self._sent_once = True
            return [{
                "side": "LONG",
                "reason": f"CrossUp>{thr}",
                "symbol": symbol
            }]
        return []

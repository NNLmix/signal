from typing import List, Dict, Any
from ..indicators import close_prices
from ...config import settings

class Strategy:
    name = "btc_price_gt_threshold"
    timeframe = "1m"  # check frequent 1-minute candles

    def run(self, klines: List[List[Any]], symbol: str) -> List[Dict[str, Any]]:
        if not settings.TEST_SIGNAL_ENABLED:
            return []
        if symbol != "BTCUSDT":
            return []
        closes = close_prices(klines)
        if not closes:
            return []
        last_close = closes[-1]
        if last_close > settings.TEST_SIGNAL_PRICE:
            return [{
                "side": "LONG",
                "reason": f"Price>{settings.TEST_SIGNAL_PRICE}",
                "symbol": symbol
            }]
        return []

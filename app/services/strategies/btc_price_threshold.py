from typing import Dict, Any, List, Optional
from ...config import settings

class Strategy:
    name = "btc_price_gt_threshold"
    timeframe = "1m"
    _emitted_once: bool = False  # class-level, one-shot per process/deploy

    def run(self, klines: List[List[Any]], symbol: str) -> List[Dict[str, Any]]:
        """
        One-time BTC test signal per deploy if last price > TEST_SIGNAL_PRICE.
        Emits LONG with simple SL/TP bands for visibility.
        Returns a list (empty or with a single dict) to match engine expectations.
        """
        if not settings.TEST_SIGNAL_ENABLED:
            return []
        if symbol != "BTCUSDT":
            return []
        if Strategy._emitted_once:
            return []
        if not klines:
            return []

        last_close = float(klines[-1][4])
        thr = float(settings.TEST_SIGNAL_PRICE)

        if last_close > thr:
            entry = last_close
            sl = round(entry * 0.98, 2)   # -2%
            tp = round(entry * 1.02, 2)   # +2%
            Strategy._emitted_once = True
            return [{
                "symbol": symbol,
                "side": "LONG",
                "reason": f"TEST one-shot: price {last_close} > threshold {thr}",
                "strategy": self.name,
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "timeframe": self.timeframe,
            }]
        return []

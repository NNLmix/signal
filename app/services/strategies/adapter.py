
from typing import List, Dict, Any
from .base import BaseStrategy, Kline

class CandleAdapter(BaseStrategy):
    def __init__(self, name: str, timeframe: str, inner):
        self.name = name
        self.timeframe = timeframe
        self.inner = inner
    def run(self, klines: List[Kline], symbol: str) -> List[Dict[str, Any]]:
        # если стратегия умеет on_candle(window)->signal
        out: List[Dict[str, Any]] = []
        for i in range(100, len(klines)):
            window = klines[:i+1]
            sig = self.inner.on_candle(window) if hasattr(self.inner, "on_candle") else None
            if sig:
                out.append(sig)
        return out

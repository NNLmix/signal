
from __future__ import annotations
from typing import List, Dict, Any, Protocol

Kline = List[Any]

class BaseStrategy(Protocol):
    name: str
    timeframe: str
    def run(self, klines: List[Kline], symbol: str) -> List[Dict[str, Any]]: ...

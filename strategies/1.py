from typing import Optional

class Signal:
    def __init__(self, symbol, side, size, entry_price, reason, confidence, metadata=None):
        self.symbol = symbol
        self.side = side
        self.size = size
        self.entry_price = entry_price
        self.reason = reason
        self.confidence = confidence
        self.metadata = metadata or {}

class Strategy:
    name = "momentum_v1"

    def __init__(self, config):
        self.config = config

    async def evaluate(self, window) -> Optional[Signal]:
        prices = window.get("prices", [])
        if len(prices) < 5:
            return None

        last_price = prices[-1]
        avg_price = sum(prices) / len(prices)

        if last_price > avg_price * 1.02:
            return Signal(
                symbol=window["symbol"],
                side="long",
                size=0.1,
                entry_price=last_price,
                reason="Momentum breakout >2%",
                confidence=75,
            )
        return None

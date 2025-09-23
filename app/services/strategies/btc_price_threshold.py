from typing import Dict, Any, List, Optional
from ...config import settings

_emitted_once = False  # one-shot per process/deploy

def run(symbol: str, klines: List[List[Any]]) -> Optional[Dict[str, Any]]:
    """
    One-time test signal per deploy if last price > TEST_SIGNAL_PRICE.
    Emits LONG with simple SL/TP bands for visibility.
    """
    global _emitted_once
    if not settings.TEST_SIGNAL_ENABLED:
        return None
    if _emitted_once:
        return None

    if not klines:
        return None

    last_close = float(klines[-1][4])
    thr = float(settings.TEST_SIGNAL_PRICE)

    if last_close > thr:
        # Construct a simple test payload. (No crossing, just current > threshold)
        entry = last_close
        sl = round(entry * 0.98, 2)   # -2% for visibility
        tp = round(entry * 1.02, 2)   # +2% for visibility
        _emitted_once = True
        return {
            "symbol": symbol,
            "side": "LONG",
            "reason": f"TEST one-shot: price {last_close} > threshold {thr}",
            "strategy": "btc_price_gt_threshold",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "timeframe": "1m",
        }

    return None

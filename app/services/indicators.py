from typing import List, Tuple

def ema(series: List[float], period: int) -> List[float]:
    if not series or period <= 1:
        return series[:]
    k = 2 / (period + 1)
    ema_vals = []
    ema_prev = sum(series[:period]) / period
    ema_vals.extend([None]*(period-1))
    ema_vals.append(ema_prev)
    for price in series[period:]:
        ema_prev = price * k + ema_prev * (1 - k)
        ema_vals.append(ema_prev)
    return ema_vals

def close_prices(kl: List[List]) -> List[float]:
    return [float(x[4]) for x in kl]

def hl2(kl: List[List]) -> List[float]:
    return [(float(x[2]) + float(x[3]))/2 for x in kl]

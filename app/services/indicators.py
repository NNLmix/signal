from typing import List

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

def true_range(kl: List[List]) -> List[float]:
    trs = []
    prev_close = None
    for k in kl:
        high = float(k[2]); low = float(k[3]); close = float(k[4])
        if prev_close is None:
            trs.append(high - low)
        else:
            trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
        prev_close = close
    return trs

def atr(kl: List[List], period: int = 14) -> List[float]:
    trs = true_range(kl)
    if len(trs) < period:
        return [None]*len(trs)
    # Wilder's smoothing
    atr_vals = [None]*(period-1)
    first = sum(trs[:period]) / period
    atr_vals.append(first)
    prev = first
    for tr in trs[period:]:
        prev = (prev*(period-1) + tr) / period
        atr_vals.append(prev)
    return atr_vals

from typing import List
from indicators import ema, macd

class Strategy:
    """
    MACD Retest (5m):
      - HTF bias: 1h EMA200 slope up -> prefer LONG; slope down -> prefer SHORT
      - Trigger (5m):
         * LONG: MACD histogram crosses from negative to positive AND price retests EMA20 from above (close > EMA20 and prev close < EMA20)
         * SHORT: MACD histogram crosses from positive to negative AND price retests EMA20 from below (close < EMA20 and prev close > EMA20)
      - TP/SL: based on ATR proxy from 5m (same as scalp baseline) but with milder RR ~ 1:1.5
    """
    def __init__(self, config):
        self.name = "macd_retest_5m"
        self.timeframe = "5m"

    def _atr_proxy(self, df):
        hh = float(df["high"].iloc[-14:].max())
        ll = float(df["low"].iloc[-14:].min())
        return (hh - ll) / 14.0

    def generate_signals(self, df_ltf, df_htf) -> List[dict]:
        if len(df_ltf) < 60 or len(df_htf) < 210:
            return []

        c5 = df_ltf["close"]
        e20 = ema(c5, 20)
        macd_line, signal_line, hist = macd(c5, 12, 26, 9)

        # HTF trend bias via EMA200 slope
        e200_htf = ema(df_htf["close"], 200)
        slope_htf = float(e200_htf.iloc[-1] - e200_htf.iloc[-2])
        bias = "up" if slope_htf > 0 else ("down" if slope_htf < 0 else "flat")

        c0, c1 = float(c5.iloc[-1]), float(c5.iloc[-2])
        e20_0, e20_1 = float(e20.iloc[-1]), float(e20.iloc[-2])
        h0, h1 = float(hist.iloc[-1]), float(hist.iloc[-2])

        atr = self._atr_proxy(df_ltf)
        atr_pct = atr / max(1e-9, c0)
        if not (0.0015 <= atr_pct <= 0.03):
            return []

        out: List[dict] = []

        # LONG retest: hist crosses up, price flips back above EMA20
        long_cross = (h1 <= 0 < h0)
        long_retest = (c1 <= e20_1) and (c0 > e20_0)
        # SHORT retest: hist crosses down, price flips back below EMA20
        short_cross = (h1 >= 0 > h0)
        short_retest = (c1 >= e20_1) and (c0 < e20_0)

        cond_long = long_cross and long_retest
        cond_short = short_cross and short_retest

        if bias == "up":
            cond_short = False
        elif bias == "down":
            cond_long = False

        # RR ~ 1:1.5 here
        SL_M, TP_M = 1.0, 1.5
        if cond_long:
            sl = round(c0 - SL_M * atr, 4)
            tp = round(c0 + TP_M * atr, 4)
            out.append({"side":"LONG","entry_price":round(c0,4),"sl":sl,"tp":tp,
                        "reason": f"MACD up cross + EMA20 retest (ATR%={atr_pct:.3%}, bias={bias}, RR≈{TP_M/SL_M:.2f})"})

        if cond_short:
            sl = round(c0 + SL_M * atr, 4)
            tp = round(c0 - TP_M * atr, 4)
            out.append({"side":"SHORT","entry_price":round(c0,4),"sl":sl,"tp":tp,
                        "reason": f"MACD down cross + EMA20 retest (ATR%={atr_pct:.3%}, bias={bias}, RR≈{TP_M/SL_M:.2f})"})

        return out

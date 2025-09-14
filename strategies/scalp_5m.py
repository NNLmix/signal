from typing import List
from indicators import ema, rsi
from config import SCALP_SL_ATR, SCALP_TP_ATR

class Strategy:
    def __init__(self, config):
        self.name = "scalp_5m"
        self.timeframe = "5m"

    def _atr_proxy(self, df):
        hh = float(df["high"].iloc[-14:].max())
        ll = float(df["low"].iloc[-14:].min())
        return (hh - ll) / 14.0

    def generate_signals(self, df_ltf, df_htf) -> List[dict]:
        if len(df_ltf) < 210:
            return []

        close = df_ltf["close"]
        e20 = ema(close, 20)
        e50 = ema(close, 50)
        e200 = ema(close, 200)
        r = rsi(close, 14)

        c0, c1 = float(close.iloc[-1]), float(close.iloc[-2])
        e20_0, e20_1 = float(e20.iloc[-1]), float(e20.iloc[-2])
        e50_0, e50_1 = float(e50.iloc[-1]), float(e50.iloc[-2])
        e200_0, e200_1 = float(e200.iloc[-1]), float(e200.iloc[-2])
        r0, r1 = float(r.iloc[-1]), float(r.iloc[-2])

        slope200 = e200_0 - e200_1
        trend = "up" if slope200 > 0 else ("down" if slope200 < 0 else "flat")

        atr = self._atr_proxy(df_ltf)
        atr_pct = atr / max(1e-9, c0)
        if not (0.002 <= atr_pct <= 0.025):
            return []

        out: List[dict] = []
        cond_long = (c0 > e20_0 > e50_0) and (r1 <= 50 < r0)
        cond_short = (c0 < e20_0 < e50_0) and (r1 >= 50 > r0)

        if trend == "up":
            cond_short = False
        elif trend == "down":
            cond_long = False

        if cond_long:
            sl = round(c0 - SCALP_SL_ATR * atr, 4)
            tp = round(c0 + SCALP_TP_ATR * atr, 4)
            out.append({"side":"LONG","entry_price":round(c0,4),"sl":sl,"tp":tp,
                        "reason": f"RSI up & above EMA20/50 (ATR%={atr_pct:.3%}, trend={trend}, RR≈{SCALP_TP_ATR/SCALP_SL_ATR:.2f})"})

        if cond_short:
            sl = round(c0 + SCALP_SL_ATR * atr, 4)
            tp = round(c0 - SCALP_TP_ATR * atr, 4)
            out.append({"side":"SHORT","entry_price":round(c0,4),"sl":sl,"tp":tp,
                        "reason": f"RSI down & below EMA20/50 (ATR%={atr_pct:.3%}, trend={trend}, RR≈{SCALP_TP_ATR/SCALP_SL_ATR:.2f})"})

        return out

from typing import List, Dict, Any
from dateutil import tz
from datetime import datetime, timedelta

class Strategy:
    name = "four_hour_reentry_5m"
    timeframe = "5m"

    NY_TZ = tz.gettz("America/New_York")

    def _ny_date(self, ts_ms: int):
        dt_utc = datetime.utcfromtimestamp(ts_ms/1000).replace(tzinfo=tz.UTC)
        return dt_utc.astimezone(self.NY_TZ).date()

    def _ny_time(self, ts_ms: int):
        dt_utc = datetime.utcfromtimestamp(ts_ms/1000).replace(tzinfo=tz.UTC)
        return dt_utc.astimezone(self.NY_TZ).time()

    def _today_first_4h_range(self, klines: List[List[Any]]) -> Dict[str, float] | None:
        if not klines:
            return None
        # Use NY date of the last closed candle as "today"
        last_close_time = int(klines[-1][6])
        ny_day = self._ny_date(last_close_time)
        # Collect 5m candles from 00:00 to 03:59:59 NY on that day
        highs, lows = [], []
        for k in klines:
            close_t = int(k[6])
            if self._ny_date(close_t) != ny_day:
                continue
            ny_t = self._ny_time(close_t)
            # include candles whose CLOSE time is < 04:00
            if ny_t.hour < 4:
                highs.append(float(k[2]))
                lows.append(float(k[3]))
        if not highs or not lows:
            return None
        return {"high": max(highs), "low": min(lows)}

    def run(self, klines: List[List[Any]], symbol: str) -> List[Dict[str, Any]]:
        # Expect Binance 5m klines
        if len(klines) < 50:
            return []
        rng = self._today_first_4h_range(klines)
        if not rng:
            return []

        # Last two fully closed 5m candles
        prev = klines[-2]
        curr = klines[-1]

        prev_close = float(prev[4])
        curr_close = float(curr[4])
        prev_high, prev_low = float(prev[2]), float(prev[3])
        curr_close_time = int(curr[6])

        # Breakouts (close outside), then re-entry (current close back inside)
        out: List[Dict[str, Any]] = []

        # Short setup: previous candle closed ABOVE range high, current closes BACK BELOW range high
        if prev_close > rng["high"] and curr_close <= rng["high"]:
            # SL = extreme of breakout candle (prev high)
            sl = prev_high
            entry = curr_close
            dist = abs(sl - entry)
            tp = entry - 2.0 * dist  # 2R
            reason = f"4H Re-entry SHORT — breakout above {rng['high']:.4f}, re-entry inside. Entry time set."
            out.append({
                "symbol": symbol,
                "side": "SHORT",
                "reason": reason,
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "entry_time_ms": curr_close_time,
                "range_high": rng["high"],
                "range_low": rng["low"],
            })

        # Long setup: previous candle closed BELOW range low, current closes BACK ABOVE range low
        if prev_close < rng["low"] and curr_close >= rng["low"]:
            # SL = extreme of breakout candle (prev low)
            sl = prev_low
            entry = curr_close
            dist = abs(entry - sl)
            tp = entry + 2.0 * dist  # 2R
            reason = f"4H Re-entry LONG — breakout below {rng['low']:.4f}, re-entry inside. Entry time set."
            out.append({
                "symbol": symbol,
                "side": "LONG",
                "reason": reason,
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "entry_time_ms": curr_close_time,
                "range_high": rng["high"],
                "range_low": rng["low"],
            })

        return out

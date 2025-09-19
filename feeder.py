import asyncio, logging, pandas as pd
from config import SYMBOLS, LTF, HTF, TRADE_EXECUTION_ENABLED
from binance_client import fetch_klines
from strategy_runner import evaluate_and_queue
from redis_client import get_last_candle_ts, set_last_candle_ts, is_available, _log_once

logger = logging.getLogger(__name__)

def _klines_to_df(klines):
    cols = ["open_time","open","high","low","close","volume","close_time","qav","trades","taker_base","taker_quote","ignore"]
    df = pd.DataFrame(klines, columns=cols)
    for c in ["open","high","low","close","volume","qav","taker_base","taker_quote"]:
        df[c] = df[c].astype(float)
    df["open_time"] = (df["open_time"] // 1000).astype(int)
    df["close_time"] = (df["close_time"] // 1000).astype(int)
    df = df.set_index(pd.to_datetime(df["close_time"], unit="s", utc=True)).sort_index()
    return df[["open","high","low","close","volume"]]

async def _process_symbol(symbol: str):
    if not is_available():
        _log_once('redis.unavailable (feeder); will retry')
        return
    ltf_raw = await fetch_klines(symbol, LTF, limit=210)
    htf_raw = await fetch_klines(symbol, HTF, limit=210)
    df_ltf = _klines_to_df(ltf_raw)
    df_htf = _klines_to_df(htf_raw)

    last_close_ts = int(df_ltf.index[-1].timestamp())
    prev = get_last_candle_ts(symbol, LTF)
    if last_close_ts == prev:
        return

    # Signals only, no execution
    await evaluate_and_queue(symbol, df_ltf, df_htf)

    set_last_candle_ts(symbol, LTF, last_close_ts)

async def run():
    logger.info("feeder.start %s", {"symbols": SYMBOLS, "ltf": LTF, "htf": HTF, "execute": False})
    while True:
        try:
            await asyncio.gather(*[ _process_symbol(s.strip()) for s in SYMBOLS if s.strip() ])
        except Exception as e:
            logger.exception("feeder.loop.error %s", {"error": str(e)})
        await asyncio.sleep(1)  # reduced to 1s - ensure rate limits are respected; consider using WebSocket

if __name__ == "__main__":
    asyncio.run(run())

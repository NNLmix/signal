import asyncio, os, pandas as pd
from logging_setup import logger
from data.binance_public import fetch_klines
from strategies.scalp_5m import Scalp5M, StrategyConfig
from storage import save_signal
SYMBOL = os.getenv("SYMBOL","BTCUSDT"); RR = float(os.getenv("RR","2.0")); RISK=float(os.getenv("RISK","0.01")); ACCOUNT=float(os.getenv("ACCOUNT","10000"))
SESSION_FILTER = os.getenv("SESSION_FILTER","1")=="1"; POLL_SECONDS=int(os.getenv("POLL_SECONDS","120"))
async def once():
    df5 = await fetch_klines(SYMBOL,"5m",500); df1 = await fetch_klines(SYMBOL,"1h",500)
    df5.index = pd.to_datetime(df5.index, utc=True); df1.index = pd.to_datetime(df1.index, utc=True)
    strat = Scalp5M(StrategyConfig(rr=RR, risk_per_trade=RISK, account_balance=ACCOUNT, enable_session_filter=SESSION_FILTER))
    sigs = strat.generate_signals(df5, df1)
    if not sigs: logger.info("strategy.no_signals %s", {"symbol": SYMBOL}); return
    last_ts = df5.index[-1].isoformat()
    for s in sigs:
        if s["time"].isoformat()==last_ts:
            await save_signal(SYMBOL, s["time"].isoformat(), s["direction"], s["entry"], s["sl"], s["tp"], s["size"], s["meta"])
            logger.info("strategy.signal_saved %s", {"symbol": SYMBOL, "time": last_ts, "dir": s["direction"]})
async def main():
    logger.info("strategy_runner.start %s", {"symbol": SYMBOL})
    while True:
        try: await once()
        except Exception as e: logger.exception("strategy_runner.error %s", {"error": str(e)})
        await asyncio.sleep(POLL_SECONDS)
if __name__ == "__main__": asyncio.run(main())

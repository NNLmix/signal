import aiohttp, pandas as pd
from typing import Literal, List
BASE = "https://api.binance.com/api/v3/klines"
async def fetch_klines(symbol: str, interval: Literal["5m","1h"], limit: int = 500) -> pd.DataFrame:
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    async with aiohttp.ClientSession() as s:
        async with s.get(BASE, params=params, timeout=30) as r:
            r.raise_for_status()
            raw: List = await r.json()
    rows = [{
        "timestamp": pd.to_datetime(k[0], unit="ms", utc=True),
        "open": float(k[1]), "high": float(k[2]), "low": float(k[3]), "close": float(k[4]), "volume": float(k[5]),
    } for k in raw]
    df = pd.DataFrame(rows).set_index("timestamp").sort_index()
    return df

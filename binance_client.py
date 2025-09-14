import aiohttp, asyncio, logging
from config import BINANCE_BASE, REQUEST_TIMEOUT, RETRY_MAX

logger = logging.getLogger(__name__)

async def _request_json(session, url, params):
    for attempt in range(1, RETRY_MAX+1):
        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json(content_type=None)
                if resp.status == 200:
                    return data
                logger.warning("binance.http %s", {"status": resp.status, "data": data})
        except Exception as e:
            logger.warning("binance.error %s", {"attempt": attempt, "error": str(e)})
        await asyncio.sleep(min(2**attempt * 0.2, 3.0))
    raise RuntimeError("Binance request failed after retries")

async def fetch_klines(symbol: str, interval: str, limit: int = 210):
    url = f"{BINANCE_BASE}/fapi/v1/klines"
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        data = await _request_json(session, url, params)
        return data

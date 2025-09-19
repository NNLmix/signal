import aiohttp, asyncio, logging, os
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

BINANCE_BASE = os.environ.get("BINANCE_BASE", "https://fapi.binance.com")
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "20"))
RETRY_MAX = int(os.environ.get("RETRY_MAX", "4"))

_SESSION = None

def _get_timeout():
    return aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

async def get_session():
    global _SESSION
    if _SESSION and not _SESSION.closed:
        return _SESSION
    _SESSION = aiohttp.ClientSession(timeout=_get_timeout())
    return _SESSION

async def close_session():
    global _SESSION
    if _SESSION and not _SESSION.closed:
        await _SESSION.close()
        _SESSION = None

async def _request_json(session, url, params):
    backoff = 0.2
    for attempt in range(1, RETRY_MAX+1):
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
                if resp.status == 429:
                    ra = resp.headers.get("Retry-After")
                    try:
                        wait = float(ra) if ra else min((2 ** attempt) * backoff, 10.0)
                    except Exception:
                        wait = min((2 ** attempt) * backoff, 10.0)
                    logger.warning("binance.rate_limited; sleeping %s", wait)
                    await asyncio.sleep(wait)
                    continue
                text = await resp.text()
                logger.warning("binance.http %s", {"status": resp.status, "body": text})
        except Exception as e:
            logger.warning("binance.error %s", {"attempt": attempt, "error": str(e)})
        await asyncio.sleep(min((2 ** attempt) * backoff, 10.0))
    raise RuntimeError("Binance request failed after retries")

async def fetch_klines(symbol: str, interval: str, limit: int = 500):
    url = urljoin(BINANCE_BASE + "/", "fapi/v1/klines")
    session = await get_session()
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    return await _request_json(session, url, params)

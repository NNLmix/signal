import aiohttp, asyncio, logging
from config import BINANCE_BASE, REQUEST_TIMEOUT, RETRY_MAX

logger = logging.getLogger(__name__)

async def _request_json(session, url, params=None):
    """Perform GET and safely parse JSON. On non-JSON responses return text and status.
    This avoids crashing when server returns empty or HTML responses which cause
    JSONDecodeError: 'Expecting value: line 1 column 1 (char 0)'.
    """
    headers = {"Accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    for attempt in range(1, RETRY_MAX + 1):
        try:
            async with session.get(url, params=params, headers=headers, timeout=timeout) as resp:
                status = resp.status
                text = await resp.text()
                # Try to parse JSON if content-type looks like JSON or text looks like JSON
                data = None
                if not text:
                    logger.debug("binance.http empty body for %s", url)
                else:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        # not JSON - leave data as None and include raw text in logs
                        logger.debug("binance.http non-json body: %.200s", text)
                if status == 200:
                    # prefer parsed JSON if available, otherwise return raw text
                    return {"ok": True, "status": status, "data": data if data is not None else text}
                logger.warning("binance.http %s", {"status": status, "data": data if data is not None else text[:500]})
                return {"ok": False, "status": status, "data": data if data is not None else text}
        except Exception as e:
            logger.warning("binance.error %s", {"attempt": attempt, "error": str(e)})
            # exponential backoff
            await asyncio.sleep(min(1 * attempt, 5))
    return {"ok": False, "status": None, "data": None, "error": "max_retries_exceeded"}

async def ping():
    url = f"{BINANCE_BASE}/api/v3/ping"
    async with aiohttp.ClientSession() as session:
        return await _request_json(session, url)

async def server_time():
    url = f"{BINANCE_BASE}/api/v3/time"
    async with aiohttp.ClientSession() as session:
        return await _request_json(session, url)

if __name__ == "__main__":
    import asyncio, logging
    logging.basicConfig(level=logging.DEBUG)
    print(asyncio.run(ping()))
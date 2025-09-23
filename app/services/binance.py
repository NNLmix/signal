import logging
import aiohttp
import time
from typing import Any, List
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from ..config import settings
log = logging.getLogger('binance')

class BinanceClient:
    def __init__(self, base: str, session: aiohttp.ClientSession):
        self.base = base.rstrip('/')
        self.session = session
        self._time_offset_ms = 0

    async def sync_time(self):
        start = time.time(); log.info('binance_sync_time_start', extra={'url': f'{self.base}/fapi/v1/time'})
        url = f"{self.base}/fapi/v1/time"
        async with self.session.get(url, timeout=settings.REQUEST_TIMEOUT) as r:
            r.raise_for_status()
            data = await r.json()
            log.info('binance_sync_time_ok', extra={'delta_ms': data.get('serverTime', 0) - int(time.time()*1000), 'status': r.status, 'elapsed_ms': int((time.time()-start)*1000)})
            server_time = int(data["serverTime"])
            local = int(time.time() * 1000)
            self._time_offset_ms = server_time - local

    def _timestamp(self) -> int:
        return int(time.time() * 1000) + self._time_offset_ms

    @retry(stop=stop_after_attempt(settings.RETRY_MAX),
           wait=wait_exponential_jitter(initial=settings.RETRY_BASE_DELAY, max=8))
    async def klines(self, symbol: str, interval: str, limit: int = 150) -> List[List[Any]]:
        url = f"{self.base}/fapi/v1/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        async with self.session.get(url, params=params, timeout=settings.REQUEST_TIMEOUT) as r:
            if r.status in (429, 418):
                raise RuntimeError(f"binance_rate_limit status={r.status}")
            r.raise_for_status()
            return await r.json()

    @retry(stop=stop_after_attempt(settings.RETRY_MAX),
           wait=wait_exponential_jitter(initial=settings.RETRY_BASE_DELAY, max=8))
    async def ticker_price(self, symbol: str) -> float:
        url = f"{self.base}/fapi/v1/ticker/price"
        params = {"symbol": symbol}
        async with self.session.get(url, params=params, timeout=settings.REQUEST_TIMEOUT) as r:
            if r.status in (429, 418):
                raise RuntimeError(f"binance_rate_limit status={r.status}")
            r.raise_for_status()
            data = await r.json()
            log.info('binance_sync_time_ok', extra={'delta_ms': data.get('serverTime', 0) - int(time.time()*1000), 'status': r.status, 'elapsed_ms': int((time.time()-start)*1000)})
            return float(data["price"])

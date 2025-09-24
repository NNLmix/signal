
import logging
import time
from typing import Any, List, Optional
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from ..config import settings

log = logging.getLogger("binance")

class BinanceClient:
    """Minimal async client for Binance Futures public endpoints used by strategies."""

    def __init__(self, base: str, session: aiohttp.ClientSession):
        self.base = (base or "https://fapi.binance.com").rstrip("/")
        self.session = session

    # --- Public endpoints ---
    @retry(stop=stop_after_attempt(settings.RETRY_MAX), wait=wait_exponential_jitter(initial=settings.RETRY_BASE_DELAY, max=8))
    async def get_klines(self, symbol: str, interval: str, limit: int = 150) -> List[List[Any]]:
        """Compatibility method: worker expects get_klines()."""
        return await self.klines(symbol, interval, limit)

    @retry(stop=stop_after_attempt(settings.RETRY_MAX), wait=wait_exponential_jitter(initial=settings.RETRY_BASE_DELAY, max=8))
    async def klines(self, symbol: str, interval: str, limit: int = 150) -> List[List[Any]]:
        url = f"{self.base}/fapi/v1/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        t0 = time.time()
        async with self.session.get(url, params=params, timeout=getattr(settings, 'REQUEST_TIMEOUT', 10)) as r:
            if r.status in (429, 418):
                # Surface rate limiting to tenacity
                raise RuntimeError(f"binance_rate_limit status={r.status}")
            r.raise_for_status()
            data = await r.json()
            try:
                log.debug("binance_klines_ok", extra={"symbol": symbol, "interval": interval, "limit": limit, "status": r.status, "elapsed_ms": int((time.time()-t0)*1000)})
            except Exception:
                pass
            return data

    @retry(stop=stop_after_attempt(settings.RETRY_MAX), wait=wait_exponential_jitter(initial=settings.RETRY_BASE_DELAY, max=8))
    async def ticker_price(self, symbol: str) -> float:
        url = f"{self.base}/fapi/v1/ticker/price"
        params = {"symbol": symbol}
        t0 = time.time()
        async with self.session.get(url, params=params, timeout=getattr(settings, 'REQUEST_TIMEOUT', 10)) as r:
            r.raise_for_status()
            data = await r.json()
            price = float(data.get("price", 0.0))
            try:
                log.debug("binance_ticker_price_ok", extra={"symbol": symbol, "status": r.status, "elapsed_ms": int((time.time()-t0)*1000), "price": price})
            except Exception:
                pass
            return price

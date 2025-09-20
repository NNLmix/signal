import redis.asyncio as redis
from typing import Any, Dict
from ..config import settings

class RedisClient:
    def __init__(self):
        self.url = settings.REDIS_URL
        kwargs = {"decode_responses": True}
        if self.url.startswith("rediss://"):
            # TLS on
            kwargs["ssl"] = True
            if not settings.REDIS_SSL_VERIFY:
                # Disable certificate verification if requested
                kwargs["ssl_cert_reqs"] = None
        self._kwargs = kwargs
        self.r = redis.from_url(self.url, **kwargs)

    async def ping(self):
        try:
            return await self.r.ping()
        except Exception as e:
            # Optional downgrade to non-TLS if the endpoint isn't actually TLS
            if settings.REDIS_ALLOW_TLS_DOWNGRADE and "record layer failure" in str(e).lower() and self.url.startswith("rediss://"):
                # Retry without TLS
                url2 = "redis://" + self.url[len("rediss://"):]
                self.r = redis.from_url(url2, decode_responses=True)
                return await self.r.ping()
            raise

    async def dedup_try_set(self, key: str, ttl: int) -> bool:
        try:
            res = await self.r.set(key, "1", ex=ttl, nx=True)
            return bool(res)
        except Exception as e:
            # Best-effort: don't crash the worker on Redis errors
            return False

    async def cache_set(self, key: str, value: str, ttl: int = 300):
        try:
            await self.r.set(key, value, ex=ttl)
        except Exception:
            pass

    async def queue_signal(self, payload: dict):
        try:
            await self.r.lpush("signals:outgoing", str(payload))
        except Exception:
            pass

    async def pop_signal(self):
        try:
            return await self.r.rpop("signals:outgoing")
        except Exception:
            return None

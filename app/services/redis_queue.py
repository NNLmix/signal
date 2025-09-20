import redis.asyncio as redis
from typing import Any, Dict
from ..config import settings

class RedisClient:
    def __init__(self):
        self.r = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def ping(self):
        return await self.r.ping()

    async def dedup_try_set(self, key: str, ttl: int) -> bool:
        return await self.r.set(key, "1", ex=ttl, nx=True) is True

    async def cache_set(self, key: str, value: str, ttl: int = 300):
        await self.r.set(key, value, ex=ttl)

    async def queue_signal(self, payload: dict):
        await self.r.lpush("signals:outgoing", str(payload))

    async def pop_signal(self):
        return await self.r.rpop("signals:outgoing")

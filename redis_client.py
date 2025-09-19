import os
import json
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_DEFAULT_TTL = int(os.environ.get("REDIS_DEFAULT_TTL", "3600"))

_redis = None
def _get_redis_sync():
    global _redis
    if _redis:
        return _redis
    try:
        import redis.asyncio as aioredis
    except Exception as e:
        raise RuntimeError("redis.asyncio required but not installed") from e
    _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis

async def close_client():
    global _redis
    if _redis:
        try:
            await _redis.close()
        except Exception:
            logger.exception("Error closing redis client")
        _redis = None

async def is_available() -> bool:
    try:
        client = _get_redis_sync()
        pong = await client.ping()
        return bool(pong)
    except Exception as e:
        logger.exception("redis.is_available.error %s", e)
        return False

async def dedup_try_set(key: str, ttl: int) -> bool:
    try:
        client = _get_redis_sync()
        res = await client.set(key, "1", ex=int(ttl), nx=True)
        return bool(res)
    except Exception as e:
        logger.exception("redis.dedup_try_set.error %s", e)
        return False

async def queue_signal(signal_obj: dict) -> bool:
    try:
        client = _get_redis_sync()
        await client.rpush("signals:queue", json.dumps(signal_obj, default=str))
        return True
    except Exception as e:
        logger.exception("redis.queue_signal.error %s", e)
        return False

async def cache_features(key: str, features: dict, ttl: int = REDIS_DEFAULT_TTL) -> bool:
    try:
        client = _get_redis_sync()
        k = f"features:{key}"
        await client.set(k, json.dumps(features, default=str), ex=int(ttl))
        return True
    except Exception as e:
        logger.exception("redis.cache_features.error %s", e)
        return False

async def get_last_candle_ts(symbol: str, timeframe: str):
    try:
        client = _get_redis_sync()
        v = await client.get(f"last_candle:{symbol}:{timeframe}")
        return int(v) if v else None
    except Exception as e:
        logger.exception("redis.get_last_candle_ts.error %s", e)
        return None

async def set_last_candle_ts(symbol: str, timeframe: str, ts: int):
    try:
        client = _get_redis_sync()
        await client.set(f"last_candle:{symbol}:{timeframe}", int(ts))
    except Exception as e:
        logger.exception("redis.set_last_candle_ts.error %s", e)

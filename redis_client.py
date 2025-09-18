# /app/redis_client.py
"""
Compatibility Redis client helper.

This version expects REDIS_URL to be either redis:// or rediss://.
If rediss:// is used, we pass ssl_cert_reqs=None to redis.from_url(...) to avoid
AbstractConnection.__init__() unexpected 'ssl' kwarg errors in some redis-py versions.
"""

import os
import logging
import json
from typing import Optional, Any, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    import redis
    try:
        from redis import asyncio as redis_asyncio  # type: ignore
    except Exception:
        redis_asyncio = None
except Exception as exc:
    logger.exception("Failed to import redis library. Install redis>=4.0.0")
    raise

# Env
REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_TLS_INSECURE = os.getenv("REDIS_TLS_INSECURE", "0").lower() in ("1", "true", "yes")

_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "2.0"))
_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.5"))
_HEALTH_CHECK_INTERVAL = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))

_client: Optional["redis.Redis"] = None
_logged_once: set = set()

def _needs_tls(url: str) -> bool:
    if not url:
        return False
    return urlparse(url).scheme.lower() == "rediss"

def _build_from_url_kwargs() -> dict:
    return {
        "decode_responses": True,
        "socket_connect_timeout": _SOCKET_CONNECT_TIMEOUT,
        "socket_timeout": _SOCKET_TIMEOUT,
        "health_check_interval": _HEALTH_CHECK_INTERVAL,
    }

def get_redis() -> "redis.Redis":
    global _client
    if _client is not None:
        return _client
    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is not set")
    tls_required = _needs_tls(REDIS_URL)
    kwargs = _build_from_url_kwargs()
    # If TLS required, use ssl_cert_reqs=None to allow TLS without passing 'ssl' kwarg that some versions reject.
    if tls_required:
        kwargs["ssl_cert_reqs"] = None
        if REDIS_TLS_INSECURE:
            # Some redis-py versions accept ssl_cert_reqs=None only; REDIS_TLS_INSECURE kept for compatibility
            logger.warning("REDIS_TLS_INSECURE is set; certificate verification may be skipped depending on client.")
    logger.info("Creating Redis client with url=%s tls=%s", REDIS_URL, tls_required)
    try:
        _client = redis.from_url(REDIS_URL, **kwargs)
        return _client
    except TypeError as exc:
        logger.exception("TypeError creating Redis client: %s. Check redis-py version.", exc)
        raise
    except Exception:
        logger.exception("Unexpected error creating Redis client")
        raise

async def get_async_redis() -> "redis_asyncio.Redis":
    if redis_asyncio is None:
        raise ImportError("redis.asyncio not available; ensure redis-py v4+ is installed")
    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is not set")
    tls_required = _needs_tls(REDIS_URL)
    kwargs = _build_from_url_kwargs()
    if tls_required:
        kwargs["ssl_cert_reqs"] = None
    logger.info("Creating async Redis client with url=%s tls=%s", REDIS_URL, tls_required)
    try:
        r = redis_asyncio.from_url(REDIS_URL, **kwargs)
        return r
    except TypeError as exc:
        logger.exception("TypeError creating async Redis client: %s", exc)
        raise
    except Exception:
        logger.exception("Unexpected error creating async Redis client")
        raise

# Compatibility helpers (queue, cache, dedup etc.)
def is_available() -> bool:
    try:
        r = get_redis()
        return bool(r.ping())
    except Exception as exc:
        logger.debug("Redis is_available() ping failed: %s", exc)
        return False

def queue_len(queue_name: str = "signals") -> int:
    try:
        r = get_redis()
        return int(r.llen(queue_name) or 0)
    except Exception as exc:
        logger.exception("Failed to get queue_len for %s: %s", queue_name, exc)
        return 0

def queue_signal(queue_name: str = "signals", value: Any = None) -> int:
    try:
        r = get_redis()
        payload = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        return int(r.lpush(queue_name, payload))
    except Exception as exc:
        logger.exception("Failed to queue_signal to %s: %s", queue_name, exc)
        return -1

def pop_signal(queue_name: str = "signals", timeout: float = 0.0) -> Optional[str]:
    try:
        r = get_redis()
        if timeout and float(timeout) > 0:
            res = r.brpop(queue_name, timeout=float(timeout))
            if res is None:
                return None
            return res[1] if isinstance(res, (list, tuple)) and len(res) >= 2 else res
        else:
            return r.rpop(queue_name)
    except Exception as exc:
        logger.exception("Failed to pop_signal from %s: %s", queue_name, exc)
        return None

def pop_signals_batch(queue_name: str = "signals", batch: int = 10):
    items = []
    try:
        r = get_redis()
        for _ in range(int(batch)):
            v = r.rpop(queue_name)
            if v is None:
                break
            items.append(v)
        return items
    except Exception as exc:
        logger.exception("pop_signals_batch failed: %s", exc)
        return items

def cache_features(key: str, features: Any, ex: int = 3600) -> bool:
    try:
        r = get_redis()
        payload = features if isinstance(features, str) else json.dumps(features, ensure_ascii=False)
        ok = r.set(name=key, value=payload, ex=int(ex))
        return bool(ok)
    except Exception as exc:
        logger.exception("Failed to cache_features for key=%s: %s", key, exc)
        return False

def get_features(key: str) -> Optional[Any]:
    try:
        r = get_redis()
        val = r.get(key)
        if val is None:
            return None
        if isinstance(val, str) and (val.startswith("{") or val.startswith("[")):
            try:
                return json.loads(val)
            except Exception:
                return val
        return val
    except Exception as exc:
        logger.exception("get_features failed for key=%s: %s", key, exc)
        return None

def dedup_try_set(key: str, ttl_seconds: int = 60) -> bool:
    try:
        r = get_redis()
        ok = r.set(name=key, value="1", nx=True, ex=int(ttl_seconds))
        return bool(ok)
    except Exception as exc:
        logger.exception("dedup_try_set failed for key=%s: %s", key, exc)
        return False

def _host_port_tls() -> Tuple[str, int, bool]:
    if not REDIS_URL:
        raise ValueError("REDIS_URL not set")
    u = urlparse(REDIS_URL)
    host = u.hostname or "localhost"
    port = u.port or (6379 if u.scheme == "redis" else 6380)
    return host, port, _needs_tls(REDIS_URL)

def get_last_candle_ts(key: str = "last_candle_ts") -> Optional[int]:
    try:
        val = get_redis().get(key)
        return int(val) if val is not None else None
    except Exception as exc:
        logger.exception("get_last_candle_ts failed: %s", exc)
        return None

def set_last_candle_ts(ts: int, key: str = "last_candle_ts", ex: int = 3600) -> bool:
    try:
        return bool(get_redis().set(key, str(int(ts)), ex=ex))
    except Exception as exc:
        logger.exception("set_last_candle_ts failed: %s", exc)
        return False

def _log_once(msg: str, level: int = logging.INFO) -> None:
    if msg in _logged_once:
        return
    _logged_once.add(msg)
    logger.log(level, msg)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print("Redis available:", is_available())
    print("Queue length signals:", queue_len("signals"))
    print("Host/Port/TLS:", _host_port_tls())

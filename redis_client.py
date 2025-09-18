# /app/redis_client.py
"""
Redis client helper with compatibility helpers expected by the bot.

Provides:
- get_redis() / get_async_redis()
- is_available()
- queue_len(queue_name="signals")
- queue_signal(queue_name="signals", value)
- cache_features(key, features_dict, ex=3600)
- dedup_try_set(key, ttl_seconds)

TLS handling:
- If REDIS_URL scheme is rediss://, an SSLContext is created and passed to redis.from_url(...)
  (avoids passing boolean ssl flags that may cause AbstractConnection.__init__() errors).
"""

import os
import ssl
import logging
import json
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Try to import redis (redis-py v4+ expected)
try:
    import redis
    try:
        from redis import asyncio as redis_asyncio  # type: ignore
    except Exception:
        redis_asyncio = None
except Exception as exc:
    logger.exception("Failed to import 'redis' library. Ensure 'redis>=4.0.0' is installed.")
    raise

from urllib.parse import urlparse

# Environment variables used by this module
REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_TLS_INSECURE = os.getenv("REDIS_TLS_INSECURE", "0").lower() in ("1", "true", "yes")
REDIS_CA_PATH = os.getenv("REDIS_CA_PATH") or None

_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "2.0"))
_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.5"))
_HEALTH_CHECK_INTERVAL = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))

# Singleton client to reuse connections
_client: Optional["redis.Redis"] = None


def _needs_tls(url: str) -> bool:
    if not url:
        return False
    scheme = urlparse(url).scheme.lower()
    return scheme == "rediss"


def _create_ssl_context(ca_path: Optional[str] = None, insecure: bool = False) -> Optional[ssl.SSLContext]:
    """
    Create and return an SSLContext for TLS-enabled Redis. Returns None if not needed.
    """
    ctx = ssl.create_default_context()

    if ca_path:
        try:
            ctx.load_verify_locations(cafile=ca_path)
            logger.debug("Loaded REDIS_CA_PATH=%s", ca_path)
        except Exception as exc:
            logger.warning("Failed to load REDIS_CA_PATH=%s: %s", ca_path, exc)

    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        logger.warning("REDIS_TLS_INSECURE set: skipping TLS certificate verification (insecure).")

    return ctx


def _build_from_url_kwargs() -> dict:
    return {
        "decode_responses": True,
        "socket_connect_timeout": _SOCKET_CONNECT_TIMEOUT,
        "socket_timeout": _SOCKET_TIMEOUT,
        "health_check_interval": _HEALTH_CHECK_INTERVAL,
    }


def get_redis() -> "redis.Redis":
    """
    Return a synchronous redis.Redis client (singleton). Raises ValueError if REDIS_URL not set.
    """
    global _client
    if _client is not None:
        return _client

    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is not set")

    tls_required = _needs_tls(REDIS_URL)
    ssl_ctx = _create_ssl_context(ca_path=REDIS_CA_PATH, insecure=REDIS_TLS_INSECURE) if tls_required else None

    kwargs = _build_from_url_kwargs()
    if ssl_ctx:
        kwargs["ssl"] = ssl_ctx

    logger.info("Creating Redis (sync) client, url=%s tls=%s", REDIS_URL, tls_required)
    try:
        _client = redis.Redis.from_url(REDIS_URL, **kwargs)
        return _client
    except TypeError as exc:
        logger.exception("TypeError creating Redis client: %s. Check redis-py version (v4+).", exc)
        raise
    except Exception:
        logger.exception("Unexpected error creating Redis client")
        raise


async def get_async_redis() -> "redis_asyncio.Redis":
    """
    Return an asyncio redis client. Requires redis.asyncio to be present (redis-py v4+).
    """
    if redis_asyncio is None:
        raise ImportError("redis.asyncio not available; ensure redis-py v4+ is installed")

    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is not set")

    tls_required = _needs_tls(REDIS_URL)
    ssl_ctx = _create_ssl_context(ca_path=REDIS_CA_PATH, insecure=REDIS_TLS_INSECURE) if tls_required else None

    kwargs = _build_from_url_kwargs()
    if ssl_ctx:
        kwargs["ssl"] = ssl_ctx

    logger.info("Creating Redis (async) client, url=%s tls=%s", REDIS_URL, tls_required)
    try:
        r = redis_asyncio.Redis.from_url(REDIS_URL, **kwargs)
        return r
    except TypeError as exc:
        logger.exception("TypeError creating async Redis client: %s", exc)
        raise
    except Exception:
        logger.exception("Unexpected error creating async Redis client")
        raise


# ------------------------
# Compatibility helper API
# ------------------------

def is_available(timeout: float = 2.0) -> bool:
    """
    Return True if Redis responds to PING, else False. Safe for importing at module load.
    """
    try:
        r = get_redis()
        # Use a short socket timeout override to avoid long blocking
        return bool(r.ping())
    except Exception as exc:
        logger.debug("Redis is_available() ping failed: %s", exc)
        return False


def queue_len(queue_name: str = "signals") -> int:
    """
    Return length of a Redis list (queue). Returns 0 on error.
    """
    try:
        r = get_redis()
        length = r.llen(queue_name)
        return int(length or 0)
    except Exception as exc:
        logger.exception("Failed to get queue_len for %s: %s", queue_name, exc)
        return 0


def queue_signal(queue_name: str = "signals", value: Any = None) -> int:
    """
    Push `value` (any JSON-serializable object) to the given queue (LPUSH).
    Returns new length of the list on success, -1 on error.
    """
    try:
        r = get_redis()
        payload = value
        # If it's not a string, convert to JSON
        if not isinstance(value, str):
            payload = json.dumps(value, ensure_ascii=False)

        length = r.lpush(queue_name, payload)
        logger.debug("Pushed to queue %s; new length=%s", queue_name, length)
        return int(length)
    except Exception as exc:
        logger.exception("Failed to queue_signal to %s: %s", queue_name, exc)
        return -1


def cache_features(key: str, features: Any, ex: int = 3600) -> bool:
    """
    Cache a mapping (or any JSON-serializable object) under the given key.
    Uses SET key value EX ex. Returns True if OK, False on error.
    """
    try:
        r = get_redis()
        payload = features if isinstance(features, str) else json.dumps(features, ensure_ascii=False)
        # Set with expiry
        ok = r.set(name=key, value=payload, ex=int(ex))
        return bool(ok)
    except Exception as exc:
        logger.exception("Failed to cache_features for key=%s: %s", key, exc)
        return False


def dedup_try_set(key: str, ttl_seconds: int = 60) -> bool:
    """
    Try set a deduplication key: return True if the key was set (didn't exist),
    False if it already existed. Uses SET NX EX atomically.
    """
    try:
        r = get_redis()
        # redis-py returns True if set, None/False if not set
        ok = r.set(name=key, value="1", nx=True, ex=int(ttl_seconds))
        return bool(ok)
    except Exception as exc:
        logger.exception("dedup_try_set failed for key=%s: %s", key, exc)
        return False


# If run directly, do a simple ping test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    available = is_available()
    print("Redis available:", available)
    if available:
        print("Queue length (signals):", queue_len("signals"))

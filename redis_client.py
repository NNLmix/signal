# signal/redis_client.py
"""
Redis client helper for the bot.

This module:
- Reads REDIS_URL from env (expects redis:// or rediss://).
- If TLS is required (rediss://) it creates and passes an SSLContext to redis.from_url(...)
  instead of passing boolean ssl flags. This avoids the error:
    AbstractConnection.__init__() got an unexpected keyword argument 'ssl'

Usage:
    from signal.redis_client import get_redis, get_async_redis

    r = get_redis()
    r.ping()

    # async:
    r_async = await get_async_redis()
    await r_async.ping()
"""

import os
import ssl
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try imports for both sync and async clients
try:
    import redis
    # redis.asyncio may be available as part of redis-py v4+
    try:
        from redis import asyncio as redis_asyncio  # type: ignore
    except Exception:
        redis_asyncio = None
except Exception as exc:
    logger.exception("Failed to import redis library. Make sure 'redis>=4.0.0' is installed.")
    raise

from urllib.parse import urlparse

# Environment variables
REDIS_URL = os.getenv("REDIS_URL", "").strip()
# If set to "1", "true", "yes" (case-insensitive) then certificate verification will be skipped.
REDIS_TLS_INSECURE = os.getenv("REDIS_TLS_INSECURE", "0").lower() in ("1", "true", "yes")
# Optional path to CA bundle file (PEM) if you need to use a custom CA.
REDIS_CA_PATH = os.getenv("REDIS_CA_PATH") or None

# Default connection timeouts (seconds)
_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "2.0"))
_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.5"))
_HEALTH_CHECK_INTERVAL = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))

def _create_ssl_context(ca_path: Optional[str] = None, insecure: bool = False) -> Optional[ssl.SSLContext]:
    """
    Create an SSLContext for connecting to a TLS-enabled Redis server.
    Return None if TLS is not needed.
    """
    ctx = ssl.create_default_context()

    if ca_path:
        # Use custom CA bundle
        try:
            ctx.load_verify_locations(cafile=ca_path)
            logger.debug("Loaded custom Redis CA file from %s", ca_path)
        except Exception as exc:
            logger.warning("Failed to load REDIS_CA_PATH=%s: %s", ca_path, exc)

    if insecure:
        # Disable hostname checking and certificate verification (not recommended in production)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        logger.warning("REDIS_TLS_INSECURE is set: TLS certificate verification disabled (insecure).")

    return ctx

def _needs_tls(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    return scheme == "rediss"

def _build_from_url_kwargs() -> dict:
    """Return standardized kwargs for redis.from_url calls."""
    kwargs = {
        "decode_responses": True,
        "socket_connect_timeout": _SOCKET_CONNECT_TIMEOUT,
        "socket_timeout": _SOCKET_TIMEOUT,
        "health_check_interval": _HEALTH_CHECK_INTERVAL,
    }
    return kwargs

def get_redis() -> "redis.Redis":
    """
    Return a synchronous redis.Redis instance connected according to REDIS_URL.

    Raises ValueError if REDIS_URL is not provided.
    """
    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is not set")

    tls_required = _needs_tls(REDIS_URL)
    ssl_ctx = None
    if tls_required:
        ssl_ctx = _create_ssl_context(ca_path=REDIS_CA_PATH, insecure=REDIS_TLS_INSECURE)

    kwargs = _build_from_url_kwargs()

    # If we have an SSLContext, pass it as 'ssl' to redis.from_url()
    if ssl_ctx:
        kwargs["ssl"] = ssl_ctx

    logger.info("Connecting to Redis (sync) url=%s tls=%s", REDIS_URL, tls_required)
    try:
        r = redis.Redis.from_url(REDIS_URL, **kwargs)
        # Optionally validate connection now by pinging in a safe manner.
        # We avoid raising in module import, so do this lazily in callers if desired.
        return r
    except TypeError as exc:
        # More help if redis library version mismatches expected kwargs
        logger.exception(
            "Failed to create Redis client. TypeError: %s. Check your redis library version (redis-py v4+ expected).", exc
        )
        raise
    except Exception:
        logger.exception("Unexpected error while creating Redis client")
        raise

async def get_async_redis() -> "redis_asyncio.Redis":
    """
    Return an asyncio redis client (redis.asyncio.Redis). If redis.asyncio isn't
    available, raises ImportError.

    Usage:
        r = await get_async_redis()
        await r.ping()
    """
    if redis_asyncio is None:
        raise ImportError("redis.asyncio not available; ensure redis-py v4+ is installed")

    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is not set")

    tls_required = _needs_tls(REDIS_URL)
    ssl_ctx = None
    if tls_required:
        ssl_ctx = _create_ssl_context(ca_path=REDIS_CA_PATH, insecure=REDIS_TLS_INSECURE)

    kwargs = _build_from_url_kwargs()

    if ssl_ctx:
        kwargs["ssl"] = ssl_ctx

    logger.info("Connecting to Redis (async) url=%s tls=%s", REDIS_URL, tls_required)
    try:
        r = redis_asyncio.Redis.from_url(REDIS_URL, **kwargs)
        return r
    except TypeError as exc:
        logger.exception(
            "Failed to create async Redis client. TypeError: %s. Check your redis library version (redis-py v4+ expected).", exc
        )
        raise
    except Exception:
        logger.exception("Unexpected error while creating async Redis client")
        raise

# Optional helper: small test function that attempts to PING and returns True/False.
def test_ping_sync() -> bool:
    """Return True if Redis PING succeeds, else False (and log the error)."""
    try:
        r = get_redis()
        pong = r.ping()
        logger.info("Redis PING -> %s", pong)
        return bool(pong)
    except Exception as exc:
        logger.exception("Redis ping failed: %s", exc)
        return False

# If someone runs this module directly, perform a simple ping test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ok = test_ping_sync()
    if ok:
        print("PING -> True")
    else:
        print("PING failed; see logs for details.")

# /app/redis_client.py
"""
Redis client helper with compatibility shims for the bot.

Includes:
- get_redis(), get_async_redis()
- is_available(), queue_len(), queue_signal(), cache_features(), dedup_try_set()
- _host_port_tls()
- get_last_candle_ts(), set_last_candle_ts()
- _log_once()

TLS handling is safe: passes SSLContext when using rediss://.
"""

import os
import ssl
import logging
import json
from typing import Optional, Any, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Redis imports
try:
    import redis
    try:
        from redis import asyncio as redis_asyncio  # type: ignore
    except Exception:
        redis_asyncio = None
except Exception as exc:
    logger.exception("Failed to import redis library. Install redis>=4.0.0")
    raise

# -------------------------
# Environment configuration
# -------------------------
REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_TLS_INSECURE = os.getenv("REDIS_TLS_INSECURE", "0").lower() in ("1", "true", "yes")
REDIS_CA_PATH = os.getenv("REDIS_CA_PATH") or None

_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "2.0"))
_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.5"))
_HEALTH_CHECK_INTERVAL = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))

_client: Optional["redis.Redis"] = None
_logged_once: set[str] = set()

# -----------------
# Internal helpers
# -----------------
def _needs_tls(url: str) -> bool:
    return urlparse(url).scheme.lower() == "rediss"


def _create_ssl_context(ca_path: Optional[str] = None, insecure: bool = False) -> Optional[ssl.SSLContext]:
    ctx = ssl.create_default_context()
    if ca_path:
        try:
            ctx.load_verify_locations(cafile=ca_path)
        except Exception as exc:
            logger.warning("Failed to load REDIS_CA_PATH=%s: %s", ca_path, exc)
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        logger.warning("TLS insecure mode enabled: certificates will not be verified")
    return ctx


def _build_from_url_kwargs() -> dict:
    return {
        "decode_responses": True,
        "socket_connect_timeout": _SOCKET_CONNECT_TIMEOUT,
        "socket_timeout": _SOCKET_TIMEOUT,
        "health_check_interval": _HEALTH_CHECK_INTERVAL,
    }


# -----------------
# Public API
# -----------------
def get_redis() -> "redis.Redis":
    global _client
    if _client:
        return _client
    if not REDIS_URL:
        raise ValueError("REDIS_URL not set")
    tls_required = _needs_tls(REDIS_URL)
    ssl_ctx = _create_ssl_context(REDIS_CA_PATH, REDIS_TLS_INSECURE) if tls_required else None
    kwargs = _build_from_url_kwargs()
    if ssl_ctx:
        kwargs["ssl"] = ssl_ctx
    _client = redis.Redis.from_url(REDIS_URL, **kwargs)
    return _client


async def get_async_redis() -> "redis_asyncio.Redis":
    if redis_asyncio is None:
        raise ImportError("redis.asyncio not available (need redis>=4.0.0)")
    if not REDIS_URL:
        raise ValueError("REDIS_URL not set")
    tls_required = _needs_tls(REDIS_URL)
    ssl_ctx = _create_ssl_context(REDIS_CA_PATH, REDIS_TLS_INSECURE) if tls_required else None
    kwargs = _build_from_url_kwargs()
    if ssl_ctx:
        kwargs["ssl"] = ssl_ctx
    return redis_asyncio.Redis.from_url(REDIS_URL, **kwargs)


def is_available() -> bool:
    try:
        r = get_redis()
        return bool(r.ping())
    except Exception:
        return False


def queue_len(queue_name: str = "signals") -> int:
    try:
        return int(get_redis().llen(queue_name) or 0)
    except Exception:
        return 0


def queue_signal(queue_name: str = "signals", value: Any = None) -> int:
    try:
        payload = value if isinstance(value, str) else json.dumps(value)
        return int(get_redis().lpush(queue_name, payload))
    except Exception:
        return -1


def cache_features(key: str, features: Any, ex: int = 3600) -> bool:
    try:
        payload = features if isinstance(features, str) else json.dumps(features)
        return bool(get_redis().set(key, payload, ex=ex))
    except Exception:
        return False


def dedup_try_set(key: str, ttl_seconds: int = 60) -> bool:
    try:
        return bool(get_redis().set(key, "1", nx=True, ex=ttl_seconds))
    except Exception:
        return False


# -----------------
# Extra shims
# -----------------
def _host_port_tls() -> Tuple[str, int, bool]:
    """
    Return (host, port, tls_enabled) parsed from REDIS_URL.
    """
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
    except Exception:
        return None


def set_last_candle_ts(ts: int, key: str = "last_candle_ts", ex: int = 3600) -> bool:
    try:
        return bool(get_redis().set(key, str(int(ts)), ex=ex))
    except Exception:
        return False


def _log_once(msg: str, level: int = logging.INFO) -> None:
    if msg in _logged_once:
        return
    _logged_once.add(msg)
    logger.log(level, msg)


# -----------------
# CLI test
# -----------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print("Redis available:", is_available())
    print("Queue length signals:", queue_len("signals"))
    print("Host/Port/TLS:", _host_port_tls())

# /app/redis_client.py
"""
Redis client helper with compatibility shims for the bot.

Provides:
- get_redis(), get_async_redis()
- is_available(), queue_len(), queue_signal(), pop_signal(), pop_signals_batch()
- cache_features(), get_features()
- dedup_try_set()
- _host_port_tls(), get_last_candle_ts(), set_last_candle_ts(), _log_once()

TLS handling:
- If REDIS_URL scheme is rediss://, an SSLContext is created and passed to redis.from_url(...)
  (avoids passing boolean ssl flags that may cause AbstractConnection.__init__() errors).
"""

import os
import ssl
import logging
import json
from typing import Optional, Any, Tuple, List
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
_logged_once: set = set()

# -----------------
# Internal helpers
# -----------------
def _needs_tls(url: str) -> bool:
    if not url:
        return False
    return urlparse(url).scheme.lower() == "rediss"


def _create_ssl_context(ca_path: Optional[str] = None, insecure: bool = False) -> Optional[ssl.SSLContext]:
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


# -----------------
# Redis client APIs
# -----------------
def get_redis() -> "redis.Redis":
    """
    Return a synchronous redis.Redis client (singleton).
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
# Compatibility helpers
# ------------------------
def is_available() -> bool:
    """Return True if Redis responds to PING, else False."""
    try:
        r = get_redis()
        return bool(r.ping())
    except Exception as exc:
        logger.debug("Redis is_available() ping failed: %s", exc)
        return False


def queue_len(queue_name: str = "signals") -> int:
    """Return length of a Redis list (queue)."""
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
    Returns new length on success, -1 on error.
    """
    try:
        r = get_redis()
        payload = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        return int(r.lpush(queue_name, payload))
    except Exception as exc:
        logger.exception("Failed to queue_signal to %s: %s", queue_name, exc)
        return -1


def pop_signal(queue_name: str = "signals", timeout: float = 0.0) -> Optional[str]:
    """
    Pop a single signal from the tail (RPOP). If timeout > 0, use BRPOP with that timeout (seconds).
    Returns string payload or None.
    """
    try:
        r = get_redis()
        if timeout and float(timeout) > 0:
            # BRPOP returns (queue_name, value) on success
            res = r.brpop(queue_name, timeout=float(timeout))
            if res is None:
                return None
            # res may be a tuple (key, value) when decode_responses=True
            # ensure we return the value part
            return res[1] if isinstance(res, (list, tuple)) and len(res) >= 2 else res
        else:
            return r.rpop(queue_name)
    except Exception as exc:
        logger.exception("Failed to pop_signal from %s: %s", queue_name, exc)
        return None


def pop_signals_batch(queue_name: str = "signals", batch: int = 10) -> List[str]:
    """
    Pop up to `batch` items from the queue using a non-blocking approach.
    Returns list of payloads (may be empty).
    """
    items: List[str] = []
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
    """Cache a mapping (or any JSON-serializable object) under the given key."""
    try:
        r = get_redis()
        payload = features if isinstance(features, str) else json.dumps(features, ensure_ascii=False)
        ok = r.set(name=key, value=payload, ex=int(ex))
        return bool(ok)
    except Exception as exc:
        logger.exception("Failed to cache_features for key=%s: %s", key, exc)
        return False


def get_features(key: str) -> Optional[Any]:
    """
    Retrieve features previously cached with cache_features(). Returns parsed JSON or raw string, or None.
    """
    try:
        r = get_redis()
        val = r.get(key)
        if val is None:
            return None
        # Try JSON parse if it looks like JSON
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
    """Try set a deduplication key: return True if the key was set (didn't exist)."""
    try:
        r = get_redis()
        ok = r.set(name=key, value="1", nx=True, ex=int(ttl_seconds))
        return bool(ok)
    except Exception as exc:
        logger.exception("dedup_try_set failed for key=%s: %s", key, exc)
        return False


# -----------------
# Extra shims
# -----------------
def _host_port_tls() -> Tuple[str, int, bool]:
    """Return (host, port, tls_enabled) parsed from REDIS_URL."""
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


# -----------------
# CLI test
# -----------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print("Redis available:", is_available())
    print("Queue length signals:", queue_len("signals"))
    print("Host/Port/TLS:", _host_port_tls())

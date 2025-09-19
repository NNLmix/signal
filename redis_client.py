# redis_client.py - enhanced status checking and logging
import logging
import os
import asyncio
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL")

def _host_port_tls_from_url(url):
    if not url:
        return ("unknown", 0, False)
    try:
        p = urlparse(url)
        host = p.hostname or "unknown"
        port = p.port or 0
        tls = p.scheme.startswith("rediss")
        return (host, port, tls)
    except Exception as e:
        logger.exception("redis.url.parse.error %s", e)
        return ("unknown", 0, False)

async def check_redis(timeout: float = 2.0):
    """Return a dict with detailed Redis connectivity info:
    { available: bool, host, port, tls, error: optional string }
    This function logs exceptions with stack traces for diagnosis.
    """
    host, port, tls = _host_port_tls_from_url(REDIS_URL)
    info = {"available": False, "host": host, "port": port, "tls": tls, "error": None}
    try:
        # Try using redis.asyncio if available
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(REDIS_URL, socket_connect_timeout=timeout, socket_timeout=timeout)
            # attempt a PING
            pong = await client.ping()
            if pong is True or pong == b'PONG':
                info["available"] = True
            await client.close()
        except Exception as e:
            # Fallback: attempt a simple TCP connect to the host:port
            import socket
            logger.exception("redis.asyncio.ping.failed %s", e)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            try:
                s.connect((host, port))
                info["available"] = True
            except Exception as e2:
                logger.exception("redis.socket.connect.failed %s", e2)
                info["error"] = f"connect_error: {str(e2)}"
            finally:
                try:
                    s.close()
                except Exception:
                    pass
    except Exception as e:
        logger.exception("redis.check.unexpected %s", e)
        info["error"] = str(e)
    return info

# convenience wrappers for existing call sites (backwards compatible)
async def is_available():
    info = await check_redis()
    return info["available"]

async def queue_len():
    # best-effort: try to get length of queue key if redis reachable; return -1 on error
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(REDIS_URL)
        # assume queue key name "signals:queue" - adjust if your code uses different key
        qlen = await client.llen('signals:queue')
        await client.close()
        return qlen
    except Exception as e:
        logger.exception('queue_len.error %s', e)
        return -1

def _host_port_tls():
    return _host_port_tls_from_url(REDIS_URL)

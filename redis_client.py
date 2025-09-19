# redis_client.py - enhanced status checking and logging
import logging
import os
import asyncio
import ssl
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
    """
    Return a dict with detailed Redis connectivity info:
    {
        available: bool,
        host,
        port,
        tls,
        error: optional string
    }
    This function logs exceptions with stack traces for diagnosis.
    """
    # Ensure TLS scheme if missing
    url = REDIS_URL
    if url and url.startswith("redis://"):
        url = url.replace("redis://", "rediss://", 1)

    host, port, tls = _host_port_tls_from_url(url)
    info = {"available": False, "host": host, "port": port, "tls": tls, "error": None}

    try:
        import redis.asyncio as aioredis

        ssl_context = None
        if tls:
            ssl_context = ssl.create_default_context()

        client = aioredis.from_url(
            url,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
            ssl=tls,
            ssl_context=ssl_context,
            decode_responses=True,
        )

        pong = await client.ping()
        if pong is True or pong == b"PONG":
            info["available"] = True
        await client.close()

    except Exception as e:
        # Fallback: attempt a simple TCP connect to the host:port
        import socket

        logger.exception("redis.asyncio.ping.failed %s", e)
        info["error"] = str(e)
        try:
            with socket.create_connection((host, port), timeout=timeout):
                pass
        except Exception as se:
            logger.exception("redis.tcp.connect.failed %s", se)
            if not info["error"]:
                info["error"] = str(se)

    return info


if __name__ == "__main__":
    async def main():
        result = await check_redis()
        print(result)

    asyncio.run(main())
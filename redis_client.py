"""
redis_client.py - lightweight TCP connectivity checker for Redis/Rediss URLs.
Does not depend on redis library; suitable for diagnostics.
"""
import os, asyncio, ssl, logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
REDIS_URL = os.environ.get("REDIS_URL", "")

def _host_port_tls_from_url(url):
    if not url:
        return ("", 0, False)
    p = urlparse(url)
    host = p.hostname or ""
    port = p.port or (6380 if p.scheme == "rediss" else 6379)
    tls = p.scheme == "rediss"
    return host, port, tls

async def check_redis(timeout=3.0):
    host, port, tls = _host_port_tls_from_url(REDIS_URL)
    info = {"available": False, "host": host, "port": port, "tls": tls, "error": ""}
    if not host:
        info["error"] = "missing REDIS_URL"
        return info
    try:
        if tls:
            sslctx = ssl.create_default_context()
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port, ssl=sslctx), timeout=timeout)
        else:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        # minimal check: send Redis PING using RESP protocol and read reply
        writer.write(b"*1\r\n$4\r\nPING\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(100), timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        data = data.decode(errors='ignore') if data else ""
        if "+PONG" in data or "PONG" in data:
            info["available"] = True
        else:
            info["error"] = f"unexpected_reply:{data[:200]}"
    except Exception as e:
        logger.warning("redis.check failed %s", e)
        info["error"] = str(e)
    return info

if __name__ == "__main__":
    import asyncio
    print(asyncio.run(check_redis()))

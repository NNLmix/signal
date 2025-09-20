"""Lightweight Redis connectivity checker that supports redis:// and rediss:// URLs.
Uses asyncio.open_connection and enables TLS when scheme is rediss.
Returns a dict with keys: available (bool), host, port, tls (bool), error (str).
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
    tls = (p.scheme == "rediss")
    return (host, port, tls)

async def check_redis(timeout=5):
    info = {"available": False, "host": "", "port": None, "tls": False, "error": ""}
    host, port, tls = _host_port_tls_from_url(REDIS_URL)
    info.update({"host": host, "port": port, "tls": tls})
    if not host:
        info["error"] = "no redis url provided"
        return info
    try:
        ssl_context = None
        if tls:
            # create SSL context that does not verify certificates by default to avoid cert issues
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host=host, port=port, ssl=ssl_context),
            timeout=timeout
        )
        try:
            # Send simple PING in Redis RESP: *1\r\n$4\r\nPING\r\n
            writer.write(b"*1\r\n$4\r\nPING\r\n")
            await writer.drain()
            data = await asyncio.wait_for(reader.read(1024), timeout=timeout)
            data = data.decode(errors='ignore') if data else ""
            if "PONG" in data or "+PONG" in data:
                info["available"] = True
            else:
                info["error"] = f"unexpected_reply:{data[:200]}"
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
    except Exception as e:
        logger.warning("redis.check failed %s", e)
        info["error"] = str(e)
    return info

if __name__ == "__main__":
    import asyncio, logging
    logging.basicConfig(level=logging.DEBUG)
    print(asyncio.run(check_redis()))
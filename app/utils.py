import aiohttp
import asyncio
import logging

log = logging.getLogger("utils")

PUBLIC_IP_ENDPOINTS = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "http://checkip.amazonaws.com",
]

async def get_public_ip(timeout: float = 4.0) -> str | None:
    for url in PUBLIC_IP_ENDPOINTS:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=timeout) as r:
                    txt = (await r.text()).strip()
                    if txt and len(txt) <= 64 and all(ch in "0123456789abcdefABCDEF:." for ch in txt):
                        log.info("public_ip_detected", extra={"ip": txt, "source": url})
                        return txt
                    else:
                        log.warning("public_ip_unexpected_response", extra={"source": url, "sample": txt[:64]})
        except Exception as e:
            log.warning("public_ip_fetch_error", extra={"source": url, "error": str(e)})
    return None

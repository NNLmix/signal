import asyncio
import aiohttp
import logging
from typing import Dict, Any
from .config import settings
from .services.binance import BinanceClient
from .services.redis_queue import RedisClient

log = logging.getLogger("startup.health")

async def check_binance(session: aiohttp.ClientSession) -> Dict[str, Any]:
    client = BinanceClient(settings.BINANCE_BASE, session)
    try:
        await client.sync_time()
        # lightweight call: request 1 recent kline for BTCUSDT 1m to verify data path
        kl = await client.klines("BTCUSDT", "1m", limit=1)
        return {"ok": True, "endpoint": settings.BINANCE_BASE, "klines_ok": bool(kl)}
    except Exception as e:
        return {"ok": False, "endpoint": settings.BINANCE_BASE, "error": str(e)}

async def check_supabase(session: aiohttp.ClientSession) -> Dict[str, Any]:
    # Try a harmless GET to /rest/v1/ which should return 404/401 but proves reachability + auth header usage
    url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_KEY,
    }
    try:
        async with session.get(url, headers=headers, timeout=10) as r:
            # Consider anything under 500 as "reachable"
            ok = r.status < 500
            text = await r.text()
            return {"ok": ok, "status": r.status, "url": url, "note": "reachable" if ok else text[:200]}
    except Exception as e:
        return {"ok": False, "url": url, "error": str(e)}

async def check_redis() -> Dict[str, Any]:
    try:
        r = RedisClient()
        pong = await r.ping()
        return {"ok": bool(pong)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

async def run_startup_checks():
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            check_binance(session),
            check_supabase(session),
            check_redis(),
            return_exceptions=False
        )
    binance_res, supabase_res, redis_res = results
    log.info("startup_health", extra={"binance": binance_res, "supabase": supabase_res, "redis": redis_res, "redis_url_scheme": "rediss" if settings.REDIS_URL.startswith("rediss://") else "redis", "redis_ssl_verify": settings.REDIS_SSL_VERIFY, "redis_tls_downgrade": settings.REDIS_ALLOW_TLS_DOWNGRADE})
    return {"binance": binance_res, "supabase": supabase_res, "redis": redis_res}

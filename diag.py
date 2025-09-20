"""
diag.py - provide diagnostics for services: Binance, Redis, Supabase, Telegram token presence.
"""
import logging
import asyncio
import aiohttp
from typing import Dict, Any
from config import SUPABASE_URL, SUPABASE_ANON_KEY, TELEGRAM_BOT_TOKEN
from binance_client import ping, server_time
from redis_client import check_redis

logger = logging.getLogger(__name__)

async def check_supabase():
    info = {"available": False, "status": None}
    if not SUPABASE_URL:
        info["error"] = "missing SUPABASE_URL"
        return info
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(SUPABASE_URL, headers={"apikey": SUPABASE_ANON_KEY}) as resp:
                info["status"] = resp.status
                info["available"] = resp.status < 400
    except Exception as e:
        info["error"] = str(e)
    return info

async def gather_diag() -> Dict[str, Any]:
    diagnostics = {}
    # Binance
    try:
        ping_res = await ping()
        time_res = await server_time()
        diagnostics["binance"] = {"ping": ping_res, "time": time_res}
    except Exception as e:
        diagnostics["binance"] = {"error": str(e)}

    # Redis
    try:
        redis_res = await check_redis()
        diagnostics["redis"] = redis_res
    except Exception as e:
        diagnostics["redis"] = {"available": False, "error": str(e)}

    # Supabase
    diagnostics["supabase"] = await check_supabase()

    # Telegram token presence (we do not display the token)
    diagnostics["telegram_token_present"] = bool(TELEGRAM_BOT_TOKEN)

    # Build pretty text
    lines = []
    b = diagnostics.get("binance", {})
    if "error" in b:
        lines.append(f"Binance: error - {b['error']}")
    else:
        ping_ok = b.get("ping", {}).get("ok")
        st = b.get("time", {}).get("data")
        lines.append(f"Binance ping OK: {bool(ping_ok)}; server_time: {st}")

    r = diagnostics.get("redis", {})
    lines.append(f"Redis available: {r.get('available', False)}; host: {r.get('host')}:{r.get('port')}; tls: {r.get('tls')}; err: {r.get('error','')[:200]}")

    s = diagnostics.get("supabase", {})
    lines.append(f"Supabase reachable: {s.get('available', False)}; status: {s.get('status')}; err: {s.get('error','')[:200]}")

    lines.append(f"Telegram token present: {diagnostics.get('telegram_token_present')}")

    diagnostics['pretty'] = "\n".join(lines)
    logger.info("diag summary: %s", diagnostics.get('pretty'))
    return diagnostics

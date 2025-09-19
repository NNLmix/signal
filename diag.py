# diag.py - patched v3: produce concise human-readable status lines and include Redis error details
import logging
import aiohttp
from typing import Dict, Any

logger = logging.getLogger(__name__)

# robust imports
try:
    from .redis_client import check_redis, _host_port_tls
except Exception:
    try:
        from redis_client import check_redis, _host_port_tls
    except Exception:
        async def check_redis():
            return {"available": False, "host": "unknown", "port": 0, "tls": False, "error": "redis client import failed"}
        def _host_port_tls():
            return ("unknown", 0, False)

# config import (robust)
TELEGRAM_BOT_TOKEN = None
SUPABASE_URL = None
SUPABASE_ANON_KEY = None
SUPABASE_SIGNALS_TABLE = "signals"
SUPABASE_TIMEOUT = 5
try:
    from .config import TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SIGNALS_TABLE, SUPABASE_TIMEOUT
except Exception:
    try:
        import config as _cfg
        TELEGRAM_BOT_TOKEN = getattr(_cfg, 'TELEGRAM_BOT_TOKEN', TELEGRAM_BOT_TOKEN)
        SUPABASE_URL = getattr(_cfg, 'SUPABASE_URL', SUPABASE_URL)
        SUPABASE_ANON_KEY = getattr(_cfg, 'SUPABASE_ANON_KEY', SUPABASE_ANON_KEY)
        SUPABASE_SIGNALS_TABLE = getattr(_cfg, 'SUPABASE_SIGNALS_TABLE', SUPABASE_SIGNALS_TABLE)
        SUPABASE_TIMEOUT = getattr(_cfg, 'SUPABASE_TIMEOUT', SUPABASE_TIMEOUT)
    except Exception:
        pass

_SUPABASE_HEADERS = {
    "apikey": SUPABASE_ANON_KEY or "",
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}" if SUPABASE_ANON_KEY else "",
    "Content-Type": "application/json",
}

async def _check_supabase() -> Dict[str, Any]:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return {"status": "not_configured", "details": "SUPABASE_URL or SUPABASE_ANON_KEY not set"}
    url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_SIGNALS_TABLE}"
    params = {"select": "id", "limit": 1}
    try:
        timeout = aiohttp.ClientTimeout(total=SUPABASE_TIMEOUT or 5)
        async with aiohttp.ClientSession(headers=_SUPABASE_HEADERS, timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                text = await resp.text()
                if 200 <= resp.status < 300:
                    return {"status": "ok", "code": resp.status, "details": "table reachable"}
                else:
                    return {"status": "error", "code": resp.status, "details": text[:500]}
    except Exception as e:
        logger.exception("supabase.check.error %s", e)
        return {"status": "error", "details": str(e)}

async def gather_diag() -> Dict[str, Any]:
    """Return a dict with both 'pretty' (human string) and 'raw' details for programmatic use."""
    diagnostics = {}
    # Supabase
    supa = await _check_supabase()
    diagnostics['supabase_raw'] = supa
    supa_status = "OK" if supa.get("status") == "ok" else "Unreachable"

    # Redis
    rinfo = await check_redis()
    diagnostics['redis_raw'] = rinfo
    if rinfo.get("available"):
        redis_status = "OK"
        redis_detail = ""
    else:
        redis_status = "Unreachable"
        err = rinfo.get("error") or "no_detail"
        # keep a short error message
        redis_detail = f": {err[:200]}"

    # Telegram
    tg_status = "OK" if TELEGRAM_BOT_TOKEN else "Missing"

    # Build pretty multiline text as requested
    lines = [
        f"Supabase: {supa_status}",
        f"Redis: {redis_status}{redis_detail}",
        f"Telegram: {tg_status}",
    ]
    pretty = "\n".join(lines)
    diagnostics['pretty'] = pretty
    # also log detailed structured info
    logger.info("diag: supabase=%s redis_available=%s redis_err=%s telegram=%s", supa.get('status'), rinfo.get('available'), rinfo.get('error'), bool(TELEGRAM_BOT_TOKEN))
    return diagnostics

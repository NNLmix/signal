# diag.py - patched v2: robust imports to avoid 'signal' stdlib conflict
import logging
import asyncio
import aiohttp
from typing import Dict, Any

# Robust import of config and redis helpers: try relative import first (package), fallback to top-level module.
try:
    # when package installed or running as module (preferred)
    from .redis_client import is_available as redis_ok, queue_len, _host_port_tls
except Exception:
    try:
        from redis_client import is_available as redis_ok, queue_len, _host_port_tls
    except Exception:
        async def redis_ok(): return False
        async def queue_len(): return 0
        def _host_port_tls(): return ("unknown", 0, False)

# attempt to import config values with both relative and absolute imports to avoid 'signal' stdlib collisions
SUPABASE_URL = None
SUPABASE_ANON_KEY = None
SUPABASE_SIGNALS_TABLE = "signals"
SUPABASE_TIMEOUT = 5
TELEGRAM_BOT_TOKEN = None

try:
    # preferred when package layout is used
    from .config import TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SIGNALS_TABLE, SUPABASE_TIMEOUT
except Exception:
    try:
        # fallback to top-level module import
        import config as _cfg
        TELEGRAM_BOT_TOKEN = getattr(_cfg, "TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
        SUPABASE_URL = getattr(_cfg, "SUPABASE_URL", SUPABASE_URL)
        SUPABASE_ANON_KEY = getattr(_cfg, "SUPABASE_ANON_KEY", SUPABASE_ANON_KEY)
        SUPABASE_SIGNALS_TABLE = getattr(_cfg, "SUPABASE_SIGNALS_TABLE", SUPABASE_SIGNALS_TABLE)
        SUPABASE_TIMEOUT = getattr(_cfg, "SUPABASE_TIMEOUT", SUPABASE_TIMEOUT)
    except Exception:
        # leave defaults if nothing available
        pass

logger = logging.getLogger(__name__)

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
                    return {"status": "ok", "code": resp.status, "details": "table reachable", "sample": text[:500]}
                else:
                    return {"status": "error", "code": resp.status, "details": text[:500]}
    except Exception as e:
        logger.exception("supabase.check.error %s", e)
        return {"status": "error", "details": str(e)}

async def gather_diag() -> Dict[str, Any]:
    diagnostics: Dict[str, Any] = {}

    host, port, tls = _host_port_tls()
    redis_status = await redis_ok()
    qlen = await queue_len()
    diagnostics["redis"] = {
        "host": host,
        "port": port,
        "tls": tls,
        "available": bool(redis_status),
        "queue_len": qlen,
    }

    supa = await _check_supabase()
    diagnostics["supabase"] = supa

    diagnostics["telegram"] = {
        "token_set": bool(TELEGRAM_BOT_TOKEN),
        "status": "configured" if TELEGRAM_BOT_TOKEN else "missing token",
    }

    diagnostics["processor"] = {"status": "running"}

    pretty_lines = [
        "==== Service Diagnostics ====",
        f"Redis: host={host}, port={port}, tls={tls}, available={redis_status}, queue_len={qlen}",
        f"Supabase: status={supa.get('status')}, code={supa.get('code','')}, detail={supa.get('details','')}",
        f"Telegram: {'configured' if TELEGRAM_BOT_TOKEN else 'missing token'}",
        f"Processor: running",
    ]
    pretty_text = "\n".join(pretty_lines)
    diagnostics["pretty"] = pretty_text
    logger.info(pretty_text)
    return diagnostics

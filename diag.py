import logging
logger = logging.getLogger(__name__)

async def gather_diag() -> dict:
    diagnostics = {}
    try:
        from .config import SUPABASE_URL, SUPABASE_ANON_KEY, TELEGRAM_BOT_TOKEN
    except Exception:
        SUPABASE_URL = SUPABASE_ANON_KEY = TELEGRAM_BOT_TOKEN = None

    supa_ok = bool(SUPABASE_URL and SUPABASE_ANON_KEY)
    diagnostics['supabase'] = {"url_set": bool(SUPABASE_URL), "key_set": bool(SUPABASE_ANON_KEY)}
    try:
        from .redis_client import is_available as redis_is_available
        redis_ok = await redis_is_available()
    except Exception:
        redis_ok = False
    diagnostics['redis'] = {"available": redis_ok}
    diagnostics['telegram'] = {"token_set": bool(TELEGRAM_BOT_TOKEN)}
    pretty = (
        f"Supabase: {'OK' if supa_ok else 'Missing/Invalid'}\n"
        f"Redis: {'OK' if redis_ok else 'Unavailable'}\n"
        f"Telegram: {'OK' if TELEGRAM_BOT_TOKEN else 'Missing'}"
    )
    diagnostics['pretty'] = pretty
    logger.info("diag: supabase=%s redis_available=%s telegram_token_set=%s", supa_ok, redis_ok, bool(TELEGRAM_BOT_TOKEN))
    return diagnostics

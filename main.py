import aiohttp
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

stop_event = asyncio.Event()
worker_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP TEST & LOGGING ---
    log.info("startup_begin", extra={"env_log_level": os.getenv("LOG_LEVEL", "INFO")})
    # Explicit one-off test message independent of strategies
    try:
        from app.config import settings  # type: ignore
        from app.telegram import send_message  # optional helper if exists
    except Exception:
        settings = None

    async def _send_test_message(session):
        chat_id = None
        try:
            if settings:
                chat_id = settings.TELEGRAM_CHAT_ID
        except Exception:
            pass
        # Fallback to env
        if not chat_id:
            chat_id = os.getenv("TELEGRAM_CHAT_ID")

        token = None
        try:
            if settings:
                token = settings.TELEGRAM_BOT_TOKEN
        except Exception:
            pass
        if not token:
            token = os.getenv("TELEGRAM_BOT_TOKEN")

        if not (chat_id and token):
            log.warning("test_message_skip_no_creds")
            return

        # Dedup via Redis if available
        sent_once = False
        try:
            from app.services.redis_queue import RedisClient  # type: ignore
            rc = RedisClient()
            if await rc.try_set("test:startup:sent", ttl=24*3600):
                sent_once = True
        except Exception:
            # If Redis not available, default to sending once per process
            if not hasattr(_send_test_message, "_did"):
                _send_test_message._did = True  # type: ignore
                sent_once = True

        if not sent_once:
            log.info("test_message_already_sent_recently")
            return

        # Fetch current BTC price directly from Binance public endpoint
        price = None
        try:
            url = (os.getenv("BINANCE_BASE") or "https://fapi.binance.com").rstrip("/") + "/fapi/v1/ticker/price?symbol=BTCUSDT"
            async with session.get(url, timeout=5) as r:
                data = await r.json()
                price = data.get("price")
        except Exception as e:
            log.warning("binance_price_fetch_failed", extra={"error": str(e)})

        text = f"🚀 Bot startup OK. BTCUSDT price: {price or 'n/a'}"
        # Use Telegram HTTP API directly to avoid depending on internal helpers
        try:
            tg_url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            async with session.post(tg_url, json=payload, timeout=10) as r:
                ok = r.status
                resp = await r.text()
                log.info("test_message_sent", extra={"status": ok, "resp": resp[:200]})
        except Exception as e:
            log.error("test_message_failed", extra={"error": str(e)})
    # --- END STARTUP TEST ---

    # Initialize logging if available
    try:
        setup_logging(settings.LOG_LEVEL)  # type: ignore[name-defined]
    except Exception:
        logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('startup')

    # Optional diagnostics
    try:
        ip = await get_public_ip()  # type: ignore[name-defined]
        if ip: log.info(f'public_ip={ip}')
    except Exception:
        pass

    # If using Telegram, ensure webhook is disabled (polling-free sender)
    try:
        await bot.delete_webhook(drop_pending_updates=True)  # type: ignore[name-defined]
    except Exception:
        pass

    # Start background worker if present
    global worker_task
    try:
        worker_task = asyncio.create_task(run_worker(stop_event))
    # fire-and-forget startup test message
    try:
        session = aiohttp.ClientSession()
        asyncio.create_task(_send_test_message(session))
    except Exception:
        pass  # type: ignore[name-defined]
    except Exception:
        worker_task = None

    try:
        yield
    finally:
        stop_event.set()
        if worker_task:
            try:
                await worker_task
            except Exception:
                pass
        try:
            await bot.session.close()  # type: ignore[attr-defined]
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

@app.get('/healthz')
async def healthz():
    return {'status': 'ok'}

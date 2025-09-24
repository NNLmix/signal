import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

def _env_true(name: str) -> bool:
    v = os.getenv(name, '')
    return v.strip().lower() in ('1','true','yes','on')


# Optional imports guarded to avoid ImportError at import time
try:
    from app.api import app as api_app  # type: ignore
except Exception:
    api_app = None
try:
    from app.telegram import bot  # type: ignore
except Exception:
    bot = None
try:
    from app.config import settings  # type: ignore
except Exception:
    settings = None
try:
    from app.logging import setup_logging  # type: ignore
except Exception:
    setup_logging = None
try:
    from app.utils import get_public_ip  # type: ignore
except Exception:
    async def get_public_ip():
        return None
try:
    from app.worker import run_worker  # type: ignore
except Exception:
    async def run_worker(stop_event: asyncio.Event):
        # Minimal no-op worker so app can still boot
        log = logging.getLogger("worker")
        log.info("worker_boot (fallback)")
        while not stop_event.is_set():
            await asyncio.sleep(5)

stop_event: asyncio.Event | None = None
worker_task: asyncio.Task | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging
    if setup_logging and settings is not None:
        try:
            setup_logging(getattr(settings, "LOG_LEVEL", "INFO"))
        except Exception:
            logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)

    log = logging.getLogger("startup")
    log.info("startup_begin", extra={"env_log_level": os.getenv("LOG_LEVEL", "INFO")})

    # Log public IP (best effort)
    try:
        ip = await get_public_ip()
        if ip:
            log.info("public_ip", extra={"ip": ip})
    except Exception:
        pass

    # Ensure Telegram webhook is disabled (we're not receiving updates)
    if bot is not None:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass

    # Start background worker
    global stop_event, worker_task
    stop_event = asyncio.Event()
    try:
        worker_task = asyncio.create_task(run_worker(stop_event))
    except Exception as e:
        log.error("worker_start_failed", extra={"error": str(e)})
        worker_task = None

    # Fire-and-forget startup test message (independent of strategies)
    try:
        import aiohttp

        async def _send_test_message():
            chat_id = None
            token = None
            # Prefer settings if available
            try:
                if settings:
                    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)
                    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
            except Exception:
                pass
            # Fallback to env
            chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
            token = token or os.getenv("TELEGRAM_BOT_TOKEN")
            if not (chat_id and token):
                log.warning("test_message_skip_no_creds")
                return

            # Deduplicate via Redis if available, but bypass if TEST_SIGNAL_ENABLED=true
            should_send = True
            if not _env_true("TEST_SIGNAL_ENABLED"):
                try:
                    from app.services.redis_queue import RedisClient  # type: ignore
                    rc = RedisClient()
                    if not await rc.try_set("test:startup:sent", ttl=24*3600):
                        should_send = False
                except Exception:
                    # If Redis not available, send once per process
                    if hasattr(_send_test_message, "_did"):
                        should_send = False
                    else:
                        _send_test_message._did = True  # type: ignore

            if not should_send:
                log.info("test_message_already_sent_recently")
                return

            price = None
            base = (os.getenv("BINANCE_BASE") or "https://fapi.binance.com").rstrip("/")
            async with aiohttp.ClientSession() as session:
                try:
                    url = f"{base}/fapi/v1/ticker/price?symbol=BTCUSDT"
                    async with session.get(url, timeout=5) as r:
                        data = await r.json()
                        price = data.get("price")
                except Exception as e:
                    log.warning("binance_price_fetch_failed", extra={"error": str(e)})
                text = f"🚀 Bot startup OK. BTCUSDT price: {price or 'n/a'}"
                try:
                    tg_url = f"https://api.telegram.org/bot{token}/sendMessage"
                    payload = {"chat_id": chat_id, "text": text}
                    async with session.post(tg_url, json=payload, timeout=10) as r:
                        resp_text = await r.text()
                        log.info("test_message_sent", extra={"status": r.status, "resp": resp_text[:200]})
                except Exception as e:
                    log.error("test_message_failed", extra={"error": str(e)})

        asyncio.create_task(_send_test_message())
    except Exception as e:
        log.warning("startup_test_scheduling_failed", extra={"error": str(e)})

    try:
        yield
    finally:
        try:
            if stop_event is not None:
                stop_event.set()
            if worker_task is not None:
                await worker_task
        except Exception:
            pass
        # Close bot session if exists
        try:
            if bot is not None and getattr(bot, "session", None):
                await bot.session.close()
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

# Mount API app if provided
if api_app is not None:
    app.mount("", api_app)

# Health endpoint
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

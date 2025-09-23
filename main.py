import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import app as fastapi_app
from app.telegram import bot
from app.config import settings
from app.logging import setup_logging
from app.worker import run_worker
from app.utils import get_public_ip

stop_event = asyncio.Event()
worker_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    # Detect and log public IP for whitelisting
    try:
        import logging
        log = logging.getLogger('startup')
        ip = await get_public_ip()
        log.info('public_ip', extra={'ip': ip})
    except Exception as e:
        logging.getLogger('startup').warning('public_ip_error', extra={'error': str(e)})

    # Determine public URL
    public_url = (settings.PUBLIC_URL or settings.KOYEB_APP_URL)
    if public_url:
        public_url = public_url.rstrip("/")
    else:
        print("WARN: No PUBLIC_URL or KOYEB_APP_URL set. Telegram webhook will NOT be configured; bot will not receive updates.")

    # Telegram webhook lifecycle
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(1.0)
    if public_url:
        await bot.set_webhook(f"{public_url}/webhook")

    # Start worker
    global worker_task
    worker_task = asyncio.create_task(run_worker(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        if worker_task:
            await worker_task
        await bot.delete_webhook()
        await bot.session.close()

app = FastAPI(lifespan=lifespan)

# Mount routes
app.mount("", fastapi_app)
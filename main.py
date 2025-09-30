import os
import asyncio
import logging
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
    # initialize logging level (env wins if provided)
    setup_logging(os.getenv("LOG_LEVEL", getattr(settings, "LOG_LEVEL", "INFO")))
    logger = logging.getLogger("startup")

    # discover and log public IP (best effort)
    try:
        ip = await get_public_ip()
        logger.info("public_ip", extra={"ip": ip})
    except Exception:
        logger.warning("public_ip_failed", exc_info=True)

    # configure webhook
    public_url = getattr(settings, "PUBLIC_URL", os.getenv("PUBLIC_URL", ""))
    webhook_url = f"{public_url.rstrip('/')}/webhook" if public_url else None
    if webhook_url:
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("webhook_set", extra={"url": webhook_url})
    else:
        logger.warning("no_public_url_for_webhook")

    global worker_task
    worker_task = asyncio.create_task(run_worker(stop_event))

    try:
        yield
    finally:
        stop_event.set()
        if worker_task:
            await worker_task
        try:
            await bot.delete_webhook()
        finally:
            await bot.session.close()

app = FastAPI(lifespan=lifespan)

# Mount routes
app.mount("", fastapi_app)

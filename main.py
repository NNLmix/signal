import logging
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram.types import Update
from bot import bot, dp
from config import KOYEB_APP_URL, WEBHOOK_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop lifecycle for FastAPI which ensures the Telegram bot dispatcher
    is running (either webhook or long polling). This keeps the process alive so
    the Koyeb health checks won't see the container exit immediately.
    """
    polling_task = None
    # Consider webhook enabled only if KOYEB_APP_URL is not the default placeholder
    webhook_enabled = bool(KOYEB_APP_URL and "your-app.koyeb.app" not in KOYEB_APP_URL)
    try:
        if webhook_enabled:
            logger.info("Webhook mode enabled. Setting webhook to %s", WEBHOOK_URL)
            try:
                await bot.set_webhook(WEBHOOK_URL)
            except Exception as e:
                logger.exception("Failed to set webhook: %s", e)
        else:
            logger.info("Starting aiogram long polling in background task")
            polling_task = asyncio.create_task(dp.start_polling())
        yield
    finally:
        logger.info("Shutting down bot lifecycle")
        try:
            if webhook_enabled:
                await bot.delete_webhook()
        except Exception as e:
            logger.exception("Error while deleting webhook: %s", e)
        if polling_task:
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                logger.info("Polling task cancelled")
        try:
            await bot.session.close()
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    bot.set_current(bot)
    try:
        # process with aiogram v2 dispatcher
        await dp.process_update(update)
    finally:
        bot.reset_current()
    return {"ok": True}
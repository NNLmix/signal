import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram updates via webhook.
    """
    data = await request.json()
    update = Update(**data)
    await dp.process_update(update)  # ✅ correct for aiogram 2.x
    return {"ok": True}


@app.on_event("startup")
async def on_startup():
    logging.info("Bot started")


@app.on_event("shutdown")
async def on_shutdown():
    logging.info("Bot stopped")
    await bot.session.close()

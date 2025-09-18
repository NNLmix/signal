import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Initialize bot and dispatcher
bot = Bot(token="YOUR_TELEGRAM_BOT_TOKEN")
dp = Dispatcher()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    # Correct method for aiogram v3
    await dp.update.update(update, bot)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    logging.info("Bot started")

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("Bot stopped")

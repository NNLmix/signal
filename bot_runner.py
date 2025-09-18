import asyncio
from aiogram import Bot, Dispatcher
from config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL

# Create bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot=bot)

async def on_startup():
    # Set Telegram webhook
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

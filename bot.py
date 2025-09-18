import logging
from aiogram import Bot, Dispatcher
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)


async def start_polling():
    """Асинхронный запуск бота (без executor, чтобы не ломать event loop uvicorn)."""
    logger.info("Starting Telegram bot polling...")
    await dp.start_polling()

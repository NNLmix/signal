import logging
from aiogram import Bot, Dispatcher, types
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from diag import gather_diag
import json

logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=['diag'])
async def handle_diag(message: types.Message):
    """Handle /diag command. Works in private and group chats."""
    try:
        diag = await gather_diag()
        # send a concise JSON summary
        text = json.dumps(diag, ensure_ascii=False, indent=2)
        # respect chat from which command came
        await message.reply(f"<pre>{text}</pre>", parse_mode="HTML")
    except Exception as e:
        logger.exception("Error while running /diag: %s", e)
        await message.reply(f"Diag failed: {e}")


async def start_polling():
    """Асинхронный запуск бота (без executor, чтобы не ломать event loop uvicorn)."""
    logger.info("Starting Telegram bot polling...")
    await dp.start_polling()

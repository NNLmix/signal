import logging
from aiogram import Bot, Dispatcher, types
from config import TELEGRAM_BOT_TOKEN
from diag import gather_diag

logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=['diag'])
async def handle_diag(message: types.Message):
    """Run diagnostics and reply in the same chat where the command arrived."""
    try:
        diag = await gather_diag()
        pretty = diag.get('pretty') if isinstance(diag, dict) else str(diag)
        if not pretty:
            pretty = 'No diagnostics available'
        if len(pretty) > 3500:
            pretty = pretty[:3500] + '\n\n[truncated]'
        await message.reply(pretty)
    except Exception as e:
        logger.exception('Error handling /diag: %s', e)
        await message.reply('Failed to collect diagnostics. Check logs.')

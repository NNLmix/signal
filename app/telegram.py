import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.exceptions import Throttled
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
from .config import settings

log = logging.getLogger('telegram')

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

_rate_lock = asyncio.Lock()
_last_sent = 0.0
_min_interval = 1.0  # one message per second global

async def send_signal_message(text: str):
    global _last_sent
    async with _rate_lock:
        now = asyncio.get_event_loop().time()
        delta = now - _last_sent
        if delta < _min_interval:
            await asyncio.sleep(_min_interval - delta)
        try:
            log.info('telegram_send', extra={'chat_id': settings.TELEGRAM_CHAT_ID})
            await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=text, disable_web_page_preview=True)
        except Throttled:
            log.warning('telegram_throttled')
            await asyncio.sleep(_min_interval)
            await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=text, disable_web_page_preview=True)
        finally:
            _last_sent = asyncio.get_event_loop().time()

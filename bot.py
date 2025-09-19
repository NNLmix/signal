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
    """Run diagnostics and reply in the same chat where the command arrived."""
    try:
        diag = await gather_diag()
        # send a concise JSON summary
        text = json.dumps(diag, ensure_ascii=False, indent=2)
        # reply in the same chat
        await message.reply(f"<pre>{text}</pre>", parse_mode="HTML")
    except Exception as e:
        logger.exception("Error while running /diag: %s", e)
        # Best-effort reply
        try:
            await message.reply(f"Diag failed: {e}")
        except Exception:
            logger.exception("Also failed to send failure message")

@dp.message_handler(commands=['ping'])
async def handle_ping(message: types.Message):
    """Simple ping — should reply in the same chat (group or private)."""
    try:
        await message.reply("pong")
    except Exception as e:
        logger.exception("Error handling /ping: %s", e)
        # Fallback: try sending to configured TELEGRAM_CHAT_ID if available
        if TELEGRAM_CHAT_ID:
            try:
                await bot.send_message(TELEGRAM_CHAT_ID, "pong (fallback)")
            except Exception:
                logger.exception("Fallback send_message also failed")

async def start_polling():
    """Start polling (kept for backward compatibility)."""
    logger.info("Starting Telegram bot polling...")
    await dp.start_polling()


@dp.message_handler(commands=['help'])
async def handle_help(message: types.Message):
    help_text = (
        "/diag - run human-readable diagnostics (Redis/Supabase/Processor)\n"
        "/ping - quick ping (if available)\n"
        "/diag_json - raw diagnostics (if enabled)\n"
        "/help - show this message"
    )
    await message.reply(help_text)



# Ensure /diag uses pretty text if available
@dp.message_handler(commands=['diag'])
async def handle_diag(message: types.Message):
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

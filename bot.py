import logging
from aiogram import Bot, Dispatcher, executor, types
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
logger = logging.getLogger(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start","help"])
async def cmd_start(message: types.Message):
    await message.reply("Signal Router is alive. Use /ping to check.")

@dp.message_handler(commands=["ping"])
async def cmd_ping(message: types.Message):
    await message.reply("pong")

async def send_signal_message(sig: dict):
    text = (
        f"📣 *Signal* — `{sig.get('strategy','?')}`\n"
        f"• Pair: `{sig.get('symbol')}`\n"
        f"• Direction: `{sig.get('side')}`\n"
        f"• Entry: `{sig.get('entry_price')}`\n"
        f"• TP/SL: `{sig.get('tp')}` / `{sig.get('sl')}`\n"
        f"• Score: `{sig.get('model_score', 0):.3f}`\n"
    )
    await bot.send_message(TELEGRAM_CHAT_ID, text, parse_mode="Markdown")

def start_polling():
    logger.info("aiogram Bot: Signal Router [@signalrouter_mixbot]")
    # Guard polling against TerminatedByOtherGetUpdates to avoid restart loops
    try:
        from aiogram.utils.exceptions import TerminatedByOtherGetUpdates
    except Exception:
        TerminatedByOtherGetUpdates = None

    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as exc:
        # If it's the specific Telegram conflict, log and exit gracefully
        if TerminatedByOtherGetUpdates is not None and isinstance(exc, TerminatedByOtherGetUpdates):
            logger.error("Another getUpdates poller exists for this token. Exiting polling to avoid conflict.")
            return
        # aiogram may raise a wrapped exception; also check exception type name
        if exc.__class__.__name__ == 'TerminatedByOtherGetUpdates':
            logger.error("Another getUpdates poller exists for this token (caught by name). Exiting polling to avoid conflict.")
            return
        # Otherwise re-raise after logging
        logger.exception("Unhandled exception while starting polling: %s", exc)
        raise

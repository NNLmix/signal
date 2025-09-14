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
    executor.start_polling(dp, skip_updates=True)


from router import STRATEGIES
from diag import gather_diag

@dp.message_handler(commands=["diag"])
async def cmd_diag(message: types.Message):
    info = await gather_diag()
    strategies = [getattr(s, "name", "unknown") for s in STRATEGIES]
    ok = lambda d: "✅" if d.get("ok") else "❌"
    text = (
        "*Diagnostics*\n"
        f"Redis: {ok(info.get('redis', {}))} (queue={info.get('redis',{}).get('queue_len',0)})\n"
        f"Supabase: {ok(info.get('supabase', {}))} (status={info.get('supabase',{}).get('status','?')}, "
        f"latency={info.get('supabase',{}).get('latency_ms','?')}ms)\n"
        f"Binance: {ok(info.get('binance', {}))} (latency={info.get('binance',{}).get('latency_ms','?')}ms)\n"
        f"Symbols: `{','.join(info.get('symbols', []))}`  TF: `{info.get('ltf')} / {info.get('htf')}`\n"
        f"Strategies: `{', '.join(strategies)}`\n"
    )
    await message.reply(text, parse_mode="Markdown")

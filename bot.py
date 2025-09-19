import logging
import os
from aiogram import Bot, Dispatcher, types
# robust import for config and diag
try:
    from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except Exception:
    try:
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    except Exception:
        TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
        TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

try:
    from .diag import gather_diag
except Exception:
    try:
        from diag import gather_diag
    except Exception:
        async def gather_diag():
            return {'pretty': 'Diagnostics unavailable (import error)'}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

@dp.message_handler(commands=['ping'])
async def handle_ping(message: types.Message):
    await message.reply('pong')

@dp.message_handler(commands=['help'])
async def handle_help(message: types.Message):
    help_text = (
        "/diag - run human-readable diagnostics (Redis/Supabase/Processor)\n"
        "/redis - dump Redis keys and sample values\n"
        "/ping - quick ping\n"
        "/help - show this message"
    )
    await message.reply(help_text)

@dp.message_handler(commands=['diag'])
async def handle_diag(message: types.Message):
    """Run diagnostics and reply in plain human-readable text (no JSON)."""
    try:
        diag = await gather_diag()
        if isinstance(diag, dict):
            pretty = diag.get('pretty')
            if not pretty:
                # build short lines from known keys
                parts = []
                for k in ('supabase', 'redis', 'telegram'):
                    v = diag.get(k)
                    if isinstance(v, dict):
                        status = v.get('status') or ('OK' if v.get('available') else 'Unreachable')
                        parts.append(f"{k.capitalize()}: {status}")
                pretty = "\n".join(parts) or str(diag)
        else:
            pretty = str(diag)
        if len(pretty) > 3500:
            pretty = pretty[:3500] + "\n\n[truncated]"
        # send plain text (no <pre> or JSON)
        await message.reply(pretty)
    except Exception as e:
        logger.exception('Error handling /diag: %s', e)
        await message.reply('Failed to collect diagnostics. Check logs.')

@dp.message_handler(commands=['redis'])
async def handle_redis(message: types.Message):
    """Dump a summary of Redis keys and sample values (limited)."""
    try:
        REDIS_URL = os.environ.get('REDIS_URL')
        if not REDIS_URL:
            await message.reply("REDIS_URL not configured")
            return
        try:
            import redis.asyncio as aioredis
        except Exception:
            await message.reply("redis.asyncio not available in runtime")
            return
        client = aioredis.from_url(REDIS_URL)
        try:
            keys = await client.keys('*')
            if not keys:
                await message.reply("Redis is empty.")
                return
            sample = {}
            for k in keys[:20]:
                try:
                    val = await client.get(k)
                    if val is not None:
                        k_str = k.decode() if isinstance(k, bytes) else str(k)
                        v_str = val.decode() if isinstance(val, bytes) else str(val)
                        sample[k_str] = v_str
                except Exception as e:
                    sample[str(k)] = f"<error {e}>"
            reply = f"Redis keys: {len(keys)}\nSample (up to 20):\n" + "\n".join(f"{k}: {v}" for k,v in sample.items())
        except Exception as e:
            reply = f"Redis unavailable: {e}"
        finally:
            await client.close()
        if len(reply) > 4000:
            reply = reply[:3900] + "\n\n[truncated]"
        await message.reply(reply)
    except Exception as e:
        logger.exception('redis dump error: %s', e)
        await message.reply('Failed to fetch Redis content. Check logs.')

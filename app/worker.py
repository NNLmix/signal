import asyncio, hashlib, json
from typing import List
import aiohttp

from .config import settings
from .services.binance import BinanceClient
from .services.redis_queue import RedisClient
from .services.supabase import SupabaseClient
from .services.strategies.scalp_ema import Strategy
from .telegram import send_signal_message

async def run_worker(stop_event: asyncio.Event):
    redis = RedisClient()
    async with aiohttp.ClientSession() as session:
        supa = SupabaseClient(session)
        binance = BinanceClient(settings.BINANCE_BASE, session)
        await binance.sync_time()
        strategy = Strategy()

        # schedule loop
        while not stop_event.is_set():
            for symbol in settings.PAIRS:
                try:
                    kl = await binance.klines(symbol, strategy.timeframe, limit=200)
                    signals = strategy.run(kl, symbol)
                    for sig in signals:
                        text = format_signal_text(sig, kl)
                        dedup_key = make_dedup_key(sig, strategy.name)
                        fresh = await redis.dedup_try_set(dedup_key, settings.DEDUP_TTL_SEC)
                        if not fresh:
                            continue
                        await supa.insert_signal({
                            "symbol": sig["symbol"],
                            "side": sig["side"],
                            "reason": sig["reason"],
                            "strategy": strategy.name,
                        })
                        await send_signal_message(text)
                except Exception as e:
                    # Log to stdout; in production use structured logger
                    print("worker_error", symbol, str(e))
                await asyncio.sleep(0.4)  # jitter pacing per symbol
            # Sleep between full scans of all pairs
            await asyncio.sleep(10)

def make_dedup_key(sig: dict, strategy: str) -> str:
    payload = f"{sig['symbol']}|{strategy}|{sig['side']}|{sig.get('reason','')}"
    return "dedup:signal:" + hashlib.sha1(payload.encode()).hexdigest()

def format_signal_text(sig: dict, klines: List[list]) -> str:
    last = klines[-1]
    price = float(last[4])
    return (
        f"<b>{sig['symbol']}</b> \- <b>{sig['side']}</b>\n"
        f"Price: <code>{price:.2f}</code>\n"
        f"Reason: {sig.get('reason','')}\n"
        f"Strategy: <code>scalp_ema_cross_5m</code>"
    )

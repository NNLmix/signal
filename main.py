import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram.types import Update
from bot import bot, dp
import bot_runner

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting application lifespan: attaching bot and dispatcher")
    # Optionally perform webhook setup if using webhook mode
    try:
        await bot_runner.on_startup()
    except Exception as e:
        logging.warning("bot_runner.on_startup failed: %s", e)
    app.state.bot = bot
    app.state.dp = dp
    try:
        yield
    finally:
        logging.info("Shutting down application lifespan")
        try:
            await bot_runner.on_shutdown()
        except Exception as e:
            logging.warning("bot_runner.on_shutdown failed: %s", e)
        try:
            await bot.session.close()
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    # process with aiogram v2 dispatcher
    await dp.process_update(update)
    return {"ok": True}

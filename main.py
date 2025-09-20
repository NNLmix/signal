import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import app as fastapi_app
from app.telegram import bot
from app.config import settings
from app.logging import setup_logging
from app.worker import run_worker

stop_event = asyncio.Event()
worker_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    # Set Telegram webhook to PUBLIC_URL/webhook
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(1.0)
    await bot.set_webhook(f"{settings.PUBLIC_URL.rstrip('/')}/webhook")
    # Start worker
    global worker_task
    worker_task = asyncio.create_task(run_worker(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        if worker_task:
            await worker_task
        await bot.delete_webhook()
        await bot.session.close()

app = FastAPI(lifespan=lifespan)

# Mount routes
app.mount("", fastapi_app)

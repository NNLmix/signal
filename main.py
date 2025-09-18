import logging
import asyncio
import uvicorn
from fastapi import FastAPI, Request

from logging_setup import setup_json_logging
from config import LOG_LEVEL, HEALTH_PORT, TELEGRAM_BOT_TOKEN, WEBHOOK_PATH
from bot_runner import bot, dp, on_startup, on_shutdown
from processor import run as run_processor
from health import app as health_app
from diag import gather_diag

setup_json_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI()

# Include health endpoints
app.mount("/health", health_app)

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    update = await request.json()
    await dp.feed_update(bot, update)
    return {"ok": True}


async def _run_processor():
    await run_processor()


async def _health_logger(period_sec: int = 60):
    while True:
        try:
            info = await gather_diag()
            r = info.get("redis", {})
            s = info.get("supabase", {})
            logger.info("health.short", extra={"redis": r.get("status"), "supabase": s.get("status")})
        except Exception as e:
            logger.warning(f"Health logger failed: {e}")
        await asyncio.sleep(period_sec)


@app.on_event("startup")
async def startup_event():
    await on_startup()
    asyncio.create_task(_run_processor())
    asyncio.create_task(_health_logger())


@app.on_event("shutdown")
async def shutdown_event():
    await on_shutdown()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")

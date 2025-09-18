import asyncio
import logging
import uvicorn

from logging_setup import setup_json_logging
from config import LOG_LEVEL, HEALTH_PORT
from bot import start_polling
from processor import run as run_processor
from health import app as health_app
from diag import gather_diag

setup_json_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)


async def _run_bot():
    await start_polling()


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


async def main():
    await asyncio.gather(
        _run_bot(),
        _run_processor(),
        _health_logger(),
    )


if __name__ == "__main__":
    config = uvicorn.Config(health_app, host="0.0.0.0", port=HEALTH_PORT, log_level="info")
    server = uvicorn.Server(config)

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_until_complete(server.serve())

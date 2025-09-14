import asyncio, logging, uvicorn
from logging_setup import setup_json_logging
from config import LOG_LEVEL, HEALTH_PORT
from bot import start_polling
from processor import run as run_processor
from health import app as health_app

setup_json_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

async def _run_processor():
    await run_processor()

def run_health():
    uvicorn.run(health_app, host="0.0.0.0", port=HEALTH_PORT, log_level="warning")

if __name__ == "__main__":
    logger.info("starting.all {}", {})
    asyncio.get_event_loop().create_task(_run_processor())
    start_polling()

# near other imports
import asyncio, logging, uvicorn
from logging_setup import setup_json_logging
from config import LOG_LEVEL, HEALTH_PORT
from bot import start_polling
from processor import run as run_processor
from health import app as health_app
from diag import gather_diag

setup_json_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

async def _run_processor():
    await run_processor()

async def _health_logger(period_sec: int = 60):
    # short status line for Koyeb logs; uses gather_diag() already in diag.py
    while True:
        try:
            info = await gather_diag()
            r = info.get("redis", {})
            s = info.get("supabase", {})
            # small JSON-like short info logged to stdout (logging configured to stdout)
            logger.info("health.short %s", {
                "redis_ok": bool(r.get("ok")),
                "queue_len": int(r.get("queue_len", 0)),
                "supabase_ok": bool(s.get("ok")),
                "supabase_status": s.get("status", None),
                "supabase_latency_ms": s.get("latency_ms", None),
            })
        except Exception as e:
            logger.exception("health.logger.error %s", {"error": str(e)})
        await asyncio.sleep(period_sec)

def run_health():
    uvicorn.run(health_app, host="0.0.0.0", port=HEALTH_PORT, log_level="warning")

if __name__ == "__main__":
    logger.info("starting.all {}", {})
    # start processor
    asyncio.get_event_loop().create_task(_run_processor())
    # start periodic health logger (use small period during debugging)
    asyncio.get_event_loop().create_task(_health_logger(60))
    start_polling()

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

stop_event = asyncio.Event()
worker_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging if available
    try:
        setup_logging(settings.LOG_LEVEL)  # type: ignore[name-defined]
    except Exception:
        logging.basicConfig(level=logging.INFO)
    log = logging.getLogger('startup')

    # Optional diagnostics
    try:
        ip = await get_public_ip()  # type: ignore[name-defined]
        if ip: log.info(f'public_ip={ip}')
    except Exception:
        pass

    # If using Telegram, ensure webhook is disabled (polling-free sender)
    try:
        await bot.delete_webhook(drop_pending_updates=True)  # type: ignore[name-defined]
    except Exception:
        pass

    # Start background worker if present
    global worker_task
    try:
        worker_task = asyncio.create_task(run_worker(stop_event))  # type: ignore[name-defined]
    except Exception:
        worker_task = None

    try:
        yield
    finally:
        stop_event.set()
        if worker_task:
            try:
                await worker_task
            except Exception:
                pass
        try:
            await bot.session.close()  # type: ignore[attr-defined]
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

@app.get('/healthz')
async def healthz():
    return {'status': 'ok'}

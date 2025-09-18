import logging
import asyncio
from redis_client import is_available as redis_ok, queue_len, _host_port_tls
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

async def gather_diag():
    """Собирает диагностику сервиса."""
    diagnostics = {}

    # Redis
    host, port, tls = _host_port_tls()
    redis_status = await redis_ok()
    qlen = await queue_len()
    diagnostics["redis"] = {
        "host": host,
        "port": port,
        "tls": tls,
        "available": redis_status,
        "queue_len": qlen,
    }

    # Telegram Bot
    diagnostics["telegram_bot"] = {
        "token_set": bool(TELEGRAM_BOT_TOKEN),
        "status": "configured" if TELEGRAM_BOT_TOKEN else "missing token",
    }

    # Processor (здесь можно будет расширить)
    diagnostics["processor"] = {"status": "running"}

    # Логирование в читаемом виде
    logger.info("==== Service Diagnostics ====")
    logger.info(f"Redis: host={host}, port={port}, tls={tls}, available={redis_status}, queue_len={qlen}")
    logger.info(f"Telegram Bot: {'configured' if TELEGRAM_BOT_TOKEN else 'missing token'}")
    logger.info("Processor: running")

    return diagnostics

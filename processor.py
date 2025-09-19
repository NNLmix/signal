import logging
import asyncio

logger = logging.getLogger(__name__)


async def run():
    """Основной процессор сигналов."""
    logger.info("Processor started")
    try:
        while True:
            # TODO: логика обработки сигналов
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        logger.info("Processor stopped")

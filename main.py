import asyncio
import logging
from signal.redis_client import close_client
from signal.binance_client import BinanceClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

binance_client = BinanceClient()

async def main():
    try:
        logger.info("Bot starting up...")
        # TODO: Add startup logic (load feeders, strategies, etc.)
        await asyncio.sleep(1)  # placeholder to simulate work
    except Exception as e:
        logger.exception(f"Fatal error in bot: {e}")
        raise
    finally:
        logger.info("Shutting down... cleaning resources")
        try:
            await close_client()
        except Exception as e:
            logger.warning(f"Error closing Redis: {e}")
        try:
            await binance_client.close()
        except Exception as e:
            logger.warning(f"Error closing Binance client: {e}")

if __name__ == "__main__":
    asyncio.run(main())

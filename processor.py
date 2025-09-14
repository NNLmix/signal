import asyncio, logging
from ai_evaluator import ask_ai_async
from bot import send_signal_message
from redis_client import pop_signal, get_features
from storage import save_signal
logger = logging.getLogger(__name__)

async def _process_once():
    sig = pop_signal()
    if not sig:
        await asyncio.sleep(0.5); return
    saved = await save_signal(sig)
    try:
        sig_id = saved[0]["id"] if isinstance(saved, list) else saved.get("id")
        sig["id"] = sig_id
    except Exception:
        logger.warning("processor.save_signal.no_id %s", {"saved": saved})
    await send_signal_message(sig)
    features = get_features(sig["symbol"])
    try:
        await ask_ai_async(sig, features)
    except Exception as e:
        logger.warning("processor.ai_eval.error %s", {"error": str(e)})

async def run():
    logger.info("processor.start {}", {})
    while True:
        try: await _process_once()
        except Exception as e:
            logger.exception("processor.loop.error %s", {"error": str(e)})
            await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(run())

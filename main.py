import asyncio
from redis_client import pop_signal, get_features
from notifier import notify_group
from fast_model import fast_score
from ai_evaluator import ask_ai_async
from storage import save_signal

FAST_THRESHOLD = 0.65

async def process_signals():
    while True:
        signal = pop_signal()
        if not signal:
            await asyncio.sleep(0.5)
            continue

        features = get_features(signal["symbol"])
        if not features:
            continue

        prob = fast_score(features)
        if prob >= FAST_THRESHOLD:
            saved = await save_signal(signal)
            if saved:
                await notify_group(saved)
                asyncio.create_task(ask_ai_async(saved, features))
        else:
            print(f"Сигнал отклонён fast-model: {prob:.2f}")

async def main():
    await asyncio.gather(process_signals())

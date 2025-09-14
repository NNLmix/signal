import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import openai

from config import TELEGRAM_TOKEN, OPENAI_API_KEY
from storage import get_signal, save_ai_evaluation

# Init Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Init OpenAI legacy SDK
openai.api_key = OPENAI_API_KEY


async def ask_ai_about_signal(signal: dict) -> dict:
    """
    Send signal data to OpenAI and parse the response into a structured dict.
    """
    prompt = f"""
Оцени сделку:
Символ: {signal['symbol']}
Сторона: {signal['side']}
Цена входа: {signal['entry_price']}
Размер: {signal['size']}
Уверенность стратегии: {signal['confidence']}
Причина: {signal['reason']}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",  # ✅ safer than "gpt-5" (not available on legacy SDK)
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    answer = response["choices"][0]["message"]["content"]

    score = None
    if "%" in answer:
        try:
            score = float([s for s in answer.split() if "%" in s][0].replace("%", ""))
        except Exception:
            score = None

    verdict = "удачно" if "да" in answer.lower() else "сомнительно"

    return {
        "prompt": prompt,
        "answer": answer,
        "score": score,
        "verdict": verdict,
    }


# --- Telegram commands --- #

@dp.message_handler(commands=["ping"])
async def ping_handler(message: types.Message):
    """Quick check to confirm the bot is alive."""
    await message.reply("✅ Bot is alive and responding!")


@dp.message_handler(commands=["ai"])
async def ai_handler(message: types.Message):
    """
    /ai <signal_id> → fetches a signal from storage and asks OpenAI for evaluation.
    """
    args = message.get_args().strip()
    if not args.isdigit():
        await message.reply("Укажи ID сигнала: /ai <signal_id>")
        return

    signal_id = int(args)
    signal = await get_signal(signal_id)
    if not signal:
        await message.reply(f"Сигнал {signal_id} не найден.")
        return

    await message.reply("⏳ Запрашиваю AI-оценку...")
    result = await ask_ai_about_signal(signal)

    await save_ai_evaluation(
        signal_id=signal_id,
        prompt=result["prompt"],
        model="gpt-4",
        response_text=result["answer"],
        verdict=result["verdict"],
        score=result["score"] or 0,
    )

    await message.reply(f"🤖 AI-оценка сигнала {signal_id}:\n\n{result['answer']}")


if __name__ == "__main__":
    # Launch polling (supervisord will run this process)
    executor.start_polling(dp, skip_updates=True)

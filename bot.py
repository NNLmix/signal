import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import openai

from config import TELEGRAM_TOKEN, OPENAI_API_KEY
from storage import get_signal, save_ai_evaluation

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

async def ask_ai_about_signal(signal: dict) -> dict:
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
        model="gpt-5",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    answer = response["choices"][0]["message"]["content"]
    score = None
    if "%" in answer:
        try:
            score = float([s for s in answer.split() if "%" in s][0].replace("%", ""))
        except:
            score = None
    return {"prompt": prompt, "answer": answer, "score": score, "verdict": "удачно" if "да" in answer.lower() else "сомнительно"}

@dp.message_handler(commands=["ai"])
async def ai_handler(message: types.Message):
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
        model="gpt-5",
        response_text=result["answer"],
        verdict=result["verdict"],
        score=result["score"] or 0,
    )
    await message.reply(f"🤖 AI-оценка сигнала {signal_id}:\n\n{result['answer']}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

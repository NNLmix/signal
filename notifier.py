from aiogram import Bot
from config import TELEGRAM_TOKEN, TG_GROUP_ID
from storage import update_signal_status

bot = Bot(token=TELEGRAM_TOKEN)


async def notify_group(signal: dict):
    text = (
        f"🚨 Новый сигнал!\n\n"
        f"📈 Символ: {signal['symbol']}\n"
        f"🔀 Сторона: {signal['side'].upper()}\n"
        f"💰 Размер: {signal['size']}\n"
        f"💵 Цена входа: {signal['entry_price']}\n"
        f"🤔 Уверенность: {signal['confidence']}%\n"
        f"📋 Причина: {signal['reason']}\n"
        f"⏰ Время: {signal['created_at']}"
    )

    msg = await bot.send_message(chat_id=TG_GROUP_ID, text=text)

    # Обновляем статус в базе
    await update_signal_status(signal["id"], status="sent", tg_message_id=str(msg.message_id))
    return msg.message_id

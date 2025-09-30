
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .telegram import dp
from .config import settings
from .services.strategies import STRATEGIES
from .services.backtest import run_backtest

def _kb():
    kb = InlineKeyboardMarkup(row_width=1)
    for s in STRATEGIES:
        name = getattr(s, "name", s.__class__.__name__)
        kb.add(InlineKeyboardButton(text=name, callback_data=f"backtest:{name}"))
    return kb

@dp.message_handler(Command("backtest"))
async def backtest_cmd(m: types.Message):
    await m.answer("Выберите стратегию для бэктеста (3 месяца, старт $100):", reply_markup=_kb())

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("backtest:"))
async def backtest_click(c: types.CallbackQuery):
    name = c.data.split(":",1)[1]
    strat = None
    for s in STRATEGIES:
        if getattr(s, "name", None) == name:
            strat = s; break
    if not strat:
        await c.message.answer(f"Стратегия '{name}' не найдена")
        await c.answer()
        return
    pairs = getattr(settings, "PAIRS", ["BTCUSDT"])
    interval = getattr(strat, "timeframe", "5m")
    await c.message.answer(f"▶️ Бэктест '{name}' · {interval}\nПары: {', '.join(pairs)}\nПериод: 3 месяца\nКапитал: $100")
    res = await run_backtest(name, strat, pairs, interval, months=3)
    lines = [f"{sym}: {r['trades']} сделок, winrate {r['winrate']:.1f}%" for sym, r in res['per_symbol'].items()]
    txt = (f"✅ *{res['strategy']}* · {res['interval']}\n"
           f"Сделок: *{res['trades']}*, Winrate: *{res['winrate']:.1f}%*\n\n"
           + "\n".join(lines))
    await c.message.answer(txt, parse_mode="Markdown")
    await c.answer()

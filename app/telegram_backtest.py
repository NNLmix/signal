
import logging
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.telegram import dp
from app.config import settings

try:
    from app.services.strategies.loader import load_all
    def _get_strategies_dict():
        return load_all()
except Exception:
    from app.services.strategies import STRATEGIES as _STRATEGIES_LIST
    def _get_strategies_dict():
        return {getattr(s, "name", s.__class__.__name__): s for s in _STRATEGIES_LIST}

log = logging.getLogger("tg_backtest")

def _kb():
    kb = InlineKeyboardMarkup(row_width=1)
    try:
        for name in _get_strategies_dict().keys():
            kb.add(InlineKeyboardButton(text=name, callback_data=f"backtest:{name}"))
        return kb
    except Exception as e:
        log.exception("kb_build_failed", extra={"error": str(e)})
        return InlineKeyboardMarkup()

@dp.message_handler(Command("backtest"))
async def backtest_cmd(m: types.Message):
    log.info("cmd_backtest_received", extra={"chat_id": m.chat.id, "user_id": m.from_user.id if m.from_user else None})
    await m.answer("Выберите стратегию для бэктеста (3 месяца, старт $100):", reply_markup=_kb())

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("backtest:"))
async def backtest_click(c: types.CallbackQuery):
    try:
        name = c.data.split(":",1)[1]
    except Exception:
        await c.answer()
        return
    log.info("cb_backtest_click", extra={"chat_id": c.message.chat.id if c.message else None, "name": name})

    strategies = _get_strategies_dict()
    strat = strategies.get(name)
    if not strat:
        await c.message.answer(f"Стратегия '{name}' не найдена")
        await c.answer()
        return

    interval = getattr(strat, "timeframe", "5m")
    pairs = getattr(settings, "PAIRS", ["BTCUSDT"])

    try:
        from app.services.backtest import run_backtest
        await c.message.answer(
            f"▶️ Бэктест '{name}' · {interval}\nПары: {', '.join(pairs)}\nПериод: 3 месяца\nКапитал: $100"
        )
        res = await run_backtest(name, strat, pairs, interval, months=3)
        lines = [f"{sym}: {r['trades']} сделок, winrate {r['winrate']:.1f}%" for sym, r in res['per_symbol'].items()]
        txt = (f"✅ *{res['strategy']}* · {res['interval']}\n"
               f"Сделок: *{res['trades']}*, Winrate: *{res['winrate']:.1f}%*\n\n"
               + "\n".join(lines))
        await c.message.answer(txt, parse_mode="Markdown")
    except Exception as e:
        log.exception("backtest_failed", extra={"error": str(e)})
        await c.message.answer(f"❌ Ошибка бэктеста: {e}")
    finally:
        await c.answer()

log.info("tg_backtest_handlers_registered")

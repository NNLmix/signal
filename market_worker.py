import asyncio
from features import update_and_compute
from redis_client import queue_signal

async def handle_market_data(symbol: str, price: float, volume: float):
    features = update_and_compute(symbol, price, volume)

    # если есть стратегии → проверяем
    from router import strategies
    for strat in strategies:
        signal = await strat.evaluate(features)
        if signal:
            queue_signal(signal)

async def market_loop():
    while True:
        # тут фейковая генерация цен, на деле = Binance Websocket
        symbol = "BTCUSDT"
        price = 25000.0
        volume = 1.5
        await handle_market_data(symbol, price, volume)
        await asyncio.sleep(1)

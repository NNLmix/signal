# binance_ws.py - lightweight websocket kline subscriber prototype
# This is a non-blocking aiohttp-based sketch. It receives kline updates and calls a user-provided callback.
import asyncio
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

BINANCE_WS_BASE = "wss://fstream.binance.com/stream?streams="

async def _default_callback(symbol, kline):
    logger.info("ws kline %s %s", symbol, kline.get('k',{}).get('t'))

async def run_ws_kline_subscriber(symbols, interval='1m', callback=_default_callback):
    """Subscribe to multiple symbol kline streams. symbols: list of 'BTCUSDT' etc.
    This function reconnects on failure and calls callback(symbol, kline_payload) for each kline event.
    """
    if not symbols:
        raise ValueError('symbols list required')
    streams = '/'.join([f"{s.lower()}@kline_{interval}" for s in symbols])
    url = BINANCE_WS_BASE + streams
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url, heartbeat=30) as ws:
                    logger.info('ws connected to %s', url)
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                payload = json.loads(msg.data)
                                data = payload.get('data', {})
                                # data contains 's' symbol and 'k' kline object
                                symbol = data.get('s')
                                await callback(symbol, data)
                            except Exception:
                                logger.exception('failed to process ws message')
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.warning('ws error encountered')
                            break
        except Exception:
            logger.exception('ws connection failed, reconnecting in 2s')
            await asyncio.sleep(2)

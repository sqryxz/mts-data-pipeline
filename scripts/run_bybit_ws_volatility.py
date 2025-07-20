import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from api.websockets.bybit_websocket import BybitWebSocket

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'TAOUSDT', 'FETUSDT', 'AGIXUSDT', 'RNDRUSDT', 'OCEANUSDT']

async def main():
    ws = BybitWebSocket()
    await ws.connect()
    # Subscribe to 1m kline channels for BTCUSDT and ETHUSDT
    kline_channels = [f'kline.1.{symbol}' for symbol in SYMBOLS]
    await ws.subscribe(kline_channels)
    print(f"Subscribed to: {kline_channels}")
    await ws.listen()

if __name__ == '__main__':
    asyncio.run(main()) 
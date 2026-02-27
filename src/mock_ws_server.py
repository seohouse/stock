import asyncio
import json
import random
import websockets
import os

HOST = os.getenv('MOCK_WS_HOST', 'localhost')
PORT = int(os.getenv('MOCK_WS_PORT', '8765'))

async def producer(ws, path):
    symbols = ['005930', '000660', '120056']
    while True:
        # simulate a trade tick event
        s = random.choice(symbols)
        msg = {'type': 'trade', 'symbol': s, 'price': round(random.uniform(10000, 80000), 0), 'qty': random.randint(1, 1000), 'side': random.choice(['B', 'S'])}
        await ws.send(json.dumps(msg))
        await asyncio.sleep(0.5)

async def handler(ws, path):
    try:
        await producer(ws, path)
    except websockets.exceptions.ConnectionClosed:
        pass

if __name__ == '__main__':
    print(f'Starting mock WS server on ws://{HOST}:{PORT}')
    asyncio.get_event_loop().run_until_complete(websockets.serve(handler, HOST, PORT))
    asyncio.get_event_loop().run_forever()

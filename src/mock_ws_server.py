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

async def consumer(ws, path):
    # receive messages from client and handle PING echo (and simple LOGIN ack)
    async for message in ws:
        try:
            data = json.loads(message)
        except Exception:
            # not json - ignore or echo raw
            await ws.send(message)
            continue
        # echo PING messages to keep connection alive
        trnm = data.get('trnm') or data.get('type')
        if trnm == 'PING':
            # send back the same payload (mirror) to simulate server keepalive
            await ws.send(json.dumps({'trnm': 'PING', 'return_code': 0, 'echo': data}))
        elif trnm == 'LOGIN':
            # simple mock login acceptance for local testing
            await ws.send(json.dumps({'trnm': 'LOGIN', 'return_code': 0, 'return_msg': '', 'sor_yn': 'Y'}))
        else:
            # for other messages, optionally echo or ignore
            await ws.send(json.dumps({'trnm': trnm or 'MSG', 'return_code': 0, 'echo': data}))

async def handler(ws, path):
    consumer_task = asyncio.ensure_future(consumer(ws, path))
    producer_task = asyncio.ensure_future(producer(ws, path))
    done, pending = await asyncio.wait([consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()

if __name__ == '__main__':
    print(f'Starting mock WS server on ws://{HOST}:{PORT}')
    asyncio.get_event_loop().run_until_complete(websockets.serve(handler, HOST, PORT))
    asyncio.get_event_loop().run_forever()

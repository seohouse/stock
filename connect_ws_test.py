import asyncio,os
import websockets
from dotenv import load_dotenv
load_dotenv('.env')
url=os.getenv('KIWOOM_WS_URL')
print('Attempting connect to', url)
async def run():
    try:
        async with websockets.connect(url, ping_interval=10, max_size=None) as ws:
            print('Connected')
            msg='{"action":"login","trnm":"T1","api_key":"test","mode":"mock"}'
            await ws.send(msg)
            print('Sent LOGIN')
            try:
                resp=await asyncio.wait_for(ws.recv(), timeout=5)
                print('Received:', resp)
            except asyncio.TimeoutError:
                print('No response within 5s')
    except Exception as e:
        print('Connect failed:', type(e).__name__, e)
asyncio.run(run())

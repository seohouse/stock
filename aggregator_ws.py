import asyncio
import json
import websockets
import time
from collections import deque, defaultdict

class AggregatorWS:
    def __init__(self):
        self.today_cum=defaultdict(int)
        self.recent=defaultdict(lambda:deque(maxlen=60))
        self.trade_buy=defaultdict(int)
        self.trade_total=defaultdict(int)
        self.updated_at=time.time()

    async def connect(self, uri='ws://localhost:8765'):
        async with websockets.connect(uri) as ws:
            async for msg in ws:
                self.process(json.loads(msg))

    def process(self, evt):
        # evt: {type:'trade', symbol, price, qty, side}
        if evt.get('type')!='trade':
            return
        s=evt['symbol']
        q=int(evt['qty'])
        self.today_cum[s]+=q
        self.recent[s].append((time.time(), q))
        if evt.get('side')=='B':
            self.trade_buy[s]+=q
        self.trade_total[s]+=q
        self.updated_at=time.time()

    def get_metrics(self, symbol):
        buy = self.trade_buy.get(symbol,0)
        tot = self.trade_total.get(symbol,0)
        ti = (buy / tot) if tot>0 else 0
        return {'today_cum': self.today_cum.get(symbol,0), 'trade_intensity': round(ti,2), 'updated_at': self.updated_at}

if __name__=='__main__':
    agg=AggregatorWS()
    print('Connecting to ws://localhost:8765 and aggregating... (Ctrl-C to stop)')
    asyncio.get_event_loop().run_until_complete(agg.connect())

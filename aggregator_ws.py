import asyncio
import json
import os
import websockets
import time
from collections import deque, defaultdict

class AggregatorWS:
    def __init__(self):
        self.today_cum = defaultdict(int)
        self.recent = defaultdict(lambda: deque(maxlen=60))
        self.trade_buy = defaultdict(int)
        self.trade_total = defaultdict(int)
        self.updated_at = time.time()

    async def connect(self, uri: str = None):
        """
        Connect to a websocket URI and consume market tick events.
        URI resolution order:
          1) explicit uri argument
          2) environment AGGREGATOR_WS_URI
          3) environment KIWOOM_WS_URL (useful to point directly to Kiwoom WS)
          4) default 'ws://localhost:8765'
        """
        if uri is None:
            uri = os.getenv('AGGREGATOR_WS_URI') or os.getenv('KIWOOM_WS_URL') or 'ws://localhost:8765'
        print(time.strftime('%Y-%m-%d %H:%M:%S'), 'AggregatorWS connecting to', uri)
        async with websockets.connect(uri) as ws:
            async for msg in ws:
                try:
                    self.process(json.loads(msg))
                except Exception:
                    # ignore malformed events
                    continue

    def process(self, evt):
        # evt: {type:'trade', symbol, price, qty, side}
        if evt.get('type') != 'trade':
            return
        s = evt['symbol']
        q = int(evt['qty'])
        self.today_cum[s] += q
        self.recent[s].append((time.time(), q))
        if evt.get('side') == 'B':
            self.trade_buy[s] += q
        self.trade_total[s] += q
        self.updated_at = time.time()

    def get_metrics(self, symbol):
        buy = self.trade_buy.get(symbol, 0)
        tot = self.trade_total.get(symbol, 0)
        ti = (buy / tot) if tot > 0 else 0
        return {'today_cum': self.today_cum.get(symbol, 0), 'trade_intensity': round(ti, 2), 'updated_at': self.updated_at}

if __name__ == '__main__':
    agg = AggregatorWS()
    uri = os.getenv('AGGREGATOR_WS_URI') or os.getenv('KIWOOM_WS_URL') or 'ws://localhost:8765'
    print('Connecting to', uri, 'and aggregating... (Ctrl-C to stop)')
    asyncio.get_event_loop().run_until_complete(agg.connect(uri))

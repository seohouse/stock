import time
import asyncio
from order_manager_stub import OrderManagerStub

class Position:
    def __init__(self, symbol, entry_price, qty):
        self.symbol = symbol
        self.entry_price = entry_price
        self.qty = qty
        self.remaining = qty
        self.highest = entry_price
        self.entry_ts = time.time()
        self.part1_sold = False
        self.closed = False

class PositionManager:
    def __init__(self, aggregator, order_manager=None, cfg=None):
        self.agg = aggregator
        self.om = order_manager or OrderManagerStub()
        self.cfg = cfg or {
            'part1_pct': 0.25,
            'part1_tp': 0.0075,
            'part2_tp': 0.015,
            'stop_loss': -0.015,
            'trailing_pct': 0.007,
            'time_cut_minutes': 30,
            'poll_interval': 0.5,
        }
        self._lock = asyncio.Lock()
        self.active_position = None
        self._task = None
        self._running = False

    async def start_monitor(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop_monitor(self):
        self._running = False
        if self._task:
            await asyncio.wait_for(self._task, timeout=2)

    async def open_position(self, symbol, entry_price, qty):
        async with self._lock:
            if self.active_position and not self.active_position.closed:
                raise RuntimeError('Another position active')
            pos = Position(symbol, entry_price, qty)
            self.active_position = pos
            # simulate buy already executed (scanner handles placing buy)
            return pos

    async def _run_loop(self):
        while self._running:
            try:
                async with self._lock:
                    pos = self.active_position
                if pos and not pos.closed:
                    metrics = self.agg.get_metrics(pos.symbol)
                    price = metrics.get('last_price') or (metrics.get('today_cum')%70000 + 10000)
                    # update highest
                    if price > pos.highest:
                        pos.highest = price
                    elapsed = time.time() - pos.entry_ts
                    # part1 TP
                    if (not pos.part1_sold) and price >= pos.entry_price*(1+self.cfg['part1_tp']):
                        sell_qty = max(1, int(pos.qty * self.cfg['part1_pct']))
                        await self.om.place_sell_market(pos.symbol, sell_qty)
                        pos.remaining -= sell_qty
                        pos.part1_sold = True
                    # part2 TP (final)
                    if price >= pos.entry_price*(1+self.cfg['part2_tp']):
                        if pos.remaining>0:
                            await self.om.place_sell_market(pos.symbol, pos.remaining)
                            pos.remaining = 0
                            pos.closed = True
                    # stop loss
                    if price <= pos.entry_price*(1+self.cfg['stop_loss']):
                        if pos.remaining>0:
                            await self.om.place_sell_market(pos.symbol, pos.remaining)
                            pos.remaining = 0
                            pos.closed = True
                    # trailing
                    if pos.remaining>0 and price <= pos.highest*(1-self.cfg['trailing_pct']):
                        await self.om.place_sell_market(pos.symbol, pos.remaining)
                        pos.remaining = 0
                        pos.closed = True
                    # time cut
                    if elapsed >= self.cfg['time_cut_minutes']*60:
                        if pos.remaining>0:
                            await self.om.place_sell_market(pos.symbol, pos.remaining)
                            pos.remaining = 0
                            pos.closed = True
                    # if closed, clear active after logging
                    if pos.closed:
                        # keep record but clear active
                        async with self._lock:
                            self.active_position = None
                await asyncio.sleep(self.cfg['poll_interval'])
            except Exception as e:
                print('PositionManager error', e)
                await asyncio.sleep(1)

if __name__=='__main__':
    import asyncio
    from aggregator_mock import AggregatorMock
    agg=AggregatorMock()
    om=OrderManagerStub()
    pm=PositionManager(agg, om)
    async def main():
        await pm.start_monitor()
        pos=await pm.open_position('005930',10000,1)
        await asyncio.sleep(5)
        await pm.stop_monitor()
    asyncio.run(main())

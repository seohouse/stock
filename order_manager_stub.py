import time
import json
import asyncio
import aiofiles
import aiofiles.os
from asyncio import Lock

class OrderManagerStub:
    def __init__(self, log_path='logs/mock_orders.log'):
        self._lock = Lock()
        self.log_path = log_path

    async def _log(self, obj):
        obj['ts'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        # ensure logs dir exists
        try:
            await aiofiles.os.makedirs('logs', exist_ok=True)
        except Exception:
            pass
        async with aiofiles.open(self.log_path, 'a', encoding='utf8') as f:
            await f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        print('[ORDER]', obj)

    async def place_buy_limit(self, symbol, price, qty, tif='IOC'):
        async with self._lock:
            await self._log({'action':'place_buy_limit','symbol':symbol,'price':price,'qty':qty,'tif':tif,'status':'placed'})
            await asyncio.sleep(0.2)
            await self._log({'action':'buy_filled','symbol':symbol,'price':price,'qty':qty,'status':'filled'})
            return {'status':'filled','filled_qty':qty,'avg_price':price}

    async def place_sell_market(self, symbol, qty):
        async with self._lock:
            await self._log({'action':'place_sell_market','symbol':symbol,'qty':qty,'status':'placed'})
            await asyncio.sleep(0.1)
            await self._log({'action':'sell_filled','symbol':symbol,'qty':qty,'status':'filled','avg_price':'market'})
            return {'status':'filled','filled_qty':qty}

    async def get_positions(self):
        # For stub, return empty
        return []

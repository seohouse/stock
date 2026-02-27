"""
Async mock Kiwoom REST client for integration testing (mock-only).
Provides async get_prev_close and async get_ohlcv and async place_order/get_positions that return simulated data.
"""
import asyncio
import random

async def get_prev_close(symbol):
    # simulate network delay
    await asyncio.sleep(0.01)
    # return a mock previous day volume and close
    return {'symbol':symbol, 'prev_close': random.randint(1000,90000), 'prev_volume': random.randint(10000,2000000)}

async def get_ohlcv(symbol, period='D', limit=30):
    await asyncio.sleep(0.01)
    base = random.randint(1000,90000)
    data = []
    for i in range(limit):
        o = base - i*10
        h = o + random.randint(0,200)
        l = max(1, o - random.randint(0,200))
        c = o + random.randint(-50,50)
        v = random.randint(1000,100000)
        data.append({'ts':i,'open':o,'high':h,'low':l,'close':c,'volume':v})
    return data

async def place_order(kind, symbol, price=None, qty=1, tif='IOC'):
    await asyncio.sleep(0.02)
    # simulate immediate fill
    return {'status':'filled','filled_qty':qty,'avg_price':price or 'market'}

async def get_positions():
    await asyncio.sleep(0.01)
    return []

import asyncio
import time
import math
from aggregator_ws import AggregatorWS
from kiwoom_rest_loader_mock import fetch_prev_day, fetch_ranking_top_m
from order_manager_stub import OrderManagerStub

# Config
INITIAL_UNIVERSE_TOP_M = 100
FINAL_TOP_K = 1
VOLUME_RATIO_THRESHOLD = 1.5

om = OrderManagerStub()
agg = AggregatorWS()

def compute_score(prev_volume, today_cum, trade_intensity):
    if prev_volume<=0:
        return 0, 0
    volume_ratio = today_cum / prev_volume
    score = math.log1p(volume_ratio) * 2.0 + trade_intensity
    return score, volume_ratio

import os

TRADING_FLAG_PATH = 'trading_enabled.flag'


def is_trading_enabled():
    # Trading is enabled only if the flag file exists
    return os.path.exists(TRADING_FLAG_PATH)


async def run_scanner():
    while True:
        if not is_trading_enabled():
            print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Trading disabled (waiting for market open)')
            await asyncio.sleep(5)
            continue
        universe = fetch_ranking_top_m(INITIAL_UNIVERSE_TOP_M)
        scored = []
        for sym in universe:
            prev = fetch_prev_day(sym)
            metrics = agg.get_metrics(sym)
            score, vol_ratio = compute_score(prev['prev_volume'], metrics['today_cum'], metrics['trade_intensity'])
            scored.append({'symbol':sym,'score':score,'vol_ratio':vol_ratio,'today_cum':metrics['today_cum'],'prev_volume':prev['prev_volume'],'trade_intensity':metrics['trade_intensity']})
        scored.sort(key=lambda x: x['score'], reverse=True)
        top = scored[0]
        print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Top candidate', top)
        if top['vol_ratio']>=VOLUME_RATIO_THRESHOLD:
            print('Top1 passes threshold, executing mock trade for', top['symbol'])
            price = round( (top['today_cum']%70000)+10000, -2)
            qty = 1
            res = await om.place_buy_limit(top['symbol'], price, qty, tif='IOC')
            if res.get('status')=='filled':
                await asyncio.sleep(2)
                await om.place_sell_market(top['symbol'], qty)
        else:
            print('No candidate passes threshold. Skipping trade.')
        await asyncio.sleep(5)  # wait before next scan

async def main():
    # start aggregator connect in background
    uri = 'ws://localhost:8765'
    print('Starting AggregatorWS connect to', uri)
    connect_task = asyncio.create_task(agg.connect(uri))
    # give it a moment to collect
    await asyncio.sleep(1)
    # start scanner loop
    try:
        await run_scanner()
    except asyncio.CancelledError:
        pass
    finally:
        connect_task.cancel()

if __name__=='__main__':
    asyncio.run(main())

import asyncio, time, random
from kiwoom_rest_loader_mock import fetch_prev_day, fetch_ranking_top_m
from aggregator_mock import AggregatorMock
from order_manager_stub import OrderManagerStub
from position_manager import PositionManager

# Config
INITIAL_UNIVERSE_TOP_M = 50
VOLUME_RATIO_THRESHOLD = 1.5

om = OrderManagerStub()
agg = AggregatorMock()
pm = PositionManager(agg, om)

import math

def compute_score(prev_volume, today_cum, trade_intensity):
    if prev_volume<=0:
        return 0,0
    volume_ratio = today_cum / prev_volume
    score = math.log1p(volume_ratio) * 2.0 + trade_intensity
    return score, volume_ratio

async def main():
    await pm.start_monitor()
    # Simulate a single scan + trade flow
    universe = fetch_ranking_top_m(INITIAL_UNIVERSE_TOP_M)
    scored=[]
    for sym in universe:
        prev = fetch_prev_day(sym)
        metrics = agg.update_mock(sym)
        score, vol_ratio = compute_score(prev['prev_volume'], metrics['today_cum'], metrics['trade_intensity'])
        scored.append({'symbol':sym,'score':score,'vol_ratio':vol_ratio,'today_cum':metrics['today_cum'],'prev_volume':prev['prev_volume'],'trade_intensity':metrics['trade_intensity']})
    scored.sort(key=lambda x: x['score'], reverse=True)
    if not scored:
        print('No candidates')
        return
    best = scored[0]
    print('Selected Top-1', best)
    if best['vol_ratio']>=VOLUME_RATIO_THRESHOLD:
        # place buy limit (mock) at mock price
        price = round(random.uniform(10000,80000), -2)
        qty = 1
        res = await om.place_buy_limit(best['symbol'], price, qty, tif='IOC')
        if res.get('status')=='filled':
            # open position in PM
            pos = await pm.open_position(best['symbol'], price, qty)
            print('Position opened', pos.symbol, pos.entry_price)
            # Let position manager run for a while to simulate exits
            await asyncio.sleep(5)
        else:
            print('Buy not filled')
    else:
        print('No candidate passed threshold')

    # stop monitor
    await pm.stop_monitor()
    print('Done')

if __name__=='__main__':
    asyncio.run(main())

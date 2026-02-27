import time
from kiwoom_rest_loader_mock import fetch_prev_day, fetch_ranking_top_m
from aggregator_mock import AggregatorMock
from order_manager_stub import OrderManagerStub

# Config
INITIAL_UNIVERSE_TOP_M = 100
FINAL_TOP_K = 1
VOLUME_RATIO_THRESHOLD = 1.5

om = OrderManagerStub()
agg = AggregatorMock()

def compute_score(prev_volume, today_cum, trade_intensity):
    # simple composite: log(volume_ratio) * weight + trade_intensity
    import math
    if prev_volume<=0:
        return 0
    volume_ratio = today_cum / prev_volume
    score = math.log1p(volume_ratio) * 2.0 + trade_intensity
    return score, volume_ratio


def run_once():
    # 1) get top M ranking
    universe = fetch_ranking_top_m(INITIAL_UNIVERSE_TOP_M)
    scored = []
    for sym in universe:
        prev = fetch_prev_day(sym)
        metrics = agg.update_mock(sym)
        score, vol_ratio = compute_score(prev['prev_volume'], metrics['today_cum'], metrics['trade_intensity'])
        scored.append({'symbol':sym,'score':score,'vol_ratio':vol_ratio,'today_cum':metrics['today_cum'],'prev_volume':prev['prev_volume'],'trade_intensity':metrics['trade_intensity']})
    # sort
    scored.sort(key=lambda x: x['score'], reverse=True)
    topK = scored[:FINAL_TOP_K]
    print('Top candidates:', topK)
    # apply threshold and pick top1
    top = topK[0]
    if top['vol_ratio']>=VOLUME_RATIO_THRESHOLD:
        print('Top1 passes threshold, executing mock trade for', top['symbol'])
        price = round( (top['today_cum']%70000)+10000, -2)
        qty = 1
        res = om.place_buy_limit(top['symbol'], price, qty, tif='IOC')
        if res.get('status')=='filled':
            time.sleep(2)
            om.place_sell_market(top['symbol'], qty)
    else:
        print('No candidate passes threshold. Skipping trade.')

if __name__=='__main__':
    run_once()

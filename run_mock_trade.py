import time
import json
import random
from order_manager_stub import OrderManagerStub

# Simple mock runner: pick top-1 from parsed_sheet1_2.json (or random) and simulate buy then sell after delay
PARSED='parsed_sheet1_2.json'

om = OrderManagerStub()

def load_symbols():
    try:
        with open(PARSED,'r',encoding='utf8') as f:
            data=json.load(f)
    except Exception:
        return ['005930']
    # find numeric entries and return first valid symbol-like strings
    symbols=[]
    for r in data:
        v=r.get('키움 REST API')
        if v and isinstance(v,str) and v.isdigit() and len(v)>=4:
            symbols.append(v.zfill(6))
    if not symbols:
        symbols=['005930']
    return symbols

symbols=load_symbols()
print('mock symbols count', len(symbols))

# mock scoring: random scores
scores=[(s, random.random()*5) for s in symbols]
scores.sort(key=lambda x: x[1], reverse=True)
print('Top 5:', scores[:5])

# Choose top-1
top=scores[0][0]
print('Top-1 chosen:', top)

# Simulate buy at best ask (mock price)
mock_price = round( random.uniform(10000,80000), -2)
qty = 1
print('Placing buy limit (IOC) on', top, 'price', mock_price)
res = om.place_buy_limit(top, mock_price, qty, tif='IOC')

if res.get('status')=='filled':
    print('Buy filled, holding for 3 seconds then sell at market')
    time.sleep(3)
    res2 = om.place_sell_market(top, qty)
    print('Sell result', res2)
else:
    print('Buy not filled; exiting')

print('Mock trading done')

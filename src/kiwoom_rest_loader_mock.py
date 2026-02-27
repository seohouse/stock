import time
import json

# Mock REST loader: returns prev_day_total_volume for a symbol from parsed_sheet or random
import random

def fetch_prev_day(symbol):
    # In real use: call Kiwoom REST to get previous day volume
    # Here: return a mock value
    v = random.randint(500000, 5000000)
    return {'symbol':symbol,'prev_date':time.strftime('%Y-%m-%d'), 'prev_close':random.randint(10000,80000), 'prev_volume':v, 'fetched_at':time.time()}

def fetch_ranking_top_m(m=100):
    # return list of mock symbols
    return [f"{random.randint(1,999999):06d}" for _ in range(m)]

if __name__=='__main__':
    print(fetch_prev_day('005930'))

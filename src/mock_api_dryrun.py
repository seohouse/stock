import json
import random
import time

APIS = [
    ('ka10023','거래량급증요청'),
    ('ka10024','거래량갱신요청'),
    ('ka10030','당일거래량상위요청'),
    ('ka10031','전일거래량상위요청'),
    ('ka10055','당일전일체결량요청'),
    ('ka10079','주식틱차트조회요청'),
    ('ka10021','호가잔량급증요청'),
    ('ka10022','잔량율급증요청'),
]

SYMBOLS = ['005930','000660','120056','530694']


def mock_ka10023(params):
    # 거래량급증요청: return list of symbols with prev/current/급증량/급증률
    results=[]
    for s in SYMBOLS:
        prev=random.randint(100000,1000000)
        curr=prev * random.uniform(0.5,8.0)
        delta=int(curr-prev)
        rate=round((curr-prev)/prev*100,2)
        results.append({'symbol':s,'prev_volume':prev,'current_volume':int(curr),'delta':delta,'delta_rate_pct':rate})
    return {'api':'ka10023','desc':'거래량급증요청','data':results}


def mock_ka10024(params):
    # 거래량갱신요청: per symbol current vs prev
    s=params.get('symbol',random.choice(SYMBOLS))
    prev=random.randint(100000,1000000)
    curr=prev*random.uniform(0.2,5.0)
    return {'api':'ka10024','symbol':s,'prev_volume':prev,'current_volume':int(curr),'prev_diff':int(curr-prev)}


def mock_ka10030(params):
    # 당일거래량상위요청: return top N by today vol
    items=[]
    for s in SYMBOLS:
        vol=random.randint(10000,2000000)
        items.append({'symbol':s,'today_volume':vol,'current_price':random.randint(10000,80000)})
    items.sort(key=lambda x:x['today_volume'],reverse=True)
    return {'api':'ka10030','top':items}


def mock_ka10031(params):
    # 전일거래량상위요청
    items=[]
    for s in SYMBOLS:
        vol=random.randint(10000,2000000)
        items.append({'symbol':s,'prev_day_volume':vol,'prev_close':random.randint(10000,80000)})
    items.sort(key=lambda x:x['prev_day_volume'],reverse=True)
    return {'api':'ka10031','top':items}


def mock_ka10055(params):
    # 당일전일체결량요청: returns today vs prev and ratio
    s=params.get('symbol',random.choice(SYMBOLS))
    prev=random.randint(50000,1000000)
    today=random.randint(0, int(prev*3))
    return {'api':'ka10055','symbol':s,'prev_day_volume':prev,'today_volume':today,'today_vs_prev_pct':round((today/prev*100) if prev else 0,2)}


def mock_ka10079(params):
    # 주식틱차트조회요청: return recent ticks
    s=params.get('symbol',random.choice(SYMBOLS))
    ticks=[]
    for i in range(10):
        ticks.append({'time':time.time()- (10-i), 'price':random.randint(10000,80000),'qty':random.randint(1,1000),'side':random.choice(['B','S'])})
    return {'api':'ka10079','symbol':s,'ticks':ticks}


def mock_ka10021(params):
    # 호가잔량급증요청: return bids/asks changes
    s=params.get('symbol',random.choice(SYMBOLS))
    return {'api':'ka10021','symbol':s,'ask_volume_increase':random.randint(0,10000),'bid_volume_increase':random.randint(0,10000),'ratio':round(random.uniform(0,10),2)}


def mock_ka10022(params):
    s=params.get('symbol',random.choice(SYMBOLS))
    return {'api':'ka10022','symbol':s,'residual_rate_increase_pct':round(random.uniform(0,200),2)}

MAPPING={
    'ka10023':mock_ka10023,
    'ka10024':mock_ka10024,
    'ka10030':mock_ka10030,
    'ka10031':mock_ka10031,
    'ka10055':mock_ka10055,
    'ka10079':mock_ka10079,
    'ka10021':mock_ka10021,
    'ka10022':mock_ka10022,
}


def run_dryrun():
    print('Starting mock dry-run for key Kiwoom APIs...')
    results={}
    for code,desc in APIS:
        print('\n---',code,desc,'---')
        func=MAPPING.get(code)
        res=func({})
        print(json.dumps(res, ensure_ascii=False, indent=2))
        results[code]=res
    # Save summary
    with open('mock_api_dryrun_result.json','w',encoding='utf8') as f:
        json.dump(results,f,ensure_ascii=False,indent=2)
    print('\nSaved mock_api_dryrun_result.json')

if __name__=='__main__':
    run_dryrun()

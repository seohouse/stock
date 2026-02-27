#!/usr/bin/env python3
import subprocess, time, json, os

N=10
script='scanner_with_pm.py'
logs='logs/mock_orders.log'

# ensure logs exist
os.makedirs('logs', exist_ok=True)
open(logs,'a').close()

for i in range(N):
    print(f'Run {i+1}/{N}')
    r = subprocess.run(['python3', script], capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print('ERR:', r.stderr)
    time.sleep(0.5)

print('All runs done. Generating summary...')

# analyze logs
with open(logs,'r',encoding='utf8') as f:
    lines=[json.loads(l) for l in f if l.strip()]

# pair buys and sells by symbol in chronological order
from collections import defaultdict
buys=defaultdict(list)
sells=defaultdict(list)
for entry in lines:
    a=entry.get('action')
    ts=entry.get('ts')
    if a=='buy_filled':
        buys[entry['symbol']].append({'ts':ts,'price':entry.get('price'),'qty':entry.get('qty')})
    if a=='sell_filled':
        sells[entry['symbol']].append({'ts':ts,'qty':entry.get('qty'),'price':entry.get('avg_price')})

pairs=[]
for sym in buys:
    nb=min(len(buys[sym]), len(sells.get(sym,[])))
    for i in range(nb):
        b=buys[sym][i]
        s=sells[sym][i]
        # parse timestamps
        from datetime import datetime
        fmt='%Y-%m-%dT%H:%M:%S'
        try:
            bt=datetime.strptime(b['ts'],fmt)
            st=datetime.strptime(s['ts'],fmt)
            dur=(st-bt).total_seconds()
        except Exception:
            dur=None
        pairs.append({'symbol':sym,'buy_ts':b['ts'],'sell_ts':s['ts'],'duration_s':dur,'buy_price':b.get('price'),'sell_price':s.get('price')})

summary={'total_runs':N,'total_trades':len(pairs),'pairs':pairs}
with open('simulation_summary.json','w',encoding='utf8') as f:
    json.dump(summary,f,ensure_ascii=False,indent=2)

print('Saved simulation_summary.json')
print('Total trades:', len(pairs))
for p in pairs:
    print(p)

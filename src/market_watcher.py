import time, os, datetime

FLAG='trading_enabled.flag'
LOG='logs/market_watcher.log'

# Market schedule (Asia/Seoul) local time assumed
MARKET_OPEN_HOUR=9
MARKET_OPEN_MIN=0
MARKET_CLOSE_HOUR=15
MARKET_CLOSE_MIN=20

CHECK_INTERVAL=5  # seconds


def log(msg):
    s=f"{datetime.datetime.now().isoformat()} {msg}\n"
    with open(LOG,'a',encoding='utf8') as f:
        f.write(s)
    print(s, end='')


def enable_trading():
    open(FLAG,'w').close()
    log('Trading ENABLED')


def disable_trading():
    if os.path.exists(FLAG):
        os.remove(FLAG)
    log('Trading DISABLED')


def next_event_times(now=None):
    now = now or datetime.datetime.now()
    open_today = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0)
    close_today = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0)
    return open_today, close_today


def main():
    os.makedirs('logs', exist_ok=True)
    log('Market watcher started')
    while True:
        now = datetime.datetime.now()
        open_t, close_t = next_event_times(now)
        if now < open_t:
            # before open: ensure disabled
            if os.path.exists(FLAG):
                disable_trading()
            # wait until open
            secs = (open_t - now).total_seconds()
            log(f'Before open; sleeping until open in {int(secs)}s')
            time.sleep(min(secs, CHECK_INTERVAL))
            continue
        if open_t <= now < close_t:
            # market open
            if not os.path.exists(FLAG):
                enable_trading()
            # sleep until close
            secs = (close_t - now).total_seconds()
            time.sleep(min(secs, CHECK_INTERVAL))
            continue
        # after close
        if os.path.exists(FLAG):
            disable_trading()
        # compute next day's open (tomorrow)
        tomorrow = now + datetime.timedelta(days=1)
        next_open = tomorrow.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0)
        secs = (next_open - now).total_seconds()
        log(f'After close; sleeping until next open in {int(secs)}s')
        time.sleep(min(secs, CHECK_INTERVAL))

if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('market_watcher stopped')

import random
import time

class AggregatorMock:
    def __init__(self):
        self.data = {}

    def update_mock(self, symbol):
        # simulate today cumulative volume and trade intensity
        today_cum = random.randint(1000, 5000000)
        trade_intensity = round(random.random(), 2)
        self.data[symbol] = {'today_cum': today_cum, 'trade_intensity': trade_intensity, 'updated_at': time.time()}
        return self.data[symbol]

    def get_metrics(self, symbol):
        if symbol not in self.data:
            return self.update_mock(symbol)
        return self.data[symbol]

if __name__=='__main__':
    a=AggregatorMock()
    print(a.update_mock('005930'))

"""
Simple Kiwoom REST client wrapper using TokenManager.
- Provides basic methods: get_prev_close, get_ohlcv, place_order, get_positions
- The exact endpoint paths are placeholders; replace with Kiwoom REST spec values.
"""
import os
import json
from typing import List, Dict, Any
from urllib.parse import urljoin

from kiwoom_token_manager import TokenManager, auth_request

BASE_URL = os.getenv('KIWOOM_API_BASE', 'https://api.kiwoom.example/')

class KiwoomRestClient:
    def __init__(self, token_manager: TokenManager, base_url: str = None):
        self.tm = token_manager
        self.base = base_url or BASE_URL

    def _url(self, path: str) -> str:
        return urljoin(self.base, path)

    def get_prev_close(self, symbol: str) -> Dict[str, Any]:
        # placeholder endpoint; replace with actual
        url = self._url(f'/v1/markets/{symbol}/daily?count=2')
        r = auth_request('GET', url, self.tm)
        if r.status_code != 200:
            raise RuntimeError(f'prev_close failed: {r.status_code} {r.text}')
        j = r.json()
        # assuming j contains 'data' array with latest first
        data = j.get('data', [])
        if not data:
            return {}
        prev = data[1] if len(data) > 1 else data[0]
        return prev

    def get_ohlcv(self, symbol: str, interval: str = '1m', count: int = 120) -> List[Dict[str, Any]]:
        url = self._url(f'/v1/markets/{symbol}/ohlcv?interval={interval}&count={count}')
        r = auth_request('GET', url, self.tm)
        if r.status_code != 200:
            raise RuntimeError(f'ohlcv failed: {r.status_code} {r.text}')
        return r.json().get('data', [])

    def place_order(self, account: str, symbol: str, side: str, qty: int, order_type: str = 'market', price: int = None) -> Dict[str, Any]:
        url = self._url('/v1/orders')
        body = {
            'account': account,
            'symbol': symbol,
            'side': side,
            'qty': qty,
            'type': order_type,
        }
        if price is not None:
            body['price'] = price
        r = auth_request('POST', url, self.tm, json=body)
        if r.status_code not in (200,201):
            raise RuntimeError(f'place_order failed: {r.status_code} {r.text}')
        return r.json()

    def get_positions(self, account: str) -> Dict[str, Any]:
        url = self._url(f'/v1/accounts/{account}/positions')
        r = auth_request('GET', url, self.tm)
        if r.status_code != 200:
            raise RuntimeError(f'get_positions failed: {r.status_code} {r.text}')
        return r.json()

# small CLI helper for testing (requires env vars for client id/secret and token store)
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--prev', help='symbol to get prev_close')
    parser.add_argument('--ohlcv', help='symbol for ohlcv')
    parser.add_argument('--place', nargs=5, help='place order: account symbol side qty type')
    args = parser.parse_args()
    tm = TokenManager()
    k = KiwoomRestClient(tm)
    if args.prev:
        print(k.get_prev_close(args.prev))
    if args.ohlcv:
        print(k.get_ohlcv(args.ohlcv)[:5])
    if args.place:
        acc, sym, side, qty, typ = args.place
        print(k.place_order(acc, sym, side, int(qty), typ))

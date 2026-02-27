"""
TokenManager for OAuth-based Kiwoom REST API
- Provides: synchronous and async helpers to load/store tokens, get access token with auto-refresh,
  and an HTTP request wrapper that handles 401->refresh->retry logic.

NOTES:
- This is a template. Fill OAUTH_CONFIG with real token_url/client_id/client_secret.
- For production, replace file-backed TokenStore with a secret manager/keyring.
"""
import time
import json
import os
import threading
from typing import Optional
import requests

# CONFIG: replace with real values or load from environment
OAUTH_CONFIG = {
    'token_url': os.getenv('KIWOOM_TOKEN_URL', 'https://auth.kiwoom.example/oauth/token'),
    'client_id': os.getenv('KIWOOM_CLIENT_ID', ''),
    'client_secret': os.getenv('KIWOOM_CLIENT_SECRET', ''),
}

TOKEN_STORE_PATH = os.getenv('KIWOOM_TOKEN_STORE', 'kiwoom_token_store.json')
SAFETY_MARGIN = int(os.getenv('KIWOOM_TOKEN_SAFETY_MARGIN', '60'))  # seconds

_lock = threading.Lock()

class TokenStore:
    @staticmethod
    def load():
        if not os.path.exists(TOKEN_STORE_PATH):
            return None
        try:
            with open(TOKEN_STORE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def save(data: dict):
        tmp = TOKEN_STORE_PATH + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(data, f)
        os.replace(tmp, TOKEN_STORE_PATH)

class TokenManager:
    def __init__(self, config: dict = None):
        self.config = config or OAUTH_CONFIG
        self._token = None
        self._load()
        self._refresh_lock = threading.Lock()

    def _load(self):
        data = TokenStore.load()
        if not data:
            self._token = None
        else:
            self._token = data

    def _persist(self):
        if self._token is None:
            try:
                if os.path.exists(TOKEN_STORE_PATH):
                    os.remove(TOKEN_STORE_PATH)
            except Exception:
                pass
            return
        TokenStore.save(self._token)

    def _is_expired_or_soon(self) -> bool:
        if not self._token:
            return True
        expires_at = self._token.get('expires_at', 0)
        return time.time() > (expires_at - SAFETY_MARGIN)

    def get_access_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        if self._token and not self._is_expired_or_soon():
            return self._token['access_token']
        # acquire refresh lock
        with self._refresh_lock:
            # double-check
            if self._token and not self._is_expired_or_soon():
                return self._token['access_token']
            self._refresh()
            if not self._token:
                raise RuntimeError('No token available; interactive auth required')
            return self._token['access_token']

    def force_refresh(self):
        with self._refresh_lock:
            self._refresh()

    def _refresh(self):
        # if we have a refresh_token use it
        if not self._token or not self._token.get('refresh_token'):
            # cannot refresh
            self._token = None
            self._persist()
            return
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self._token['refresh_token'],
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
        }
        url = self.config['token_url']
        for attempt in range(3):
            try:
                r = requests.post(url, data=data, timeout=5)
                if r.status_code == 200:
                    j = r.json()
                    access = j.get('access_token')
                    refresh = j.get('refresh_token', self._token.get('refresh_token'))
                    expires_in = int(j.get('expires_in', 3600))
                    self._token = {
                        'access_token': access,
                        'refresh_token': refresh,
                        'expires_at': int(time.time() + expires_in),
                    }
                    self._persist()
                    return
                elif r.status_code in (400,401):
                    # refresh token invalid -> clear
                    self._token = None
                    self._persist()
                    return
                else:
                    time.sleep(0.5 * (2**attempt))
            except Exception:
                time.sleep(0.5 * (2**attempt))
        # if we reach here, refresh failed
        raise RuntimeError('Failed to refresh token')

    def save_token_response(self, token_response: dict):
        """Save a fresh token response from an authorization code exchange.
        token_response should include access_token, expires_in, and optionally refresh_token.
        """
        access = token_response.get('access_token')
        refresh = token_response.get('refresh_token')
        expires_in = int(token_response.get('expires_in', 3600))
        self._token = {
            'access_token': access,
            'refresh_token': refresh,
            'expires_at': int(time.time() + expires_in),
        }
        self._persist()

# convenience HTTP wrapper

def auth_request(method: str, url: str, token_manager: TokenManager, **kwargs):
    """Make an HTTP request with bearer token; on 401 attempt refresh once and retry."""
    headers = kwargs.pop('headers', {}) or {}
    try:
        token = token_manager.get_access_token()
    except Exception as e:
        raise
    headers['Authorization'] = f'Bearer {token}'
    r = requests.request(method, url, headers=headers, timeout=10, **kwargs)
    if r.status_code == 401:
        # try refresh and retry once
        try:
            token_manager.force_refresh()
            token = token_manager.get_access_token()
            headers['Authorization'] = f'Bearer {token}'
            r = requests.request(method, url, headers=headers, timeout=10, **kwargs)
        except Exception:
            pass
    return r

# Async helpers using aiohttp
try:
    import aiohttp
    import asyncio
except Exception:
    aiohttp = None

async def async_auth_request(method: str, url: str, token_manager: TokenManager, **kwargs):
    """Async version of auth_request using aiohttp. On 401 attempt refresh once and retry."""
    if aiohttp is None:
        raise RuntimeError('aiohttp not available')
    headers = kwargs.pop('headers', {}) or {}
    try:
        token = token_manager.get_access_token()
    except Exception:
        # try to refresh synchronously
        token_manager.force_refresh()
        token = token_manager.get_access_token()
    headers['Authorization'] = f'Bearer {token}'
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.request(method, url, headers=headers, **kwargs) as resp:
            if resp.status == 401:
                # try refresh
                try:
                    token_manager.force_refresh()
                    token = token_manager.get_access_token()
                    headers['Authorization'] = f'Bearer {token}'
                    async with session.request(method, url, headers=headers, **kwargs) as resp2:
                        return resp2
                except Exception:
                    return resp
            return resp

async def async_get_access_token(token_manager: TokenManager):
    """Async-friendly getter for access token. Uses sync TokenManager but avoids race by running in default loop executor when necessary."""
    import asyncio as _asyncio
    loop = _asyncio.get_event_loop()
    try:
        # call sync get_access_token in executor to avoid blocking
        token = await loop.run_in_executor(None, token_manager.get_access_token)
        return token
    except Exception:
        # fallback: if token present in memory, return it to allow mock flows
        try:
            t = token_manager._token
            if t and 'access_token' in t:
                return t['access_token']
        except Exception:
            pass
        # try force refresh in executor
        try:
            await loop.run_in_executor(None, token_manager.force_refresh)
            token = await loop.run_in_executor(None, token_manager.get_access_token)
            return token
        except Exception:
            return None

# simple interactive helper to exchange authorization code

def exchange_authorization_code(code: str, redirect_uri: str, config: dict = None) -> dict:
    cfg = config or OAUTH_CONFIG
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': cfg['client_id'],
        'client_secret': cfg['client_secret'],
    }
    r = requests.post(cfg['token_url'], data=data, timeout=10)
    r.raise_for_status()
    return r.json()

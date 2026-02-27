import time
from kiwoom_token_manager import TokenManager
import kiwoom_token_manager as ktm
import requests

# Monkeypatch requests.post and requests.request to simulate token server and API
class FakeResponse:
    def __init__(self, status_code, json_data=None, text=''):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text
    def json(self):
        return self._json
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

# Save originals
orig_post = requests.post
orig_request = requests.request

call_log = []

def fake_post(url, data=None, timeout=None, **kwargs):
    call_log.append(('post', url, data))
    # Simulate refresh token endpoint
    if data and data.get('grant_type') == 'refresh_token':
        # If refresh_token matches 'valid-refresh', return new access token
        if data.get('refresh_token') == 'valid-refresh':
            return FakeResponse(200, {'access_token':'access-new-1','refresh_token':'valid-refresh','expires_in':5})
        else:
            return FakeResponse(401, {'error':'invalid_grant'})
    # Simulate authorization_code exchange
    if data and data.get('grant_type') == 'authorization_code':
        return FakeResponse(200, {'access_token':'access-initial','refresh_token':'valid-refresh','expires_in':5})
    return FakeResponse(500, {})

# fake request to simulate API returning 200 or 401 depending on token
def fake_request(method, url, headers=None, timeout=None, **kwargs):
    call_log.append(('req', method, url, headers.get('Authorization') if headers else None))
    auth = headers.get('Authorization','') if headers else ''
    if 'access-new-1' in auth or 'access-initial' in auth:
        return FakeResponse(200, {'ok':True})
    # simulate expired access leading to 401
    return FakeResponse(401, {'error':'unauthorized'})

requests.post = fake_post
requests.request = fake_request

print('Starting TokenManager mock dryrun')
manager = TokenManager(config={
    'token_url':'https://auth.mock/oauth/token',
    'client_id':'mock-client',
    'client_secret':'mock-secret'
})

# Simulate obtaining initial token via authorization code flow
print('Exchanging authorization code (simulated)')
resp = ktm.exchange_authorization_code('fake-code','https://localhost/cb', manager.config)
print('Exchange response:', resp)
manager.save_token_response(resp)
print('Saved token. Access token:', manager.get_access_token())

print('Sleeping until token near expiry (6s)')
time.sleep(6)

print('Now calling auth_request to trigger refresh on 401')
r = ktm.auth_request('GET','https://api.mock/resource', manager)
print('auth_request status:', r.status_code, 'body:', r.json())

print('\nCall log:')
for c in call_log:
    print(c)

# restore
requests.post = orig_post
requests.request = orig_request
print('Done')

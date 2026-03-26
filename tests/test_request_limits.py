from fastapi_app.services.request_limits import RequestRateLimiter, get_client_ip


# EN: Define class `_FakeClient`.
# JP: クラス `_FakeClient` を定義する。
class _FakeClient:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, host):
		self.host = host


# EN: Define class `_FakeRequest`.
# JP: クラス `_FakeRequest` を定義する。
class _FakeRequest:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, host='127.0.0.1', headers=None):
		self.client = _FakeClient(host)
		self.headers = headers or {}


# EN: Define function `test_rate_limiter_blocks_after_threshold`.
# JP: 関数 `test_rate_limiter_blocks_after_threshold` を定義する。
def test_rate_limiter_blocks_after_threshold():
	limiter = RequestRateLimiter(max_requests=2, window_seconds=60, now_fn=lambda: 1000.0)
	assert limiter.allow('1.1.1.1') is True
	assert limiter.allow('1.1.1.1') is True
	assert limiter.allow('1.1.1.1') is False


# EN: Define function `test_rate_limiter_allows_again_after_window`.
# JP: 関数 `test_rate_limiter_allows_again_after_window` を定義する。
def test_rate_limiter_allows_again_after_window():
	now = {'value': 1000.0}
	limiter = RequestRateLimiter(max_requests=1, window_seconds=10, now_fn=lambda: now['value'])
	assert limiter.allow('2.2.2.2') is True
	assert limiter.allow('2.2.2.2') is False
	now['value'] = 1011.0
	assert limiter.allow('2.2.2.2') is True


# EN: Define function `test_get_client_ip_prefers_forwarded_headers_when_enabled`.
# JP: 関数 `test_get_client_ip_prefers_forwarded_headers_when_enabled` を定義する。
def test_get_client_ip_prefers_forwarded_headers_when_enabled():
	req = _FakeRequest(headers={'X-Forwarded-For': '203.0.113.10, 10.0.0.1'})
	assert get_client_ip(req, trust_proxy_headers=True) == '203.0.113.10'


# EN: Define function `test_get_client_ip_uses_remote_host_when_proxy_disabled`.
# JP: 関数 `test_get_client_ip_uses_remote_host_when_proxy_disabled` を定義する。
def test_get_client_ip_uses_remote_host_when_proxy_disabled():
	req = _FakeRequest(host='198.51.100.5', headers={'X-Forwarded-For': '203.0.113.10'})
	assert get_client_ip(req, trust_proxy_headers=False) == '198.51.100.5'

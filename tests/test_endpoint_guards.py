from fastapi_app.services.endpoint_guards import ip_rate_limit_guard


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
	def __init__(self):
		self.client = _FakeClient('127.0.0.1')
		self.headers = {}


# EN: Define function `test_ip_rate_limit_guard_returns_429_when_limited`.
# JP: 関数 `test_ip_rate_limit_guard_returns_429_when_limited` を定義する。
def test_ip_rate_limit_guard_returns_429_when_limited(monkeypatch):
	from fastapi_app.services import endpoint_guards

	monkeypatch.setattr(endpoint_guards, 'is_ip_rate_limited', lambda _request: (True, '127.0.0.1'))
	response = ip_rate_limit_guard(_FakeRequest())
	assert response is not None
	assert response.status_code == 429


# EN: Define function `test_ip_rate_limit_guard_returns_none_when_allowed`.
# JP: 関数 `test_ip_rate_limit_guard_returns_none_when_allowed` を定義する。
def test_ip_rate_limit_guard_returns_none_when_allowed(monkeypatch):
	from fastapi_app.services import endpoint_guards

	monkeypatch.setattr(endpoint_guards, 'is_ip_rate_limited', lambda _request: (False, '127.0.0.1'))
	response = ip_rate_limit_guard(_FakeRequest())
	assert response is None

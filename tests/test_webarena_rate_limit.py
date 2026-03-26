import json

from fastapi_app.webarena import routes as webarena_routes


# EN: Define class `_FakeRequest`.
# JP: クラス `_FakeRequest` を定義する。
class _FakeRequest:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, payload=None):
		self._payload = payload or {}
		self.client = type('C', (), {'host': '127.0.0.1'})()
		self.headers = {}
		self.query_params = {}

	# EN: Define async function `json`.
	# JP: 非同期関数 `json` を定義する。
	async def json(self):
		return self._payload


# EN: Define function `_body`.
# JP: 関数 `_body` を定義する。
def _body(response):
	return json.loads(response.body.decode('utf-8'))


# EN: Define function `test_get_tasks_returns_429_when_rate_limited`.
# JP: 関数 `test_get_tasks_returns_429_when_rate_limited` を定義する。
def test_get_tasks_returns_429_when_rate_limited(monkeypatch):
	monkeypatch.setattr(
		webarena_routes,
		'ip_rate_limit_guard',
		lambda _request: webarena_routes.JSONResponse({'error': 'limited'}, status_code=429),
	)
	response = webarena_routes.get_tasks(_FakeRequest())
	assert response.status_code == 429
	assert _body(response)['error'] == 'limited'

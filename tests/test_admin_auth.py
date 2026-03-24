import pytest
from fastapi import HTTPException

from fastapi_app.routes.admin_auth import require_admin_api_token


# EN: Define function `test_require_admin_api_token_accepts_header_token`.
# JP: 関数 `test_require_admin_api_token_accepts_header_token` を定義する。
def test_require_admin_api_token_accepts_header_token(monkeypatch):
	monkeypatch.setenv('ADMIN_API_TOKEN', 'secret-token')
	require_admin_api_token(x_admin_token='secret-token', authorization=None)


# EN: Define function `test_require_admin_api_token_accepts_bearer_token`.
# JP: 関数 `test_require_admin_api_token_accepts_bearer_token` を定義する。
def test_require_admin_api_token_accepts_bearer_token(monkeypatch):
	monkeypatch.setenv('ADMIN_API_TOKEN', 'secret-token')
	require_admin_api_token(x_admin_token=None, authorization='Bearer secret-token')


# EN: Define function `test_require_admin_api_token_rejects_when_missing`.
# JP: 関数 `test_require_admin_api_token_rejects_when_missing` を定義する。
def test_require_admin_api_token_rejects_when_missing(monkeypatch):
	monkeypatch.delenv('ADMIN_API_TOKEN', raising=False)
	with pytest.raises(HTTPException) as exc_info:
		require_admin_api_token(x_admin_token='anything', authorization=None)
	assert exc_info.value.status_code == 503


# EN: Define function `test_require_admin_api_token_rejects_invalid_token`.
# JP: 関数 `test_require_admin_api_token_rejects_invalid_token` を定義する。
def test_require_admin_api_token_rejects_invalid_token(monkeypatch):
	monkeypatch.setenv('ADMIN_API_TOKEN', 'secret-token')
	with pytest.raises(HTTPException) as exc_info:
		require_admin_api_token(x_admin_token='wrong-token', authorization=None)
	assert exc_info.value.status_code == 403

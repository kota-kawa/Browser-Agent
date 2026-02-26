# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.routes import api_user_profile


# EN: Define class `_FakeRequest`.
# JP: クラス `_FakeRequest` を定義する。
class _FakeRequest:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, payload):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._payload = payload

    # EN: Define async function `json`.
    # JP: 非同期関数 `json` を定義する。
    async def json(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return self._payload


# EN: Define function `_body`.
# JP: 関数 `_body` を定義する。
def _body(response):
    # EN: Return a value from the function.
    # JP: 関数から値を返す。
    return json.loads(response.body.decode("utf-8"))


# EN: Define function `test_get_user_profile`.
# JP: 関数 `test_get_user_profile` を定義する。
def test_get_user_profile(monkeypatch):
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_user_profile, "load_user_profile", lambda: "profile")
    # EN: Assign value to response.
    # JP: response に値を代入する。
    response = api_user_profile.get_user_profile()
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert response.status_code == 200
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _body(response) == {"text": "profile"}


# EN: Define function `test_update_user_profile_requires_text`.
# JP: 関数 `test_update_user_profile_requires_text` を定義する。
def test_update_user_profile_requires_text(monkeypatch):
    # EN: Define async function `_fake_read_payload`.
    # JP: 非同期関数 `_fake_read_payload` を定義する。
    async def _fake_read_payload(_request):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return {}

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_user_profile, "read_json_payload", _fake_read_payload)
    # EN: Assign value to response.
    # JP: response に値を代入する。
    response = asyncio.run(api_user_profile.update_user_profile(_FakeRequest({})))
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert response.status_code == 400
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "text" in _body(response)["error"]


# EN: Define function `test_update_user_profile_success`.
# JP: 関数 `test_update_user_profile_success` を定義する。
def test_update_user_profile_success(monkeypatch):
    # EN: Define async function `_fake_read_payload`.
    # JP: 非同期関数 `_fake_read_payload` を定義する。
    async def _fake_read_payload(_request):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return {"text": "value"}

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_user_profile, "read_json_payload", _fake_read_payload)
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_user_profile, "save_user_profile", lambda text: f"saved:{text}")

    # EN: Assign value to response.
    # JP: response に値を代入する。
    response = asyncio.run(api_user_profile.update_user_profile(_FakeRequest({"text": "value"})))
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert response.status_code == 200
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _body(response) == {"status": "ok", "text": "saved:value"}


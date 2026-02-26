# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.routes.utils import read_json_payload


# EN: Define class `_FakeRequest`.
# JP: クラス `_FakeRequest` を定義する。
class _FakeRequest:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, payload=None, raises=False):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._payload = payload
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._raises = raises

    # EN: Define async function `json`.
    # JP: 非同期関数 `json` を定義する。
    async def json(self):
        # EN: Branch logic based on a condition.
        # JP: 条件に応じて処理を分岐する。
        if self._raises:
            # EN: Raise an exception.
            # JP: 例外を送出する。
            raise ValueError("invalid json")
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return self._payload


# EN: Define function `test_read_json_payload_returns_dict`.
# JP: 関数 `test_read_json_payload_returns_dict` を定義する。
def test_read_json_payload_returns_dict():
    # EN: Assign value to req.
    # JP: req に値を代入する。
    req = _FakeRequest(payload={"a": 1})
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert asyncio.run(read_json_payload(req)) == {"a": 1}


# EN: Define function `test_read_json_payload_returns_empty_for_non_dict`.
# JP: 関数 `test_read_json_payload_returns_empty_for_non_dict` を定義する。
def test_read_json_payload_returns_empty_for_non_dict():
    # EN: Assign value to req.
    # JP: req に値を代入する。
    req = _FakeRequest(payload=["x"])
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert asyncio.run(read_json_payload(req)) == {}


# EN: Define function `test_read_json_payload_returns_empty_on_error`.
# JP: 関数 `test_read_json_payload_returns_empty_on_error` を定義する。
def test_read_json_payload_returns_empty_on_error():
    # EN: Assign value to req.
    # JP: req に値を代入する。
    req = _FakeRequest(raises=True)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert asyncio.run(read_json_payload(req)) == {}


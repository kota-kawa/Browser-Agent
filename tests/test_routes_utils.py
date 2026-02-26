import asyncio

from fastapi_app.routes.utils import read_json_payload


# EN: Define class `_FakeRequest`.
# JP: クラス `_FakeRequest` を定義する。
class _FakeRequest:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, payload=None, raises=False):
        self._payload = payload
        self._raises = raises

    # EN: Define async function `json`.
    # JP: 非同期関数 `json` を定義する。
    async def json(self):
        if self._raises:
            raise ValueError("invalid json")
        return self._payload


# EN: Define function `test_read_json_payload_returns_dict`.
# JP: 関数 `test_read_json_payload_returns_dict` を定義する。
def test_read_json_payload_returns_dict():
    req = _FakeRequest(payload={"a": 1})
    assert asyncio.run(read_json_payload(req)) == {"a": 1}


# EN: Define function `test_read_json_payload_returns_empty_for_non_dict`.
# JP: 関数 `test_read_json_payload_returns_empty_for_non_dict` を定義する。
def test_read_json_payload_returns_empty_for_non_dict():
    req = _FakeRequest(payload=["x"])
    assert asyncio.run(read_json_payload(req)) == {}


# EN: Define function `test_read_json_payload_returns_empty_on_error`.
# JP: 関数 `test_read_json_payload_returns_empty_on_error` を定義する。
def test_read_json_payload_returns_empty_on_error():
    req = _FakeRequest(raises=True)
    assert asyncio.run(read_json_payload(req)) == {}


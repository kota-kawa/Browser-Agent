import asyncio

from fastapi_app.routes.utils import read_json_payload


class _FakeRequest:
    def __init__(self, payload=None, raises=False):
        self._payload = payload
        self._raises = raises

    async def json(self):
        if self._raises:
            raise ValueError("invalid json")
        return self._payload


def test_read_json_payload_returns_dict():
    req = _FakeRequest(payload={"a": 1})
    assert asyncio.run(read_json_payload(req)) == {"a": 1}


def test_read_json_payload_returns_empty_for_non_dict():
    req = _FakeRequest(payload=["x"])
    assert asyncio.run(read_json_payload(req)) == {}


def test_read_json_payload_returns_empty_on_error():
    req = _FakeRequest(raises=True)
    assert asyncio.run(read_json_payload(req)) == {}


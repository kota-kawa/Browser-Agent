import asyncio
import json

from fastapi_app.routes import api_user_profile


class _FakeRequest:
    def __init__(self, payload):
        self._payload = payload

    async def json(self):
        return self._payload


def _body(response):
    return json.loads(response.body.decode("utf-8"))


def test_get_user_profile(monkeypatch):
    monkeypatch.setattr(api_user_profile, "load_user_profile", lambda: "profile")
    response = api_user_profile.get_user_profile()
    assert response.status_code == 200
    assert _body(response) == {"text": "profile"}


def test_update_user_profile_requires_text(monkeypatch):
    async def _fake_read_payload(_request):
        return {}

    monkeypatch.setattr(api_user_profile, "read_json_payload", _fake_read_payload)
    response = asyncio.run(api_user_profile.update_user_profile(_FakeRequest({})))
    assert response.status_code == 400
    assert "text" in _body(response)["error"]


def test_update_user_profile_success(monkeypatch):
    async def _fake_read_payload(_request):
        return {"text": "value"}

    monkeypatch.setattr(api_user_profile, "read_json_payload", _fake_read_payload)
    monkeypatch.setattr(api_user_profile, "save_user_profile", lambda text: f"saved:{text}")

    response = asyncio.run(api_user_profile.update_user_profile(_FakeRequest({"text": "value"})))
    assert response.status_code == 200
    assert _body(response) == {"status": "ok", "text": "saved:value"}


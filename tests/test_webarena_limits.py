import asyncio
import json

from fastapi_app.webarena import routes as webarena_routes


# EN: Define class `_FakeRequest`.
# JP: クラス `_FakeRequest` を定義する。
class _FakeRequest:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, payload):
        self._payload = payload
        self.client = type("C", (), {"host": "127.0.0.1"})()

    # EN: Define async function `json`.
    # JP: 非同期関数 `json` を定義する。
    async def json(self):
        return self._payload


# EN: Define class `_FakeController`.
# JP: クラス `_FakeController` を定義する。
class _FakeController:
    # EN: Define function `is_running`.
    # JP: 関数 `is_running` を定義する。
    def is_running(self):
        return False

    # EN: Define function `run`.
    # JP: 関数 `run` を定義する。
    def run(self, *_args, **_kwargs):
        raise AssertionError("run should not be called for over-limit prompt")


# EN: Define function `test_webarena_run_rejects_too_long_custom_intent`.
# JP: 関数 `test_webarena_run_rejects_too_long_custom_intent` を定義する。
def test_webarena_run_rejects_too_long_custom_intent(monkeypatch):
    monkeypatch.setattr(webarena_routes, "_LLM_INPUT_MAX_CHARS", 5)

    monkeypatch.setenv("ADMIN_API_TOKEN", "admin-secret")

    # Patch runtime import used inside run_task
    import sys
    import types as _types

    fake_runtime = _types.ModuleType("fastapi_app.services.agent_runtime")
    fake_runtime.get_agent_controller = lambda: _FakeController()
    monkeypatch.setitem(sys.modules, "fastapi_app.services.agent_runtime", fake_runtime)
    monkeypatch.setattr(webarena_routes, "_RUNTIME_SLOT_GUARD", type("G", (), {"acquire": lambda self: True, "release": lambda self: None})())
    monkeypatch.setattr(webarena_routes, "ip_rate_limit_guard", lambda _request: None)

    req = _FakeRequest({"custom_task": {"intent": "abcdef"}})
    res = asyncio.run(webarena_routes.run_task(req))
    assert res.status_code == 400
    payload = json.loads(res.body.decode("utf-8"))
    assert "5" in payload.get("error", "")


# EN: Define function `test_webarena_run_rejects_when_runtime_slot_unavailable`.
# JP: 関数 `test_webarena_run_rejects_when_runtime_slot_unavailable` を定義する。
def test_webarena_run_rejects_when_runtime_slot_unavailable(monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "admin-secret")
    monkeypatch.setattr(webarena_routes, "_RUNTIME_SLOT_GUARD", type("G", (), {"acquire": lambda self: False, "release": lambda self: None})())

    import sys
    import types as _types

    fake_runtime = _types.ModuleType("fastapi_app.services.agent_runtime")
    fake_runtime.get_agent_controller = lambda: _FakeController()
    monkeypatch.setitem(sys.modules, "fastapi_app.services.agent_runtime", fake_runtime)
    monkeypatch.setattr(webarena_routes, "ip_rate_limit_guard", lambda _request: None)

    req = _FakeRequest({"custom_task": {"intent": "valid", "start_url": "https://shopping"}})
    res = asyncio.run(webarena_routes.run_task(req))
    assert res.status_code == 429

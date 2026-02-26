import json

from fastapi_app.core.exceptions import AgentControllerError
from fastapi_app.routes import api_controls


# EN: Define class `_FakeController`.
# JP: クラス `_FakeController` を定義する。
class _FakeController:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, reset_error=None, pause_error=None, resume_error=None):
        self._reset_error = reset_error
        self._pause_error = pause_error
        self._resume_error = resume_error
        self.ensure_start_page_ready_calls = 0
        self.close_additional_tabs_calls = 0

    # EN: Define function `reset`.
    # JP: 関数 `reset` を定義する。
    def reset(self):
        if self._reset_error:
            raise self._reset_error

    # EN: Define function `ensure_start_page_ready`.
    # JP: 関数 `ensure_start_page_ready` を定義する。
    def ensure_start_page_ready(self):
        self.ensure_start_page_ready_calls += 1

    # EN: Define function `close_additional_tabs`.
    # JP: 関数 `close_additional_tabs` を定義する。
    def close_additional_tabs(self):
        self.close_additional_tabs_calls += 1

    # EN: Define function `pause`.
    # JP: 関数 `pause` を定義する。
    def pause(self):
        if self._pause_error:
            raise self._pause_error

    # EN: Define function `resume`.
    # JP: 関数 `resume` を定義する。
    def resume(self):
        if self._resume_error:
            raise self._resume_error


# EN: Define function `_body`.
# JP: 関数 `_body` を定義する。
def _body(response):
    return json.loads(response.body.decode("utf-8"))


# EN: Define function `test_reset_conversation_success_without_controller`.
# JP: 関数 `test_reset_conversation_success_without_controller` を定義する。
def test_reset_conversation_success_without_controller(monkeypatch):
    monkeypatch.setattr(api_controls, "get_controller_if_initialized", lambda: None)
    monkeypatch.setattr(api_controls, "_reset_history", lambda: [{"id": 1, "content": "x"}])

    response = api_controls.reset_conversation()
    assert response.status_code == 200
    assert _body(response)["messages"] == [{"id": 1, "content": "x"}]


# EN: Define function `test_reset_conversation_returns_400_on_controller_error`.
# JP: 関数 `test_reset_conversation_returns_400_on_controller_error` を定義する。
def test_reset_conversation_returns_400_on_controller_error(monkeypatch):
    controller = _FakeController(reset_error=AgentControllerError("bad reset"))
    monkeypatch.setattr(api_controls, "get_controller_if_initialized", lambda: controller)

    response = api_controls.reset_conversation()
    assert response.status_code == 400
    assert "bad reset" in _body(response)["error"]


# EN: Define function `test_reset_conversation_normalizes_browser_state`.
# JP: 関数 `test_reset_conversation_normalizes_browser_state` を定義する。
def test_reset_conversation_normalizes_browser_state(monkeypatch):
    controller = _FakeController()
    monkeypatch.setattr(api_controls, "get_controller_if_initialized", lambda: controller)
    monkeypatch.setattr(api_controls, "_reset_history", lambda: [])

    response = api_controls.reset_conversation()
    assert response.status_code == 200
    assert controller.ensure_start_page_ready_calls == 1
    assert controller.close_additional_tabs_calls == 1


# EN: Define function `test_pause_and_resume_success`.
# JP: 関数 `test_pause_and_resume_success` を定義する。
def test_pause_and_resume_success(monkeypatch):
    controller = _FakeController()
    monkeypatch.setattr(api_controls, "get_existing_controller", lambda: controller)

    pause_res = api_controls.pause_agent()
    resume_res = api_controls.resume_agent()

    assert pause_res.status_code == 200
    assert _body(pause_res)["status"] == "paused"
    assert resume_res.status_code == 200
    assert _body(resume_res)["status"] == "resumed"


# EN: Define function `test_pause_and_resume_return_400_for_agent_controller_error`.
# JP: 関数 `test_pause_and_resume_return_400_for_agent_controller_error` を定義する。
def test_pause_and_resume_return_400_for_agent_controller_error(monkeypatch):
    pause_controller = _FakeController(pause_error=AgentControllerError("cant pause"))
    resume_controller = _FakeController(resume_error=AgentControllerError("cant resume"))

    monkeypatch.setattr(api_controls, "get_existing_controller", lambda: pause_controller)
    pause_res = api_controls.pause_agent()
    assert pause_res.status_code == 400
    assert "cant pause" in _body(pause_res)["error"]

    monkeypatch.setattr(api_controls, "get_existing_controller", lambda: resume_controller)
    resume_res = api_controls.resume_agent()
    assert resume_res.status_code == 400
    assert "cant resume" in _body(resume_res)["error"]

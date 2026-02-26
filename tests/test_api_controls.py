# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.core.exceptions import AgentControllerError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.routes import api_controls


# EN: Define class `_FakeController`.
# JP: クラス `_FakeController` を定義する。
class _FakeController:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, reset_error=None, pause_error=None, resume_error=None):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._reset_error = reset_error
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._pause_error = pause_error
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._resume_error = resume_error

    # EN: Define function `reset`.
    # JP: 関数 `reset` を定義する。
    def reset(self):
        # EN: Branch logic based on a condition.
        # JP: 条件に応じて処理を分岐する。
        if self._reset_error:
            # EN: Raise an exception.
            # JP: 例外を送出する。
            raise self._reset_error

    # EN: Define function `pause`.
    # JP: 関数 `pause` を定義する。
    def pause(self):
        # EN: Branch logic based on a condition.
        # JP: 条件に応じて処理を分岐する。
        if self._pause_error:
            # EN: Raise an exception.
            # JP: 例外を送出する。
            raise self._pause_error

    # EN: Define function `resume`.
    # JP: 関数 `resume` を定義する。
    def resume(self):
        # EN: Branch logic based on a condition.
        # JP: 条件に応じて処理を分岐する。
        if self._resume_error:
            # EN: Raise an exception.
            # JP: 例外を送出する。
            raise self._resume_error


# EN: Define function `_body`.
# JP: 関数 `_body` を定義する。
def _body(response):
    # EN: Return a value from the function.
    # JP: 関数から値を返す。
    return json.loads(response.body.decode("utf-8"))


# EN: Define function `test_reset_conversation_success_without_controller`.
# JP: 関数 `test_reset_conversation_success_without_controller` を定義する。
def test_reset_conversation_success_without_controller(monkeypatch):
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_controls, "get_controller_if_initialized", lambda: None)
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_controls, "_reset_history", lambda: [{"id": 1, "content": "x"}])

    # EN: Assign value to response.
    # JP: response に値を代入する。
    response = api_controls.reset_conversation()
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert response.status_code == 200
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _body(response)["messages"] == [{"id": 1, "content": "x"}]


# EN: Define function `test_reset_conversation_returns_400_on_controller_error`.
# JP: 関数 `test_reset_conversation_returns_400_on_controller_error` を定義する。
def test_reset_conversation_returns_400_on_controller_error(monkeypatch):
    # EN: Assign value to controller.
    # JP: controller に値を代入する。
    controller = _FakeController(reset_error=AgentControllerError("bad reset"))
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_controls, "get_controller_if_initialized", lambda: controller)

    # EN: Assign value to response.
    # JP: response に値を代入する。
    response = api_controls.reset_conversation()
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert response.status_code == 400
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "bad reset" in _body(response)["error"]


# EN: Define function `test_pause_and_resume_success`.
# JP: 関数 `test_pause_and_resume_success` を定義する。
def test_pause_and_resume_success(monkeypatch):
    # EN: Assign value to controller.
    # JP: controller に値を代入する。
    controller = _FakeController()
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_controls, "get_existing_controller", lambda: controller)

    # EN: Assign value to pause_res.
    # JP: pause_res に値を代入する。
    pause_res = api_controls.pause_agent()
    # EN: Assign value to resume_res.
    # JP: resume_res に値を代入する。
    resume_res = api_controls.resume_agent()

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert pause_res.status_code == 200
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _body(pause_res)["status"] == "paused"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert resume_res.status_code == 200
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _body(resume_res)["status"] == "resumed"


# EN: Define function `test_pause_and_resume_return_400_for_agent_controller_error`.
# JP: 関数 `test_pause_and_resume_return_400_for_agent_controller_error` を定義する。
def test_pause_and_resume_return_400_for_agent_controller_error(monkeypatch):
    # EN: Assign value to pause_controller.
    # JP: pause_controller に値を代入する。
    pause_controller = _FakeController(pause_error=AgentControllerError("cant pause"))
    # EN: Assign value to resume_controller.
    # JP: resume_controller に値を代入する。
    resume_controller = _FakeController(resume_error=AgentControllerError("cant resume"))

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_controls, "get_existing_controller", lambda: pause_controller)
    # EN: Assign value to pause_res.
    # JP: pause_res に値を代入する。
    pause_res = api_controls.pause_agent()
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert pause_res.status_code == 400
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "cant pause" in _body(pause_res)["error"]

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_controls, "get_existing_controller", lambda: resume_controller)
    # EN: Assign value to resume_res.
    # JP: resume_res に値を代入する。
    resume_res = api_controls.resume_agent()
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert resume_res.status_code == 400
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "cant resume" in _body(resume_res)["error"]


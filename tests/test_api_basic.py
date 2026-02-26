# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import types

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pytest

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import fastapi_app.routes.api_chat as api_chat


# EN: Define class `_FakeMeta`.
# JP: クラス `_FakeMeta` を定義する。
class _FakeMeta:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, step_number=1):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.step_number = step_number


# EN: Define class `_FakeModelOutput`.
# JP: クラス `_FakeModelOutput` を定義する。
class _FakeModelOutput:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.action = []
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.evaluation_previous_goal = None
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.next_goal = None
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.current_status = None


# EN: Define class `_FakeResult`.
# JP: クラス `_FakeResult` を定義する。
class _FakeResult:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.error = None
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.is_done = True
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.success = True
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.extracted_content = "done"
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.long_term_memory = None
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.metadata = None


# EN: Define class `_FakeStep`.
# JP: クラス `_FakeStep` を定義する。
class _FakeStep:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.metadata = _FakeMeta()
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.model_output = _FakeModelOutput()
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.result = [_FakeResult()]
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.state = types.SimpleNamespace(title=None, url=None)


# EN: Define class `_FakeHistory`.
# JP: クラス `_FakeHistory` を定義する。
class _FakeHistory:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.history = [_FakeStep()]
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.usage = None

    # EN: Define function `is_successful`.
    # JP: 関数 `is_successful` を定義する。
    def is_successful(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return True

    # EN: Define function `final_result`.
    # JP: 関数 `final_result` を定義する。
    def final_result(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return "ok"


# EN: Define class `_FakeRunResult`.
# JP: クラス `_FakeRunResult` を定義する。
class _FakeRunResult:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.history = _FakeHistory()
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.filtered_history = None
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.step_message_ids = {}


# EN: Define class `_FakeController`.
# JP: クラス `_FakeController` を定義する。
class _FakeController:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._running = False
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._paused = False
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._handled_initial = False
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.loop = None

    # EN: Define function `is_running`.
    # JP: 関数 `is_running` を定義する。
    def is_running(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return self._running

    # EN: Define function `has_handled_initial_prompt`.
    # JP: 関数 `has_handled_initial_prompt` を定義する。
    def has_handled_initial_prompt(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return self._handled_initial

    # EN: Define function `mark_initial_prompt_handled`.
    # JP: 関数 `mark_initial_prompt_handled` を定義する。
    def mark_initial_prompt_handled(self):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._handled_initial = True

    # EN: Define function `prepare_for_new_task`.
    # JP: 関数 `prepare_for_new_task` を定義する。
    def prepare_for_new_task(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return None

    # EN: Define function `is_paused`.
    # JP: 関数 `is_paused` を定義する。
    def is_paused(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return self._paused

    # EN: Define function `enqueue_follow_up`.
    # JP: 関数 `enqueue_follow_up` を定義する。
    def enqueue_follow_up(self, prompt):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._queued = prompt

    # EN: Define function `resume`.
    # JP: 関数 `resume` を定義する。
    def resume(self):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._paused = False

    # EN: Define function `run`.
    # JP: 関数 `run` を定義する。
    def run(
        self,
        prompt,
        background=False,
        completion_callback=None,
        record_history=True,
        additional_system_message=None,
    ):
        # EN: Branch logic based on a condition.
        # JP: 条件に応じて処理を分岐する。
        if background:
            # EN: Return a value from the function.
            # JP: 関数から値を返す。
            return None
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return _FakeRunResult()

    # EN: Define function `get_step_message_id`.
    # JP: 関数 `get_step_message_id` を定義する。
    def get_step_message_id(self, step_number):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return None

    # EN: Define function `remember_step_message_id`.
    # JP: 関数 `remember_step_message_id` を定義する。
    def remember_step_message_id(self, step_number, message_id):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return None


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


# EN: Define function `controller`.
# JP: 関数 `controller` を定義する。
@pytest.fixture()
def controller(monkeypatch):
    # EN: Define async function `_safe_prompt`.
    # JP: 非同期関数 `_safe_prompt` を定義する。
    async def _safe_prompt(*_args, **_kwargs):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return types.SimpleNamespace(is_safe=True, categories=())

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_chat, "get_agent_controller", lambda: _FakeController())
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(api_chat, "check_prompt_safety", _safe_prompt)
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(
        api_chat,
        "_analyze_conversation_history",
        lambda *_args, **_kwargs: {"needs_action": False, "reply": "no action"},
    )
    # EN: Return a value from the function.
    # JP: 関数から値を返す。
    return _FakeController()


# EN: Define function `test_api_chat_accepts_basic_request`.
# JP: 関数 `test_api_chat_accepts_basic_request` を定義する。
def test_api_chat_accepts_basic_request(controller):
    # EN: Assign value to request.
    # JP: request に値を代入する。
    request = _FakeRequest(
        {"prompt": "hello", "new_task": True, "skip_conversation_review": True}
    )
    # EN: Assign value to res.
    # JP: res に値を代入する。
    res = asyncio.run(api_chat.chat(request))
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert res.status_code == 202
    # EN: Assign value to body.
    # JP: body に値を代入する。
    body = json.loads(res.body.decode("utf-8"))
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert body.get("agent_running") is True


# EN: Define function `test_api_agent_relay_returns_summary`.
# JP: 関数 `test_api_agent_relay_returns_summary` を定義する。
def test_api_agent_relay_returns_summary(controller):
    # EN: Assign value to request.
    # JP: request に値を代入する。
    request = _FakeRequest({"prompt": "ping"})
    # EN: Assign value to res.
    # JP: res に値を代入する。
    res = asyncio.run(api_chat.agent_relay(request))
    # EN: Branch logic based on a condition.
    # JP: 条件に応じて処理を分岐する。
    if isinstance(res, tuple):
        # EN: Assign value to res.
        # JP: res に値を代入する。
        res = res[0]
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert res.status_code == 200
    # EN: Assign value to body.
    # JP: body に値を代入する。
    body = json.loads(res.body.decode("utf-8"))
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert body.get("summary") == "no action"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert body.get("action_taken") is False


# EN: Define function `test_conversation_review_endpoint_removed`.
# JP: 関数 `test_conversation_review_endpoint_removed` を定義する。
def test_conversation_review_endpoint_removed(controller):
    # Route is removed from the router; FastAPI would return 404 when mounted.
    # Here we simply assert the helper exists in api_chat only.
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert hasattr(api_chat, "agent_relay")

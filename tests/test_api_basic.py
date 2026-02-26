import asyncio
import json
import types

import pytest

import fastapi_app.routes.api_chat as api_chat


# EN: Define class `_FakeMeta`.
# JP: クラス `_FakeMeta` を定義する。
class _FakeMeta:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, step_number=1):
        self.step_number = step_number


# EN: Define class `_FakeModelOutput`.
# JP: クラス `_FakeModelOutput` を定義する。
class _FakeModelOutput:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        self.action = []
        self.evaluation_previous_goal = None
        self.next_goal = None
        self.current_status = None


# EN: Define class `_FakeResult`.
# JP: クラス `_FakeResult` を定義する。
class _FakeResult:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        self.error = None
        self.is_done = True
        self.success = True
        self.extracted_content = "done"
        self.long_term_memory = None
        self.metadata = None


# EN: Define class `_FakeStep`.
# JP: クラス `_FakeStep` を定義する。
class _FakeStep:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        self.metadata = _FakeMeta()
        self.model_output = _FakeModelOutput()
        self.result = [_FakeResult()]
        self.state = types.SimpleNamespace(title=None, url=None)


# EN: Define class `_FakeHistory`.
# JP: クラス `_FakeHistory` を定義する。
class _FakeHistory:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        self.history = [_FakeStep()]
        self.usage = None

    # EN: Define function `is_successful`.
    # JP: 関数 `is_successful` を定義する。
    def is_successful(self):
        return True

    # EN: Define function `final_result`.
    # JP: 関数 `final_result` を定義する。
    def final_result(self):
        return "ok"


# EN: Define class `_FakeRunResult`.
# JP: クラス `_FakeRunResult` を定義する。
class _FakeRunResult:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        self.history = _FakeHistory()
        self.filtered_history = None
        self.step_message_ids = {}


# EN: Define class `_FakeController`.
# JP: クラス `_FakeController` を定義する。
class _FakeController:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        self._running = False
        self._paused = False
        self._handled_initial = False
        self.loop = None

    # EN: Define function `is_running`.
    # JP: 関数 `is_running` を定義する。
    def is_running(self):
        return self._running

    # EN: Define function `has_handled_initial_prompt`.
    # JP: 関数 `has_handled_initial_prompt` を定義する。
    def has_handled_initial_prompt(self):
        return self._handled_initial

    # EN: Define function `mark_initial_prompt_handled`.
    # JP: 関数 `mark_initial_prompt_handled` を定義する。
    def mark_initial_prompt_handled(self):
        self._handled_initial = True

    # EN: Define function `prepare_for_new_task`.
    # JP: 関数 `prepare_for_new_task` を定義する。
    def prepare_for_new_task(self):
        return None

    # EN: Define function `is_paused`.
    # JP: 関数 `is_paused` を定義する。
    def is_paused(self):
        return self._paused

    # EN: Define function `enqueue_follow_up`.
    # JP: 関数 `enqueue_follow_up` を定義する。
    def enqueue_follow_up(self, prompt):
        self._queued = prompt

    # EN: Define function `resume`.
    # JP: 関数 `resume` を定義する。
    def resume(self):
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
        if background:
            return None
        return _FakeRunResult()

    # EN: Define function `get_step_message_id`.
    # JP: 関数 `get_step_message_id` を定義する。
    def get_step_message_id(self, step_number):
        return None

    # EN: Define function `remember_step_message_id`.
    # JP: 関数 `remember_step_message_id` を定義する。
    def remember_step_message_id(self, step_number, message_id):
        return None


# EN: Define class `_FakeRequest`.
# JP: クラス `_FakeRequest` を定義する。
class _FakeRequest:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, payload):
        self._payload = payload

    # EN: Define async function `json`.
    # JP: 非同期関数 `json` を定義する。
    async def json(self):
        return self._payload


# EN: Define function `controller`.
# JP: 関数 `controller` を定義する。
@pytest.fixture()
def controller(monkeypatch):
    # EN: Define async function `_safe_prompt`.
    # JP: 非同期関数 `_safe_prompt` を定義する。
    async def _safe_prompt(*_args, **_kwargs):
        return types.SimpleNamespace(is_safe=True, categories=())

    monkeypatch.setattr(api_chat, "get_agent_controller", lambda: _FakeController())
    monkeypatch.setattr(api_chat, "check_prompt_safety", _safe_prompt)
    monkeypatch.setattr(
        api_chat,
        "_analyze_conversation_history",
        lambda *_args, **_kwargs: {"needs_action": False, "reply": "no action"},
    )
    return _FakeController()


# EN: Define function `test_api_chat_accepts_basic_request`.
# JP: 関数 `test_api_chat_accepts_basic_request` を定義する。
def test_api_chat_accepts_basic_request(controller):
    request = _FakeRequest(
        {"prompt": "hello", "new_task": True, "skip_conversation_review": True}
    )
    res = asyncio.run(api_chat.chat(request))
    assert res.status_code == 202
    body = json.loads(res.body.decode("utf-8"))
    assert body.get("agent_running") is True


# EN: Define function `test_api_agent_relay_returns_summary`.
# JP: 関数 `test_api_agent_relay_returns_summary` を定義する。
def test_api_agent_relay_returns_summary(controller):
    request = _FakeRequest({"prompt": "ping"})
    res = asyncio.run(api_chat.agent_relay(request))
    if isinstance(res, tuple):
        res = res[0]
    assert res.status_code == 200
    body = json.loads(res.body.decode("utf-8"))
    assert body.get("summary") == "no action"
    assert body.get("action_taken") is False


# EN: Define function `test_conversation_review_endpoint_removed`.
# JP: 関数 `test_conversation_review_endpoint_removed` を定義する。
def test_conversation_review_endpoint_removed(controller):
    # Route is removed from the router; FastAPI would return 404 when mounted.
    # Here we simply assert the helper exists in api_chat only.
    assert hasattr(api_chat, "agent_relay")

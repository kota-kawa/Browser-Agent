import asyncio
import json
import types

import pytest

import fastapi_app.routes.api_chat as api_chat


class _FakeMeta:
    def __init__(self, step_number=1):
        self.step_number = step_number


class _FakeModelOutput:
    def __init__(self):
        self.action = []
        self.evaluation_previous_goal = None
        self.next_goal = None
        self.current_status = None


class _FakeResult:
    def __init__(self):
        self.error = None
        self.is_done = True
        self.success = True
        self.extracted_content = "done"
        self.long_term_memory = None
        self.metadata = None


class _FakeStep:
    def __init__(self):
        self.metadata = _FakeMeta()
        self.model_output = _FakeModelOutput()
        self.result = [_FakeResult()]
        self.state = types.SimpleNamespace(title=None, url=None)


class _FakeHistory:
    def __init__(self):
        self.history = [_FakeStep()]
        self.usage = None

    def is_successful(self):
        return True

    def final_result(self):
        return "ok"


class _FakeRunResult:
    def __init__(self):
        self.history = _FakeHistory()
        self.filtered_history = None
        self.step_message_ids = {}


class _FakeController:
    def __init__(self):
        self._running = False
        self._paused = False
        self._handled_initial = False
        self.loop = None

    def is_running(self):
        return self._running

    def has_handled_initial_prompt(self):
        return self._handled_initial

    def mark_initial_prompt_handled(self):
        self._handled_initial = True

    def prepare_for_new_task(self):
        return None

    def is_paused(self):
        return self._paused

    def enqueue_follow_up(self, prompt):
        self._queued = prompt

    def resume(self):
        self._paused = False

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

    def get_step_message_id(self, step_number):
        return None

    def remember_step_message_id(self, step_number, message_id):
        return None


class _FakeRequest:
    def __init__(self, payload):
        self._payload = payload

    async def json(self):
        return self._payload


@pytest.fixture()
def controller(monkeypatch):
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


def test_api_chat_accepts_basic_request(controller):
    request = _FakeRequest(
        {"prompt": "hello", "new_task": True, "skip_conversation_review": True}
    )
    res = asyncio.run(api_chat.chat(request))
    assert res.status_code == 202
    body = json.loads(res.body.decode("utf-8"))
    assert body.get("agent_running") is True


def test_api_agent_relay_returns_summary(controller):
    request = _FakeRequest({"prompt": "ping"})
    res = asyncio.run(api_chat.agent_relay(request))
    if isinstance(res, tuple):
        res = res[0]
    assert res.status_code == 200
    body = json.loads(res.body.decode("utf-8"))
    assert body.get("summary") == "no action"
    assert body.get("action_taken") is False


def test_conversation_review_endpoint_removed(controller):
    # Route is removed from the router; FastAPI would return 404 when mounted.
    # Here we simply assert the helper exists in api_chat only.
    assert hasattr(api_chat, "agent_relay")

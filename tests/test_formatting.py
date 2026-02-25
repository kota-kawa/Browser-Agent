import types

from fastapi_app.services import formatting


class _FakeAction:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self, exclude_none=True):
        return self._payload


class _FakeHistory:
    def __init__(self, steps, success=True, final="done"):
        self.history = steps
        self._success = success
        self._final = final

    def is_successful(self):
        return self._success

    def final_result(self):
        return self._final


def _build_step(step_number=1):
    return types.SimpleNamespace(
        metadata=types.SimpleNamespace(step_number=step_number),
        state=types.SimpleNamespace(title="page", url="https://example.com"),
        model_output=types.SimpleNamespace(
            action=[_FakeAction({"click": {"selector": "#submit"}})],
            evaluation_previous_goal="ok",
            next_goal="next",
            current_status="running",
            memory="m",
            persistent_notes="n",
        ),
        result=[
            types.SimpleNamespace(
                error=None,
                is_done=True,
                success=True,
                extracted_content="value",
                long_term_memory="memo",
                metadata=None,
            )
        ],
    )


def test_append_final_response_notice_is_idempotent():
    message = formatting._append_final_response_notice("summary")
    again = formatting._append_final_response_notice(message)

    assert formatting._FINAL_RESPONSE_MARKER in message
    assert message == again


def test_format_action_and_result():
    action_text = formatting._format_action(_FakeAction({"type": {"a": 1, "b": "x"}}))
    unknown_action = formatting._format_action(_FakeAction({}))

    assert action_text == 'type(a=1, b=x)'
    assert unknown_action == "不明なアクション"

    error_result = types.SimpleNamespace(
        error=" failed ",
        is_done=False,
        success=False,
        extracted_content=None,
        long_term_memory=None,
        metadata=None,
    )
    ok_result = types.SimpleNamespace(
        error=None,
        is_done=True,
        success=True,
        extracted_content=" data ",
        long_term_memory=" memo ",
        metadata=None,
    )

    assert formatting._format_result(error_result) == "failed"
    assert formatting._format_result(ok_result) == "完了[成功] / data / memo"


def test_format_history_messages_and_summary():
    step1 = _build_step(step_number=1)
    step2 = _build_step(step_number=0)  # invalid step number -> normalized
    history = _FakeHistory([step1, step2], success=True, final="final answer")

    messages = formatting._format_history_messages(history)
    assert messages[0][0] == 1
    assert messages[1][0] == 2
    assert "アクション: click(selector=#submit)" in messages[0][1]

    summary = formatting._summarize_history(history)
    assert "2ステップ" in summary
    assert "最終報告: final answer" in summary
    assert "最終URL: https://example.com" in summary
    assert formatting._FINAL_RESPONSE_MARKER in summary


def test_format_step_plan_includes_fields():
    model_output = types.SimpleNamespace(
        evaluation_previous_goal="eval",
        memory="memory",
        next_goal="goal",
        current_status="status",
        persistent_notes="notes",
    )
    state = types.SimpleNamespace()

    text = formatting._format_step_plan(3, state, model_output)
    assert "ステップ3" in text
    assert "評価: eval" in text
    assert "メモリ: memory" in text
    assert "次の目標: goal" in text
    assert "現在の状況: status" in text
    assert "永続メモ: notes" in text


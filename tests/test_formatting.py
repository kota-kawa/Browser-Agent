# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import types

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.services import formatting


# EN: Define class `_FakeAction`.
# JP: クラス `_FakeAction` を定義する。
class _FakeAction:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, payload):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._payload = payload

    # EN: Define function `model_dump`.
    # JP: 関数 `model_dump` を定義する。
    def model_dump(self, exclude_none=True):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return self._payload


# EN: Define class `_FakeHistory`.
# JP: クラス `_FakeHistory` を定義する。
class _FakeHistory:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, steps, success=True, final="done"):
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self.history = steps
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._success = success
        # EN: Assign value to target variable.
        # JP: target variable に値を代入する。
        self._final = final

    # EN: Define function `is_successful`.
    # JP: 関数 `is_successful` を定義する。
    def is_successful(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return self._success

    # EN: Define function `final_result`.
    # JP: 関数 `final_result` を定義する。
    def final_result(self):
        # EN: Return a value from the function.
        # JP: 関数から値を返す。
        return self._final


# EN: Define function `_build_step`.
# JP: 関数 `_build_step` を定義する。
def _build_step(step_number=1):
    # EN: Return a value from the function.
    # JP: 関数から値を返す。
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


# EN: Define function `test_append_final_response_notice_is_idempotent`.
# JP: 関数 `test_append_final_response_notice_is_idempotent` を定義する。
def test_append_final_response_notice_is_idempotent():
    # EN: Assign value to message.
    # JP: message に値を代入する。
    message = formatting._append_final_response_notice("summary")
    # EN: Assign value to again.
    # JP: again に値を代入する。
    again = formatting._append_final_response_notice(message)

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert formatting._FINAL_RESPONSE_MARKER in message
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert message == again


# EN: Define function `test_format_action_and_result`.
# JP: 関数 `test_format_action_and_result` を定義する。
def test_format_action_and_result():
    # EN: Assign value to action_text.
    # JP: action_text に値を代入する。
    action_text = formatting._format_action(_FakeAction({"type": {"a": 1, "b": "x"}}))
    # EN: Assign value to unknown_action.
    # JP: unknown_action に値を代入する。
    unknown_action = formatting._format_action(_FakeAction({}))

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert action_text == 'type(a=1, b=x)'
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert unknown_action == "不明なアクション"

    # EN: Assign value to error_result.
    # JP: error_result に値を代入する。
    error_result = types.SimpleNamespace(
        error=" failed ",
        is_done=False,
        success=False,
        extracted_content=None,
        long_term_memory=None,
        metadata=None,
    )
    # EN: Assign value to ok_result.
    # JP: ok_result に値を代入する。
    ok_result = types.SimpleNamespace(
        error=None,
        is_done=True,
        success=True,
        extracted_content=" data ",
        long_term_memory=" memo ",
        metadata=None,
    )

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert formatting._format_result(error_result) == "failed"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert formatting._format_result(ok_result) == "完了[成功] / data / memo"


# EN: Define function `test_format_history_messages_and_summary`.
# JP: 関数 `test_format_history_messages_and_summary` を定義する。
def test_format_history_messages_and_summary():
    # EN: Assign value to step1.
    # JP: step1 に値を代入する。
    step1 = _build_step(step_number=1)
    # EN: Assign value to step2.
    # JP: step2 に値を代入する。
    step2 = _build_step(step_number=0)  # invalid step number -> normalized
    # EN: Assign value to history.
    # JP: history に値を代入する。
    history = _FakeHistory([step1, step2], success=True, final="final answer")

    # EN: Assign value to messages.
    # JP: messages に値を代入する。
    messages = formatting._format_history_messages(history)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert messages[0][0] == 1
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert messages[1][0] == 2
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "アクション: click(selector=#submit)" in messages[0][1]

    # EN: Assign value to summary.
    # JP: summary に値を代入する。
    summary = formatting._summarize_history(history)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "2ステップ" in summary
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "最終報告: final answer" in summary
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "最終URL: https://example.com" in summary
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert formatting._FINAL_RESPONSE_MARKER in summary


# EN: Define function `test_format_step_plan_includes_fields`.
# JP: 関数 `test_format_step_plan_includes_fields` を定義する。
def test_format_step_plan_includes_fields():
    # EN: Assign value to model_output.
    # JP: model_output に値を代入する。
    model_output = types.SimpleNamespace(
        evaluation_previous_goal="eval",
        memory="memory",
        next_goal="goal",
        current_status="status",
        persistent_notes="notes",
    )
    # EN: Assign value to state.
    # JP: state に値を代入する。
    state = types.SimpleNamespace()

    # EN: Assign value to text.
    # JP: text に値を代入する。
    text = formatting._format_step_plan(3, state, model_output)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "ステップ3" in text
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "評価: eval" in text
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "メモリ: memory" in text
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "次の目標: goal" in text
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "現在の状況: status" in text
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "永続メモ: notes" in text


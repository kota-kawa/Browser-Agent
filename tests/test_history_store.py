# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.services import history_store


# EN: Define function `setup_function`.
# JP: 関数 `setup_function` を定義する。
def setup_function():
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    history_store._reset_history()


# EN: Define function `test_append_and_copy_history`.
# JP: 関数 `test_append_and_copy_history` を定義する。
def test_append_and_copy_history():
    # EN: Assign value to first.
    # JP: first に値を代入する。
    first = history_store._append_history_message("user", "hello")
    # EN: Assign value to second.
    # JP: second に値を代入する。
    second = history_store._append_history_message("assistant", "world")

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert first["id"] == 0
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert second["id"] == 1

    # EN: Assign value to snapshot.
    # JP: snapshot に値を代入する。
    snapshot = history_store._copy_history()
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert len(snapshot) == 2
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert snapshot[0]["content"] == "hello"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert snapshot[1]["content"] == "world"

    # Copy should not mutate internal state.
    # EN: Assign value to target variable.
    # JP: target variable に値を代入する。
    snapshot[0]["content"] = "changed"
    # EN: Assign value to internal.
    # JP: internal に値を代入する。
    internal = history_store._copy_history()
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert internal[0]["content"] == "hello"


# EN: Define function `test_update_history_message_and_missing_id`.
# JP: 関数 `test_update_history_message_and_missing_id` を定義する。
def test_update_history_message_and_missing_id():
    # EN: Assign value to stored.
    # JP: stored に値を代入する。
    stored = history_store._append_history_message("assistant", "before")
    # EN: Assign value to updated.
    # JP: updated に値を代入する。
    updated = history_store._update_history_message(int(stored["id"]), "after")
    # EN: Assign value to missing.
    # JP: missing に値を代入する。
    missing = history_store._update_history_message(9999, "ignored")

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert updated is not None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert updated["content"] == "after"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert missing is None


# EN: Define function `test_broadcaster_events_for_message_update_and_reset`.
# JP: 関数 `test_broadcaster_events_for_message_update_and_reset` を定義する。
def test_broadcaster_events_for_message_update_and_reset():
    # EN: Assign value to listener.
    # JP: listener に値を代入する。
    listener = history_store._broadcaster.subscribe()
    # EN: Handle exceptions around this block.
    # JP: このブロックで例外処理を行う。
    try:
        # EN: Assign value to message.
        # JP: message に値を代入する。
        message = history_store._append_history_message("user", "ping")
        # EN: Assign value to msg_event.
        # JP: msg_event に値を代入する。
        msg_event = listener.get(timeout=0.2)
        # EN: Validate a required condition.
        # JP: 必須条件を検証する。
        assert msg_event["type"] == "message"
        # EN: Validate a required condition.
        # JP: 必須条件を検証する。
        assert msg_event["payload"]["content"] == "ping"

        # EN: Evaluate an expression.
        # JP: 式を評価する。
        history_store._update_history_message(int(message["id"]), "pong")
        # EN: Assign value to update_event.
        # JP: update_event に値を代入する。
        update_event = listener.get(timeout=0.2)
        # EN: Validate a required condition.
        # JP: 必須条件を検証する。
        assert update_event["type"] == "update"
        # EN: Validate a required condition.
        # JP: 必須条件を検証する。
        assert update_event["payload"]["content"] == "pong"

        # EN: Evaluate an expression.
        # JP: 式を評価する。
        history_store._reset_history()
        # EN: Assign value to reset_event.
        # JP: reset_event に値を代入する。
        reset_event = listener.get(timeout=0.2)
        # EN: Validate a required condition.
        # JP: 必須条件を検証する。
        assert reset_event["type"] == "reset"
    finally:
        # EN: Evaluate an expression.
        # JP: 式を評価する。
        history_store._broadcaster.unsubscribe(listener)


from fastapi_app.services import history_store


# EN: Define function `setup_function`.
# JP: 関数 `setup_function` を定義する。
def setup_function():
    history_store._reset_history()


# EN: Define function `test_append_and_copy_history`.
# JP: 関数 `test_append_and_copy_history` を定義する。
def test_append_and_copy_history():
    first = history_store._append_history_message("user", "hello")
    second = history_store._append_history_message("assistant", "world")

    assert first["id"] == 0
    assert second["id"] == 1

    snapshot = history_store._copy_history()
    assert len(snapshot) == 2
    assert snapshot[0]["content"] == "hello"
    assert snapshot[1]["content"] == "world"

    # Copy should not mutate internal state.
    snapshot[0]["content"] = "changed"
    internal = history_store._copy_history()
    assert internal[0]["content"] == "hello"


# EN: Define function `test_update_history_message_and_missing_id`.
# JP: 関数 `test_update_history_message_and_missing_id` を定義する。
def test_update_history_message_and_missing_id():
    stored = history_store._append_history_message("assistant", "before")
    updated = history_store._update_history_message(int(stored["id"]), "after")
    missing = history_store._update_history_message(9999, "ignored")

    assert updated is not None
    assert updated["content"] == "after"
    assert missing is None


# EN: Define function `test_broadcaster_events_for_message_update_and_reset`.
# JP: 関数 `test_broadcaster_events_for_message_update_and_reset` を定義する。
def test_broadcaster_events_for_message_update_and_reset():
    listener = history_store._broadcaster.subscribe()
    try:
        message = history_store._append_history_message("user", "ping")
        msg_event = listener.get(timeout=0.2)
        assert msg_event["type"] == "message"
        assert msg_event["payload"]["content"] == "ping"

        history_store._update_history_message(int(message["id"]), "pong")
        update_event = listener.get(timeout=0.2)
        assert update_event["type"] == "update"
        assert update_event["payload"]["content"] == "pong"

        history_store._reset_history()
        reset_event = listener.get(timeout=0.2)
        assert reset_event["type"] == "reset"
    finally:
        history_store._broadcaster.unsubscribe(listener)


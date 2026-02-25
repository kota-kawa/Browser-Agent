import pytest

from fastapi_app.services import conversation_review as review


def test_normalize_analysis_payload_fills_defaults():
    assert review._normalize_analysis_payload(None) == {}

    payload = {
        "reply": "回答",
        "action_type": "unknown",
    }
    normalized = review._normalize_analysis_payload(payload)

    assert normalized["should_reply"] is True
    assert normalized["reply"] == "回答"
    assert normalized["action_type"] is None
    assert normalized["needs_action"] is False
    assert normalized["reason"] == "LLM output did not include a reason."


def test_extract_json_from_text_with_code_block_and_raw():
    from_block = review._extract_json_from_text('```json\n{"needs_action": false, "reply": "ok"}\n```')
    assert isinstance(from_block, dict)
    assert from_block["reply"] == "ok"

    from_raw = review._extract_json_from_text('prefix {"needs_action": true, "reply": "go"} suffix')
    assert isinstance(from_raw, dict)
    assert from_raw["needs_action"] is True


def test_get_completion_payload_supports_multiple_shapes():
    class CompletionResp:
        completion = "a"

    class ResultResp:
        result = "b"

    assert review._get_completion_payload(CompletionResp()) == "a"
    assert review._get_completion_payload(ResultResp()) == "b"
    assert review._get_completion_payload({"completion": "c"}) == "c"
    assert review._get_completion_payload({"result": "d"}) == "d"

    with pytest.raises(AttributeError):
        review._get_completion_payload(object())


def test_trim_conversation_history_keeps_anchor_and_recent_tail():
    history = [
        {"id": 1, "role": "system", "content": "s"},
        {"id": 2, "role": "user", "content": "first question"},
        {"id": 3, "role": "assistant", "content": "answer1"},
        {"id": 4, "role": "user", "content": "follow up"},
        {"id": 5, "role": "assistant", "content": "answer2"},
    ]
    trimmed = review._trim_conversation_history(history, window_size=2)

    assert trimmed[0]["id"] == 2
    assert [item["id"] for item in trimmed] == [2, 4, 5]


def test_trim_conversation_history_deduplicates_without_id():
    repeated = {"role": "user", "content": "same", "timestamp": "t1"}
    history = [repeated, repeated, {"role": "assistant", "content": "x", "timestamp": "t2"}]
    trimmed = review._trim_conversation_history(history, window_size=10)

    assert len(trimmed) == 2
    assert trimmed[0]["role"] == "user"
    assert trimmed[1]["role"] == "assistant"


def test_refusal_detection_and_stringify_reply():
    assert review._looks_like_refusal("I cannot answer this request")
    assert not review._looks_like_refusal("これは通常の回答です")

    assert review._stringify_reply("  text  ") == "text"
    assert review._stringify_reply({"content": "  body  "}) == "body"
    assert review._stringify_reply({"x": 1}) == '{"x": 1}'


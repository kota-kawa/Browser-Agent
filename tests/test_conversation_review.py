# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pytest

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.services import conversation_review as review


# EN: Define function `test_normalize_analysis_payload_fills_defaults`.
# JP: 関数 `test_normalize_analysis_payload_fills_defaults` を定義する。
def test_normalize_analysis_payload_fills_defaults():
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._normalize_analysis_payload(None) == {}

    # EN: Assign value to payload.
    # JP: payload に値を代入する。
    payload = {
        "reply": "回答",
        "action_type": "unknown",
    }
    # EN: Assign value to normalized.
    # JP: normalized に値を代入する。
    normalized = review._normalize_analysis_payload(payload)

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert normalized["should_reply"] is True
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert normalized["reply"] == "回答"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert normalized["action_type"] is None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert normalized["needs_action"] is False
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert normalized["reason"] == "LLM output did not include a reason."


# EN: Define function `test_extract_json_from_text_with_code_block_and_raw`.
# JP: 関数 `test_extract_json_from_text_with_code_block_and_raw` を定義する。
def test_extract_json_from_text_with_code_block_and_raw():
    # EN: Assign value to from_block.
    # JP: from_block に値を代入する。
    from_block = review._extract_json_from_text('```json\n{"needs_action": false, "reply": "ok"}\n```')
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert isinstance(from_block, dict)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert from_block["reply"] == "ok"

    # EN: Assign value to from_raw.
    # JP: from_raw に値を代入する。
    from_raw = review._extract_json_from_text('prefix {"needs_action": true, "reply": "go"} suffix')
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert isinstance(from_raw, dict)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert from_raw["needs_action"] is True


# EN: Define function `test_get_completion_payload_supports_multiple_shapes`.
# JP: 関数 `test_get_completion_payload_supports_multiple_shapes` を定義する。
def test_get_completion_payload_supports_multiple_shapes():
    # EN: Define class `CompletionResp`.
    # JP: クラス `CompletionResp` を定義する。
    class CompletionResp:
        # EN: Assign value to completion.
        # JP: completion に値を代入する。
        completion = "a"

    # EN: Define class `ResultResp`.
    # JP: クラス `ResultResp` を定義する。
    class ResultResp:
        # EN: Assign value to result.
        # JP: result に値を代入する。
        result = "b"

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._get_completion_payload(CompletionResp()) == "a"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._get_completion_payload(ResultResp()) == "b"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._get_completion_payload({"completion": "c"}) == "c"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._get_completion_payload({"result": "d"}) == "d"

    # EN: Execute logic with managed resources.
    # JP: リソース管理付きで処理を実行する。
    with pytest.raises(AttributeError):
        # EN: Evaluate an expression.
        # JP: 式を評価する。
        review._get_completion_payload(object())


# EN: Define function `test_trim_conversation_history_keeps_anchor_and_recent_tail`.
# JP: 関数 `test_trim_conversation_history_keeps_anchor_and_recent_tail` を定義する。
def test_trim_conversation_history_keeps_anchor_and_recent_tail():
    # EN: Assign value to history.
    # JP: history に値を代入する。
    history = [
        {"id": 1, "role": "system", "content": "s"},
        {"id": 2, "role": "user", "content": "first question"},
        {"id": 3, "role": "assistant", "content": "answer1"},
        {"id": 4, "role": "user", "content": "follow up"},
        {"id": 5, "role": "assistant", "content": "answer2"},
    ]
    # EN: Assign value to trimmed.
    # JP: trimmed に値を代入する。
    trimmed = review._trim_conversation_history(history, window_size=2)

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert trimmed[0]["id"] == 2
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert [item["id"] for item in trimmed] == [2, 4, 5]


# EN: Define function `test_trim_conversation_history_deduplicates_without_id`.
# JP: 関数 `test_trim_conversation_history_deduplicates_without_id` を定義する。
def test_trim_conversation_history_deduplicates_without_id():
    # EN: Assign value to repeated.
    # JP: repeated に値を代入する。
    repeated = {"role": "user", "content": "same", "timestamp": "t1"}
    # EN: Assign value to history.
    # JP: history に値を代入する。
    history = [repeated, repeated, {"role": "assistant", "content": "x", "timestamp": "t2"}]
    # EN: Assign value to trimmed.
    # JP: trimmed に値を代入する。
    trimmed = review._trim_conversation_history(history, window_size=10)

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert len(trimmed) == 2
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert trimmed[0]["role"] == "user"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert trimmed[1]["role"] == "assistant"


# EN: Define function `test_refusal_detection_and_stringify_reply`.
# JP: 関数 `test_refusal_detection_and_stringify_reply` を定義する。
def test_refusal_detection_and_stringify_reply():
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._looks_like_refusal("I cannot answer this request")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert not review._looks_like_refusal("これは通常の回答です")

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._stringify_reply("  text  ") == "text"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._stringify_reply({"content": "  body  "}) == "body"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert review._stringify_reply({"x": 1}) == '{"x": 1}'


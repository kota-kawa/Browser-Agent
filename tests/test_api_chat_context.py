# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.routes.api_chat import _build_recent_conversation_context


# EN: Define function `test_build_recent_conversation_context_filters_step_messages`.
# JP: 関数 `test_build_recent_conversation_context_filters_step_messages` を定義する。
def test_build_recent_conversation_context_filters_step_messages():
    # EN: Assign value to messages.
    # JP: messages に値を代入する。
    messages = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "ステップ1\nアクション: click"},
        {"role": "assistant", "content": "回答です"},
    ]
    # EN: Assign value to context.
    # JP: context に値を代入する。
    context = _build_recent_conversation_context(messages, limit=5)

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert context is not None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "ステップ1" not in context
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "ユーザー: first" in context
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "アシスタント: 回答です" in context


# EN: Define function `test_build_recent_conversation_context_limit_and_empty_cases`.
# JP: 関数 `test_build_recent_conversation_context_limit_and_empty_cases` を定義する。
def test_build_recent_conversation_context_limit_and_empty_cases():
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _build_recent_conversation_context([], limit=5) is None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _build_recent_conversation_context([{"role": "user", "content": "x"}], limit=0) is None

    # EN: Assign value to messages.
    # JP: messages に値を代入する。
    messages = [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
    ]
    # EN: Assign value to context.
    # JP: context に値を代入する。
    context = _build_recent_conversation_context(messages, limit=2)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "ユーザー: q1" not in context
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "アシスタント: a1" in context
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert "ユーザー: q2" in context


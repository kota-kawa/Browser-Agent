from fastapi_app.routes.api_chat import _build_recent_conversation_context


# EN: Define function `test_build_recent_conversation_context_filters_step_messages`.
# JP: 関数 `test_build_recent_conversation_context_filters_step_messages` を定義する。
def test_build_recent_conversation_context_filters_step_messages():
    messages = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "ステップ1\nアクション: click"},
        {"role": "assistant", "content": "回答です"},
    ]
    context = _build_recent_conversation_context(messages, limit=5)

    assert context is not None
    assert "ステップ1" not in context
    assert "ユーザー: first" in context
    assert "アシスタント: 回答です" in context


# EN: Define function `test_build_recent_conversation_context_limit_and_empty_cases`.
# JP: 関数 `test_build_recent_conversation_context_limit_and_empty_cases` を定義する。
def test_build_recent_conversation_context_limit_and_empty_cases():
    assert _build_recent_conversation_context([], limit=5) is None
    assert _build_recent_conversation_context([{"role": "user", "content": "x"}], limit=0) is None

    messages = [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
    ]
    context = _build_recent_conversation_context(messages, limit=2)
    assert "ユーザー: q1" not in context
    assert "アシスタント: a1" in context
    assert "ユーザー: q2" in context


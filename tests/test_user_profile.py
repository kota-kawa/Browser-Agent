# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.services import user_profile


# EN: Define function `test_normalize_user_profile_handles_whitespace_and_newlines`.
# JP: 関数 `test_normalize_user_profile_handles_whitespace_and_newlines` を定義する。
def test_normalize_user_profile_handles_whitespace_and_newlines():
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert user_profile._normalize_user_profile(None) == ""
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert user_profile._normalize_user_profile(" \r\nhello\rworld\n ") == "hello\nworld"


# EN: Define function `test_save_and_load_user_profile_roundtrip`.
# JP: 関数 `test_save_and_load_user_profile_roundtrip` を定義する。
def test_save_and_load_user_profile_roundtrip(monkeypatch, tmp_path):
    # EN: Assign value to profile_path.
    # JP: profile_path に値を代入する。
    profile_path = tmp_path / "profile.json"
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    # EN: Assign value to saved.
    # JP: saved に値を代入する。
    saved = user_profile.save_user_profile("  hello\r\nbrowser agent  ")
    # EN: Assign value to loaded.
    # JP: loaded に値を代入する。
    loaded = user_profile.load_user_profile()

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert saved == "hello\nbrowser agent"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert loaded == "hello\nbrowser agent"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert profile_path.exists()


# EN: Define function `test_save_user_profile_deletes_file_when_empty`.
# JP: 関数 `test_save_user_profile_deletes_file_when_empty` を定義する。
def test_save_user_profile_deletes_file_when_empty(monkeypatch, tmp_path):
    # EN: Assign value to profile_path.
    # JP: profile_path に値を代入する。
    profile_path = tmp_path / "profile.json"
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    profile_path.write_text('{"text":"x"}', encoding="utf-8")
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    # EN: Assign value to saved.
    # JP: saved に値を代入する。
    saved = user_profile.save_user_profile("   ")

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert saved == ""
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert not profile_path.exists()


# EN: Define function `test_load_user_profile_returns_empty_on_invalid_json`.
# JP: 関数 `test_load_user_profile_returns_empty_on_invalid_json` を定義する。
def test_load_user_profile_returns_empty_on_invalid_json(monkeypatch, tmp_path):
    # EN: Assign value to profile_path.
    # JP: profile_path に値を代入する。
    profile_path = tmp_path / "profile.json"
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    profile_path.write_text("{invalid json", encoding="utf-8")
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert user_profile.load_user_profile() == ""


# EN: Define function `test_normalize_user_profile_truncates`.
# JP: 関数 `test_normalize_user_profile_truncates` を定義する。
def test_normalize_user_profile_truncates(monkeypatch):
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setattr(user_profile, "_MAX_USER_PROFILE_CHARS", 5)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert user_profile._normalize_user_profile(" 123456 ") == "12345"

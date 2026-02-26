from fastapi_app.services import user_profile


# EN: Define function `test_normalize_user_profile_handles_whitespace_and_newlines`.
# JP: 関数 `test_normalize_user_profile_handles_whitespace_and_newlines` を定義する。
def test_normalize_user_profile_handles_whitespace_and_newlines():
    assert user_profile._normalize_user_profile(None) == ""
    assert user_profile._normalize_user_profile(" \r\nhello\rworld\n ") == "hello\nworld"


# EN: Define function `test_save_and_load_user_profile_roundtrip`.
# JP: 関数 `test_save_and_load_user_profile_roundtrip` を定義する。
def test_save_and_load_user_profile_roundtrip(monkeypatch, tmp_path):
    profile_path = tmp_path / "profile.json"
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    saved = user_profile.save_user_profile("  hello\r\nbrowser agent  ")
    loaded = user_profile.load_user_profile()

    assert saved == "hello\nbrowser agent"
    assert loaded == "hello\nbrowser agent"
    assert profile_path.exists()


# EN: Define function `test_save_user_profile_deletes_file_when_empty`.
# JP: 関数 `test_save_user_profile_deletes_file_when_empty` を定義する。
def test_save_user_profile_deletes_file_when_empty(monkeypatch, tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text('{"text":"x"}', encoding="utf-8")
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    saved = user_profile.save_user_profile("   ")

    assert saved == ""
    assert not profile_path.exists()


# EN: Define function `test_load_user_profile_returns_empty_on_invalid_json`.
# JP: 関数 `test_load_user_profile_returns_empty_on_invalid_json` を定義する。
def test_load_user_profile_returns_empty_on_invalid_json(monkeypatch, tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text("{invalid json", encoding="utf-8")
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    assert user_profile.load_user_profile() == ""


# EN: Define function `test_normalize_user_profile_truncates`.
# JP: 関数 `test_normalize_user_profile_truncates` を定義する。
def test_normalize_user_profile_truncates(monkeypatch):
    monkeypatch.setattr(user_profile, "_MAX_USER_PROFILE_CHARS", 5)
    assert user_profile._normalize_user_profile(" 123456 ") == "12345"

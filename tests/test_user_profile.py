from fastapi_app.services import user_profile


def test_normalize_user_profile_handles_whitespace_and_newlines():
    assert user_profile._normalize_user_profile(None) == ""
    assert user_profile._normalize_user_profile(" \r\nhello\rworld\n ") == "hello\nworld"


def test_save_and_load_user_profile_roundtrip(monkeypatch, tmp_path):
    profile_path = tmp_path / "profile.json"
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    saved = user_profile.save_user_profile("  hello\r\nbrowser agent  ")
    loaded = user_profile.load_user_profile()

    assert saved == "hello\nbrowser agent"
    assert loaded == "hello\nbrowser agent"
    assert profile_path.exists()


def test_save_user_profile_deletes_file_when_empty(monkeypatch, tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text('{"text":"x"}', encoding="utf-8")
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    saved = user_profile.save_user_profile("   ")

    assert saved == ""
    assert not profile_path.exists()


def test_load_user_profile_returns_empty_on_invalid_json(monkeypatch, tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text("{invalid json", encoding="utf-8")
    monkeypatch.setattr(user_profile, "_USER_PROFILE_PATH", profile_path)

    assert user_profile.load_user_profile() == ""


def test_normalize_user_profile_truncates(monkeypatch):
    monkeypatch.setattr(user_profile, "_MAX_USER_PROFILE_CHARS", 5)
    assert user_profile._normalize_user_profile(" 123456 ") == "12345"

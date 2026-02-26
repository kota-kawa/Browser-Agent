from urllib.parse import parse_qs, urlparse

from fastapi_app.core.env import (
    _env_int,
    _get_env_trimmed,
    _normalize_embed_browser_url,
    _normalize_start_url,
)


# EN: Define function `test_env_int_uses_default_for_missing_or_invalid`.
# JP: 関数 `test_env_int_uses_default_for_missing_or_invalid` を定義する。
def test_env_int_uses_default_for_missing_or_invalid(monkeypatch):
    monkeypatch.delenv("X_INT", raising=False)
    assert _env_int("X_INT", 7) == 7

    monkeypatch.setenv("X_INT", "abc")
    assert _env_int("X_INT", 7) == 7

    monkeypatch.setenv("X_INT", "0")
    assert _env_int("X_INT", 7) == 7

    monkeypatch.setenv("X_INT", "-3")
    assert _env_int("X_INT", 7) == 7

    monkeypatch.setenv("X_INT", "12")
    assert _env_int("X_INT", 7) == 12


# EN: Define function `test_normalize_embed_browser_url_adds_scale_and_resize_when_missing`.
# JP: 関数 `test_normalize_embed_browser_url_adds_scale_and_resize_when_missing` を定義する。
def test_normalize_embed_browser_url_adds_scale_and_resize_when_missing():
    url = "http://127.0.0.1:7900/vnc_lite.html?autoconnect=1"
    normalized = _normalize_embed_browser_url(url)
    parsed = urlparse(normalized)
    params = parse_qs(parsed.query)

    assert params["autoconnect"] == ["1"]
    assert params["scale"] == ["auto"]
    assert params["resize"] == ["scale"]


# EN: Define function `test_normalize_embed_browser_url_keeps_valid_resize_and_fixes_invalid`.
# JP: 関数 `test_normalize_embed_browser_url_keeps_valid_resize_and_fixes_invalid` を定義する。
def test_normalize_embed_browser_url_keeps_valid_resize_and_fixes_invalid():
    valid = "http://localhost:7900/vnc?resize=remote&scale=1"
    valid_norm = _normalize_embed_browser_url(valid)
    valid_params = parse_qs(urlparse(valid_norm).query)
    assert valid_params["resize"] == ["remote"]
    assert valid_params["scale"] == ["1"]

    invalid = "http://localhost:7900/vnc?resize=bad"
    invalid_norm = _normalize_embed_browser_url(invalid)
    invalid_params = parse_qs(urlparse(invalid_norm).query)
    assert invalid_params["resize"] == ["scale"]
    assert invalid_params["scale"] == ["auto"]


# EN: Define function `test_get_env_trimmed_returns_none_for_blank`.
# JP: 関数 `test_get_env_trimmed_returns_none_for_blank` を定義する。
def test_get_env_trimmed_returns_none_for_blank(monkeypatch):
    monkeypatch.delenv("X_TEXT", raising=False)
    assert _get_env_trimmed("X_TEXT") is None

    monkeypatch.setenv("X_TEXT", "   ")
    assert _get_env_trimmed("X_TEXT") is None

    monkeypatch.setenv("X_TEXT", "  hello  ")
    assert _get_env_trimmed("X_TEXT") == "hello"


# EN: Define function `test_normalize_start_url_handles_special_values`.
# JP: 関数 `test_normalize_start_url_handles_special_values` を定義する。
def test_normalize_start_url_handles_special_values():
    assert _normalize_start_url(None) is None
    assert _normalize_start_url("") is None
    assert _normalize_start_url("   ") is None
    assert _normalize_start_url("none") is None
    assert _normalize_start_url("off") is None
    assert _normalize_start_url("false") is None

    assert _normalize_start_url("//example.com/path") == "https://example.com/path"
    assert _normalize_start_url("example.com/path") == "https://example.com/path"
    assert _normalize_start_url("http://example.com") == "http://example.com"
    assert _normalize_start_url("about:blank") == "about:blank"
    assert _normalize_start_url("chrome://newtab") == "chrome://newtab"

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.parse import parse_qs, urlparse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.core.env import (
    _env_int,
    _get_env_trimmed,
    _normalize_embed_browser_url,
    _normalize_start_url,
)


# EN: Define function `test_env_int_uses_default_for_missing_or_invalid`.
# JP: 関数 `test_env_int_uses_default_for_missing_or_invalid` を定義する。
def test_env_int_uses_default_for_missing_or_invalid(monkeypatch):
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.delenv("X_INT", raising=False)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _env_int("X_INT", 7) == 7

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setenv("X_INT", "abc")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _env_int("X_INT", 7) == 7

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setenv("X_INT", "0")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _env_int("X_INT", 7) == 7

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setenv("X_INT", "-3")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _env_int("X_INT", 7) == 7

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setenv("X_INT", "12")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _env_int("X_INT", 7) == 12


# EN: Define function `test_normalize_embed_browser_url_adds_scale_and_resize_when_missing`.
# JP: 関数 `test_normalize_embed_browser_url_adds_scale_and_resize_when_missing` を定義する。
def test_normalize_embed_browser_url_adds_scale_and_resize_when_missing():
    # EN: Assign value to url.
    # JP: url に値を代入する。
    url = "http://127.0.0.1:7900/vnc_lite.html?autoconnect=1"
    # EN: Assign value to normalized.
    # JP: normalized に値を代入する。
    normalized = _normalize_embed_browser_url(url)
    # EN: Assign value to parsed.
    # JP: parsed に値を代入する。
    parsed = urlparse(normalized)
    # EN: Assign value to params.
    # JP: params に値を代入する。
    params = parse_qs(parsed.query)

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert params["autoconnect"] == ["1"]
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert params["scale"] == ["auto"]
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert params["resize"] == ["scale"]


# EN: Define function `test_normalize_embed_browser_url_keeps_valid_resize_and_fixes_invalid`.
# JP: 関数 `test_normalize_embed_browser_url_keeps_valid_resize_and_fixes_invalid` を定義する。
def test_normalize_embed_browser_url_keeps_valid_resize_and_fixes_invalid():
    # EN: Assign value to valid.
    # JP: valid に値を代入する。
    valid = "http://localhost:7900/vnc?resize=remote&scale=1"
    # EN: Assign value to valid_norm.
    # JP: valid_norm に値を代入する。
    valid_norm = _normalize_embed_browser_url(valid)
    # EN: Assign value to valid_params.
    # JP: valid_params に値を代入する。
    valid_params = parse_qs(urlparse(valid_norm).query)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert valid_params["resize"] == ["remote"]
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert valid_params["scale"] == ["1"]

    # EN: Assign value to invalid.
    # JP: invalid に値を代入する。
    invalid = "http://localhost:7900/vnc?resize=bad"
    # EN: Assign value to invalid_norm.
    # JP: invalid_norm に値を代入する。
    invalid_norm = _normalize_embed_browser_url(invalid)
    # EN: Assign value to invalid_params.
    # JP: invalid_params に値を代入する。
    invalid_params = parse_qs(urlparse(invalid_norm).query)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert invalid_params["resize"] == ["scale"]
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert invalid_params["scale"] == ["auto"]


# EN: Define function `test_get_env_trimmed_returns_none_for_blank`.
# JP: 関数 `test_get_env_trimmed_returns_none_for_blank` を定義する。
def test_get_env_trimmed_returns_none_for_blank(monkeypatch):
    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.delenv("X_TEXT", raising=False)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _get_env_trimmed("X_TEXT") is None

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setenv("X_TEXT", "   ")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _get_env_trimmed("X_TEXT") is None

    # EN: Evaluate an expression.
    # JP: 式を評価する。
    monkeypatch.setenv("X_TEXT", "  hello  ")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _get_env_trimmed("X_TEXT") == "hello"


# EN: Define function `test_normalize_start_url_handles_special_values`.
# JP: 関数 `test_normalize_start_url_handles_special_values` を定義する。
def test_normalize_start_url_handles_special_values():
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url(None) is None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("") is None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("   ") is None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("none") is None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("off") is None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("false") is None

    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("//example.com/path") == "https://example.com/path"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("example.com/path") == "https://example.com/path"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("http://example.com") == "http://example.com"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("about:blank") == "about:blank"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_start_url("chrome://newtab") == "chrome://newtab"

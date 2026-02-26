# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from httpx import URL

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.services.input_guard import (
    _is_llama_guard_model,
    _normalize_groq_base_url,
    _parse_guard_output,
)


# EN: Define function `test_is_llama_guard_model`.
# JP: 関数 `test_is_llama_guard_model` を定義する。
def test_is_llama_guard_model():
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _is_llama_guard_model("meta-llama/Llama-Guard-4-12B")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert not _is_llama_guard_model("openai/gpt-oss-safeguard-20b")


# EN: Define function `test_normalize_groq_base_url`.
# JP: 関数 `test_normalize_groq_base_url` を定義する。
def test_normalize_groq_base_url():
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_groq_base_url(None) is None
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_groq_base_url("https://api.groq.com/openai/v1") == "https://api.groq.com"
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert _normalize_groq_base_url("https://api.groq.com/v1") == "https://api.groq.com/v1"

    # EN: Assign value to url.
    # JP: url に値を代入する。
    url = URL("https://api.groq.com/openai/v1")
    # EN: Assign value to normalized.
    # JP: normalized に値を代入する。
    normalized = _normalize_groq_base_url(url)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert isinstance(normalized, URL)
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert str(normalized) == "https://api.groq.com"


# EN: Define function `test_parse_guard_output_from_json_payload`.
# JP: 関数 `test_parse_guard_output_from_json_payload` を定義する。
def test_parse_guard_output_from_json_payload():
    # EN: Assign value to safe.
    # JP: safe に値を代入する。
    safe = _parse_guard_output('{"violation":0,"category":null}')
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert safe.is_safe is True
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert safe.categories == ()

    # EN: Assign value to blocked.
    # JP: blocked に値を代入する。
    blocked = _parse_guard_output('{"violation":"1","category":["S2","S2","S5"]}')
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert blocked.is_safe is False
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert blocked.categories == ("S2", "S2", "S5")


# EN: Define function `test_parse_guard_output_from_plain_text`.
# JP: 関数 `test_parse_guard_output_from_plain_text` を定義する。
def test_parse_guard_output_from_plain_text():
    # EN: Assign value to safe.
    # JP: safe に値を代入する。
    safe = _parse_guard_output("SAFE")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert safe.is_safe is True
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert safe.categories == ()

    # EN: Assign value to blocked.
    # JP: blocked に値を代入する。
    blocked = _parse_guard_output("violation S2 and S3 detected\nS3 repeated")
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert blocked.is_safe is False
    # EN: Validate a required condition.
    # JP: 必須条件を検証する。
    assert blocked.categories == ("S2", "S3")


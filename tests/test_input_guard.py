from httpx import URL

from fastapi_app.services.input_guard import (
    _is_llama_guard_model,
    _normalize_groq_base_url,
    _parse_guard_output,
)


def test_is_llama_guard_model():
    assert _is_llama_guard_model("meta-llama/Llama-Guard-4-12B")
    assert not _is_llama_guard_model("openai/gpt-oss-safeguard-20b")


def test_normalize_groq_base_url():
    assert _normalize_groq_base_url(None) is None
    assert _normalize_groq_base_url("https://api.groq.com/openai/v1") == "https://api.groq.com"
    assert _normalize_groq_base_url("https://api.groq.com/v1") == "https://api.groq.com/v1"

    url = URL("https://api.groq.com/openai/v1")
    normalized = _normalize_groq_base_url(url)
    assert isinstance(normalized, URL)
    assert str(normalized) == "https://api.groq.com"


def test_parse_guard_output_from_json_payload():
    safe = _parse_guard_output('{"violation":0,"category":null}')
    assert safe.is_safe is True
    assert safe.categories == ()

    blocked = _parse_guard_output('{"violation":"1","category":["S2","S2","S5"]}')
    assert blocked.is_safe is False
    assert blocked.categories == ("S2", "S2", "S5")


def test_parse_guard_output_from_plain_text():
    safe = _parse_guard_output("SAFE")
    assert safe.is_safe is True
    assert safe.categories == ()

    blocked = _parse_guard_output("violation S2 and S3 detected\nS3 repeated")
    assert blocked.is_safe is False
    assert blocked.categories == ("S2", "S3")


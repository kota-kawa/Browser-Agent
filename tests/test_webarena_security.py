import pytest

from fastapi_app.webarena import routes as webarena_routes


# EN: Define function `test_validate_custom_start_url_rejects_localhost`.
# JP: 関数 `test_validate_custom_start_url_rejects_localhost` を定義する。
def test_validate_custom_start_url_rejects_localhost(monkeypatch):
	monkeypatch.setenv('WEBARENA_ALLOWED_CUSTOM_TASK_DOMAINS', 'example.com')
	with pytest.raises(ValueError) as exc_info:
		webarena_routes._validate_custom_start_url('http://localhost:8080/path')
	assert '内部ネットワーク' in str(exc_info.value)


# EN: Define function `test_validate_custom_start_url_rejects_private_ip`.
# JP: 関数 `test_validate_custom_start_url_rejects_private_ip` を定義する。
def test_validate_custom_start_url_rejects_private_ip(monkeypatch):
	monkeypatch.setenv('WEBARENA_ALLOWED_CUSTOM_TASK_DOMAINS', 'example.com')
	with pytest.raises(ValueError) as exc_info:
		webarena_routes._validate_custom_start_url('http://10.0.0.2/dashboard')
	assert '内部ネットワーク' in str(exc_info.value)


# EN: Define function `test_validate_custom_start_url_rejects_metadata_ip`.
# JP: 関数 `test_validate_custom_start_url_rejects_metadata_ip` を定義する。
def test_validate_custom_start_url_rejects_metadata_ip(monkeypatch):
	monkeypatch.setenv('WEBARENA_ALLOWED_CUSTOM_TASK_DOMAINS', 'example.com')
	with pytest.raises(ValueError) as exc_info:
		webarena_routes._validate_custom_start_url('http://169.254.169.254/latest/meta-data')
	assert '内部ネットワーク' in str(exc_info.value)


# EN: Define function `test_validate_custom_start_url_rejects_disallowed_domain`.
# JP: 関数 `test_validate_custom_start_url_rejects_disallowed_domain` を定義する。
def test_validate_custom_start_url_rejects_disallowed_domain(monkeypatch):
	monkeypatch.setenv('WEBARENA_ALLOWED_CUSTOM_TASK_DOMAINS', 'example.com')
	with pytest.raises(ValueError) as exc_info:
		webarena_routes._validate_custom_start_url('https://attacker.invalid/path')
	assert '許可リスト' in str(exc_info.value)


# EN: Define function `test_validate_custom_start_url_allows_allowed_domain`.
# JP: 関数 `test_validate_custom_start_url_allows_allowed_domain` を定義する。
def test_validate_custom_start_url_allows_allowed_domain(monkeypatch):
	monkeypatch.setenv('WEBARENA_ALLOWED_CUSTOM_TASK_DOMAINS', 'example.com')
	value = webarena_routes._validate_custom_start_url('https://sub.example.com/path')
	assert value == 'https://sub.example.com/path'


# EN: Define function `test_parse_allowed_domains_falls_back_to_defaults`.
# JP: 関数 `test_parse_allowed_domains_falls_back_to_defaults` を定義する。
def test_parse_allowed_domains_falls_back_to_defaults(monkeypatch):
	monkeypatch.delenv('WEBARENA_ALLOWED_CUSTOM_TASK_DOMAINS', raising=False)
	domains = webarena_routes._parse_allowed_custom_task_domains()
	assert 'shopping' in domains

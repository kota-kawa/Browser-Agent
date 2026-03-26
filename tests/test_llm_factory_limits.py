import sys

import fastapi_app.services.llm_factory as llm_factory


# EN: Define class `_BaseStubChat`.
# JP: クラス `_BaseStubChat` を定義する。
class _BaseStubChat:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, **kwargs):
		self.kwargs = kwargs


# EN: Define class `_StubOpenAI`.
# JP: クラス `_StubOpenAI` を定義する。
class _StubOpenAI(_BaseStubChat):
	pass


# EN: Define class `_StubGoogle`.
# JP: クラス `_StubGoogle` を定義する。
class _StubGoogle(_BaseStubChat):
	pass


# EN: Define class `_StubAnthropic`.
# JP: クラス `_StubAnthropic` を定義する。
class _StubAnthropic(_BaseStubChat):
	pass


# EN: Define class `_StubGroq`.
# JP: クラス `_StubGroq` を定義する。
class _StubGroq(_BaseStubChat):
	pass


# EN: Define function `_patch_common`.
# JP: 関数 `_patch_common` を定義する。
def _patch_common(monkeypatch):
	monkeypatch.setattr(llm_factory, '_get_env_trimmed', lambda _name: 'dummy-key')
	monkeypatch.setattr(llm_factory, 'apply_monthly_llm_limit', lambda llm: llm)
	monkeypatch.setattr(
		llm_factory,
		'PROVIDER_DEFAULTS',
		{
			'openai': {'api_key_env': 'OPENAI_API_KEY'},
			'gemini': {'api_key_env': 'GOOGLE_API_KEY'},
			'claude': {'api_key_env': 'ANTHROPIC_API_KEY'},
			'groq': {'api_key_env': 'GROQ_API_KEY'},
		},
	)


# EN: Define function `test_openai_receives_output_token_limit`.
# JP: 関数 `test_openai_receives_output_token_limit` を定義する。
def test_openai_receives_output_token_limit(monkeypatch):
	_patch_common(monkeypatch)
	monkeypatch.setattr(llm_factory, '_LLM_MAX_OUTPUT_TOKENS', 5000)
	monkeypatch.setitem(sys.modules, 'browser_use.llm.openai.chat', type('M', (), {'ChatOpenAI': _StubOpenAI})())

	created = llm_factory._create_selected_llm({'provider': 'openai', 'model': 'gpt-5.1', 'base_url': 'https://example.test'})
	assert isinstance(created, _StubOpenAI)
	assert created.kwargs['max_completion_tokens'] == 5000


# EN: Define function `test_gemini_receives_output_token_limit`.
# JP: 関数 `test_gemini_receives_output_token_limit` を定義する。
def test_gemini_receives_output_token_limit(monkeypatch):
	_patch_common(monkeypatch)
	monkeypatch.setattr(llm_factory, '_LLM_MAX_OUTPUT_TOKENS', 5000)
	monkeypatch.setitem(sys.modules, 'browser_use.llm.google.chat', type('M', (), {'ChatGoogle': _StubGoogle})())

	created = llm_factory._create_selected_llm({'provider': 'gemini', 'model': 'gemini-3-pro-preview'})
	assert isinstance(created, _StubGoogle)
	assert created.kwargs['max_output_tokens'] == 5000


# EN: Define function `test_claude_receives_output_token_limit`.
# JP: 関数 `test_claude_receives_output_token_limit` を定義する。
def test_claude_receives_output_token_limit(monkeypatch):
	_patch_common(monkeypatch)
	monkeypatch.setattr(llm_factory, '_LLM_MAX_OUTPUT_TOKENS', 5000)
	monkeypatch.setitem(
		sys.modules,
		'browser_use.llm.anthropic.chat',
		type('M', (), {'ChatAnthropic': _StubAnthropic})(),
	)

	created = llm_factory._create_selected_llm({'provider': 'claude', 'model': 'claude-3-5-haiku-latest'})
	assert isinstance(created, _StubAnthropic)
	assert created.kwargs['max_tokens'] == 5000


# EN: Define function `test_groq_receives_output_token_limit`.
# JP: 関数 `test_groq_receives_output_token_limit` を定義する。
def test_groq_receives_output_token_limit(monkeypatch):
	_patch_common(monkeypatch)
	monkeypatch.setattr(llm_factory, '_LLM_MAX_OUTPUT_TOKENS', 5000)
	monkeypatch.setitem(sys.modules, 'browser_use.llm.groq.chat', type('M', (), {'ChatGroq': _StubGroq})())

	created = llm_factory._create_selected_llm({'provider': 'groq', 'model': 'llama-3.1-8b-instant'})
	assert isinstance(created, _StubGroq)
	assert created.kwargs['max_tokens'] == 5000


# EN: Define function `test_unknown_provider_falls_back_to_openai_token_field`.
# JP: 関数 `test_unknown_provider_falls_back_to_openai_token_field` を定義する。
def test_unknown_provider_falls_back_to_openai_token_field(monkeypatch):
	_patch_common(monkeypatch)
	monkeypatch.setattr(llm_factory, '_LLM_MAX_OUTPUT_TOKENS', 5000)
	monkeypatch.setitem(sys.modules, 'browser_use.llm.openai.chat', type('M', (), {'ChatOpenAI': _StubOpenAI})())

	created = llm_factory._create_selected_llm({'provider': 'unknown', 'model': 'x-model'})
	assert isinstance(created, _StubOpenAI)
	assert created.kwargs['max_completion_tokens'] == 5000

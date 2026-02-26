# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Load shared model selection from Multi-Agent-Platform/model_settings.json."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path

# EN: Assign value to DEFAULT_SELECTION.
# JP: DEFAULT_SELECTION に値を代入する。
DEFAULT_SELECTION = {'provider': 'groq', 'model': 'openai/gpt-oss-20b'}

# EN: Assign annotated value to PROVIDER_DEFAULTS.
# JP: PROVIDER_DEFAULTS に型付きの値を代入する。
PROVIDER_DEFAULTS: dict[str, dict[str, str | None]] = {
	'openai': {'api_key_env': 'OPENAI_API_KEY', 'base_url_env': 'OPENAI_BASE_URL', 'default_base_url': None},
	'claude': {
		'api_key_env': 'CLAUDE_API_KEY',
		'base_url_env': 'CLAUDE_API_BASE',
		'default_base_url': None,
	},
	'gemini': {
		'api_key_env': 'GEMINI_API_KEY',
		'base_url_env': 'GEMINI_API_BASE',
		'default_base_url': 'https://generativelanguage.googleapis.com/v1beta',
	},
	'groq': {
		'api_key_env': 'GROQ_API_KEY',
		'base_url_env': 'GROQ_API_BASE',
		'default_base_url': 'https://api.groq.com/openai/v1',
	},
}

# EN: Assign annotated value to _OVERRIDE_SELECTION.
# JP: _OVERRIDE_SELECTION に型付きの値を代入する。
_OVERRIDE_SELECTION: dict[str, str] | None = None


# EN: Define function `_load_selection`.
# JP: 関数 `_load_selection` を定義する。
def _load_selection(agent_key: str) -> dict[str, str]:
	# Try local cache first (for Docker/persistence)
	# EN: Assign value to local_path.
	# JP: local_path に値を代入する。
	local_path = Path('local_model_settings.json')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if local_path.is_file():
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to data.
			# JP: data に値を代入する。
			data = json.loads(local_path.read_text(encoding='utf-8'))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(data, dict) and data.get('provider') and data.get('model'):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return {'provider': data['provider'], 'model': data['model']}
		except (OSError, json.JSONDecodeError):
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass

	# EN: Assign value to platform_path.
	# JP: platform_path に値を代入する。
	platform_path = Path(__file__).resolve().parents[2] / 'Multi-Agent-Platform' / 'model_settings.json'
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to data.
		# JP: data に値を代入する。
		data = json.loads(platform_path.read_text(encoding='utf-8'))
	except (FileNotFoundError, json.JSONDecodeError):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return dict(DEFAULT_SELECTION)

	# EN: Assign value to selection.
	# JP: selection に値を代入する。
	selection = data.get('selection') or data
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not isinstance(selection, dict):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return dict(DEFAULT_SELECTION)

	# EN: Assign value to chosen.
	# JP: chosen に値を代入する。
	chosen = selection.get(agent_key)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not isinstance(chosen, dict):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return dict(DEFAULT_SELECTION)

	# EN: Assign value to provider.
	# JP: provider に値を代入する。
	provider = (chosen.get('provider') or DEFAULT_SELECTION['provider']).strip()
	# EN: Assign value to model.
	# JP: model に値を代入する。
	model = (chosen.get('model') or DEFAULT_SELECTION['model']).strip()
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return {'provider': provider, 'model': model}


# EN: Define function `_normalize_base_url`.
# JP: 関数 `_normalize_base_url` を定義する。
def _normalize_base_url(provider: str, base_url: str | None, explicit: bool = False) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Strip provider-mismatched base URLs left over from previous selections.

	`explicit=True` means the caller intentionally set the base_url (e.g. via UI),
	so we preserve it unless it's empty. Environment-derived values are treated
	as best-effort hints and filtered if they clearly belong to a different
	provider (e.g. Groq URL while OpenAI is selected).
	"""

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not base_url:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

	# EN: Assign value to normalized.
	# JP: normalized に値を代入する。
	normalized = base_url.strip().rstrip('/')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not normalized:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

	# EN: Assign value to provider_defaults.
	# JP: provider_defaults に値を代入する。
	provider_defaults = {
		key: (cfg.get('default_base_url') or '').rstrip('/')
		for key, cfg in PROVIDER_DEFAULTS.items()
		if cfg.get('default_base_url')
	}
	# EN: Assign value to current_default.
	# JP: current_default に値を代入する。
	current_default = provider_defaults.get(provider, '')
	# EN: Assign value to other_defaults.
	# JP: other_defaults に値を代入する。
	other_defaults = {val for key, val in provider_defaults.items() if key != provider}

	# Force cleanup of known provider mismatches, even if explicit=True
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider != 'groq' and 'api.groq.com' in normalized:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider != 'gemini' and 'generativelanguage.googleapis.com' in normalized:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider == 'claude' and 'openrouter.ai' in normalized:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider == 'gemini' and normalized.endswith('/openai/v1'):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not explicit:
		# Avoid reusing obvious cross-provider URLs (e.g. Groq -> OpenAI)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if normalized in other_defaults:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return normalized or current_default


# EN: Define function `apply_model_selection`.
# JP: 関数 `apply_model_selection` を定義する。
def apply_model_selection(agent_key: str = 'browser', override: dict[str, str] | None = None) -> dict[str, str]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Set env vars DEFAULT_LLM/OPENAI_API_KEY/OPENAI_BASE_URL according to selection."""

	# EN: Assign value to selection.
	# JP: selection に値を代入する。
	selection = override or _OVERRIDE_SELECTION or _load_selection(agent_key)
	# EN: Assign value to provider.
	# JP: provider に値を代入する。
	provider = selection.get('provider') or DEFAULT_SELECTION['provider']
	# EN: Assign value to model.
	# JP: model に値を代入する。
	model = selection.get('model') or DEFAULT_SELECTION['model']

	# EN: Assign value to meta.
	# JP: meta に値を代入する。
	meta = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS['openai'])
	# EN: Assign value to api_key_env.
	# JP: api_key_env に値を代入する。
	api_key_env = meta.get('api_key_env') or 'OPENAI_API_KEY'
	# EN: Assign value to base_url_env.
	# JP: base_url_env に値を代入する。
	base_url_env = meta.get('base_url_env') or ''

	# Handle OPENAI_API_KEY backup/restore to prevent overwriting with other provider keys
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider == 'openai':
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if '_ORIGINAL_OPENAI_API_KEY' in os.environ:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			os.environ['OPENAI_API_KEY'] = os.environ['_ORIGINAL_OPENAI_API_KEY']

	# EN: Assign value to api_key.
	# JP: api_key に値を代入する。
	api_key = os.getenv(api_key_env) or os.getenv(api_key_env.lower()) or os.getenv('OPENAI_API_KEY')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if api_key:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if provider != 'openai':
			# If we are switching away from OpenAI, backup the original key if it exists
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'OPENAI_API_KEY' in os.environ and '_ORIGINAL_OPENAI_API_KEY' not in os.environ:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				os.environ['_ORIGINAL_OPENAI_API_KEY'] = os.environ['OPENAI_API_KEY']

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		os.environ['OPENAI_API_KEY'] = api_key

	# EN: Assign value to base_url_raw.
	# JP: base_url_raw に値を代入する。
	base_url_raw = selection.get('base_url')
	# EN: Assign value to base_url_provided.
	# JP: base_url_provided に値を代入する。
	base_url_provided = isinstance(base_url_raw, str) and base_url_raw.strip() != ''
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not base_url_provided:
		# EN: Assign value to base_url_raw.
		# JP: base_url_raw に値を代入する。
		base_url_raw = os.getenv(base_url_env, '') if base_url_env else ''

	# EN: Assign value to base_url.
	# JP: base_url に値を代入する。
	base_url = _normalize_base_url(provider, base_url_raw, explicit=base_url_provided)

	# Avoid picking up leftover base_urls from other providers
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not base_url and not base_url_provided:
		# EN: Assign value to base_url.
		# JP: base_url に値を代入する。
		base_url = meta.get('default_base_url') or ''

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if base_url:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		os.environ['OPENAI_BASE_URL'] = base_url
	else:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		os.environ.pop('OPENAI_BASE_URL', None)

	# DEFAULT_LLM expects a provider prefix; convert model id to underscore form
	# EN: Assign value to safe_model.
	# JP: safe_model に値を代入する。
	safe_model = model.replace('-', '_')
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	os.environ['DEFAULT_LLM'] = f'{provider}_{safe_model}'

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return {'provider': provider, 'model': model, 'base_url': base_url}


# EN: Define function `update_override`.
# JP: 関数 `update_override` を定義する。
def update_override(selection: dict[str, str] | None) -> dict[str, str]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Set in-memory override and apply immediately."""

	# EN: Execute this statement.
	# JP: この文を実行する。
	global _OVERRIDE_SELECTION
	# EN: Assign value to _OVERRIDE_SELECTION.
	# JP: _OVERRIDE_SELECTION に値を代入する。
	_OVERRIDE_SELECTION = selection or None
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return apply_model_selection(override=_OVERRIDE_SELECTION or None)

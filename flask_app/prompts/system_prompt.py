from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

# JP: システムプロンプトの読み込みと埋め込みを担当
# EN: Load and render the system prompt template
from browser_use.model_selection import _load_selection

from ..core.config import logger
from ..services.user_profile import load_user_profile

# JP: 画像入力（Vision）に非対応のモデル一覧
# EN: Models that are not multimodal and must not receive vision inputs
NON_MULTIMODAL_MODELS = [
	'llama-3.3-70b-versatile',
	'llama-3.1-8b-instant',
	'openai/gpt-oss-20b',
	'qwen/qwen3-32b',
]
VISION_CAPABLE_PROVIDERS = {'claude', 'gemini', 'openai'}
_NON_MULTIMODAL_MODELS_LOWER = {model.lower() for model in NON_MULTIMODAL_MODELS}

# JP: 既定の言語ルール（日本語出力など）
# EN: Default language rules (Japanese output, etc.)
_LANGUAGE_EXTENSION = (
	'### Additional Language Guidelines\n'
	'- All thought processes, action evaluations, memories, next goals, final reports, etc., must be written in natural Japanese.\n'
	'- Statuses such as success or failure must also be explicitly stated in Japanese (e.g., 成功, 失敗, 不明).\n'
	'- Proper nouns, quotes, or original text on web pages that need to be presented to the user may be kept in their original language.\n'
	'- Do not use Google for search. Use yahoo.co.jp by default. If Yahoo Japan is absolutely impossible, you may use another non-Google search engine as a last resort (not recommended).\n'
)

_SYSTEM_PROMPT_FILENAME = 'system_prompt_browser_agent.md'
_CUSTOM_SYSTEM_PROMPT_TEMPLATE: str | None = None
_DEFAULT_MAX_ACTIONS_PER_STEP = 10


def _should_disable_vision(provider: str | None, model: str | None) -> bool:
	"""Return True when the selected model/provider should not receive vision inputs."""

	# JP: プロバイダとモデルの組み合わせから Vision 可否を判定
	# EN: Decide vision capability based on provider/model
	provider_normalized = (provider or '').strip().lower()
	model_normalized = (model or '').strip().lower()

	if provider_normalized == 'groq':
		return True

	if provider_normalized and provider_normalized not in VISION_CAPABLE_PROVIDERS:
		return True

	return model_normalized in _NON_MULTIMODAL_MODELS_LOWER


def _system_prompt_candidate_paths() -> tuple[Path, ...]:
	# JP: システムプロンプトはこのモジュール直下のみ許可
	# EN: Only allow prompt templates colocated with this module
	script_path = Path(__file__).resolve()
	# Only allow the prompt that lives alongside this module
	return (script_path.parent / _SYSTEM_PROMPT_FILENAME,)


def _load_custom_system_prompt_template() -> str | None:
	# JP: テンプレートを一度だけ読み込みキャッシュする
	# EN: Load and cache the template once
	global _CUSTOM_SYSTEM_PROMPT_TEMPLATE
	if _CUSTOM_SYSTEM_PROMPT_TEMPLATE is not None:
		return _CUSTOM_SYSTEM_PROMPT_TEMPLATE or None

	for candidate in _system_prompt_candidate_paths():
		if candidate.exists():
			try:
				_CUSTOM_SYSTEM_PROMPT_TEMPLATE = candidate.read_text(encoding='utf-8')
				logger.info('Loaded system prompt template from %s', candidate)
				return _CUSTOM_SYSTEM_PROMPT_TEMPLATE
			except OSError:
				logger.exception('Failed to read system prompt template at %s', candidate)
				break

	logger.warning(
		'Custom system prompt file %s not found next to flask_app; no other prompt sources will be used.',
		_system_prompt_candidate_paths()[0],
	)
	_CUSTOM_SYSTEM_PROMPT_TEMPLATE = ''
	return None


def _build_custom_system_prompt(
	max_actions_per_step: int = _DEFAULT_MAX_ACTIONS_PER_STEP,
	force_disable_vision: bool = False,
	provider: str | None = None,
	model: str | None = None,
) -> str | None:
	# JP: テンプレートに現在時刻・ユーザープロファイル等を埋め込む
	# EN: Inject current time and user profile into the template
	template = _load_custom_system_prompt_template()
	if not template:
		return None

	selection = _load_selection('browser')
	provider = provider or selection.get('provider', '')
	model = model or selection.get('model', '')

	vision_disabled = force_disable_vision or _should_disable_vision(provider, model)

	if vision_disabled:
		# JP: Vision を使わないモデル向けに関連セクションを削除
		# EN: Remove vision sections for non-vision models
		# Remove vision-related sections for non-multimodal models
		template = re.sub(r'<browser_vision>.*?</browser_vision>\n', '', template, flags=re.DOTALL)
		# Adjust reasoning rules to remove dependency on screenshots
		reasoning_rules_pattern = re.compile(r'(<reasoning_rules>.*?</reasoning_rules>)', re.DOTALL)
		template = reasoning_rules_pattern.sub(
			lambda m: m.group(1).replace(
				'Always verify using <browser_vision> (screenshot) as the primary ground truth. If a screenshot is unavailable, fall back to <browser_state>.',
				'Always verify the result of your actions using <browser_state> as the primary ground truth.',
			),
			template,
		)

	now = datetime.now().astimezone()
	# JP: ローカル日時の文字列を生成して埋め込む
	# EN: Build a localized datetime string for the prompt
	weekday_ja = '月火水木金土日'[now.weekday()]
	current_datetime_line = (
		f'{now.strftime("%Y-%m-%d %H:%M %Z (UTC%z, %A)")}'
		f' / ローカル日時: {now.strftime("%Y年%m月%d日")}({weekday_ja}) {now.strftime("%H時%M分")} {now.strftime("%Z")}'
	)
	user_profile_text = load_user_profile()
	if not user_profile_text:
		user_profile_text = '未設定'
	# Avoid str.format() so literal braces in the template (e.g., action schemas) are preserved
	# without triggering KeyError for names like "go_to_url".
	template = template.replace('{max_actions}', str(max_actions_per_step))
	template = template.replace('{current_datetime}', current_datetime_line)
	template = template.replace('{user_profile}', user_profile_text)
	return template

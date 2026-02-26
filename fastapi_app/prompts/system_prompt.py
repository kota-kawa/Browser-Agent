# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path

# JP: システムプロンプトの読み込みと埋め込みを担当
# EN: Load and render the system prompt template
from browser_use.model_selection import _load_selection

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.user_profile import load_user_profile

# JP: 画像入力（Vision）に非対応のモデル一覧
# EN: Models that are not multimodal and must not receive vision inputs
NON_MULTIMODAL_MODELS = [
	'llama-3.3-70b-versatile',
	'llama-3.1-8b-instant',
	'openai/gpt-oss-20b',
	'qwen/qwen3-32b',
]
# EN: Assign value to VISION_CAPABLE_PROVIDERS.
# JP: VISION_CAPABLE_PROVIDERS に値を代入する。
VISION_CAPABLE_PROVIDERS = {'claude', 'gemini', 'openai'}
# EN: Assign value to _NON_MULTIMODAL_MODELS_LOWER.
# JP: _NON_MULTIMODAL_MODELS_LOWER に値を代入する。
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

# EN: Assign value to _SYSTEM_PROMPT_FILENAME.
# JP: _SYSTEM_PROMPT_FILENAME に値を代入する。
_SYSTEM_PROMPT_FILENAME = 'system_prompt_browser_agent.md'
# EN: Assign annotated value to _CUSTOM_SYSTEM_PROMPT_TEMPLATE.
# JP: _CUSTOM_SYSTEM_PROMPT_TEMPLATE に型付きの値を代入する。
_CUSTOM_SYSTEM_PROMPT_TEMPLATE: str | None = None
# EN: Assign value to _DEFAULT_MAX_ACTIONS_PER_STEP.
# JP: _DEFAULT_MAX_ACTIONS_PER_STEP に値を代入する。
_DEFAULT_MAX_ACTIONS_PER_STEP = 10


# EN: Define function `_should_disable_vision`.
# JP: 関数 `_should_disable_vision` を定義する。
def _should_disable_vision(provider: str | None, model: str | None) -> bool:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return True when the selected model/provider should not receive vision inputs."""

	# JP: プロバイダとモデルの組み合わせから Vision 可否を判定
	# EN: Decide vision capability based on provider/model
	provider_normalized = (provider or '').strip().lower()
	# EN: Assign value to model_normalized.
	# JP: model_normalized に値を代入する。
	model_normalized = (model or '').strip().lower()

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider_normalized == 'groq':
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider_normalized and provider_normalized not in VISION_CAPABLE_PROVIDERS:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return model_normalized in _NON_MULTIMODAL_MODELS_LOWER


# EN: Define function `_system_prompt_candidate_paths`.
# JP: 関数 `_system_prompt_candidate_paths` を定義する。
def _system_prompt_candidate_paths() -> tuple[Path, ...]:
	# JP: システムプロンプトはこのモジュール直下のみ許可
	# EN: Only allow prompt templates colocated with this module
	script_path = Path(__file__).resolve()
	# Only allow the prompt that lives alongside this module
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return (script_path.parent / _SYSTEM_PROMPT_FILENAME,)


# EN: Define function `_load_custom_system_prompt_template`.
# JP: 関数 `_load_custom_system_prompt_template` を定義する。
def _load_custom_system_prompt_template() -> str | None:
	# JP: テンプレートを一度だけ読み込みキャッシュする
	# EN: Load and cache the template once
	global _CUSTOM_SYSTEM_PROMPT_TEMPLATE
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _CUSTOM_SYSTEM_PROMPT_TEMPLATE is not None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _CUSTOM_SYSTEM_PROMPT_TEMPLATE or None

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for candidate in _system_prompt_candidate_paths():
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if candidate.exists():
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to _CUSTOM_SYSTEM_PROMPT_TEMPLATE.
				# JP: _CUSTOM_SYSTEM_PROMPT_TEMPLATE に値を代入する。
				_CUSTOM_SYSTEM_PROMPT_TEMPLATE = candidate.read_text(encoding='utf-8')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('Loaded system prompt template from %s', candidate)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return _CUSTOM_SYSTEM_PROMPT_TEMPLATE
			except OSError:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.exception('Failed to read system prompt template at %s', candidate)
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.warning(
		'Custom system prompt file %s not found next to fastapi_app; no other prompt sources will be used.',
		_system_prompt_candidate_paths()[0],
	)
	# EN: Assign value to _CUSTOM_SYSTEM_PROMPT_TEMPLATE.
	# JP: _CUSTOM_SYSTEM_PROMPT_TEMPLATE に値を代入する。
	_CUSTOM_SYSTEM_PROMPT_TEMPLATE = ''
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define function `_build_custom_system_prompt`.
# JP: 関数 `_build_custom_system_prompt` を定義する。
def _build_custom_system_prompt(
	max_actions_per_step: int = _DEFAULT_MAX_ACTIONS_PER_STEP,
	force_disable_vision: bool = False,
	provider: str | None = None,
	model: str | None = None,
) -> str | None:
	# JP: テンプレートに現在時刻・ユーザープロファイル等を埋め込む
	# EN: Inject current time and user profile into the template
	template = _load_custom_system_prompt_template()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not template:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Assign value to selection.
	# JP: selection に値を代入する。
	selection = _load_selection('browser')
	# EN: Assign value to provider.
	# JP: provider に値を代入する。
	provider = provider or selection.get('provider', '')
	# EN: Assign value to model.
	# JP: model に値を代入する。
	model = model or selection.get('model', '')

	# EN: Assign value to vision_disabled.
	# JP: vision_disabled に値を代入する。
	vision_disabled = force_disable_vision or _should_disable_vision(provider, model)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if vision_disabled:
		# JP: Vision を使わないモデル向けに関連セクションを削除
		# EN: Remove vision sections for non-vision models
		# Remove vision-related sections for non-multimodal models
		template = re.sub(r'<browser_vision>.*?</browser_vision>\n', '', template, flags=re.DOTALL)
		# Adjust reasoning rules to remove dependency on screenshots
		# EN: Assign value to reasoning_rules_pattern.
		# JP: reasoning_rules_pattern に値を代入する。
		reasoning_rules_pattern = re.compile(r'(<reasoning_rules>.*?</reasoning_rules>)', re.DOTALL)
		# EN: Assign value to template.
		# JP: template に値を代入する。
		template = reasoning_rules_pattern.sub(
			lambda m: m.group(1).replace(
				'Always verify using <browser_vision> (screenshot) as the primary ground truth. If a screenshot is unavailable, fall back to <browser_state>.',
				'Always verify the result of your actions using <browser_state> as the primary ground truth.',
			),
			template,
		)

	# EN: Assign value to now.
	# JP: now に値を代入する。
	now = datetime.now().astimezone()
	# JP: ローカル日時の文字列を生成して埋め込む
	# EN: Build a localized datetime string for the prompt
	weekday_ja = '月火水木金土日'[now.weekday()]
	# EN: Assign value to current_datetime_line.
	# JP: current_datetime_line に値を代入する。
	current_datetime_line = (
		f'{now.strftime("%Y-%m-%d %H:%M %Z (UTC%z, %A)")}'
		f' / ローカル日時: {now.strftime("%Y年%m月%d日")}({weekday_ja}) {now.strftime("%H時%M分")} {now.strftime("%Z")}'
	)
	# EN: Assign value to user_profile_text.
	# JP: user_profile_text に値を代入する。
	user_profile_text = load_user_profile()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not user_profile_text:
		# EN: Assign value to user_profile_text.
		# JP: user_profile_text に値を代入する。
		user_profile_text = '未設定'
	# Avoid str.format() so literal braces in the template (e.g., action schemas) are preserved
	# without triggering KeyError for names like "go_to_url".
	# EN: Assign value to template.
	# JP: template に値を代入する。
	template = template.replace('{max_actions}', str(max_actions_per_step))
	# EN: Assign value to template.
	# JP: template に値を代入する。
	template = template.replace('{current_datetime}', current_datetime_line)
	# EN: Assign value to template.
	# JP: template に値を代入する。
	template = template.replace('{user_profile}', user_profile_text)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return template

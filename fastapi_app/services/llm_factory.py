# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# JP: モデル選択に基づいて LLM クライアントを生成
# EN: Build LLM clients based on selected provider/model
from ..core.config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.env import _get_env_trimmed
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.exceptions import AgentControllerError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .llm_daily_limit import apply_daily_llm_limit

# JP: 開発環境でも browser_use を読み込めるようにパス調整
# EN: Handle imports and adjust sys.path when necessary
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.base import BaseChatModel
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.model_selection import PROVIDER_DEFAULTS, apply_model_selection, update_override
except ModuleNotFoundError:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import sys

	# EN: Assign value to ROOT_DIR.
	# JP: ROOT_DIR に値を代入する。
	ROOT_DIR = Path(__file__).resolve().parents[2]
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if str(ROOT_DIR) not in sys.path:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.path.insert(0, str(ROOT_DIR))
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.base import BaseChatModel
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.model_selection import PROVIDER_DEFAULTS, apply_model_selection, update_override


# EN: Define function `_create_selected_llm`.
# JP: 関数 `_create_selected_llm` を定義する。
def _create_selected_llm(selection_override: dict | None = None) -> BaseChatModel:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Create an LLM instance based on the selected provider and model."""

	# JP: 選択済みのプロバイダ/モデルを反映して設定を確定
	# EN: Resolve provider/model configuration using selection overrides
	# Apply model selection to get the correct provider, model, and configuration
	applied = update_override(selection_override) if selection_override else apply_model_selection('browser')
	# EN: Assign value to provider.
	# JP: provider に値を代入する。
	provider = applied.get('provider', 'openai')
	# EN: Assign value to model.
	# JP: model に値を代入する。
	model = applied.get('model')
	# EN: Assign value to base_url.
	# JP: base_url に値を代入する。
	base_url = applied.get('base_url')

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not model:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AgentControllerError('モデル名が設定されていません。設定モーダルから再保存してください。')

	# JP: プロバイダごとの API キーを取得
	# EN: Resolve provider-specific API key
	# Get provider-specific settings from the defaults map
	provider_config = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS['openai'])
	# EN: Assign value to api_key_env.
	# JP: api_key_env に値を代入する。
	api_key_env = provider_config.get('api_key_env', 'OPENAI_API_KEY')
	# EN: Assign value to api_key.
	# JP: api_key に値を代入する。
	api_key = _get_env_trimmed(api_key_env)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not api_key:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AgentControllerError(f'{api_key_env} が設定されていません。ブラウザエージェントの secrets.env を確認してください。')

	# JP: 必要に応じて base_url を付与
	# EN: Attach base_url when specified
	llm_kwargs: dict[str, Any] = {'model': model, 'api_key': api_key}
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if base_url:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		llm_kwargs['base_url'] = base_url

	# Instantiate the correct client based on the provider
	# JP: プロバイダ別にクライアントを生成して日次制限を適用
	# EN: Instantiate provider client and apply daily limit wrapper
	if provider == 'gemini':
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'Using Google (Gemini) model: {model}')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from browser_use.llm.google.chat import ChatGoogle
		except ModuleNotFoundError as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('Gemini 用の依存関係が見つかりません。必要なライブラリをインストールしてください。') from exc
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return apply_daily_llm_limit(ChatGoogle(**llm_kwargs))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider == 'claude':
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'Using Anthropic (Claude) model: {model}')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from browser_use.llm.anthropic.chat import ChatAnthropic
		except ModuleNotFoundError as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('Claude 用の依存関係が見つかりません。必要なライブラリをインストールしてください。') from exc
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return apply_daily_llm_limit(ChatAnthropic(**llm_kwargs))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider == 'groq':
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'Using Groq model: {model}')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from browser_use.llm.groq.chat import ChatGroq
		except ModuleNotFoundError as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('Groq 用の依存関係が見つかりません。必要なライブラリをインストールしてください。') from exc
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return apply_daily_llm_limit(ChatGroq(**llm_kwargs))

	# Default to OpenAI for any other case, including 'openai' provider
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.info(f'Using OpenAI model: {model} with base_url: {base_url}')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.llm.openai.chat import ChatOpenAI
	except ModuleNotFoundError as exc:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AgentControllerError('OpenAI 用の依存関係が見つかりません。必要なライブラリをインストールしてください。') from exc
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return apply_daily_llm_limit(ChatOpenAI(**llm_kwargs))

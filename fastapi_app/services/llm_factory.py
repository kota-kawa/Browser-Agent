from __future__ import annotations

from pathlib import Path
from typing import Any

# JP: モデル選択に基づいて LLM クライアントを生成
# EN: Build LLM clients based on selected provider/model
from ..core.config import logger
from ..core.env import _get_env_trimmed
from ..core.exceptions import AgentControllerError
from .llm_daily_limit import apply_daily_llm_limit

# JP: 開発環境でも browser_use を読み込めるようにパス調整
# EN: Handle imports and adjust sys.path when necessary
try:
	from browser_use.llm.base import BaseChatModel
	from browser_use.model_selection import PROVIDER_DEFAULTS, apply_model_selection, update_override
except ModuleNotFoundError:
	import sys

	ROOT_DIR = Path(__file__).resolve().parents[2]
	if str(ROOT_DIR) not in sys.path:
		sys.path.insert(0, str(ROOT_DIR))
	from browser_use.llm.base import BaseChatModel
	from browser_use.model_selection import PROVIDER_DEFAULTS, apply_model_selection, update_override


# EN: Define function `_create_selected_llm`.
# JP: 関数 `_create_selected_llm` を定義する。
def _create_selected_llm(selection_override: dict | None = None) -> BaseChatModel:
	"""Create an LLM instance based on the selected provider and model."""

	# JP: 選択済みのプロバイダ/モデルを反映して設定を確定
	# EN: Resolve provider/model configuration using selection overrides
	# Apply model selection to get the correct provider, model, and configuration
	applied = update_override(selection_override) if selection_override else apply_model_selection('browser')
	provider = applied.get('provider', 'openai')
	model = applied.get('model')
	base_url = applied.get('base_url')

	if not model:
		raise AgentControllerError('モデル名が設定されていません。設定モーダルから再保存してください。')

	# JP: プロバイダごとの API キーを取得
	# EN: Resolve provider-specific API key
	# Get provider-specific settings from the defaults map
	provider_config = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS['openai'])
	api_key_env = provider_config.get('api_key_env', 'OPENAI_API_KEY')
	api_key = _get_env_trimmed(api_key_env)

	if not api_key:
		raise AgentControllerError(f'{api_key_env} が設定されていません。ブラウザエージェントの secrets.env を確認してください。')

	# JP: 必要に応じて base_url を付与
	# EN: Attach base_url when specified
	llm_kwargs: dict[str, Any] = {'model': model, 'api_key': api_key}
	if base_url:
		llm_kwargs['base_url'] = base_url

	# Instantiate the correct client based on the provider
	# JP: プロバイダ別にクライアントを生成して日次制限を適用
	# EN: Instantiate provider client and apply daily limit wrapper
	if provider == 'gemini':
		logger.info(f'Using Google (Gemini) model: {model}')
		try:
			from browser_use.llm.google.chat import ChatGoogle
		except ModuleNotFoundError as exc:
			raise AgentControllerError('Gemini 用の依存関係が見つかりません。必要なライブラリをインストールしてください。') from exc
		return apply_daily_llm_limit(ChatGoogle(**llm_kwargs))
	if provider == 'claude':
		logger.info(f'Using Anthropic (Claude) model: {model}')
		try:
			from browser_use.llm.anthropic.chat import ChatAnthropic
		except ModuleNotFoundError as exc:
			raise AgentControllerError('Claude 用の依存関係が見つかりません。必要なライブラリをインストールしてください。') from exc
		return apply_daily_llm_limit(ChatAnthropic(**llm_kwargs))
	if provider == 'groq':
		logger.info(f'Using Groq model: {model}')
		try:
			from browser_use.llm.groq.chat import ChatGroq
		except ModuleNotFoundError as exc:
			raise AgentControllerError('Groq 用の依存関係が見つかりません。必要なライブラリをインストールしてください。') from exc
		return apply_daily_llm_limit(ChatGroq(**llm_kwargs))

	# Default to OpenAI for any other case, including 'openai' provider
	logger.info(f'Using OpenAI model: {model} with base_url: {base_url}')
	try:
		from browser_use.llm.openai.chat import ChatOpenAI
	except ModuleNotFoundError as exc:
		raise AgentControllerError('OpenAI 用の依存関係が見つかりません。必要なライブラリをインストールしてください。') from exc
	return apply_daily_llm_limit(ChatOpenAI(**llm_kwargs))

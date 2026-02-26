# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Convenient access to LLM models.

Usage:
    from browser_use import llm

    # Simple model access
    model = llm.azure_gpt_4_1_mini
    model = llm.openai_gpt_4o
    model = llm.google_gemini_2_5_pro
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.azure.chat import ChatAzureOpenAI
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.google.chat import ChatGoogle
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.openai.chat import ChatOpenAI

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.base import BaseChatModel

# Type stubs for IDE autocomplete
# EN: Assign annotated value to openai_gpt_4o.
# JP: openai_gpt_4o に型付きの値を代入する。
openai_gpt_4o: 'BaseChatModel'
# EN: Assign annotated value to openai_gpt_4o_mini.
# JP: openai_gpt_4o_mini に型付きの値を代入する。
openai_gpt_4o_mini: 'BaseChatModel'
# EN: Assign annotated value to openai_gpt_4_1_mini.
# JP: openai_gpt_4_1_mini に型付きの値を代入する。
openai_gpt_4_1_mini: 'BaseChatModel'
# EN: Assign annotated value to openai_o1.
# JP: openai_o1 に型付きの値を代入する。
openai_o1: 'BaseChatModel'
# EN: Assign annotated value to openai_o1_mini.
# JP: openai_o1_mini に型付きの値を代入する。
openai_o1_mini: 'BaseChatModel'
# EN: Assign annotated value to openai_o1_pro.
# JP: openai_o1_pro に型付きの値を代入する。
openai_o1_pro: 'BaseChatModel'
# EN: Assign annotated value to openai_o3.
# JP: openai_o3 に型付きの値を代入する。
openai_o3: 'BaseChatModel'
# EN: Assign annotated value to openai_o3_mini.
# JP: openai_o3_mini に型付きの値を代入する。
openai_o3_mini: 'BaseChatModel'
# EN: Assign annotated value to openai_o3_pro.
# JP: openai_o3_pro に型付きの値を代入する。
openai_o3_pro: 'BaseChatModel'
# EN: Assign annotated value to openai_o4_mini.
# JP: openai_o4_mini に型付きの値を代入する。
openai_o4_mini: 'BaseChatModel'
# EN: Assign annotated value to openai_gpt_5.
# JP: openai_gpt_5 に型付きの値を代入する。
openai_gpt_5: 'BaseChatModel'
# EN: Assign annotated value to openai_gpt_5_mini.
# JP: openai_gpt_5_mini に型付きの値を代入する。
openai_gpt_5_mini: 'BaseChatModel'
# EN: Assign annotated value to openai_gpt_5_nano.
# JP: openai_gpt_5_nano に型付きの値を代入する。
openai_gpt_5_nano: 'BaseChatModel'

# EN: Assign annotated value to azure_gpt_4o.
# JP: azure_gpt_4o に型付きの値を代入する。
azure_gpt_4o: 'BaseChatModel'
# EN: Assign annotated value to azure_gpt_4o_mini.
# JP: azure_gpt_4o_mini に型付きの値を代入する。
azure_gpt_4o_mini: 'BaseChatModel'
# EN: Assign annotated value to azure_gpt_4_1_mini.
# JP: azure_gpt_4_1_mini に型付きの値を代入する。
azure_gpt_4_1_mini: 'BaseChatModel'
# EN: Assign annotated value to azure_o1.
# JP: azure_o1 に型付きの値を代入する。
azure_o1: 'BaseChatModel'
# EN: Assign annotated value to azure_o1_mini.
# JP: azure_o1_mini に型付きの値を代入する。
azure_o1_mini: 'BaseChatModel'
# EN: Assign annotated value to azure_o1_pro.
# JP: azure_o1_pro に型付きの値を代入する。
azure_o1_pro: 'BaseChatModel'
# EN: Assign annotated value to azure_o3.
# JP: azure_o3 に型付きの値を代入する。
azure_o3: 'BaseChatModel'
# EN: Assign annotated value to azure_o3_mini.
# JP: azure_o3_mini に型付きの値を代入する。
azure_o3_mini: 'BaseChatModel'
# EN: Assign annotated value to azure_o3_pro.
# JP: azure_o3_pro に型付きの値を代入する。
azure_o3_pro: 'BaseChatModel'
# EN: Assign annotated value to azure_gpt_5.
# JP: azure_gpt_5 に型付きの値を代入する。
azure_gpt_5: 'BaseChatModel'
# EN: Assign annotated value to azure_gpt_5_mini.
# JP: azure_gpt_5_mini に型付きの値を代入する。
azure_gpt_5_mini: 'BaseChatModel'

# EN: Assign annotated value to google_gemini_2_0_flash.
# JP: google_gemini_2_0_flash に型付きの値を代入する。
google_gemini_2_0_flash: 'BaseChatModel'
# EN: Assign annotated value to google_gemini_2_0_pro.
# JP: google_gemini_2_0_pro に型付きの値を代入する。
google_gemini_2_0_pro: 'BaseChatModel'
# EN: Assign annotated value to google_gemini_2_5_pro.
# JP: google_gemini_2_5_pro に型付きの値を代入する。
google_gemini_2_5_pro: 'BaseChatModel'
# EN: Assign annotated value to google_gemini_2_5_flash.
# JP: google_gemini_2_5_flash に型付きの値を代入する。
google_gemini_2_5_flash: 'BaseChatModel'
# EN: Assign annotated value to google_gemini_2_5_flash_lite.
# JP: google_gemini_2_5_flash_lite に型付きの値を代入する。
google_gemini_2_5_flash_lite: 'BaseChatModel'


# EN: Define function `get_llm_by_name`.
# JP: 関数 `get_llm_by_name` を定義する。
def get_llm_by_name(model_name: str):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Factory function to create LLM instances from string names with API keys from environment.

	Args:
	    model_name: String name like 'azure_gpt_4_1_mini', 'openai_gpt_4o', etc.

	Returns:
	    LLM instance with API keys from environment variables

	Raises:
	    ValueError: If model_name is not recognized
	"""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not model_name:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError('Model name cannot be empty')

	# Parse model name
	# EN: Assign value to parts.
	# JP: parts に値を代入する。
	parts = model_name.split('_', 1)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if len(parts) < 2:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f"Invalid model name format: '{model_name}'. Expected format: 'provider_model_name'")

	# EN: Assign value to provider.
	# JP: provider に値を代入する。
	provider = parts[0]
	# EN: Assign value to model_part.
	# JP: model_part に値を代入する。
	model_part = parts[1]

	# Convert underscores back to dots/dashes for actual model names
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if 'gpt_4_1_mini' in model_part:
		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = model_part.replace('gpt_4_1_mini', 'gpt-4.1-mini')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif 'gpt_4o_mini' in model_part:
		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = model_part.replace('gpt_4o_mini', 'gpt-4o-mini')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif 'gpt_4o' in model_part:
		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = model_part.replace('gpt_4o', 'gpt-4o')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif 'gemini_2_0' in model_part:
		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = model_part.replace('gemini_2_0', 'gemini-2.0').replace('_', '-')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif 'gemini_2_5' in model_part:
		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = model_part.replace('gemini_2_5', 'gemini-2.5').replace('_', '-')
	else:
		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = model_part.replace('_', '-')

	# OpenAI Models
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if provider == 'openai':
		# EN: Assign value to api_key.
		# JP: api_key に値を代入する。
		api_key = os.getenv('OPENAI_API_KEY')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatOpenAI(model=model, api_key=api_key)

	# Azure OpenAI Models
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif provider == 'azure':
		# EN: Assign value to api_key.
		# JP: api_key に値を代入する。
		api_key = os.getenv('AZURE_OPENAI_KEY') or os.getenv('AZURE_OPENAI_API_KEY')
		# EN: Assign value to azure_endpoint.
		# JP: azure_endpoint に値を代入する。
		azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatAzureOpenAI(model=model, api_key=api_key, azure_endpoint=azure_endpoint)

	# Google Models
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif provider == 'google':
		# EN: Assign value to api_key.
		# JP: api_key に値を代入する。
		api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('OPENAI_API_KEY')
		# EN: Assign value to base_url.
		# JP: base_url に値を代入する。
		base_url = os.getenv('OPENAI_BASE_URL') or os.getenv('OPENAI_API_BASE')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if base_url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ChatOpenAI(model=model, api_key=api_key, base_url=base_url)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatGoogle(model=model, api_key=api_key)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif provider in {'groq', 'claude', 'gemini'}:
		# EN: Assign value to api_key_env.
		# JP: api_key_env に値を代入する。
		api_key_env = {
			'groq': 'GROQ_API_KEY',
			'claude': 'CLAUDE_API_KEY',
			'gemini': 'GEMINI_API_KEY',
		}.get(provider, 'OPENAI_API_KEY')
		# EN: Assign value to api_key.
		# JP: api_key に値を代入する。
		api_key = os.getenv(api_key_env) or os.getenv('OPENAI_API_KEY')
		# EN: Assign value to base_url_env.
		# JP: base_url_env に値を代入する。
		base_url_env = {
			'groq': 'GROQ_API_BASE',
			'claude': 'CLAUDE_API_BASE',
			'gemini': 'GEMINI_API_BASE',
		}.get(provider, 'OPENAI_BASE_URL')
		# EN: Assign value to base_url.
		# JP: base_url に値を代入する。
		base_url = os.getenv(base_url_env) or os.getenv('OPENAI_BASE_URL') or os.getenv('OPENAI_API_BASE')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if provider == 'gemini' and not base_url:
			# EN: Assign value to base_url.
			# JP: base_url に値を代入する。
			base_url = 'https://generativelanguage.googleapis.com/openai/v1'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if provider == 'groq' and not base_url:
			# EN: Assign value to base_url.
			# JP: base_url に値を代入する。
			base_url = 'https://api.groq.com/openai/v1'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if provider == 'claude' and not base_url:
			# EN: Assign value to base_url.
			# JP: base_url に値を代入する。
			base_url = 'https://openrouter.ai/api/v1'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatOpenAI(model=model, api_key=api_key, base_url=base_url)

	else:
		# EN: Assign value to available_providers.
		# JP: available_providers に値を代入する。
		available_providers = ['openai', 'azure', 'google', 'groq', 'claude', 'gemini']
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f"Unknown provider: '{provider}'. Available providers: {', '.join(available_providers)}")


# Pre-configured model instances (lazy loaded via __getattr__)
# EN: Define function `__getattr__`.
# JP: 関数 `__getattr__` を定義する。
def __getattr__(name: str) -> 'BaseChatModel':
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Create model instances on demand with API keys from environment."""
	# Handle chat classes first
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if name == 'ChatOpenAI':
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatOpenAI  # type: ignore
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif name == 'ChatAzureOpenAI':
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatAzureOpenAI  # type: ignore
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif name == 'ChatGoogle':
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatGoogle  # type: ignore

	# Handle model instances - these are the main use case
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return get_llm_by_name(name)
	except ValueError:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# EN: Assign value to __all__.
# JP: __all__ に値を代入する。
__all__ = [
	'ChatOpenAI',
	'ChatAzureOpenAI',
	'ChatGoogle',
	'get_llm_by_name',
	# OpenAI instances - created on demand
	'openai_gpt_4o',
	'openai_gpt_4o_mini',
	'openai_gpt_4_1_mini',
	'openai_o1',
	'openai_o1_mini',
	'openai_o1_pro',
	'openai_o3',
	'openai_o3_mini',
	'openai_o3_pro',
	'openai_o4_mini',
	'openai_gpt_5',
	'openai_gpt_5_mini',
	'openai_gpt_5_nano',
	# Azure instances - created on demand
	'azure_gpt_4o',
	'azure_gpt_4o_mini',
	'azure_gpt_4_1_mini',
	'azure_o1',
	'azure_o1_mini',
	'azure_o1_pro',
	'azure_o3',
	'azure_o3_mini',
	'azure_o3_pro',
	'azure_gpt_5',
	'azure_gpt_5_mini',
	# Google instances - created on demand
	'google_gemini_2_0_flash',
	'google_gemini_2_0_pro',
	'google_gemini_2_5_pro',
	'google_gemini_2_5_flash',
	'google_gemini_2_5_flash_lite',
]

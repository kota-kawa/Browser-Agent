# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
We have switched all of our code from langchain to openai.types.chat.chat_completion_message_param.

For easier transition we have
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING

# Lightweight imports that are commonly used
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	AssistantMessage,
	BaseMessage,
	SystemMessage,
	UserMessage,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	ContentPartImageParam as ContentImage,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	ContentPartRefusalParam as ContentRefusal,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	ContentPartTextParam as ContentText,
)

# Type stubs for lazy imports
# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.anthropic.chat import ChatAnthropic
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.aws.chat_anthropic import ChatAnthropicBedrock
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.aws.chat_bedrock import ChatAWSBedrock
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.azure.chat import ChatAzureOpenAI
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.deepseek.chat import ChatDeepSeek
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.google.chat import ChatGoogle
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.groq.chat import ChatGroq
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.ollama.chat import ChatOllama
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.openai.chat import ChatOpenAI
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.openrouter.chat import ChatOpenRouter

	# Type stubs for model instances - enables IDE autocomplete
	# EN: Assign annotated value to openai_gpt_4o.
	# JP: openai_gpt_4o に型付きの値を代入する。
	openai_gpt_4o: ChatOpenAI
	# EN: Assign annotated value to openai_gpt_4o_mini.
	# JP: openai_gpt_4o_mini に型付きの値を代入する。
	openai_gpt_4o_mini: ChatOpenAI
	# EN: Assign annotated value to openai_gpt_4_1_mini.
	# JP: openai_gpt_4_1_mini に型付きの値を代入する。
	openai_gpt_4_1_mini: ChatOpenAI
	# EN: Assign annotated value to openai_o1.
	# JP: openai_o1 に型付きの値を代入する。
	openai_o1: ChatOpenAI
	# EN: Assign annotated value to openai_o1_mini.
	# JP: openai_o1_mini に型付きの値を代入する。
	openai_o1_mini: ChatOpenAI
	# EN: Assign annotated value to openai_o1_pro.
	# JP: openai_o1_pro に型付きの値を代入する。
	openai_o1_pro: ChatOpenAI
	# EN: Assign annotated value to openai_o3.
	# JP: openai_o3 に型付きの値を代入する。
	openai_o3: ChatOpenAI
	# EN: Assign annotated value to openai_o3_mini.
	# JP: openai_o3_mini に型付きの値を代入する。
	openai_o3_mini: ChatOpenAI
	# EN: Assign annotated value to openai_o3_pro.
	# JP: openai_o3_pro に型付きの値を代入する。
	openai_o3_pro: ChatOpenAI
	# EN: Assign annotated value to openai_o4_mini.
	# JP: openai_o4_mini に型付きの値を代入する。
	openai_o4_mini: ChatOpenAI
	# EN: Assign annotated value to openai_gpt_5.
	# JP: openai_gpt_5 に型付きの値を代入する。
	openai_gpt_5: ChatOpenAI
	# EN: Assign annotated value to openai_gpt_5_mini.
	# JP: openai_gpt_5_mini に型付きの値を代入する。
	openai_gpt_5_mini: ChatOpenAI
	# EN: Assign annotated value to openai_gpt_5_nano.
	# JP: openai_gpt_5_nano に型付きの値を代入する。
	openai_gpt_5_nano: ChatOpenAI

	# EN: Assign annotated value to azure_gpt_4o.
	# JP: azure_gpt_4o に型付きの値を代入する。
	azure_gpt_4o: ChatAzureOpenAI
	# EN: Assign annotated value to azure_gpt_4o_mini.
	# JP: azure_gpt_4o_mini に型付きの値を代入する。
	azure_gpt_4o_mini: ChatAzureOpenAI
	# EN: Assign annotated value to azure_gpt_4_1_mini.
	# JP: azure_gpt_4_1_mini に型付きの値を代入する。
	azure_gpt_4_1_mini: ChatAzureOpenAI
	# EN: Assign annotated value to azure_o1.
	# JP: azure_o1 に型付きの値を代入する。
	azure_o1: ChatAzureOpenAI
	# EN: Assign annotated value to azure_o1_mini.
	# JP: azure_o1_mini に型付きの値を代入する。
	azure_o1_mini: ChatAzureOpenAI
	# EN: Assign annotated value to azure_o1_pro.
	# JP: azure_o1_pro に型付きの値を代入する。
	azure_o1_pro: ChatAzureOpenAI
	# EN: Assign annotated value to azure_o3.
	# JP: azure_o3 に型付きの値を代入する。
	azure_o3: ChatAzureOpenAI
	# EN: Assign annotated value to azure_o3_mini.
	# JP: azure_o3_mini に型付きの値を代入する。
	azure_o3_mini: ChatAzureOpenAI
	# EN: Assign annotated value to azure_o3_pro.
	# JP: azure_o3_pro に型付きの値を代入する。
	azure_o3_pro: ChatAzureOpenAI
	# EN: Assign annotated value to azure_gpt_5.
	# JP: azure_gpt_5 に型付きの値を代入する。
	azure_gpt_5: ChatAzureOpenAI
	# EN: Assign annotated value to azure_gpt_5_mini.
	# JP: azure_gpt_5_mini に型付きの値を代入する。
	azure_gpt_5_mini: ChatAzureOpenAI

	# EN: Assign annotated value to google_gemini_2_0_flash.
	# JP: google_gemini_2_0_flash に型付きの値を代入する。
	google_gemini_2_0_flash: ChatGoogle
	# EN: Assign annotated value to google_gemini_2_0_pro.
	# JP: google_gemini_2_0_pro に型付きの値を代入する。
	google_gemini_2_0_pro: ChatGoogle
	# EN: Assign annotated value to google_gemini_2_5_pro.
	# JP: google_gemini_2_5_pro に型付きの値を代入する。
	google_gemini_2_5_pro: ChatGoogle
	# EN: Assign annotated value to google_gemini_2_5_flash.
	# JP: google_gemini_2_5_flash に型付きの値を代入する。
	google_gemini_2_5_flash: ChatGoogle
	# EN: Assign annotated value to google_gemini_2_5_flash_lite.
	# JP: google_gemini_2_5_flash_lite に型付きの値を代入する。
	google_gemini_2_5_flash_lite: ChatGoogle

# Models are imported on-demand via __getattr__

# Lazy imports mapping for heavy chat models
# EN: Assign value to _LAZY_IMPORTS.
# JP: _LAZY_IMPORTS に値を代入する。
_LAZY_IMPORTS = {
	'ChatAnthropic': ('browser_use.llm.anthropic.chat', 'ChatAnthropic'),
	'ChatAnthropicBedrock': ('browser_use.llm.aws.chat_anthropic', 'ChatAnthropicBedrock'),
	'ChatAWSBedrock': ('browser_use.llm.aws.chat_bedrock', 'ChatAWSBedrock'),
	'ChatAzureOpenAI': ('browser_use.llm.azure.chat', 'ChatAzureOpenAI'),
	'ChatDeepSeek': ('browser_use.llm.deepseek.chat', 'ChatDeepSeek'),
	'ChatGoogle': ('browser_use.llm.google.chat', 'ChatGoogle'),
	'ChatGroq': ('browser_use.llm.groq.chat', 'ChatGroq'),
	'ChatOllama': ('browser_use.llm.ollama.chat', 'ChatOllama'),
	'ChatOpenAI': ('browser_use.llm.openai.chat', 'ChatOpenAI'),
	'ChatOpenRouter': ('browser_use.llm.openrouter.chat', 'ChatOpenRouter'),
}

# Cache for model instances - only created when accessed
# EN: Assign annotated value to _model_cache.
# JP: _model_cache に型付きの値を代入する。
_model_cache: dict[str, 'BaseChatModel'] = {}


# EN: Define function `__getattr__`.
# JP: 関数 `__getattr__` を定義する。
def __getattr__(name: str):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Lazy import mechanism for heavy chat model imports and model instances."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if name in _LAZY_IMPORTS:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		module_path, attr_name = _LAZY_IMPORTS[name]
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from importlib import import_module

			# EN: Assign value to module.
			# JP: module に値を代入する。
			module = import_module(module_path)
			# EN: Assign value to attr.
			# JP: attr に値を代入する。
			attr = getattr(module, attr_name)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return attr
		except ImportError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ImportError(f'Failed to import {name} from {module_path}: {e}') from e

	# Check cache first for model instances
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if name in _model_cache:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _model_cache[name]

	# Try to get model instances from models module on-demand
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.llm.models import __getattr__ as models_getattr

		# EN: Assign value to attr.
		# JP: attr に値を代入する。
		attr = models_getattr(name)
		# Cache in our clean cache dict
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		_model_cache[name] = attr
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return attr
	except (AttributeError, ImportError):
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass

	# EN: Raise an exception.
	# JP: 例外を送出する。
	raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# EN: Assign value to __all__.
# JP: __all__ に値を代入する。
__all__ = [
	# Message types -> for easier transition from langchain
	'BaseMessage',
	'UserMessage',
	'SystemMessage',
	'AssistantMessage',
	# Content parts with better names
	'ContentText',
	'ContentRefusal',
	'ContentImage',
	# Chat models
	'BaseChatModel',
	'ChatOpenAI',
	'ChatDeepSeek',
	'ChatGoogle',
	'ChatAnthropic',
	'ChatAnthropicBedrock',
	'ChatAWSBedrock',
	'ChatGroq',
	'ChatAzureOpenAI',
	'ChatOllama',
	'ChatOpenRouter',
]

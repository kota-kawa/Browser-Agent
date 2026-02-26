# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Mapping
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass, field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, TypeVar, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic import (
	NOT_GIVEN,
	APIConnectionError,
	APIStatusError,
	AsyncAnthropic,
	NotGiven,
	RateLimitError,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types import CacheControlEphemeralParam, Message, ToolParam
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types.model_param import ModelParam
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types.text_block import TextBlock
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types.tool_choice_tool_param import ToolChoiceToolParam
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from httpx import Timeout
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.anthropic.serializer import AnthropicMessageSerializer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.schema import SchemaOptimizer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `ChatAnthropic`.
# JP: クラス `ChatAnthropic` を定義する。
@dataclass
class ChatAnthropic(BaseChatModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A wrapper around Anthropic's chat model.
	"""

	# Model configuration
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str | ModelParam
	# EN: Assign annotated value to max_tokens.
	# JP: max_tokens に型付きの値を代入する。
	max_tokens: int = 8192
	# EN: Assign annotated value to temperature.
	# JP: temperature に型付きの値を代入する。
	temperature: float | None = None
	# EN: Assign annotated value to top_p.
	# JP: top_p に型付きの値を代入する。
	top_p: float | None = None
	# EN: Assign annotated value to seed.
	# JP: seed に型付きの値を代入する。
	seed: int | None = None

	# Client initialization parameters
	# EN: Assign annotated value to api_key.
	# JP: api_key に型付きの値を代入する。
	api_key: str | None = None
	# EN: Assign annotated value to auth_token.
	# JP: auth_token に型付きの値を代入する。
	auth_token: str | None = None
	# EN: Assign annotated value to base_url.
	# JP: base_url に型付きの値を代入する。
	base_url: str | httpx.URL | None = None
	# EN: Assign annotated value to timeout.
	# JP: timeout に型付きの値を代入する。
	timeout: float | Timeout | None | NotGiven = NotGiven()
	# EN: Assign annotated value to max_retries.
	# JP: max_retries に型付きの値を代入する。
	max_retries: int = 10
	# EN: Assign annotated value to default_headers.
	# JP: default_headers に型付きの値を代入する。
	default_headers: Mapping[str, str] | None = None
	# EN: Assign annotated value to default_query.
	# JP: default_query に型付きの値を代入する。
	default_query: Mapping[str, object] | None = None

	# EN: Assign annotated value to _async_client.
	# JP: _async_client に型付きの値を代入する。
	_async_client: AsyncAnthropic = field(init=False, repr=False)

	# EN: Define function `__post_init__`.
	# JP: 関数 `__post_init__` を定義する。
	def __post_init__(self) -> None:
		# EN: Assign value to client_params.
		# JP: client_params に値を代入する。
		client_params = self._get_client_params()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._async_client = AsyncAnthropic(**client_params)

	# Static
	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'anthropic'

	# EN: Define function `_get_client_params`.
	# JP: 関数 `_get_client_params` を定義する。
	def _get_client_params(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Prepare client parameters dictionary."""
		# Define base client params
		# EN: Assign value to base_params.
		# JP: base_params に値を代入する。
		base_params = {
			'api_key': self.api_key,
			'auth_token': self.auth_token,
			'base_url': self.base_url,
			'timeout': self.timeout,
			'max_retries': self.max_retries,
			'default_headers': self.default_headers,
			'default_query': self.default_query,
		}

		# Create client_params dict with non-None values and non-NotGiven values
		# EN: Assign value to client_params.
		# JP: client_params に値を代入する。
		client_params = {}
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for k, v in base_params.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if v is not None and v is not NotGiven():
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				client_params[k] = v

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return client_params

	# EN: Define function `_get_client_params_for_invoke`.
	# JP: 関数 `_get_client_params_for_invoke` を定義する。
	def _get_client_params_for_invoke(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Prepare client parameters dictionary for invoke."""

		# EN: Assign value to client_params.
		# JP: client_params に値を代入する。
		client_params = {}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.temperature is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['temperature'] = self.temperature

		# max_tokens is required for Anthropic, use default if not set
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		client_params['max_tokens'] = self.max_tokens if self.max_tokens is not None else 4096

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.top_p is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['top_p'] = self.top_p

		# Note: 'seed' is currently not supported in standard Anthropic Messages API
		# but if it becomes supported, it can remain.
		# Removing it to be safe unless we know it's supported (it's not in current docs).
		# if self.seed is not None:
		# 	client_params['seed'] = self.seed

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return client_params

	# EN: Define function `get_client`.
	# JP: 関数 `get_client` を定義する。
	def get_client(self) -> AsyncAnthropic:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Returns an AsyncAnthropic client.

		Returns:
			AsyncAnthropic: An instance of the AsyncAnthropic client.
		"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._async_client

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(self.model)

	# EN: Define function `_get_usage`.
	# JP: 関数 `_get_usage` を定義する。
	def _get_usage(self, response: Message) -> ChatInvokeUsage | None:
		# EN: Assign value to usage.
		# JP: usage に値を代入する。
		usage = ChatInvokeUsage(
			prompt_tokens=response.usage.input_tokens
			+ (
				response.usage.cache_read_input_tokens or 0
			),  # Total tokens in Anthropic are a bit fucked, you have to add cached tokens to the prompt tokens
			completion_tokens=response.usage.output_tokens,
			total_tokens=response.usage.input_tokens + response.usage.output_tokens,
			prompt_cached_tokens=response.usage.cache_read_input_tokens,
			prompt_cache_creation_tokens=response.usage.cache_creation_input_tokens,
			prompt_image_tokens=None,
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return usage

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	async def ainvoke(self, messages: list[BaseMessage], output_format: None = None) -> ChatInvokeCompletion[str]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	async def ainvoke(self, messages: list[BaseMessage], output_format: type[T]) -> ChatInvokeCompletion[T]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		anthropic_messages, system_prompt = AnthropicMessageSerializer.serialize_messages(messages)

		# Important: claude-haiku-4-5 and newer models might require extra headers if in beta
		# But since I cannot confirm the exact header, I will rely on standard calls.
		# However, one common issue is that `anthropic_messages` might contain cache_control
		# on non-latest models if not handled.
		# The serializer seems to handle it.

		# Also, ensure system_prompt is passed correctly (it can be a string or list of blocks)
		# The API expects `system` to be str or list[TextBlockParam].
		# The serializer returns list[TextBlockParam] | str | None. Correct.

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format is None:
				# Normal completion without structured output
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self.get_client().messages.create(
					model=self.model,
					messages=anthropic_messages,
					system=system_prompt or NOT_GIVEN,
					**self._get_client_params_for_invoke(),
				)

				# Ensure we have a valid Message object before accessing attributes
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not isinstance(response, Message):
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ModelProviderError(
						message=f'Unexpected response type from Anthropic API: {type(response).__name__}. Response: {str(response)[:200]}',
						status_code=502,
						model=self.name,
					)

				# EN: Assign value to usage.
				# JP: usage に値を代入する。
				usage = self._get_usage(response)

				# Extract text from the first content block
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not response.content:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ChatInvokeCompletion(completion='', usage=usage)

				# EN: Assign value to first_content.
				# JP: first_content に値を代入する。
				first_content = response.content[0]
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(first_content, TextBlock):
					# EN: Assign value to response_text.
					# JP: response_text に値を代入する。
					response_text = first_content.text
				else:
					# If it's not a text block, convert to string
					# EN: Assign value to response_text.
					# JP: response_text に値を代入する。
					response_text = str(first_content)

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(
					completion=response_text,
					usage=usage,
				)

			else:
				# Use tool calling for structured output
				# Create a tool that represents the output format
				# EN: Assign value to tool_name.
				# JP: tool_name に値を代入する。
				tool_name = output_format.__name__
				# EN: Assign value to schema.
				# JP: schema に値を代入する。
				schema = SchemaOptimizer.create_optimized_json_schema(output_format)

				# Remove title from schema if present (Anthropic doesn't like it in parameters)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'title' in schema:
					# EN: Delete referenced values.
					# JP: 参照される値を削除する。
					del schema['title']

				# EN: Assign value to tool.
				# JP: tool に値を代入する。
				tool = ToolParam(
					name=tool_name,
					description=f'Extract information in the format of {tool_name}',
					input_schema=schema,
					cache_control=CacheControlEphemeralParam(type='ephemeral'),
				)

				# Force the model to use this tool
				# EN: Assign value to tool_choice.
				# JP: tool_choice に値を代入する。
				tool_choice = ToolChoiceToolParam(type='tool', name=tool_name)

				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self.get_client().messages.create(
					model=self.model,
					messages=anthropic_messages,
					tools=[tool],
					system=system_prompt or NOT_GIVEN,
					tool_choice=tool_choice,
					**self._get_client_params_for_invoke(),
				)

				# Ensure we have a valid Message object before accessing attributes
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not isinstance(response, Message):
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ModelProviderError(
						message=f'Unexpected response type from Anthropic API: {type(response).__name__}. Response: {str(response)[:200]}',
						status_code=502,
						model=self.name,
					)

				# EN: Assign value to usage.
				# JP: usage に値を代入する。
				usage = self._get_usage(response)

				# Extract the tool use block
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for content_block in response.content:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if hasattr(content_block, 'type') and content_block.type == 'tool_use':
						# Parse the tool input as the structured output
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return ChatInvokeCompletion(completion=output_format.model_validate(content_block.input), usage=usage)

				# If no tool use block found, raise an error
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError('Expected tool use in response but none found')

		except APIConnectionError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=e.message, model=self.name) from e
		except RateLimitError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelRateLimitError(message=e.message, model=self.name) from e
		except APIStatusError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=e.message, status_code=e.status_code, model=self.name) from e
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=str(e), model=self.name) from e

	# EN: Define async function `aclose`.
	# JP: 非同期関数 `aclose` を定義する。
	async def aclose(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close the underlying HTTP client."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, '_async_client') and not self._async_client.is_closed:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._async_client.aclose()
			except RuntimeError as e:
				# Ignore "Event loop is closed" error during cleanup
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'Event loop is closed' not in str(e):
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Mapping
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, TypeVar, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai.types.chat.chat_completion import ChatCompletion
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai.types.shared_params.response_format_json_schema import (
	JSONSchema,
	ResponseFormatJSONSchema,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

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
from browser_use.llm.openrouter.serializer import OpenRouterMessageSerializer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.schema import SchemaOptimizer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `ChatOpenRouter`.
# JP: クラス `ChatOpenRouter` を定義する。
@dataclass
class ChatOpenRouter(BaseChatModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A wrapper around OpenRouter's chat API, which provides access to various LLM models
	through a unified OpenAI-compatible interface.

	This class implements the BaseChatModel protocol for OpenRouter's API.
	"""

	# Model configuration
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str

	# Model params
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
	# EN: Assign annotated value to http_referer.
	# JP: http_referer に型付きの値を代入する。
	http_referer: str | None = None  # OpenRouter specific parameter for tracking
	# EN: Assign annotated value to base_url.
	# JP: base_url に型付きの値を代入する。
	base_url: str | httpx.URL = 'https://openrouter.ai/api/v1'
	# EN: Assign annotated value to timeout.
	# JP: timeout に型付きの値を代入する。
	timeout: float | httpx.Timeout | None = None
	# EN: Assign annotated value to max_retries.
	# JP: max_retries に型付きの値を代入する。
	max_retries: int = 10
	# EN: Assign annotated value to default_headers.
	# JP: default_headers に型付きの値を代入する。
	default_headers: Mapping[str, str] | None = None
	# EN: Assign annotated value to default_query.
	# JP: default_query に型付きの値を代入する。
	default_query: Mapping[str, object] | None = None
	# EN: Assign annotated value to http_client.
	# JP: http_client に型付きの値を代入する。
	http_client: httpx.AsyncClient | None = None
	# EN: Assign annotated value to _strict_response_validation.
	# JP: _strict_response_validation に型付きの値を代入する。
	_strict_response_validation: bool = False

	# Static
	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'openrouter'

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
			'base_url': self.base_url,
			'timeout': self.timeout,
			'max_retries': self.max_retries,
			'default_headers': self.default_headers,
			'default_query': self.default_query,
			'_strict_response_validation': self._strict_response_validation,
			'top_p': self.top_p,
			'seed': self.seed,
		}

		# Create client_params dict with non-None values
		# EN: Assign value to client_params.
		# JP: client_params に値を代入する。
		client_params = {k: v for k, v in base_params.items() if v is not None}

		# Add http_client if provided
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.http_client is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['http_client'] = self.http_client

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return client_params

	# EN: Define function `get_client`.
	# JP: 関数 `get_client` を定義する。
	def get_client(self) -> AsyncOpenAI:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Returns an AsyncOpenAI client configured for OpenRouter.

		Returns:
		    AsyncOpenAI: An instance of the AsyncOpenAI client with OpenRouter base URL.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not hasattr(self, '_client'):
			# EN: Assign value to client_params.
			# JP: client_params に値を代入する。
			client_params = self._get_client_params()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._client = AsyncOpenAI(**client_params)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._client

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(self.model)

	# EN: Define function `_get_usage`.
	# JP: 関数 `_get_usage` を定義する。
	def _get_usage(self, response: ChatCompletion) -> ChatInvokeUsage | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract usage information from the OpenRouter response."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if response.usage is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to prompt_details.
		# JP: prompt_details に値を代入する。
		prompt_details = getattr(response.usage, 'prompt_tokens_details', None)
		# EN: Assign value to cached_tokens.
		# JP: cached_tokens に値を代入する。
		cached_tokens = prompt_details.cached_tokens if prompt_details else None

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatInvokeUsage(
			prompt_tokens=response.usage.prompt_tokens,
			prompt_cached_tokens=cached_tokens,
			prompt_cache_creation_tokens=None,
			prompt_image_tokens=None,
			# Completion
			completion_tokens=response.usage.completion_tokens,
			total_tokens=response.usage.total_tokens,
		)

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
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Invoke the model with the given messages through OpenRouter.

		Args:
		    messages: List of chat messages
		    output_format: Optional Pydantic model class for structured output

		Returns:
		    Either a string response or an instance of output_format
		"""
		# EN: Assign value to openrouter_messages.
		# JP: openrouter_messages に値を代入する。
		openrouter_messages = OpenRouterMessageSerializer.serialize_messages(messages)

		# Set up extra headers for OpenRouter
		# EN: Assign value to extra_headers.
		# JP: extra_headers に値を代入する。
		extra_headers = {}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.http_referer:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			extra_headers['HTTP-Referer'] = self.http_referer

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format is None:
				# Return string response
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self.get_client().chat.completions.create(
					model=self.model,
					messages=openrouter_messages,
					temperature=self.temperature,
					top_p=self.top_p,
					seed=self.seed,
					extra_headers=extra_headers,
				)

				# EN: Assign value to usage.
				# JP: usage に値を代入する。
				usage = self._get_usage(response)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(
					completion=response.choices[0].message.content or '',
					usage=usage,
				)

			else:
				# Create a JSON schema for structured output
				# EN: Assign value to schema.
				# JP: schema に値を代入する。
				schema = SchemaOptimizer.create_optimized_json_schema(output_format)

				# EN: Assign annotated value to response_format_schema.
				# JP: response_format_schema に型付きの値を代入する。
				response_format_schema: JSONSchema = {
					'name': 'agent_output',
					'strict': True,
					'schema': schema,
				}

				# Return structured response
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self.get_client().chat.completions.create(
					model=self.model,
					messages=openrouter_messages,
					temperature=self.temperature,
					top_p=self.top_p,
					seed=self.seed,
					response_format=ResponseFormatJSONSchema(
						json_schema=response_format_schema,
						type='json_schema',
					),
					extra_headers=extra_headers,
				)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if response.choices[0].message.content is None:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ModelProviderError(
						message='Failed to parse structured output from model response',
						status_code=500,
						model=self.name,
					)
				# EN: Assign value to usage.
				# JP: usage に値を代入する。
				usage = self._get_usage(response)

				# EN: Assign value to parsed.
				# JP: parsed に値を代入する。
				parsed = output_format.model_validate_json(response.choices[0].message.content)

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(
					completion=parsed,
					usage=usage,
				)

		except RateLimitError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelRateLimitError(message=e.message, model=self.name) from e

		except APIConnectionError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=str(e), model=self.name) from e

		except APIStatusError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=e.message, status_code=e.status_code, model=self.name) from e

		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=str(e), model=self.name) from e

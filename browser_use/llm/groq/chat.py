# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass, field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Literal, TypeVar, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from groq import (
	APIError,
	APIResponseValidationError,
	APIStatusError,
	AsyncGroq,
	NotGiven,
	RateLimitError,
	Timeout,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from groq.types.chat import ChatCompletion, ChatCompletionToolChoiceOptionParam, ChatCompletionToolParam
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from httpx import URL
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel, ChatInvokeCompletion
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.groq.parser import try_parse_groq_failed_generation
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.groq.serializer import GroqMessageSerializer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage, UserMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.schema import SchemaOptimizer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeUsage

# EN: Assign value to GroqVerifiedModels.
# JP: GroqVerifiedModels に値を代入する。
GroqVerifiedModels = Literal[
	'llama-3.3-70b-versatile',
	'llama-3.1-8b-instant',
	'openai/gpt-oss-20b',
	'qwen/qwen3-32b',
]

# EN: Assign value to JsonSchemaModels.
# JP: JsonSchemaModels に値を代入する。
JsonSchemaModels = [
	'llama-3.3-70b-versatile',
	'llama-3.1-8b-instant',
	'openai/gpt-oss-20b',
	'qwen/qwen3-32b',
]

# EN: Assign value to ToolCallingModels.
# JP: ToolCallingModels に値を代入する。
ToolCallingModels = []

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define class `ChatGroq`.
# JP: クラス `ChatGroq` を定義する。
@dataclass
class ChatGroq(BaseChatModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A wrapper around AsyncGroq that implements the BaseLLM protocol.
	"""

	# Model configuration
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: GroqVerifiedModels | str

	# Model params
	# EN: Assign annotated value to temperature.
	# JP: temperature に型付きの値を代入する。
	temperature: float | None = None
	# EN: Assign annotated value to service_tier.
	# JP: service_tier に型付きの値を代入する。
	service_tier: Literal['auto', 'on_demand', 'flex'] | None = None
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
	# EN: Assign annotated value to base_url.
	# JP: base_url に型付きの値を代入する。
	base_url: str | URL | None = None
	# EN: Assign annotated value to timeout.
	# JP: timeout に型付きの値を代入する。
	timeout: float | Timeout | NotGiven | None = None
	# EN: Assign annotated value to max_retries.
	# JP: max_retries に型付きの値を代入する。
	max_retries: int = 10

	# EN: Assign annotated value to _async_client.
	# JP: _async_client に型付きの値を代入する。
	_async_client: AsyncGroq = field(init=False, repr=False)

	# EN: Define function `__post_init__`.
	# JP: 関数 `__post_init__` を定義する。
	def __post_init__(self) -> None:
		# The Groq SDK automatically appends '/openai/v1', so we remove it from the base_url if present
		# EN: Assign value to client_base_url.
		# JP: client_base_url に値を代入する。
		client_base_url = self.base_url
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(client_base_url, str) and client_base_url.endswith('/openai/v1'):
			# EN: Assign value to client_base_url.
			# JP: client_base_url に値を代入する。
			client_base_url = client_base_url.removesuffix('/openai/v1')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(client_base_url, URL) and client_base_url.path.endswith('/openai/v1'):
			# EN: Assign value to client_base_url.
			# JP: client_base_url に値を代入する。
			client_base_url = client_base_url.copy_with(path=client_base_url.path.removesuffix('/openai/v1'))

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._async_client = AsyncGroq(
			api_key=self.api_key, base_url=client_base_url, timeout=self.timeout, max_retries=self.max_retries
		)

	# EN: Define function `get_client`.
	# JP: 関数 `get_client` を定義する。
	def get_client(self) -> AsyncGroq:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._async_client

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'groq'

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(self.model)

	# EN: Define function `_is_vision_model`.
	# JP: 関数 `_is_vision_model` を定義する。
	def _is_vision_model(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the current model supports vision."""
		# User instruction: "In Groq-type models, vision is completely unsupported."
		# Therefore, always return False.
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `_filter_messages`.
	# JP: 関数 `_filter_messages` を定義する。
	def _filter_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Filter out image content for non-vision models."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._is_vision_model():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return messages

		# EN: Assign value to filtered_messages.
		# JP: filtered_messages に値を代入する。
		filtered_messages = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for msg in messages:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(msg, UserMessage) and isinstance(msg.content, list):
				# Filter content parts
				# EN: Assign value to new_content.
				# JP: new_content に値を代入する。
				new_content = []
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for part in msg.content:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if part.type == 'text':
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						new_content.append(part)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif part.type == 'image_url':
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.warning(f'Removing image from message for non-vision model {self.model}')
						# We simply drop the image part.

				# Create a new message with filtered content
				# We use model_copy to preserve other attributes like name, but replace content
				# EN: Assign value to new_msg.
				# JP: new_msg に値を代入する。
				new_msg = msg.model_copy(update={'content': new_content})
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				filtered_messages.append(new_msg)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				filtered_messages.append(msg)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return filtered_messages

	# EN: Define function `_get_usage`.
	# JP: 関数 `_get_usage` を定義する。
	def _get_usage(self, response: ChatCompletion) -> ChatInvokeUsage | None:
		# EN: Assign value to usage.
		# JP: usage に値を代入する。
		usage = (
			ChatInvokeUsage(
				prompt_tokens=response.usage.prompt_tokens,
				completion_tokens=response.usage.completion_tokens,
				total_tokens=response.usage.total_tokens,
				prompt_cached_tokens=None,  # Groq doesn't support cached tokens
				prompt_cache_creation_tokens=None,
				prompt_image_tokens=None,
			)
			if response.usage is not None
			else None
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
		# Filter messages based on model capabilities
		# EN: Assign value to messages.
		# JP: messages に値を代入する。
		messages = self._filter_messages(messages)

		# EN: Assign value to groq_messages.
		# JP: groq_messages に値を代入する。
		groq_messages = GroqMessageSerializer.serialize_messages(messages)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format is None:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._invoke_regular_completion(groq_messages)
			else:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._invoke_structured_output(groq_messages, output_format)

		except RateLimitError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelRateLimitError(message=e.response.text, status_code=e.response.status_code, model=self.name) from e

		except APIResponseValidationError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=e.response.text, status_code=e.response.status_code, model=self.name) from e

		except APIStatusError as e:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format is None:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(message=e.response.text, status_code=e.response.status_code, model=self.name) from e
			else:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug(f'Groq failed generation: {e.response.text}; fallback to manual parsing')

					# EN: Assign value to parsed_response.
					# JP: parsed_response に値を代入する。
					parsed_response = try_parse_groq_failed_generation(e, output_format)

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug('Manual error parsing successful ✅')

					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ChatInvokeCompletion(
						completion=parsed_response,
						usage=None,  # because this is a hacky way to get the outputs
						# TODO: @groq needs to fix their parsers and validators
					)
				except Exception as _:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ModelProviderError(message=str(e), status_code=e.response.status_code, model=self.name) from e

		except APIError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=e.message, model=self.name) from e
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=str(e), model=self.name) from e

	# EN: Define async function `_invoke_regular_completion`.
	# JP: 非同期関数 `_invoke_regular_completion` を定義する。
	async def _invoke_regular_completion(self, groq_messages) -> ChatInvokeCompletion[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle regular completion without structured output."""
		# EN: Assign value to chat_completion.
		# JP: chat_completion に値を代入する。
		chat_completion = await self.get_client().chat.completions.create(
			messages=groq_messages,
			model=self.model,
			service_tier=self.service_tier,
			temperature=self.temperature,
			top_p=self.top_p,
			seed=self.seed,
		)
		# EN: Assign value to usage.
		# JP: usage に値を代入する。
		usage = self._get_usage(chat_completion)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatInvokeCompletion(
			completion=chat_completion.choices[0].message.content or '',
			usage=usage,
		)

	# EN: Define async function `_invoke_structured_output`.
	# JP: 非同期関数 `_invoke_structured_output` を定義する。
	async def _invoke_structured_output(self, groq_messages, output_format: type[T]) -> ChatInvokeCompletion[T]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle structured output using either tool calling or JSON schema."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.model in ToolCallingModels:
				# EN: Assign value to schema.
				# JP: schema に値を代入する。
				schema = SchemaOptimizer.create_optimized_json_schema(output_format)
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self._invoke_with_tool_calling(groq_messages, output_format, schema)
				# EN: Assign value to response_text.
				# JP: response_text に値を代入する。
				response_text = response.choices[0].message.tool_calls[0].function.arguments
			else:
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self.get_client().chat.completions.create(
					model=self.model,
					messages=groq_messages,
					temperature=self.temperature,
					top_p=self.top_p,
					seed=self.seed,
					response_format={'type': 'json_object'},
					service_tier=self.service_tier,
				)
				# EN: Assign value to response_text.
				# JP: response_text に値を代入する。
				response_text = response.choices[0].message.content or ''

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not response_text:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(
					message='No content in response',
					status_code=500,
					model=self.name,
				)

			# EN: Assign value to parsed_response.
			# JP: parsed_response に値を代入する。
			parsed_response = output_format.model_validate_json(response_text)
			# EN: Assign value to usage.
			# JP: usage に値を代入する。
			usage = self._get_usage(response)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ChatInvokeCompletion(
				completion=parsed_response,
				usage=usage,
			)
		except (APIStatusError, json.JSONDecodeError, ModelProviderError) as e:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Groq failed generation: {e}; fallback to manual parsing')
				# EN: Assign value to parsed_response.
				# JP: parsed_response に値を代入する。
				parsed_response = try_parse_groq_failed_generation(e, output_format)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('Manual error parsing successful ✅')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(
					completion=parsed_response,
					usage=None,
				)
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(message=str(e), model=self.name) from e

	# EN: Define async function `_invoke_with_tool_calling`.
	# JP: 非同期関数 `_invoke_with_tool_calling` を定義する。
	async def _invoke_with_tool_calling(self, groq_messages, output_format: type[T], schema) -> ChatCompletion:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle structured output using tool calling."""
		# EN: Assign value to tool.
		# JP: tool に値を代入する。
		tool = ChatCompletionToolParam(
			function={
				'name': output_format.__name__,
				'description': f'Extract information in the format of {output_format.__name__}',
				'parameters': schema,
			},
			type='function',
		)
		# EN: Assign annotated value to tool_choice.
		# JP: tool_choice に型付きの値を代入する。
		tool_choice: ChatCompletionToolChoiceOptionParam = 'required'

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await self.get_client().chat.completions.create(
			model=self.model,
			messages=groq_messages,
			temperature=self.temperature,
			top_p=self.top_p,
			seed=self.seed,
			tools=[tool],
			tool_choice=tool_choice,
			service_tier=self.service_tier,
		)

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

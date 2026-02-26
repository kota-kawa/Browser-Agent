# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Iterable, Mapping
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass, field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, Literal, TypeVar, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai.types.chat import ChatCompletionContentPartTextParam
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai.types.chat.chat_completion import ChatCompletion
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai.types.shared.chat_model import ChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai.types.shared_params.reasoning_effort import ReasoningEffort
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.exceptions import ModelProviderError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.openai.serializer import OpenAIMessageSerializer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.schema import SchemaOptimizer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `ChatOpenAI`.
# JP: クラス `ChatOpenAI` を定義する。
@dataclass
class ChatOpenAI(BaseChatModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A wrapper around AsyncOpenAI that implements the BaseLLM protocol.

	This class accepts all AsyncOpenAI parameters while adding model
	and temperature parameters for the LLM interface (if temperature it not `None`).
	"""

	# Model configuration
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: ChatModel | str

	# Model params
	# EN: Assign annotated value to temperature.
	# JP: temperature に型付きの値を代入する。
	temperature: float | None = 0.2
	# EN: Assign annotated value to frequency_penalty.
	# JP: frequency_penalty に型付きの値を代入する。
	frequency_penalty: float | None = 0.3  # this avoids infinite generation of \t for models like 4.1-mini
	# EN: Assign annotated value to reasoning_effort.
	# JP: reasoning_effort に型付きの値を代入する。
	reasoning_effort: ReasoningEffort = 'low'
	# EN: Assign annotated value to seed.
	# JP: seed に型付きの値を代入する。
	seed: int | None = None
	# EN: Assign annotated value to service_tier.
	# JP: service_tier に型付きの値を代入する。
	service_tier: Literal['auto', 'default', 'flex', 'priority', 'scale'] | None = None
	# EN: Assign annotated value to top_p.
	# JP: top_p に型付きの値を代入する。
	top_p: float | None = None
	# EN: Assign annotated value to add_schema_to_system_prompt.
	# JP: add_schema_to_system_prompt に型付きの値を代入する。
	add_schema_to_system_prompt: bool = False  # Add JSON schema to system prompt instead of using response_format

	# Client initialization parameters
	# EN: Assign annotated value to api_key.
	# JP: api_key に型付きの値を代入する。
	api_key: str | None = None
	# EN: Assign annotated value to organization.
	# JP: organization に型付きの値を代入する。
	organization: str | None = None
	# EN: Assign annotated value to project.
	# JP: project に型付きの値を代入する。
	project: str | None = None
	# EN: Assign annotated value to base_url.
	# JP: base_url に型付きの値を代入する。
	base_url: str | httpx.URL | None = None
	# EN: Assign annotated value to websocket_base_url.
	# JP: websocket_base_url に型付きの値を代入する。
	websocket_base_url: str | httpx.URL | None = None
	# EN: Assign annotated value to timeout.
	# JP: timeout に型付きの値を代入する。
	timeout: float | httpx.Timeout | None = None
	# EN: Assign annotated value to max_retries.
	# JP: max_retries に型付きの値を代入する。
	max_retries: int = 5  # Increase default retries for automation reliability
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
	# EN: Assign annotated value to max_completion_tokens.
	# JP: max_completion_tokens に型付きの値を代入する。
	max_completion_tokens: int | None = 4096
	# EN: Assign annotated value to reasoning_models.
	# JP: reasoning_models に型付きの値を代入する。
	reasoning_models: list[ChatModel | str] | None = field(
		default_factory=lambda: [
			'o4-mini',
			'o3',
			'o3-mini',
			'o1',
			'o1-pro',
			'o3-pro',
			'gpt-5',
			'gpt-5-mini',
			'gpt-5-nano',
		]
	)

	# EN: Assign annotated value to _async_client.
	# JP: _async_client に型付きの値を代入する。
	_async_client: AsyncOpenAI = field(init=False, repr=False)

	# EN: Define function `__post_init__`.
	# JP: 関数 `__post_init__` を定義する。
	def __post_init__(self) -> None:
		# EN: Assign value to client_params.
		# JP: client_params に値を代入する。
		client_params = self._get_client_params()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._async_client = AsyncOpenAI(**client_params)

	# Static
	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'openai'

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
			'organization': self.organization,
			'project': self.project,
			'base_url': self.base_url,
			'websocket_base_url': self.websocket_base_url,
			'timeout': self.timeout,
			'max_retries': self.max_retries,
			'default_headers': self.default_headers,
			'default_query': self.default_query,
			'_strict_response_validation': self._strict_response_validation,
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
		Returns an AsyncOpenAI client.

		Returns:
			AsyncOpenAI: An instance of the AsyncOpenAI client.
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
	def _get_usage(self, response: ChatCompletion) -> ChatInvokeUsage | None:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if response.usage is not None:
			# EN: Assign value to completion_tokens.
			# JP: completion_tokens に値を代入する。
			completion_tokens = response.usage.completion_tokens
			# EN: Assign value to completion_token_details.
			# JP: completion_token_details に値を代入する。
			completion_token_details = response.usage.completion_tokens_details
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if completion_token_details is not None:
				# EN: Assign value to reasoning_tokens.
				# JP: reasoning_tokens に値を代入する。
				reasoning_tokens = completion_token_details.reasoning_tokens
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if reasoning_tokens is not None:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					completion_tokens += reasoning_tokens

			# EN: Assign value to usage.
			# JP: usage に値を代入する。
			usage = ChatInvokeUsage(
				prompt_tokens=response.usage.prompt_tokens,
				prompt_cached_tokens=response.usage.prompt_tokens_details.cached_tokens
				if response.usage.prompt_tokens_details is not None
				else None,
				prompt_cache_creation_tokens=None,
				prompt_image_tokens=None,
				# Completion
				completion_tokens=completion_tokens,
				total_tokens=response.usage.total_tokens,
			)
		else:
			# EN: Assign value to usage.
			# JP: usage に値を代入する。
			usage = None

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
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Invoke the model with the given messages.

		Args:
			messages: List of chat messages
			output_format: Optional Pydantic model class for structured output

		Returns:
			Either a string response or an instance of output_format
		"""

		# EN: Assign value to openai_messages.
		# JP: openai_messages に値を代入する。
		openai_messages = OpenAIMessageSerializer.serialize_messages(messages)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign annotated value to model_params.
			# JP: model_params に型付きの値を代入する。
			model_params: dict[str, Any] = {}

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.temperature is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_params['temperature'] = self.temperature

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.frequency_penalty is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_params['frequency_penalty'] = self.frequency_penalty

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.max_completion_tokens is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_params['max_completion_tokens'] = self.max_completion_tokens

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.top_p is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_params['top_p'] = self.top_p

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.seed is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_params['seed'] = self.seed

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.service_tier is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_params['service_tier'] = self.service_tier

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.reasoning_models and any(str(m).lower() in str(self.model).lower() for m in self.reasoning_models):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_params['reasoning_effort'] = self.reasoning_effort
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del model_params['temperature']
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del model_params['frequency_penalty']

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_params['response_format'] = {'type': 'json_object'}
			# Return string response
			# EN: Assign value to response.
			# JP: response に値を代入する。
			response = await self.get_client().chat.completions.create(
				model=self.model,
				messages=openai_messages,
				**model_params,
			)

			# EN: Assign value to usage.
			# JP: usage に値を代入する。
			usage = self._get_usage(response)
			# EN: Assign value to response_text.
			# JP: response_text に値を代入する。
			response_text = response.choices[0].message.content or ''

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format:
				# Add JSON schema to system prompt if requested
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.add_schema_to_system_prompt and openai_messages and openai_messages[0]['role'] == 'system':
					# EN: Assign value to schema.
					# JP: schema に値を代入する。
					schema = SchemaOptimizer.create_optimized_json_schema(output_format)
					# EN: Assign value to schema_text.
					# JP: schema_text に値を代入する。
					schema_text = f'\n<json_schema>\n{schema}\n</json_schema>'
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if isinstance(openai_messages[0]['content'], str):
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						openai_messages[0]['content'] += schema_text
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif isinstance(openai_messages[0]['content'], Iterable):
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						openai_messages[0]['content'] = list(openai_messages[0]['content']) + [
							ChatCompletionContentPartTextParam(text=schema_text, type='text')
						]
				# EN: Assign value to parsed.
				# JP: parsed に値を代入する。
				parsed = output_format.model_validate_json(response_text)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(
					completion=parsed,
					usage=usage,
				)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ChatInvokeCompletion(
				completion=response_text,
				usage=usage,
			)

		except RateLimitError as e:
			# EN: Assign value to error_message.
			# JP: error_message に値を代入する。
			error_message = e.response.json().get('error', {})
			# EN: Assign value to error_message.
			# JP: error_message に値を代入する。
			error_message = (
				error_message.get('message', 'Unknown model error') if isinstance(error_message, dict) else error_message
			)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(
				message=error_message,
				status_code=e.response.status_code,
				model=self.name,
			) from e

		except APIConnectionError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=str(e), model=self.name) from e

		except APIStatusError as e:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to error_message.
				# JP: error_message に値を代入する。
				error_message = e.response.json().get('error', {})
			except Exception:
				# EN: Assign value to error_message.
				# JP: error_message に値を代入する。
				error_message = e.response.text
			# EN: Assign value to error_message.
			# JP: error_message に値を代入する。
			error_message = (
				error_message.get('message', 'Unknown model error') if isinstance(error_message, dict) else error_message
			)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(
				message=error_message,
				status_code=e.response.status_code,
				model=self.name,
			) from e

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

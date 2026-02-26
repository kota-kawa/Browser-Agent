# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Mapping
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, Any, TypeVar, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic import (
	NOT_GIVEN,
	APIConnectionError,
	APIStatusError,
	AsyncAnthropicBedrock,
	RateLimitError,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types import CacheControlEphemeralParam, Message, ToolParam
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types.text_block import TextBlock
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types.tool_choice_tool_param import ToolChoiceToolParam
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.anthropic.serializer import AnthropicMessageSerializer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.aws.chat_bedrock import ChatAWSBedrock
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from boto3.session import Session  # pyright: ignore


# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `ChatAnthropicBedrock`.
# JP: クラス `ChatAnthropicBedrock` を定義する。
@dataclass
class ChatAnthropicBedrock(ChatAWSBedrock):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	AWS Bedrock Anthropic Claude chat model.

	This is a convenience class that provides Claude-specific defaults
	for the AWS Bedrock service. It inherits all functionality from
	ChatAWSBedrock but sets Anthropic Claude as the default model.
	"""

	# Anthropic Claude specific defaults
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
	# EN: Assign annotated value to max_tokens.
	# JP: max_tokens に型付きの値を代入する。
	max_tokens: int = 8192
	# EN: Assign annotated value to temperature.
	# JP: temperature に型付きの値を代入する。
	temperature: float | None = None
	# EN: Assign annotated value to top_p.
	# JP: top_p に型付きの値を代入する。
	top_p: float | None = None
	# EN: Assign annotated value to top_k.
	# JP: top_k に型付きの値を代入する。
	top_k: int | None = None
	# EN: Assign annotated value to stop_sequences.
	# JP: stop_sequences に型付きの値を代入する。
	stop_sequences: list[str] | None = None
	# EN: Assign annotated value to seed.
	# JP: seed に型付きの値を代入する。
	seed: int | None = None

	# AWS credentials and configuration
	# EN: Assign annotated value to aws_access_key.
	# JP: aws_access_key に型付きの値を代入する。
	aws_access_key: str | None = None
	# EN: Assign annotated value to aws_secret_key.
	# JP: aws_secret_key に型付きの値を代入する。
	aws_secret_key: str | None = None
	# EN: Assign annotated value to aws_session_token.
	# JP: aws_session_token に型付きの値を代入する。
	aws_session_token: str | None = None
	# EN: Assign annotated value to aws_region.
	# JP: aws_region に型付きの値を代入する。
	aws_region: str | None = None
	# EN: Assign annotated value to session.
	# JP: session に型付きの値を代入する。
	session: 'Session | None' = None

	# Client initialization parameters
	# EN: Assign annotated value to max_retries.
	# JP: max_retries に型付きの値を代入する。
	max_retries: int = 10
	# EN: Assign annotated value to default_headers.
	# JP: default_headers に型付きの値を代入する。
	default_headers: Mapping[str, str] | None = None
	# EN: Assign annotated value to default_query.
	# JP: default_query に型付きの値を代入する。
	default_query: Mapping[str, object] | None = None

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'anthropic_bedrock'

	# EN: Define function `_get_client_params`.
	# JP: 関数 `_get_client_params` を定義する。
	def _get_client_params(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Prepare client parameters dictionary for Bedrock."""
		# EN: Assign annotated value to client_params.
		# JP: client_params に型付きの値を代入する。
		client_params: dict[str, Any] = {}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.session:
			# EN: Assign value to credentials.
			# JP: credentials に値を代入する。
			credentials = self.session.get_credentials()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			client_params.update(
				{
					'aws_access_key': credentials.access_key,
					'aws_secret_key': credentials.secret_key,
					'aws_session_token': credentials.token,
					'aws_region': self.session.region_name,
				}
			)
		else:
			# Use individual credentials
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.aws_access_key:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				client_params['aws_access_key'] = self.aws_access_key
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.aws_secret_key:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				client_params['aws_secret_key'] = self.aws_secret_key
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.aws_region:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				client_params['aws_region'] = self.aws_region
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.aws_session_token:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				client_params['aws_session_token'] = self.aws_session_token

		# Add optional parameters
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.max_retries:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['max_retries'] = self.max_retries
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.default_headers:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['default_headers'] = self.default_headers
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.default_query:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['default_query'] = self.default_query

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return client_params

	# EN: Define function `_get_client_params_for_invoke`.
	# JP: 関数 `_get_client_params_for_invoke` を定義する。
	def _get_client_params_for_invoke(self) -> dict[str, Any]:
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
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.max_tokens is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['max_tokens'] = self.max_tokens
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.top_p is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['top_p'] = self.top_p
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.top_k is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['top_k'] = self.top_k
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.seed is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['seed'] = self.seed
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.stop_sequences is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			client_params['stop_sequences'] = self.stop_sequences

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return client_params

	# EN: Define function `get_client`.
	# JP: 関数 `get_client` を定義する。
	def get_client(self) -> AsyncAnthropicBedrock:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Returns an AsyncAnthropicBedrock client.

		Returns:
			AsyncAnthropicBedrock: An instance of the AsyncAnthropicBedrock client.
		"""
		# EN: Assign value to client_params.
		# JP: client_params に値を代入する。
		client_params = self._get_client_params()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return AsyncAnthropicBedrock(**client_params)

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
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract usage information from the response."""
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

				# EN: Assign value to usage.
				# JP: usage に値を代入する。
				usage = self._get_usage(response)

				# Extract text from the first content block
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
				schema = output_format.model_json_schema()

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
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return ChatInvokeCompletion(completion=output_format.model_validate(content_block.input), usage=usage)
						except Exception as e:
							# If validation fails, try to parse it as JSON first
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if isinstance(content_block.input, str):
								# EN: Assign value to data.
								# JP: data に値を代入する。
								data = json.loads(content_block.input)
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return ChatInvokeCompletion(
									completion=output_format.model_validate(data),
									usage=usage,
								)
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise e

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

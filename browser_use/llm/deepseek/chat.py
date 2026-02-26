# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
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
from openai import (
	APIConnectionError,
	APIError,
	APIStatusError,
	APITimeoutError,
	AsyncOpenAI,
	RateLimitError,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.deepseek.serializer import DeepSeekMessageSerializer
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
from browser_use.llm.views import ChatInvokeCompletion

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `ChatDeepSeek`.
# JP: クラス `ChatDeepSeek` を定義する。
@dataclass
class ChatDeepSeek(BaseChatModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""DeepSeek /chat/completions wrapper (OpenAI-compatible)."""

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str = 'deepseek-chat'

	# Generation parameters
	# EN: Assign annotated value to max_tokens.
	# JP: max_tokens に型付きの値を代入する。
	max_tokens: int | None = None
	# EN: Assign annotated value to temperature.
	# JP: temperature に型付きの値を代入する。
	temperature: float | None = None
	# EN: Assign annotated value to top_p.
	# JP: top_p に型付きの値を代入する。
	top_p: float | None = None
	# EN: Assign annotated value to seed.
	# JP: seed に型付きの値を代入する。
	seed: int | None = None

	# Connection parameters
	# EN: Assign annotated value to api_key.
	# JP: api_key に型付きの値を代入する。
	api_key: str | None = None
	# EN: Assign annotated value to base_url.
	# JP: base_url に型付きの値を代入する。
	base_url: str | httpx.URL | None = 'https://api.deepseek.com/v1'
	# EN: Assign annotated value to timeout.
	# JP: timeout に型付きの値を代入する。
	timeout: float | httpx.Timeout | None = None
	# EN: Assign annotated value to client_params.
	# JP: client_params に型付きの値を代入する。
	client_params: dict[str, Any] | None = None

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'deepseek'

	# EN: Define function `_client`.
	# JP: 関数 `_client` を定義する。
	def _client(self) -> AsyncOpenAI:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return AsyncOpenAI(
			api_key=self.api_key,
			base_url=self.base_url,
			timeout=self.timeout,
			**(self.client_params or {}),
		)

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.model

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	async def ainvoke(
		self,
		messages: list[BaseMessage],
		output_format: None = None,
		tools: list[dict[str, Any]] | None = None,
		stop: list[str] | None = None,
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	) -> ChatInvokeCompletion[str]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	async def ainvoke(
		self,
		messages: list[BaseMessage],
		output_format: type[T],
		tools: list[dict[str, Any]] | None = None,
		stop: list[str] | None = None,
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	) -> ChatInvokeCompletion[T]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	async def ainvoke(
		self,
		messages: list[BaseMessage],
		output_format: type[T] | None = None,
		tools: list[dict[str, Any]] | None = None,
		stop: list[str] | None = None,
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		DeepSeek ainvoke supports:
		1. Regular text/multi-turn conversation
		2. Function Calling
		3. JSON Output (response_format)
		4. Conversation prefix continuation (beta, prefix, stop)
		"""
		# EN: Assign value to client.
		# JP: client に値を代入する。
		client = self._client()
		# EN: Assign value to ds_messages.
		# JP: ds_messages に値を代入する。
		ds_messages = DeepSeekMessageSerializer.serialize_messages(messages)
		# EN: Assign annotated value to common.
		# JP: common に型付きの値を代入する。
		common: dict[str, Any] = {}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.temperature is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			common['temperature'] = self.temperature
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.max_tokens is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			common['max_tokens'] = self.max_tokens
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.top_p is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			common['top_p'] = self.top_p
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.seed is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			common['seed'] = self.seed

		# Beta conversation prefix continuation (see official documentation)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.base_url and str(self.base_url).endswith('/beta'):
			# The last assistant message must have prefix
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if ds_messages and isinstance(ds_messages[-1], dict) and ds_messages[-1].get('role') == 'assistant':
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				ds_messages[-1]['prefix'] = True
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if stop:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				common['stop'] = stop

		# ① Regular multi-turn conversation/text output
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if output_format is None and not tools:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to resp.
				# JP: resp に値を代入する。
				resp = await client.chat.completions.create(  # type: ignore
					model=self.model,
					messages=ds_messages,  # type: ignore
					**common,
				)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(
					completion=resp.choices[0].message.content or '',
					usage=None,
				)
			except RateLimitError as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelRateLimitError(str(e), model=self.name) from e
			except (APIError, APIConnectionError, APITimeoutError, APIStatusError) as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(str(e), model=self.name) from e
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(str(e), model=self.name) from e

		# ② Function Calling path (with tools or output_format)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tools or (output_format is not None and hasattr(output_format, 'model_json_schema')):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to call_tools.
				# JP: call_tools に値を代入する。
				call_tools = tools
				# EN: Assign value to tool_choice.
				# JP: tool_choice に値を代入する。
				tool_choice = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if output_format is not None and hasattr(output_format, 'model_json_schema'):
					# EN: Assign value to tool_name.
					# JP: tool_name に値を代入する。
					tool_name = output_format.__name__
					# EN: Assign value to schema.
					# JP: schema に値を代入する。
					schema = SchemaOptimizer.create_optimized_json_schema(output_format)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					schema.pop('title', None)
					# EN: Assign value to call_tools.
					# JP: call_tools に値を代入する。
					call_tools = [
						{
							'type': 'function',
							'function': {
								'name': tool_name,
								'description': f'Return a JSON object of type {tool_name}',
								'parameters': schema,
							},
						}
					]
					# EN: Assign value to tool_choice.
					# JP: tool_choice に値を代入する。
					tool_choice = {'type': 'function', 'function': {'name': tool_name}}
				# EN: Assign value to resp.
				# JP: resp に値を代入する。
				resp = await client.chat.completions.create(  # type: ignore
					model=self.model,
					messages=ds_messages,  # type: ignore
					tools=call_tools,  # type: ignore
					tool_choice=tool_choice,  # type: ignore
					**common,
				)
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = resp.choices[0].message
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not msg.tool_calls:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError('Expected tool_calls in response but got none')
				# EN: Assign value to raw_args.
				# JP: raw_args に値を代入する。
				raw_args = msg.tool_calls[0].function.arguments
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(raw_args, str):
					# EN: Assign value to parsed.
					# JP: parsed に値を代入する。
					parsed = json.loads(raw_args)
				else:
					# EN: Assign value to parsed.
					# JP: parsed に値を代入する。
					parsed = raw_args
				# --------- Fix: only use model_validate when output_format is not None ----------
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if output_format is not None:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ChatInvokeCompletion(
						completion=output_format.model_validate(parsed),
						usage=None,
					)
				else:
					# If no output_format, return dict directly
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ChatInvokeCompletion(
						completion=parsed,
						usage=None,
					)
			except RateLimitError as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelRateLimitError(str(e), model=self.name) from e
			except (APIError, APIConnectionError, APITimeoutError, APIStatusError) as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(str(e), model=self.name) from e
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(str(e), model=self.name) from e

		# ③ JSON Output path (official response_format)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if output_format is not None and hasattr(output_format, 'model_json_schema'):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to resp.
				# JP: resp に値を代入する。
				resp = await client.chat.completions.create(  # type: ignore
					model=self.model,
					messages=ds_messages,  # type: ignore
					response_format={'type': 'json_object'},
					**common,
				)
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = resp.choices[0].message.content
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not content:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ModelProviderError('Empty JSON content in DeepSeek response', model=self.name)
				# EN: Assign value to parsed.
				# JP: parsed に値を代入する。
				parsed = output_format.model_validate_json(content)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(
					completion=parsed,
					usage=None,
				)
			except RateLimitError as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelRateLimitError(str(e), model=self.name) from e
			except (APIError, APIConnectionError, APITimeoutError, APIStatusError) as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(str(e), model=self.name) from e
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(str(e), model=self.name) from e

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ModelProviderError('No valid ainvoke execution path for DeepSeek LLM', model=self.name)

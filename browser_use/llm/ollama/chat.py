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
from ollama import AsyncClient as OllamaAsyncClient
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ollama import Options
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
from browser_use.llm.ollama.serializer import OllamaMessageSerializer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `ChatOllama`.
# JP: クラス `ChatOllama` を定義する。
@dataclass
class ChatOllama(BaseChatModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A wrapper around Ollama's chat model.
	"""

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str

	# # Model params
	# TODO (matic): Why is this commented out?
	# temperature: float | None = None

	# Client initialization parameters
	# EN: Assign annotated value to host.
	# JP: host に型付きの値を代入する。
	host: str | None = None
	# EN: Assign annotated value to timeout.
	# JP: timeout に型付きの値を代入する。
	timeout: float | httpx.Timeout | None = None
	# EN: Assign annotated value to client_params.
	# JP: client_params に型付きの値を代入する。
	client_params: dict[str, Any] | None = None
	# EN: Assign annotated value to ollama_options.
	# JP: ollama_options に型付きの値を代入する。
	ollama_options: Mapping[str, Any] | Options | None = None

	# Static
	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'ollama'

	# EN: Define function `_get_client_params`.
	# JP: 関数 `_get_client_params` を定義する。
	def _get_client_params(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Prepare client parameters dictionary."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'host': self.host,
			'timeout': self.timeout,
			'client_params': self.client_params,
		}

	# EN: Define function `get_client`.
	# JP: 関数 `get_client` を定義する。
	def get_client(self) -> OllamaAsyncClient:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Returns an OllamaAsyncClient client.
		"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return OllamaAsyncClient(host=self.host, timeout=self.timeout, **self.client_params or {})

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
		# EN: Assign value to ollama_messages.
		# JP: ollama_messages に値を代入する。
		ollama_messages = OllamaMessageSerializer.serialize_messages(messages)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format is None:
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self.get_client().chat(
					model=self.model,
					messages=ollama_messages,
					options=self.ollama_options,
				)

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(completion=response.message.content or '', usage=None)
			else:
				# EN: Assign value to schema.
				# JP: schema に値を代入する。
				schema = output_format.model_json_schema()

				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self.get_client().chat(
					model=self.model,
					messages=ollama_messages,
					format=schema,
					options=self.ollama_options,
				)

				# EN: Assign value to completion.
				# JP: completion に値を代入する。
				completion = response.message.content or ''
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if output_format is not None:
					# EN: Assign value to completion.
					# JP: completion に値を代入する。
					completion = output_format.model_validate_json(completion)

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(completion=completion, usage=None)

		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=str(e), model=self.name) from e

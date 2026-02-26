"""
We have switched all of our code from langchain to openai.types.chat.chat_completion_message_param.

For easier transition we have
"""

from typing import Any, Protocol, TypeVar, overload, runtime_checkable

from pydantic import BaseModel

from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion

T = TypeVar('T', bound=BaseModel)


# EN: Define class `BaseChatModel`.
# JP: クラス `BaseChatModel` を定義する。
@runtime_checkable
class BaseChatModel(Protocol):
	_verified_api_keys: bool = False

	model: str

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str: ...

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str: ...

	# EN: Define function `model_name`.
	# JP: 関数 `model_name` を定義する。
	@property
	def model_name(self) -> str:
		# for legacy support
		return self.model

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	async def ainvoke(self, messages: list[BaseMessage], output_format: None = None) -> ChatInvokeCompletion[str]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	async def ainvoke(self, messages: list[BaseMessage], output_format: type[T]) -> ChatInvokeCompletion[T]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]: ...

	# EN: Define async function `aclose`.
	# JP: 非同期関数 `aclose` を定義する。
	async def aclose(self) -> None:
		"""Close the underlying HTTP client."""
		...

	# EN: Define function `__get_pydantic_core_schema__`.
	# JP: 関数 `__get_pydantic_core_schema__` を定義する。
	@classmethod
	def __get_pydantic_core_schema__(
		cls,
		source_type: type,
		handler: Any,
	) -> Any:
		"""
		Allow this Protocol to be used in Pydantic models -> very useful to typesafe the agent settings for example.
		Returns a schema that allows any object (since this is a Protocol).
		"""
		from pydantic_core import core_schema

		# Return a schema that accepts any object for Protocol types
		return core_schema.any_schema()

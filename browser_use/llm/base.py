# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
We have switched all of our code from langchain to openai.types.chat.chat_completion_message_param.

For easier transition we have
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, Protocol, TypeVar, overload, runtime_checkable

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `BaseChatModel`.
# JP: クラス `BaseChatModel` を定義する。
@runtime_checkable
class BaseChatModel(Protocol):
	# EN: Assign annotated value to _verified_api_keys.
	# JP: _verified_api_keys に型付きの値を代入する。
	_verified_api_keys: bool = False

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def provider(self) -> str: ...

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def name(self) -> str: ...

	# EN: Define function `model_name`.
	# JP: 関数 `model_name` を定義する。
	@property
	def model_name(self) -> str:
		# for legacy support
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
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]: ...

	# EN: Define async function `aclose`.
	# JP: 非同期関数 `aclose` を定義する。
	async def aclose(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close the underlying HTTP client."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		...

	# EN: Define function `__get_pydantic_core_schema__`.
	# JP: 関数 `__get_pydantic_core_schema__` を定義する。
	@classmethod
	def __get_pydantic_core_schema__(
		cls,
		source_type: type,
		handler: Any,
	) -> Any:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Allow this Protocol to be used in Pydantic models -> very useful to typesafe the agent settings for example.
		Returns a schema that allows any object (since this is a Protocol).
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from pydantic_core import core_schema

		# Return a schema that accepts any object for Protocol types
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return core_schema.any_schema()

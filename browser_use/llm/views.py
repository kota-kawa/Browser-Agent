# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Generic, TypeVar, Union

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=Union[BaseModel, str])


# EN: Define class `ChatInvokeUsage`.
# JP: クラス `ChatInvokeUsage` を定義する。
class ChatInvokeUsage(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Usage information for a chat model invocation.
	"""

	# EN: Assign annotated value to prompt_tokens.
	# JP: prompt_tokens に型付きの値を代入する。
	prompt_tokens: int
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The number of tokens in the prompt (this includes the cached tokens as well. When calculating the cost, subtract the cached tokens from the prompt tokens)"""

	# EN: Assign annotated value to prompt_cached_tokens.
	# JP: prompt_cached_tokens に型付きの値を代入する。
	prompt_cached_tokens: int | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The number of cached tokens."""

	# EN: Assign annotated value to prompt_cache_creation_tokens.
	# JP: prompt_cache_creation_tokens に型付きの値を代入する。
	prompt_cache_creation_tokens: int | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Anthropic only: The number of tokens used to create the cache."""

	# EN: Assign annotated value to prompt_image_tokens.
	# JP: prompt_image_tokens に型付きの値を代入する。
	prompt_image_tokens: int | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Google only: The number of tokens in the image (prompt tokens is the text tokens + image tokens in that case)"""

	# EN: Assign annotated value to completion_tokens.
	# JP: completion_tokens に型付きの値を代入する。
	completion_tokens: int
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The number of tokens in the completion."""

	# EN: Assign annotated value to total_tokens.
	# JP: total_tokens に型付きの値を代入する。
	total_tokens: int
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The total number of tokens in the response."""


# EN: Define class `ChatInvokeCompletion`.
# JP: クラス `ChatInvokeCompletion` を定義する。
class ChatInvokeCompletion(BaseModel, Generic[T]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Response from a chat model invocation.
	"""

	# EN: Assign annotated value to completion.
	# JP: completion に型付きの値を代入する。
	completion: T
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The completion of the response."""

	# Thinking stuff
	# EN: Assign annotated value to thinking.
	# JP: thinking に型付きの値を代入する。
	thinking: str | None = None
	# EN: Assign annotated value to redacted_thinking.
	# JP: redacted_thinking に型付きの値を代入する。
	redacted_thinking: str | None = None

	# EN: Assign annotated value to usage.
	# JP: usage に型付きの値を代入する。
	usage: ChatInvokeUsage | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The usage of the response."""

	# EN: Define function `result`.
	# JP: 関数 `result` を定義する。
	@property
	def result(self) -> T:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""DEPRECATED: an alias for completion to ensure backward compatibility."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.completion

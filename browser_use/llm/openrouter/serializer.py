# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai.types.chat import ChatCompletionMessageParam

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.openai.serializer import OpenAIMessageSerializer


# EN: Define class `OpenRouterMessageSerializer`.
# JP: クラス `OpenRouterMessageSerializer` を定義する。
class OpenRouterMessageSerializer:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Serializer for converting between custom message types and OpenRouter message formats.

	OpenRouter uses the OpenAI-compatible API, so we can reuse the OpenAI serializer.
	"""

	# EN: Define function `serialize_messages`.
	# JP: 関数 `serialize_messages` を定義する。
	@staticmethod
	def serialize_messages(messages: list[BaseMessage]) -> list[ChatCompletionMessageParam]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Serialize a list of browser_use messages to OpenRouter-compatible messages.

		Args:
		    messages: List of browser_use messages

		Returns:
		    List of OpenRouter-compatible messages (identical to OpenAI format)
		"""
		# OpenRouter uses the same message format as OpenAI
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return OpenAIMessageSerializer.serialize_messages(messages)

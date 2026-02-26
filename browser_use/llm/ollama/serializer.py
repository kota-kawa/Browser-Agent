# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import base64
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ollama._types import Image, Message

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	AssistantMessage,
	BaseMessage,
	SystemMessage,
	ToolCall,
	UserMessage,
)


# EN: Define class `OllamaMessageSerializer`.
# JP: クラス `OllamaMessageSerializer` を定義する。
class OllamaMessageSerializer:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serializer for converting between custom message types and Ollama message types."""

	# EN: Define function `_extract_text_content`.
	# JP: 関数 `_extract_text_content` を定義する。
	@staticmethod
	def _extract_text_content(content: Any) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract text content from message content, ignoring images."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if content is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return content

		# EN: Assign annotated value to text_parts.
		# JP: text_parts に型付きの値を代入する。
		text_parts: list[str] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(part, 'type'):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if part.type == 'text':
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					text_parts.append(part.text)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif part.type == 'refusal':
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					text_parts.append(f'[Refusal] {part.refusal}')
			# Skip image parts as they're handled separately

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(text_parts)

	# EN: Define function `_extract_images`.
	# JP: 関数 `_extract_images` を定義する。
	@staticmethod
	def _extract_images(content: Any) -> list[Image]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract images from message content."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if content is None or isinstance(content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []

		# EN: Assign annotated value to images.
		# JP: images に型付きの値を代入する。
		images: list[Image] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(part, 'type') and part.type == 'image_url':
				# EN: Assign value to url.
				# JP: url に値を代入する。
				url = part.image_url.url
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if url.startswith('data:'):
					# Handle base64 encoded images
					# Format: data:image/png;base64,<data>
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					_, data = url.split(',', 1)
					# Decode base64 to bytes
					# EN: Assign value to image_bytes.
					# JP: image_bytes に値を代入する。
					image_bytes = base64.b64decode(data)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					images.append(Image(value=image_bytes))
				else:
					# Handle URL images (Ollama will download them)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					images.append(Image(value=url))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return images

	# EN: Define function `_serialize_tool_calls`.
	# JP: 関数 `_serialize_tool_calls` を定義する。
	@staticmethod
	def _serialize_tool_calls(tool_calls: list[ToolCall]) -> list[Message.ToolCall]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert browser-use ToolCalls to Ollama ToolCalls."""
		# EN: Assign annotated value to ollama_tool_calls.
		# JP: ollama_tool_calls に型付きの値を代入する。
		ollama_tool_calls: list[Message.ToolCall] = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for tool_call in tool_calls:
			# Parse arguments from JSON string to dict for Ollama
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to arguments_dict.
				# JP: arguments_dict に値を代入する。
				arguments_dict = json.loads(tool_call.function.arguments)
			except json.JSONDecodeError:
				# If parsing fails, wrap in a dict
				# EN: Assign value to arguments_dict.
				# JP: arguments_dict に値を代入する。
				arguments_dict = {'arguments': tool_call.function.arguments}

			# EN: Assign value to ollama_tool_call.
			# JP: ollama_tool_call に値を代入する。
			ollama_tool_call = Message.ToolCall(
				function=Message.ToolCall.Function(name=tool_call.function.name, arguments=arguments_dict)
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			ollama_tool_calls.append(ollama_tool_call)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ollama_tool_calls

	# region - Serialize overloads
	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: UserMessage) -> Message: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: SystemMessage) -> Message: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: AssistantMessage) -> Message: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@staticmethod
	def serialize(message: BaseMessage) -> Message:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize a custom message to an Ollama Message."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(message, UserMessage):
			# EN: Assign value to text_content.
			# JP: text_content に値を代入する。
			text_content = OllamaMessageSerializer._extract_text_content(message.content)
			# EN: Assign value to images.
			# JP: images に値を代入する。
			images = OllamaMessageSerializer._extract_images(message.content)

			# EN: Assign value to ollama_message.
			# JP: ollama_message に値を代入する。
			ollama_message = Message(
				role='user',
				content=text_content if text_content else None,
			)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if images:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				ollama_message.images = images

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ollama_message

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message, SystemMessage):
			# EN: Assign value to text_content.
			# JP: text_content に値を代入する。
			text_content = OllamaMessageSerializer._extract_text_content(message.content)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return Message(
				role='system',
				content=text_content if text_content else None,
			)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message, AssistantMessage):
			# Handle content
			# EN: Assign value to text_content.
			# JP: text_content に値を代入する。
			text_content = None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.content is not None:
				# EN: Assign value to text_content.
				# JP: text_content に値を代入する。
				text_content = OllamaMessageSerializer._extract_text_content(message.content)

			# EN: Assign value to ollama_message.
			# JP: ollama_message に値を代入する。
			ollama_message = Message(
				role='assistant',
				content=text_content if text_content else None,
			)

			# Handle tool calls
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.tool_calls:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				ollama_message.tool_calls = OllamaMessageSerializer._serialize_tool_calls(message.tool_calls)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ollama_message

		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Unknown message type: {type(message)}')

	# EN: Define function `serialize_messages`.
	# JP: 関数 `serialize_messages` を定義する。
	@staticmethod
	def serialize_messages(messages: list[BaseMessage]) -> list[Message]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize a list of browser_use messages to Ollama Messages."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [OllamaMessageSerializer.serialize(m) for m in messages]

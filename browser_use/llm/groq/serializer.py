# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from groq.types.chat import (
	ChatCompletionAssistantMessageParam,
	ChatCompletionContentPartImageParam,
	ChatCompletionContentPartTextParam,
	ChatCompletionMessageParam,
	ChatCompletionMessageToolCallParam,
	ChatCompletionSystemMessageParam,
	ChatCompletionUserMessageParam,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from groq.types.chat.chat_completion_content_part_image_param import ImageURL
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from groq.types.chat.chat_completion_message_tool_call_param import Function

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	AssistantMessage,
	BaseMessage,
	ContentPartImageParam,
	ContentPartRefusalParam,
	ContentPartTextParam,
	SystemMessage,
	ToolCall,
	UserMessage,
)


# EN: Define class `GroqMessageSerializer`.
# JP: クラス `GroqMessageSerializer` を定義する。
class GroqMessageSerializer:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serializer for converting between custom message types and OpenAI message param types."""

	# EN: Define function `_serialize_content_part_text`.
	# JP: 関数 `_serialize_content_part_text` を定義する。
	@staticmethod
	def _serialize_content_part_text(part: ContentPartTextParam) -> ChatCompletionContentPartTextParam:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatCompletionContentPartTextParam(text=part.text, type='text')

	# EN: Define function `_serialize_content_part_image`.
	# JP: 関数 `_serialize_content_part_image` を定義する。
	@staticmethod
	def _serialize_content_part_image(part: ContentPartImageParam) -> ChatCompletionContentPartImageParam:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatCompletionContentPartImageParam(
			image_url=ImageURL(url=part.image_url.url, detail=part.image_url.detail),
			type='image_url',
		)

	# EN: Define function `_serialize_user_content`.
	# JP: 関数 `_serialize_user_content` を定義する。
	@staticmethod
	def _serialize_user_content(
		content: str | list[ContentPartTextParam | ContentPartImageParam],
	) -> str | list[ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize content for user messages (text and images allowed)."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return content

		# EN: Assign annotated value to serialized_parts.
		# JP: serialized_parts に型付きの値を代入する。
		serialized_parts: list[ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized_parts.append(GroqMessageSerializer._serialize_content_part_text(part))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif part.type == 'image_url':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized_parts.append(GroqMessageSerializer._serialize_content_part_image(part))
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return serialized_parts

	# EN: Define function `_serialize_system_content`.
	# JP: 関数 `_serialize_system_content` を定義する。
	@staticmethod
	def _serialize_system_content(
		content: str | list[ContentPartTextParam],
	) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize content for system messages (text only)."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return content

		# EN: Assign annotated value to serialized_parts.
		# JP: serialized_parts に型付きの値を代入する。
		serialized_parts: list[str] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized_parts.append(GroqMessageSerializer._serialize_content_part_text(part)['text'])

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(serialized_parts)

	# EN: Define function `_serialize_assistant_content`.
	# JP: 関数 `_serialize_assistant_content` を定義する。
	@staticmethod
	def _serialize_assistant_content(
		content: str | list[ContentPartTextParam | ContentPartRefusalParam] | None,
	) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize content for assistant messages (text and refusal allowed)."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if content is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return content

		# EN: Assign annotated value to serialized_parts.
		# JP: serialized_parts に型付きの値を代入する。
		serialized_parts: list[str] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized_parts.append(GroqMessageSerializer._serialize_content_part_text(part)['text'])

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(serialized_parts)

	# EN: Define function `_serialize_tool_call`.
	# JP: 関数 `_serialize_tool_call` を定義する。
	@staticmethod
	def _serialize_tool_call(tool_call: ToolCall) -> ChatCompletionMessageToolCallParam:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatCompletionMessageToolCallParam(
			id=tool_call.id,
			function=Function(name=tool_call.function.name, arguments=tool_call.function.arguments),
			type='function',
		)

	# endregion

	# region - Serialize overloads
	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: UserMessage) -> ChatCompletionUserMessageParam: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: SystemMessage) -> ChatCompletionSystemMessageParam: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: AssistantMessage) -> ChatCompletionAssistantMessageParam: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@staticmethod
	def serialize(message: BaseMessage) -> ChatCompletionMessageParam:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize a custom message to an OpenAI message param."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(message, UserMessage):
			# EN: Assign annotated value to user_result.
			# JP: user_result に型付きの値を代入する。
			user_result: ChatCompletionUserMessageParam = {
				'role': 'user',
				'content': GroqMessageSerializer._serialize_user_content(message.content),
			}
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.name is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				user_result['name'] = message.name
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return user_result

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message, SystemMessage):
			# EN: Assign annotated value to system_result.
			# JP: system_result に型付きの値を代入する。
			system_result: ChatCompletionSystemMessageParam = {
				'role': 'system',
				'content': GroqMessageSerializer._serialize_system_content(message.content),
			}
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.name is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				system_result['name'] = message.name
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return system_result

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message, AssistantMessage):
			# Handle content serialization
			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.content is not None:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = GroqMessageSerializer._serialize_assistant_content(message.content)

			# EN: Assign annotated value to assistant_result.
			# JP: assistant_result に型付きの値を代入する。
			assistant_result: ChatCompletionAssistantMessageParam = {'role': 'assistant'}

			# Only add content if it's not None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if content is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				assistant_result['content'] = content

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.name is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				assistant_result['name'] = message.name

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.tool_calls:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				assistant_result['tool_calls'] = [GroqMessageSerializer._serialize_tool_call(tc) for tc in message.tool_calls]

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return assistant_result

		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Unknown message type: {type(message)}')

	# EN: Define function `serialize_messages`.
	# JP: 関数 `serialize_messages` を定義する。
	@staticmethod
	def serialize_messages(messages: list[BaseMessage]) -> list[ChatCompletionMessageParam]:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [GroqMessageSerializer.serialize(m) for m in messages]

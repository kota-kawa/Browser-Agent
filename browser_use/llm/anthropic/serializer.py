# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types import (
	Base64ImageSourceParam,
	CacheControlEphemeralParam,
	ImageBlockParam,
	MessageParam,
	TextBlockParam,
	ToolUseBlockParam,
	URLImageSourceParam,
)

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	AssistantMessage,
	BaseMessage,
	ContentPartImageParam,
	ContentPartTextParam,
	SupportedImageMediaType,
	SystemMessage,
	UserMessage,
)

# EN: Assign value to NonSystemMessage.
# JP: NonSystemMessage に値を代入する。
NonSystemMessage = UserMessage | AssistantMessage


# EN: Define class `AnthropicMessageSerializer`.
# JP: クラス `AnthropicMessageSerializer` を定義する。
class AnthropicMessageSerializer:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serializer for converting between custom message types and Anthropic message param types."""

	# EN: Define function `_is_base64_image`.
	# JP: 関数 `_is_base64_image` を定義する。
	@staticmethod
	def _is_base64_image(url: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the URL is a base64 encoded image."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return url.startswith('data:image/')

	# EN: Define function `_parse_base64_url`.
	# JP: 関数 `_parse_base64_url` を定義する。
	@staticmethod
	def _parse_base64_url(url: str) -> tuple[SupportedImageMediaType, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Parse a base64 data URL to extract media type and data."""
		# Format: data:image/jpeg;base64,<data>
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not url.startswith('data:'):
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Invalid base64 URL: {url}')

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		header, data = url.split(',', 1)
		# EN: Assign value to media_type.
		# JP: media_type に値を代入する。
		media_type = header.split(';')[0].replace('data:', '')

		# Ensure it's a supported media type
		# EN: Assign value to supported_types.
		# JP: supported_types に値を代入する。
		supported_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if media_type not in supported_types:
			# Default to png if not recognized
			# EN: Assign value to media_type.
			# JP: media_type に値を代入する。
			media_type = 'image/png'

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return media_type, data  # type: ignore

	# EN: Define function `_serialize_cache_control`.
	# JP: 関数 `_serialize_cache_control` を定義する。
	@staticmethod
	def _serialize_cache_control(use_cache: bool) -> CacheControlEphemeralParam | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize cache control."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if use_cache:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return CacheControlEphemeralParam(type='ephemeral')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `_serialize_content_part_text`.
	# JP: 関数 `_serialize_content_part_text` を定義する。
	@staticmethod
	def _serialize_content_part_text(part: ContentPartTextParam, use_cache: bool) -> TextBlockParam:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert a text content part to Anthropic's TextBlockParam."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return TextBlockParam(
			text=part.text, type='text', cache_control=AnthropicMessageSerializer._serialize_cache_control(use_cache)
		)

	# EN: Define function `_serialize_content_part_image`.
	# JP: 関数 `_serialize_content_part_image` を定義する。
	@staticmethod
	def _serialize_content_part_image(part: ContentPartImageParam) -> ImageBlockParam:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert an image content part to Anthropic's ImageBlockParam."""
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = part.image_url.url

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if AnthropicMessageSerializer._is_base64_image(url):
			# Handle base64 encoded images
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			media_type, data = AnthropicMessageSerializer._parse_base64_url(url)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ImageBlockParam(
				source=Base64ImageSourceParam(
					data=data,
					media_type=media_type,
					type='base64',
				),
				type='image',
			)
		else:
			# Handle URL images
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ImageBlockParam(source=URLImageSourceParam(url=url, type='url'), type='image')

	# EN: Define function `_serialize_content_to_str`.
	# JP: 関数 `_serialize_content_to_str` を定義する。
	@staticmethod
	def _serialize_content_to_str(
		content: str | list[ContentPartTextParam], use_cache: bool = False
	) -> list[TextBlockParam] | str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize content to a string."""
		# EN: Assign value to cache_control.
		# JP: cache_control に値を代入する。
		cache_control = AnthropicMessageSerializer._serialize_cache_control(use_cache)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cache_control:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [TextBlockParam(text=content, type='text', cache_control=cache_control)]
			else:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return content

		# EN: Assign annotated value to serialized_blocks.
		# JP: serialized_blocks に型付きの値を代入する。
		serialized_blocks: list[TextBlockParam] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized_blocks.append(AnthropicMessageSerializer._serialize_content_part_text(part, use_cache))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return serialized_blocks

	# EN: Define function `_serialize_content`.
	# JP: 関数 `_serialize_content` を定義する。
	@staticmethod
	def _serialize_content(
		content: str | list[ContentPartTextParam | ContentPartImageParam],
		use_cache: bool = False,
	) -> str | list[TextBlockParam | ImageBlockParam]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize content to Anthropic format."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if use_cache:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [TextBlockParam(text=content, type='text', cache_control=CacheControlEphemeralParam(type='ephemeral'))]
			else:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return content

		# EN: Assign annotated value to serialized_blocks.
		# JP: serialized_blocks に型付きの値を代入する。
		serialized_blocks: list[TextBlockParam | ImageBlockParam] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized_blocks.append(AnthropicMessageSerializer._serialize_content_part_text(part, use_cache))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif part.type == 'image_url':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized_blocks.append(AnthropicMessageSerializer._serialize_content_part_image(part))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return serialized_blocks

	# EN: Define function `_serialize_tool_calls_to_content`.
	# JP: 関数 `_serialize_tool_calls_to_content` を定義する。
	@staticmethod
	def _serialize_tool_calls_to_content(tool_calls, use_cache: bool = False) -> list[ToolUseBlockParam]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert tool calls to Anthropic's ToolUseBlockParam format."""
		# EN: Assign annotated value to blocks.
		# JP: blocks に型付きの値を代入する。
		blocks: list[ToolUseBlockParam] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for tool_call in tool_calls:
			# Parse the arguments JSON string to object

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to input_obj.
				# JP: input_obj に値を代入する。
				input_obj = json.loads(tool_call.function.arguments)
			except json.JSONDecodeError:
				# If arguments aren't valid JSON, use as string
				# EN: Assign value to input_obj.
				# JP: input_obj に値を代入する。
				input_obj = {'arguments': tool_call.function.arguments}

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			blocks.append(
				ToolUseBlockParam(
					id=tool_call.id,
					input=input_obj,
					name=tool_call.function.name,
					type='tool_use',
					cache_control=AnthropicMessageSerializer._serialize_cache_control(use_cache),
				)
			)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return blocks

	# region - Serialize overloads
	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: UserMessage) -> MessageParam: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: SystemMessage) -> SystemMessage: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: AssistantMessage) -> MessageParam: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@staticmethod
	def serialize(message: BaseMessage) -> MessageParam | SystemMessage:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize a custom message to an Anthropic MessageParam.

		Note: Anthropic doesn't have a 'system' role. System messages should be
		handled separately as the system parameter in the API call, not as a message.
		If a SystemMessage is passed here, it will be converted to a user message.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(message, UserMessage):
			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = AnthropicMessageSerializer._serialize_content(message.content, use_cache=message.cache)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return MessageParam(role='user', content=content)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message, SystemMessage):
			# Anthropic doesn't have system messages in the messages array
			# System prompts are passed separately. Convert to user message.
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return message

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message, AssistantMessage):
			# Handle content and tool calls
			# EN: Assign annotated value to blocks.
			# JP: blocks に型付きの値を代入する。
			blocks: list[TextBlockParam | ToolUseBlockParam] = []

			# Add content blocks if present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.content is not None:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(message.content, str):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					blocks.append(
						TextBlockParam(
							text=message.content,
							type='text',
							cache_control=AnthropicMessageSerializer._serialize_cache_control(message.cache),
						)
					)
				else:
					# Process content parts (text and refusal)
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for part in message.content:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if part.type == 'text':
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							blocks.append(AnthropicMessageSerializer._serialize_content_part_text(part, use_cache=message.cache))
						# # Note: Anthropic doesn't have a specific refusal block type,
						# # so we convert refusals to text blocks
						# elif part.type == 'refusal':
						# 	blocks.append(TextBlockParam(text=f'[Refusal] {part.refusal}', type='text'))

			# Add tool use blocks if present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.tool_calls:
				# EN: Assign value to tool_blocks.
				# JP: tool_blocks に値を代入する。
				tool_blocks = AnthropicMessageSerializer._serialize_tool_calls_to_content(
					message.tool_calls, use_cache=message.cache
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				blocks.extend(tool_blocks)

			# If no content or tool calls, add empty text block
			# (Anthropic requires at least one content block)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not blocks:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				blocks.append(
					TextBlockParam(
						text='', type='text', cache_control=AnthropicMessageSerializer._serialize_cache_control(message.cache)
					)
				)

			# If caching is enabled or we have multiple blocks, return blocks as-is
			# Otherwise, simplify single text blocks to plain string
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.cache or len(blocks) > 1:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = blocks
			else:
				# Only simplify when no caching and single block
				# EN: Assign value to single_block.
				# JP: single_block に値を代入する。
				single_block = blocks[0]
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if single_block['type'] == 'text' and not single_block.get('cache_control'):
					# EN: Assign value to content.
					# JP: content に値を代入する。
					content = single_block['text']
				else:
					# EN: Assign value to content.
					# JP: content に値を代入する。
					content = blocks

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return MessageParam(
				role='assistant',
				content=content,
			)

		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Unknown message type: {type(message)}')

	# EN: Define function `_clean_cache_messages`.
	# JP: 関数 `_clean_cache_messages` を定義する。
	@staticmethod
	def _clean_cache_messages(messages: list[NonSystemMessage]) -> list[NonSystemMessage]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clean cache settings so only the last cache=True message remains cached.

		Because of how Claude caching works, only the last cache message matters.
		This method automatically removes cache=True from all messages except the last one.

		Args:
			messages: List of non-system messages to clean

		Returns:
			List of messages with cleaned cache settings
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not messages:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return messages

		# Create a copy to avoid modifying the original
		# EN: Assign value to cleaned_messages.
		# JP: cleaned_messages に値を代入する。
		cleaned_messages = [msg.model_copy(deep=True) for msg in messages]

		# Find the last message with cache=True
		# EN: Assign value to last_cache_index.
		# JP: last_cache_index に値を代入する。
		last_cache_index = -1
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i in range(len(cleaned_messages) - 1, -1, -1):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cleaned_messages[i].cache:
				# EN: Assign value to last_cache_index.
				# JP: last_cache_index に値を代入する。
				last_cache_index = i
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break

		# If we found a cached message, disable cache for all others
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if last_cache_index != -1:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, msg in enumerate(cleaned_messages):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if i != last_cache_index and msg.cache:
					# Set cache to False for all messages except the last cached one
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					msg.cache = False

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cleaned_messages

	# EN: Define function `serialize_messages`.
	# JP: 関数 `serialize_messages` を定義する。
	@staticmethod
	def serialize_messages(messages: list[BaseMessage]) -> tuple[list[MessageParam], list[TextBlockParam] | str | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize a list of messages, extracting any system message.

		Returns:
		    A tuple of (messages, system_message) where system_message is extracted
		    from any SystemMessage in the list.
		"""
		# EN: Assign value to messages.
		# JP: messages に値を代入する。
		messages = [m.model_copy(deep=True) for m in messages]

		# Separate system messages from normal messages
		# EN: Assign annotated value to normal_messages.
		# JP: normal_messages に型付きの値を代入する。
		normal_messages: list[NonSystemMessage] = []
		# EN: Assign annotated value to system_message.
		# JP: system_message に型付きの値を代入する。
		system_message: SystemMessage | None = None

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for message in messages:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(message, SystemMessage):
				# EN: Assign value to system_message.
				# JP: system_message に値を代入する。
				system_message = message
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				normal_messages.append(message)

		# Clean cache messages so only the last cache=True message remains cached
		# EN: Assign value to normal_messages.
		# JP: normal_messages に値を代入する。
		normal_messages = AnthropicMessageSerializer._clean_cache_messages(normal_messages)

		# Serialize normal messages
		# EN: Assign annotated value to serialized_messages.
		# JP: serialized_messages に型付きの値を代入する。
		serialized_messages: list[MessageParam] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for message in normal_messages:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			serialized_messages.append(AnthropicMessageSerializer.serialize(message))

		# Serialize system message
		# EN: Assign annotated value to serialized_system_message.
		# JP: serialized_system_message に型付きの値を代入する。
		serialized_system_message: list[TextBlockParam] | str | None = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if system_message:
			# EN: Assign value to serialized_system_message.
			# JP: serialized_system_message に値を代入する。
			serialized_system_message = AnthropicMessageSerializer._serialize_content_to_str(
				system_message.content, use_cache=system_message.cache
			)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return serialized_messages, serialized_system_message

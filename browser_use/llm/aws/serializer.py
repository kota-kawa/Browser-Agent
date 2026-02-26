# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import base64
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, overload

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


# EN: Define class `AWSBedrockMessageSerializer`.
# JP: クラス `AWSBedrockMessageSerializer` を定義する。
class AWSBedrockMessageSerializer:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serializer for converting between custom message types and AWS Bedrock message format."""

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

	# EN: Define function `_is_url_image`.
	# JP: 関数 `_is_url_image` を定義する。
	@staticmethod
	def _is_url_image(url: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the URL is a regular HTTP/HTTPS image URL."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return url.startswith(('http://', 'https://')) and any(
			url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
		)

	# EN: Define function `_parse_base64_url`.
	# JP: 関数 `_parse_base64_url` を定義する。
	@staticmethod
	def _parse_base64_url(url: str) -> tuple[str, bytes]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Parse a base64 data URL to extract format and raw bytes."""
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

		# Extract format from mime type
		# EN: Assign value to mime_match.
		# JP: mime_match に値を代入する。
		mime_match = re.search(r'image/(\w+)', header)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if mime_match:
			# EN: Assign value to format_name.
			# JP: format_name に値を代入する。
			format_name = mime_match.group(1).lower()
			# Map common formats
			# EN: Assign value to format_mapping.
			# JP: format_mapping に値を代入する。
			format_mapping = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'gif': 'gif', 'webp': 'webp'}
			# EN: Assign value to image_format.
			# JP: image_format に値を代入する。
			image_format = format_mapping.get(format_name, 'jpeg')
		else:
			# EN: Assign value to image_format.
			# JP: image_format に値を代入する。
			image_format = 'jpeg'  # Default format

		# Decode base64 data
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to image_bytes.
			# JP: image_bytes に値を代入する。
			image_bytes = base64.b64decode(data)
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Failed to decode base64 image data: {e}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return image_format, image_bytes

	# EN: Define function `_download_and_convert_image`.
	# JP: 関数 `_download_and_convert_image` を定義する。
	@staticmethod
	def _download_and_convert_image(url: str) -> tuple[str, bytes]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Download an image from URL and convert to base64 bytes."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import httpx
		except ImportError:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ImportError('httpx not available. Please install it to use URL images with AWS Bedrock.')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to response.
			# JP: response に値を代入する。
			response = httpx.get(url, timeout=30)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			response.raise_for_status()

			# Detect format from content type or URL
			# EN: Assign value to content_type.
			# JP: content_type に値を代入する。
			content_type = response.headers.get('content-type', '').lower()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'jpeg' in content_type or url.lower().endswith(('.jpg', '.jpeg')):
				# EN: Assign value to image_format.
				# JP: image_format に値を代入する。
				image_format = 'jpeg'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif 'png' in content_type or url.lower().endswith('.png'):
				# EN: Assign value to image_format.
				# JP: image_format に値を代入する。
				image_format = 'png'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif 'gif' in content_type or url.lower().endswith('.gif'):
				# EN: Assign value to image_format.
				# JP: image_format に値を代入する。
				image_format = 'gif'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif 'webp' in content_type or url.lower().endswith('.webp'):
				# EN: Assign value to image_format.
				# JP: image_format に値を代入する。
				image_format = 'webp'
			else:
				# EN: Assign value to image_format.
				# JP: image_format に値を代入する。
				image_format = 'jpeg'  # Default format

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return image_format, response.content

		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Failed to download image from {url}: {e}')

	# EN: Define function `_serialize_content_part_text`.
	# JP: 関数 `_serialize_content_part_text` を定義する。
	@staticmethod
	def _serialize_content_part_text(part: ContentPartTextParam) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert a text content part to AWS Bedrock format."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {'text': part.text}

	# EN: Define function `_serialize_content_part_image`.
	# JP: 関数 `_serialize_content_part_image` を定義する。
	@staticmethod
	def _serialize_content_part_image(part: ContentPartImageParam) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert an image content part to AWS Bedrock format."""
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = part.image_url.url

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if AWSBedrockMessageSerializer._is_base64_image(url):
			# Handle base64 encoded images
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			image_format, image_bytes = AWSBedrockMessageSerializer._parse_base64_url(url)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif AWSBedrockMessageSerializer._is_url_image(url):
			# Download and convert URL images
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			image_format, image_bytes = AWSBedrockMessageSerializer._download_and_convert_image(url)
		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Unsupported image URL format: {url}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'image': {
				'format': image_format,
				'source': {
					'bytes': image_bytes,
				},
			}
		}

	# EN: Define function `_serialize_user_content`.
	# JP: 関数 `_serialize_user_content` を定義する。
	@staticmethod
	def _serialize_user_content(
		content: str | list[ContentPartTextParam | ContentPartImageParam],
	) -> list[dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize content for user messages."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return [{'text': content}]

		# EN: Assign annotated value to content_blocks.
		# JP: content_blocks に型付きの値を代入する。
		content_blocks: list[dict[str, Any]] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_blocks.append(AWSBedrockMessageSerializer._serialize_content_part_text(part))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif part.type == 'image_url':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_blocks.append(AWSBedrockMessageSerializer._serialize_content_part_image(part))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return content_blocks

	# EN: Define function `_serialize_system_content`.
	# JP: 関数 `_serialize_system_content` を定義する。
	@staticmethod
	def _serialize_system_content(
		content: str | list[ContentPartTextParam],
	) -> list[dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize content for system messages."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return [{'text': content}]

		# EN: Assign annotated value to content_blocks.
		# JP: content_blocks に型付きの値を代入する。
		content_blocks: list[dict[str, Any]] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_blocks.append(AWSBedrockMessageSerializer._serialize_content_part_text(part))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return content_blocks

	# EN: Define function `_serialize_assistant_content`.
	# JP: 関数 `_serialize_assistant_content` を定義する。
	@staticmethod
	def _serialize_assistant_content(
		content: str | list[ContentPartTextParam | ContentPartRefusalParam] | None,
	) -> list[dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize content for assistant messages."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if content is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return [{'text': content}]

		# EN: Assign annotated value to content_blocks.
		# JP: content_blocks に型付きの値を代入する。
		content_blocks: list[dict[str, Any]] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_blocks.append(AWSBedrockMessageSerializer._serialize_content_part_text(part))
			# Skip refusal content parts - AWS Bedrock doesn't need them

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return content_blocks

	# EN: Define function `_serialize_tool_call`.
	# JP: 関数 `_serialize_tool_call` を定義する。
	@staticmethod
	def _serialize_tool_call(tool_call: ToolCall) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert a tool call to AWS Bedrock format."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to arguments.
			# JP: arguments に値を代入する。
			arguments = json.loads(tool_call.function.arguments)
		except json.JSONDecodeError:
			# If arguments aren't valid JSON, wrap them
			# EN: Assign value to arguments.
			# JP: arguments に値を代入する。
			arguments = {'arguments': tool_call.function.arguments}

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'toolUse': {
				'toolUseId': tool_call.id,
				'name': tool_call.function.name,
				'input': arguments,
			}
		}

	# region - Serialize overloads
	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: UserMessage) -> dict[str, Any]: ...

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
	def serialize(message: AssistantMessage) -> dict[str, Any]: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@staticmethod
	def serialize(message: BaseMessage) -> dict[str, Any] | SystemMessage:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize a custom message to AWS Bedrock format."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(message, UserMessage):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return {
				'role': 'user',
				'content': AWSBedrockMessageSerializer._serialize_user_content(message.content),
			}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message, SystemMessage):
			# System messages are handled separately in AWS Bedrock
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return message

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message, AssistantMessage):
			# EN: Assign annotated value to content_blocks.
			# JP: content_blocks に型付きの値を代入する。
			content_blocks: list[dict[str, Any]] = []

			# Add content blocks if present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.content is not None:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_blocks.extend(AWSBedrockMessageSerializer._serialize_assistant_content(message.content))

			# Add tool use blocks if present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.tool_calls:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for tool_call in message.tool_calls:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					content_blocks.append(AWSBedrockMessageSerializer._serialize_tool_call(tool_call))

			# AWS Bedrock requires at least one content block
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not content_blocks:
				# EN: Assign value to content_blocks.
				# JP: content_blocks に値を代入する。
				content_blocks = [{'text': ''}]

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return {
				'role': 'assistant',
				'content': content_blocks,
			}

		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Unknown message type: {type(message)}')

	# EN: Define function `serialize_messages`.
	# JP: 関数 `serialize_messages` を定義する。
	@staticmethod
	def serialize_messages(messages: list[BaseMessage]) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Serialize a list of messages, extracting any system message.

		Returns:
			Tuple of (bedrock_messages, system_message) where system_message is extracted
			from any SystemMessage in the list.
		"""
		# EN: Assign annotated value to bedrock_messages.
		# JP: bedrock_messages に型付きの値を代入する。
		bedrock_messages: list[dict[str, Any]] = []
		# EN: Assign annotated value to system_message.
		# JP: system_message に型付きの値を代入する。
		system_message: list[dict[str, Any]] | None = None

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for message in messages:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(message, SystemMessage):
				# Extract system message content
				# EN: Assign value to system_message.
				# JP: system_message に値を代入する。
				system_message = AWSBedrockMessageSerializer._serialize_system_content(message.content)
			else:
				# Serialize and add to regular messages
				# EN: Assign value to serialized.
				# JP: serialized に値を代入する。
				serialized = AWSBedrockMessageSerializer.serialize(message)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				bedrock_messages.append(serialized)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return bedrock_messages, system_message

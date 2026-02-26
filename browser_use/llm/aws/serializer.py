import base64
import json
import re
from typing import Any, overload

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
	"""Serializer for converting between custom message types and AWS Bedrock message format."""

	# EN: Define function `_is_base64_image`.
	# JP: 関数 `_is_base64_image` を定義する。
	@staticmethod
	def _is_base64_image(url: str) -> bool:
		"""Check if the URL is a base64 encoded image."""
		return url.startswith('data:image/')

	# EN: Define function `_is_url_image`.
	# JP: 関数 `_is_url_image` を定義する。
	@staticmethod
	def _is_url_image(url: str) -> bool:
		"""Check if the URL is a regular HTTP/HTTPS image URL."""
		return url.startswith(('http://', 'https://')) and any(
			url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
		)

	# EN: Define function `_parse_base64_url`.
	# JP: 関数 `_parse_base64_url` を定義する。
	@staticmethod
	def _parse_base64_url(url: str) -> tuple[str, bytes]:
		"""Parse a base64 data URL to extract format and raw bytes."""
		# Format: data:image/jpeg;base64,<data>
		if not url.startswith('data:'):
			raise ValueError(f'Invalid base64 URL: {url}')

		header, data = url.split(',', 1)

		# Extract format from mime type
		mime_match = re.search(r'image/(\w+)', header)
		if mime_match:
			format_name = mime_match.group(1).lower()
			# Map common formats
			format_mapping = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'gif': 'gif', 'webp': 'webp'}
			image_format = format_mapping.get(format_name, 'jpeg')
		else:
			image_format = 'jpeg'  # Default format

		# Decode base64 data
		try:
			image_bytes = base64.b64decode(data)
		except Exception as e:
			raise ValueError(f'Failed to decode base64 image data: {e}')

		return image_format, image_bytes

	# EN: Define function `_download_and_convert_image`.
	# JP: 関数 `_download_and_convert_image` を定義する。
	@staticmethod
	def _download_and_convert_image(url: str) -> tuple[str, bytes]:
		"""Download an image from URL and convert to base64 bytes."""
		try:
			import httpx
		except ImportError:
			raise ImportError('httpx not available. Please install it to use URL images with AWS Bedrock.')

		try:
			response = httpx.get(url, timeout=30)
			response.raise_for_status()

			# Detect format from content type or URL
			content_type = response.headers.get('content-type', '').lower()
			if 'jpeg' in content_type or url.lower().endswith(('.jpg', '.jpeg')):
				image_format = 'jpeg'
			elif 'png' in content_type or url.lower().endswith('.png'):
				image_format = 'png'
			elif 'gif' in content_type or url.lower().endswith('.gif'):
				image_format = 'gif'
			elif 'webp' in content_type or url.lower().endswith('.webp'):
				image_format = 'webp'
			else:
				image_format = 'jpeg'  # Default format

			return image_format, response.content

		except Exception as e:
			raise ValueError(f'Failed to download image from {url}: {e}')

	# EN: Define function `_serialize_content_part_text`.
	# JP: 関数 `_serialize_content_part_text` を定義する。
	@staticmethod
	def _serialize_content_part_text(part: ContentPartTextParam) -> dict[str, Any]:
		"""Convert a text content part to AWS Bedrock format."""
		return {'text': part.text}

	# EN: Define function `_serialize_content_part_image`.
	# JP: 関数 `_serialize_content_part_image` を定義する。
	@staticmethod
	def _serialize_content_part_image(part: ContentPartImageParam) -> dict[str, Any]:
		"""Convert an image content part to AWS Bedrock format."""
		url = part.image_url.url

		if AWSBedrockMessageSerializer._is_base64_image(url):
			# Handle base64 encoded images
			image_format, image_bytes = AWSBedrockMessageSerializer._parse_base64_url(url)
		elif AWSBedrockMessageSerializer._is_url_image(url):
			# Download and convert URL images
			image_format, image_bytes = AWSBedrockMessageSerializer._download_and_convert_image(url)
		else:
			raise ValueError(f'Unsupported image URL format: {url}')

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
		"""Serialize content for user messages."""
		if isinstance(content, str):
			return [{'text': content}]

		content_blocks: list[dict[str, Any]] = []
		for part in content:
			if part.type == 'text':
				content_blocks.append(AWSBedrockMessageSerializer._serialize_content_part_text(part))
			elif part.type == 'image_url':
				content_blocks.append(AWSBedrockMessageSerializer._serialize_content_part_image(part))

		return content_blocks

	# EN: Define function `_serialize_system_content`.
	# JP: 関数 `_serialize_system_content` を定義する。
	@staticmethod
	def _serialize_system_content(
		content: str | list[ContentPartTextParam],
	) -> list[dict[str, Any]]:
		"""Serialize content for system messages."""
		if isinstance(content, str):
			return [{'text': content}]

		content_blocks: list[dict[str, Any]] = []
		for part in content:
			if part.type == 'text':
				content_blocks.append(AWSBedrockMessageSerializer._serialize_content_part_text(part))

		return content_blocks

	# EN: Define function `_serialize_assistant_content`.
	# JP: 関数 `_serialize_assistant_content` を定義する。
	@staticmethod
	def _serialize_assistant_content(
		content: str | list[ContentPartTextParam | ContentPartRefusalParam] | None,
	) -> list[dict[str, Any]]:
		"""Serialize content for assistant messages."""
		if content is None:
			return []
		if isinstance(content, str):
			return [{'text': content}]

		content_blocks: list[dict[str, Any]] = []
		for part in content:
			if part.type == 'text':
				content_blocks.append(AWSBedrockMessageSerializer._serialize_content_part_text(part))
			# Skip refusal content parts - AWS Bedrock doesn't need them

		return content_blocks

	# EN: Define function `_serialize_tool_call`.
	# JP: 関数 `_serialize_tool_call` を定義する。
	@staticmethod
	def _serialize_tool_call(tool_call: ToolCall) -> dict[str, Any]:
		"""Convert a tool call to AWS Bedrock format."""
		try:
			arguments = json.loads(tool_call.function.arguments)
		except json.JSONDecodeError:
			# If arguments aren't valid JSON, wrap them
			arguments = {'arguments': tool_call.function.arguments}

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
	def serialize(message: UserMessage) -> dict[str, Any]: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	def serialize(message: SystemMessage) -> SystemMessage: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	def serialize(message: AssistantMessage) -> dict[str, Any]: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@staticmethod
	def serialize(message: BaseMessage) -> dict[str, Any] | SystemMessage:
		"""Serialize a custom message to AWS Bedrock format."""

		if isinstance(message, UserMessage):
			return {
				'role': 'user',
				'content': AWSBedrockMessageSerializer._serialize_user_content(message.content),
			}

		elif isinstance(message, SystemMessage):
			# System messages are handled separately in AWS Bedrock
			return message

		elif isinstance(message, AssistantMessage):
			content_blocks: list[dict[str, Any]] = []

			# Add content blocks if present
			if message.content is not None:
				content_blocks.extend(AWSBedrockMessageSerializer._serialize_assistant_content(message.content))

			# Add tool use blocks if present
			if message.tool_calls:
				for tool_call in message.tool_calls:
					content_blocks.append(AWSBedrockMessageSerializer._serialize_tool_call(tool_call))

			# AWS Bedrock requires at least one content block
			if not content_blocks:
				content_blocks = [{'text': ''}]

			return {
				'role': 'assistant',
				'content': content_blocks,
			}

		else:
			raise ValueError(f'Unknown message type: {type(message)}')

	# EN: Define function `serialize_messages`.
	# JP: 関数 `serialize_messages` を定義する。
	@staticmethod
	def serialize_messages(messages: list[BaseMessage]) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None]:
		"""
		Serialize a list of messages, extracting any system message.

		Returns:
			Tuple of (bedrock_messages, system_message) where system_message is extracted
			from any SystemMessage in the list.
		"""
		bedrock_messages: list[dict[str, Any]] = []
		system_message: list[dict[str, Any]] | None = None

		for message in messages:
			if isinstance(message, SystemMessage):
				# Extract system message content
				system_message = AWSBedrockMessageSerializer._serialize_system_content(message.content)
			else:
				# Serialize and add to regular messages
				serialized = AWSBedrockMessageSerializer.serialize(message)
				bedrock_messages.append(serialized)

		return bedrock_messages, system_message

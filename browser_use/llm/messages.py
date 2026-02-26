# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
This implementation is based on the OpenAI types, while removing all the parts that are not needed for Browser Use.
"""

# region - Content parts
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Literal, Union

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai import BaseModel


# EN: Define function `_truncate`.
# JP: 関数 `_truncate` を定義する。
def _truncate(text: str, max_length: int = 50) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Truncate text to max_length characters, adding ellipsis if truncated."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if len(text) <= max_length:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return text
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return text[: max_length - 3] + '...'


# EN: Define function `_format_image_url`.
# JP: 関数 `_format_image_url` を定義する。
def _format_image_url(url: str, max_length: int = 50) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Format image URL for display, truncating if necessary."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if url.startswith('data:'):
		# Base64 image
		# EN: Assign value to media_type.
		# JP: media_type に値を代入する。
		media_type = url.split(';')[0].split(':')[1] if ';' in url else 'image'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'<base64 {media_type}>'
	else:
		# Regular URL
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _truncate(url, max_length)


# EN: Define class `ContentPartTextParam`.
# JP: クラス `ContentPartTextParam` を定義する。
class ContentPartTextParam(BaseModel):
	# EN: Assign annotated value to text.
	# JP: text に型付きの値を代入する。
	text: str
	# EN: Assign annotated value to type.
	# JP: type に型付きの値を代入する。
	type: Literal['text'] = 'text'

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Text: {_truncate(self.text)}'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'ContentPartTextParam(text={_truncate(self.text)})'


# EN: Define class `ContentPartRefusalParam`.
# JP: クラス `ContentPartRefusalParam` を定義する。
class ContentPartRefusalParam(BaseModel):
	# EN: Assign annotated value to refusal.
	# JP: refusal に型付きの値を代入する。
	refusal: str
	# EN: Assign annotated value to type.
	# JP: type に型付きの値を代入する。
	type: Literal['refusal'] = 'refusal'

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Refusal: {_truncate(self.refusal)}'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'ContentPartRefusalParam(refusal={_truncate(repr(self.refusal), 50)})'


# EN: Assign value to SupportedImageMediaType.
# JP: SupportedImageMediaType に値を代入する。
SupportedImageMediaType = Literal['image/jpeg', 'image/png', 'image/gif', 'image/webp']


# EN: Define class `ImageURL`.
# JP: クラス `ImageURL` を定義する。
class ImageURL(BaseModel):
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Either a URL of the image or the base64 encoded image data."""
	# EN: Assign annotated value to detail.
	# JP: detail に型付きの値を代入する。
	detail: Literal['auto', 'low', 'high'] = 'auto'
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Specifies the detail level of the image.

    Learn more in the
    [Vision guide](https://platform.openai.com/docs/guides/vision#low-or-high-fidelity-image-understanding).
    """
	# needed for Anthropic
	# EN: Assign annotated value to media_type.
	# JP: media_type に型付きの値を代入する。
	media_type: SupportedImageMediaType = 'image/png'

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Assign value to url_display.
		# JP: url_display に値を代入する。
		url_display = _format_image_url(self.url)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'🖼️  Image[{self.media_type}, detail={self.detail}]: {url_display}'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Assign value to url_repr.
		# JP: url_repr に値を代入する。
		url_repr = _format_image_url(self.url, 30)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'ImageURL(url={repr(url_repr)}, detail={repr(self.detail)}, media_type={repr(self.media_type)})'


# EN: Define class `ContentPartImageParam`.
# JP: クラス `ContentPartImageParam` を定義する。
class ContentPartImageParam(BaseModel):
	# EN: Assign annotated value to image_url.
	# JP: image_url に型付きの値を代入する。
	image_url: ImageURL
	# EN: Assign annotated value to type.
	# JP: type に型付きの値を代入する。
	type: Literal['image_url'] = 'image_url'

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(self.image_url)

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'ContentPartImageParam(image_url={repr(self.image_url)})'


# EN: Define class `Function`.
# JP: クラス `Function` を定義する。
class Function(BaseModel):
	# EN: Assign annotated value to arguments.
	# JP: arguments に型付きの値を代入する。
	arguments: str
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
    The arguments to call the function with, as generated by the model in JSON
    format. Note that the model does not always generate valid JSON, and may
    hallucinate parameters not defined by your function schema. Validate the
    arguments in your code before calling your function.
    """
	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The name of the function to call."""

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Assign value to args_preview.
		# JP: args_preview に値を代入する。
		args_preview = _truncate(self.arguments, 80)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'{self.name}({args_preview})'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Assign value to args_repr.
		# JP: args_repr に値を代入する。
		args_repr = _truncate(repr(self.arguments), 50)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Function(name={repr(self.name)}, arguments={args_repr})'


# EN: Define class `ToolCall`.
# JP: クラス `ToolCall` を定義する。
class ToolCall(BaseModel):
	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The ID of the tool call."""
	# EN: Assign annotated value to function.
	# JP: function に型付きの値を代入する。
	function: Function
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The function that the model called."""
	# EN: Assign annotated value to type.
	# JP: type に型付きの値を代入する。
	type: Literal['function'] = 'function'
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The type of the tool. Currently, only `function` is supported."""

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'ToolCall[{self.id}]: {self.function}'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'ToolCall(id={repr(self.id)}, function={repr(self.function)})'


# endregion


# region - Message types
# EN: Define class `_MessageBase`.
# JP: クラス `_MessageBase` を定義する。
class _MessageBase(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Base class for all message types"""

	# EN: Assign annotated value to role.
	# JP: role に型付きの値を代入する。
	role: Literal['user', 'system', 'assistant']

	# EN: Assign annotated value to cache.
	# JP: cache に型付きの値を代入する。
	cache: bool = False
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Whether to cache this message. This is only applicable when using Anthropic models.
	"""


# EN: Define class `UserMessage`.
# JP: クラス `UserMessage` を定義する。
class UserMessage(_MessageBase):
	# EN: Assign annotated value to role.
	# JP: role に型付きの値を代入する。
	role: Literal['user'] = 'user'
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The role of the messages author, in this case `user`."""

	# EN: Assign annotated value to content.
	# JP: content に型付きの値を代入する。
	content: str | list[ContentPartTextParam | ContentPartImageParam]
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The contents of the user message."""

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str | None = None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""An optional name for the participant.

    Provides the model information to differentiate between participants of the same
    role.
    """

	# EN: Define function `text`.
	# JP: 関数 `text` を定義する。
	@property
	def text(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Automatically parse the text inside content, whether it's a string or a list of content parts.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(self.content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.content
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(self.content, list):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '\n'.join([part.text for part in self.content if part.type == 'text'])
		else:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'UserMessage(content={self.text})'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'UserMessage(content={repr(self.text)})'


# EN: Define class `SystemMessage`.
# JP: クラス `SystemMessage` を定義する。
class SystemMessage(_MessageBase):
	# EN: Assign annotated value to role.
	# JP: role に型付きの値を代入する。
	role: Literal['system'] = 'system'
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The role of the messages author, in this case `system`."""

	# EN: Assign annotated value to content.
	# JP: content に型付きの値を代入する。
	content: str | list[ContentPartTextParam]
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The contents of the system message."""

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str | None = None

	# EN: Define function `text`.
	# JP: 関数 `text` を定義する。
	@property
	def text(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Automatically parse the text inside content, whether it's a string or a list of content parts.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(self.content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.content
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(self.content, list):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '\n'.join([part.text for part in self.content if part.type == 'text'])
		else:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'SystemMessage(content={self.text})'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'SystemMessage(content={repr(self.text)})'


# EN: Define class `AssistantMessage`.
# JP: クラス `AssistantMessage` を定義する。
class AssistantMessage(_MessageBase):
	# EN: Assign annotated value to role.
	# JP: role に型付きの値を代入する。
	role: Literal['assistant'] = 'assistant'
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The role of the messages author, in this case `assistant`."""

	# EN: Assign annotated value to content.
	# JP: content に型付きの値を代入する。
	content: str | list[ContentPartTextParam | ContentPartRefusalParam] | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The contents of the assistant message."""

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str | None = None

	# EN: Assign annotated value to refusal.
	# JP: refusal に型付きの値を代入する。
	refusal: str | None = None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The refusal message by the assistant."""

	# EN: Assign annotated value to tool_calls.
	# JP: tool_calls に型付きの値を代入する。
	tool_calls: list[ToolCall] = []
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The tool calls generated by the model, such as function calls."""

	# EN: Define function `text`.
	# JP: 関数 `text` を定義する。
	@property
	def text(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Automatically parse the text inside content, whether it's a string or a list of content parts.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(self.content, str):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.content
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(self.content, list):
			# EN: Assign value to text.
			# JP: text に値を代入する。
			text = ''
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for part in self.content:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if part.type == 'text':
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					text += part.text
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif part.type == 'refusal':
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					text += f'[Refusal] {part.refusal}'
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return text
		else:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'AssistantMessage(content={self.text})'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'AssistantMessage(content={repr(self.text)})'


# EN: Assign value to BaseMessage.
# JP: BaseMessage に値を代入する。
BaseMessage = Union[UserMessage, SystemMessage, AssistantMessage]

# endregion

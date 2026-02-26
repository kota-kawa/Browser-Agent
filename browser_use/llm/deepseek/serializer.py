# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	AssistantMessage,
	BaseMessage,
	ContentPartImageParam,
	ContentPartTextParam,
	SystemMessage,
	ToolCall,
	UserMessage,
)

# EN: Assign value to MessageDict.
# JP: MessageDict に値を代入する。
MessageDict = dict[str, Any]


# EN: Define class `DeepSeekMessageSerializer`.
# JP: クラス `DeepSeekMessageSerializer` を定義する。
class DeepSeekMessageSerializer:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serializer for converting browser-use messages to DeepSeek messages."""

	# -------- content 处理 --------------------------------------------------
	# EN: Define function `_serialize_text_part`.
	# JP: 関数 `_serialize_text_part` を定義する。
	@staticmethod
	def _serialize_text_part(part: ContentPartTextParam) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return part.text

	# EN: Define function `_serialize_image_part`.
	# JP: 関数 `_serialize_image_part` を定義する。
	@staticmethod
	def _serialize_image_part(part: ContentPartImageParam) -> dict[str, Any]:
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = part.image_url.url
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if url.startswith('data:'):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return {'type': 'image_url', 'image_url': {'url': url}}
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {'type': 'image_url', 'image_url': {'url': url}}

	# EN: Define function `_serialize_content`.
	# JP: 関数 `_serialize_content` を定義する。
	@staticmethod
	def _serialize_content(content: Any) -> str | list[dict[str, Any]]:
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
		# EN: Assign annotated value to serialized.
		# JP: serialized に型付きの値を代入する。
		serialized: list[dict[str, Any]] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for part in content:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if part.type == 'text':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized.append({'type': 'text', 'text': DeepSeekMessageSerializer._serialize_text_part(part)})
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif part.type == 'image_url':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized.append(DeepSeekMessageSerializer._serialize_image_part(part))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif part.type == 'refusal':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				serialized.append({'type': 'text', 'text': f'[Refusal] {part.refusal}'})
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return serialized

	# -------- Tool-call 处理 -------------------------------------------------
	# EN: Define function `_serialize_tool_calls`.
	# JP: 関数 `_serialize_tool_calls` を定義する。
	@staticmethod
	def _serialize_tool_calls(tool_calls: list[ToolCall]) -> list[dict[str, Any]]:
		# EN: Assign annotated value to deepseek_tool_calls.
		# JP: deepseek_tool_calls に型付きの値を代入する。
		deepseek_tool_calls: list[dict[str, Any]] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for tc in tool_calls:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to arguments.
				# JP: arguments に値を代入する。
				arguments = json.loads(tc.function.arguments)
			except json.JSONDecodeError:
				# EN: Assign value to arguments.
				# JP: arguments に値を代入する。
				arguments = {'arguments': tc.function.arguments}
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			deepseek_tool_calls.append(
				{
					'id': tc.id,
					'type': 'function',
					'function': {
						'name': tc.function.name,
						'arguments': arguments,
					},
				}
			)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return deepseek_tool_calls

	# -------- 单条消息序列化 -------------------------------------------------
	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: UserMessage) -> MessageDict: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: SystemMessage) -> MessageDict: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@overload
	@staticmethod
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	def serialize(message: AssistantMessage) -> MessageDict: ...

	# EN: Define function `serialize`.
	# JP: 関数 `serialize` を定義する。
	@staticmethod
	def serialize(message: BaseMessage) -> MessageDict:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(message, UserMessage):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return {
				'role': 'user',
				'content': DeepSeekMessageSerializer._serialize_content(message.content),
			}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(message, SystemMessage):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return {
				'role': 'system',
				'content': DeepSeekMessageSerializer._serialize_content(message.content),
			}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(message, AssistantMessage):
			# EN: Assign annotated value to msg.
			# JP: msg に型付きの値を代入する。
			msg: MessageDict = {
				'role': 'assistant',
				'content': DeepSeekMessageSerializer._serialize_content(message.content),
			}
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if message.tool_calls:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				msg['tool_calls'] = DeepSeekMessageSerializer._serialize_tool_calls(message.tool_calls)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return msg
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f'Unknown message type: {type(message)}')

	# -------- 列表序列化 -----------------------------------------------------
	# EN: Define function `serialize_messages`.
	# JP: 関数 `serialize_messages` を定義する。
	@staticmethod
	def serialize_messages(messages: list[BaseMessage]) -> list[MessageDict]:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [DeepSeekMessageSerializer.serialize(m) for m in messages]

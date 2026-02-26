# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, ConfigDict, Field

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	BaseMessage,
)

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `HistoryItem`.
# JP: クラス `HistoryItem` を定義する。
class HistoryItem(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Represents a single agent history item with its data and string representation"""

	# EN: Assign annotated value to step_number.
	# JP: step_number に型付きの値を代入する。
	step_number: int | None = None
	# EN: Assign annotated value to evaluation_previous_goal.
	# JP: evaluation_previous_goal に型付きの値を代入する。
	evaluation_previous_goal: str | None = None
	# EN: Assign annotated value to memory.
	# JP: memory に型付きの値を代入する。
	memory: str | None = None
	# EN: Assign annotated value to next_goal.
	# JP: next_goal に型付きの値を代入する。
	next_goal: str | None = None
	# EN: Assign annotated value to current_status.
	# JP: current_status に型付きの値を代入する。
	current_status: str | None = None
	# EN: Assign annotated value to persistent_notes.
	# JP: persistent_notes に型付きの値を代入する。
	persistent_notes: str | None = None
	# EN: Assign annotated value to action_results.
	# JP: action_results に型付きの値を代入する。
	action_results: str | None = None
	# EN: Assign annotated value to error.
	# JP: error に型付きの値を代入する。
	error: str | None = None
	# EN: Assign annotated value to system_message.
	# JP: system_message に型付きの値を代入する。
	system_message: str | None = None

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True)

	# EN: Define function `model_post_init`.
	# JP: 関数 `model_post_init` を定義する。
	def model_post_init(self, __context) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Validate that error and system_message are not both provided"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.error is not None and self.system_message is not None:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError('Cannot have both error and system_message at the same time')

	# EN: Define function `to_string`.
	# JP: 関数 `to_string` を定義する。
	def to_string(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get string representation of the history item"""
		# EN: Assign value to step_str.
		# JP: step_str に値を代入する。
		step_str = 'step' if self.step_number is not None else 'step_unknown'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.error:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"""<{step_str}>
{self.error}
</{step_str}>"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.system_message:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.system_message
		else:
			# EN: Assign value to content_parts.
			# JP: content_parts に値を代入する。
			content_parts = []

			# Only include evaluation_previous_goal if it's not None/empty
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.evaluation_previous_goal:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_parts.append(f'{self.evaluation_previous_goal}')

			# Always include memory
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.memory:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_parts.append(f'{self.memory}')

			# Only include next_goal if it's not None/empty
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.next_goal:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_parts.append(f'{self.next_goal}')

			# Only include current_status if it's not None/empty
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.current_status:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_parts.append(f'現在の状況: {self.current_status}')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.action_results:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_parts.append(self.action_results)

			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = '\n'.join(content_parts)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"""<{step_str}>
{content}
</{step_str}>"""


# EN: Define class `MessageHistory`.
# JP: クラス `MessageHistory` を定義する。
class MessageHistory(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""History of messages"""

	# EN: Assign annotated value to system_message.
	# JP: system_message に型付きの値を代入する。
	system_message: BaseMessage | None = None
	# EN: Assign annotated value to state_message.
	# JP: state_message に型付きの値を代入する。
	state_message: BaseMessage | None = None
	# EN: Assign annotated value to context_messages.
	# JP: context_messages に型付きの値を代入する。
	context_messages: list[BaseMessage] = Field(default_factory=list)
	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True)

	# EN: Define function `get_messages`.
	# JP: 関数 `get_messages` を定義する。
	def get_messages(self) -> list[BaseMessage]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all messages in the correct order: system -> state -> contextual"""
		# EN: Assign value to messages.
		# JP: messages に値を代入する。
		messages = []
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.system_message:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			messages.append(self.system_message)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state_message:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			messages.append(self.state_message)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		messages.extend(self.context_messages)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return messages


# EN: Define class `MessageManagerState`.
# JP: クラス `MessageManagerState` を定義する。
class MessageManagerState(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Holds the state for MessageManager"""

	# EN: Assign annotated value to history.
	# JP: history に型付きの値を代入する。
	history: MessageHistory = Field(default_factory=MessageHistory)
	# EN: Assign annotated value to tool_id.
	# JP: tool_id に型付きの値を代入する。
	tool_id: int = 1
	# EN: Assign annotated value to agent_history_items.
	# JP: agent_history_items に型付きの値を代入する。
	agent_history_items: list[HistoryItem] = Field(
		default_factory=lambda: [HistoryItem(step_number=0, system_message='Agent initialized')]
	)
	# EN: Assign annotated value to read_state_description.
	# JP: read_state_description に型付きの値を代入する。
	read_state_description: str = ''
	# EN: Assign annotated value to persistent_notes.
	# JP: persistent_notes に型付きの値を代入する。
	persistent_notes: str = ''  # Accumulated notes that persist across history truncation

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True)

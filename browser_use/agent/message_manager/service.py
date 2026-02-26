# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Literal

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.message_manager.views import (
	HistoryItem,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.prompts import AgentMessagePrompt
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import (
	ActionResult,
	AgentOutput,
	AgentStepInfo,
	MessageManagerState,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserStateSummary
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystem
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	BaseMessage,
	ContentPartImageParam,
	ContentPartTextParam,
	SystemMessage,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe_debug
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import match_url_with_domain_pattern, time_execution_sync

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# ========== Logging Helper Functions ==========
# These functions are used ONLY for formatting debug log output.
# They do NOT affect the actual message content sent to the LLM.
# All logging functions start with _log_ for easy identification.


# EN: Define function `_log_get_message_emoji`.
# JP: 関数 `_log_get_message_emoji` を定義する。
def _log_get_message_emoji(message: BaseMessage) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get emoji for a message type - used only for logging display"""
	# EN: Assign value to emoji_map.
	# JP: emoji_map に値を代入する。
	emoji_map = {
		'UserMessage': '💬',
		'SystemMessage': '🧠',
		'AssistantMessage': '🔨',
	}
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return emoji_map.get(message.__class__.__name__, '🎮')


# EN: Define function `_log_format_message_line`.
# JP: 関数 `_log_format_message_line` を定義する。
def _log_format_message_line(message: BaseMessage, content: str, is_last_message: bool, terminal_width: int) -> list[str]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Format a single message for logging display"""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to lines.
		# JP: lines に値を代入する。
		lines = []

		# Get emoji and token info
		# EN: Assign value to emoji.
		# JP: emoji に値を代入する。
		emoji = _log_get_message_emoji(message)
		# token_str = str(message.metadata.tokens).rjust(4)
		# TODO: fix the token count
		# EN: Assign value to token_str.
		# JP: token_str に値を代入する。
		token_str = '??? (TODO)'
		# EN: Assign value to prefix.
		# JP: prefix に値を代入する。
		prefix = f'{emoji}[{token_str}]: '

		# Calculate available width (emoji=2 visual cols + [token]: =8 chars)
		# EN: Assign value to content_width.
		# JP: content_width に値を代入する。
		content_width = terminal_width - 10

		# Handle last message wrapping
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_last_message and len(content) > content_width:
			# Find a good break point
			# EN: Assign value to break_point.
			# JP: break_point に値を代入する。
			break_point = content.rfind(' ', 0, content_width)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if break_point > content_width * 0.7:  # Keep at least 70% of line
				# EN: Assign value to first_line.
				# JP: first_line に値を代入する。
				first_line = content[:break_point]
				# EN: Assign value to rest.
				# JP: rest に値を代入する。
				rest = content[break_point + 1 :]
			else:
				# No good break point, just truncate
				# EN: Assign value to first_line.
				# JP: first_line に値を代入する。
				first_line = content[:content_width]
				# EN: Assign value to rest.
				# JP: rest に値を代入する。
				rest = content[content_width:]

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(prefix + first_line)

			# Second line with 10-space indent
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if rest:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if len(rest) > terminal_width - 10:
					# EN: Assign value to rest.
					# JP: rest に値を代入する。
					rest = rest[: terminal_width - 10]
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(' ' * 10 + rest)
		else:
			# Single line - truncate if needed
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(content) > content_width:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = content[:content_width]
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(prefix + content)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return lines
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning(f'Failed to format message line for logging: {e}')
		# Return a simple fallback line
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ['❓[   ?]: [Error formatting message]']


# ========== End of Logging Helper Functions ==========


# EN: Define class `MessageManager`.
# JP: クラス `MessageManager` を定義する。
class MessageManager:
	# EN: Assign annotated value to vision_detail_level.
	# JP: vision_detail_level に型付きの値を代入する。
	vision_detail_level: Literal['auto', 'low', 'high']

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		task: str,
		system_message: SystemMessage,
		file_system: FileSystem,
		state: MessageManagerState = MessageManagerState(),
		use_thinking: bool = True,
		include_attributes: list[str] | None = None,
		sensitive_data: dict[str, str | dict[str, str]] | None = None,
		max_history_items: int | None = None,
		vision_detail_level: Literal['auto', 'low', 'high'] = 'auto',
		include_tool_call_examples: bool = False,
		include_recent_events: bool = False,
		sample_images: list[ContentPartTextParam | ContentPartImageParam] | None = None,
	):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.task = task
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state = state
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.system_prompt = system_message
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.file_system = file_system
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.sensitive_data_description = ''
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.use_thinking = use_thinking
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.max_history_items = max_history_items
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.vision_detail_level = vision_detail_level
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.include_tool_call_examples = include_tool_call_examples
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.include_recent_events = include_recent_events
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.sample_images = sample_images

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert max_history_items is None or max_history_items > 5, 'max_history_items must be None or greater than 5'

		# Store settings as direct attributes instead of in a settings object
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.include_attributes = include_attributes or []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.sensitive_data = sensitive_data
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.last_input_messages = []
		# Only initialize messages if state is empty
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(self.state.history.get_messages()) == 0:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._set_message_with_type(self.system_prompt, 'system')

	# EN: Define function `agent_history_description`.
	# JP: 関数 `agent_history_description` を定義する。
	@property
	def agent_history_description(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Build agent history description from list of items, respecting max_history_items limit"""
		# EN: Assign value to parts.
		# JP: parts に値を代入する。
		parts = []

		# Include persistent notes at the top if they exist
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.persistent_notes:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(f'<persistent_notes>\n{self.state.persistent_notes}\n</persistent_notes>')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.max_history_items is None:
			# Include all items
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append('\n'.join(item.to_string() for item in self.state.agent_history_items))
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '\n'.join(parts)

		# EN: Assign value to total_items.
		# JP: total_items に値を代入する。
		total_items = len(self.state.agent_history_items)

		# If we have fewer items than the limit, just return all items
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if total_items <= self.max_history_items:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append('\n'.join(item.to_string() for item in self.state.agent_history_items))
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '\n'.join(parts)

		# We have more items than the limit, so we need to omit some
		# EN: Assign value to omitted_count.
		# JP: omitted_count に値を代入する。
		omitted_count = total_items - self.max_history_items

		# Show first item + omitted message + most recent (max_history_items - 1) items
		# The omitted message doesn't count against the limit, only real history items do
		# EN: Assign value to recent_items_count.
		# JP: recent_items_count に値を代入する。
		recent_items_count = self.max_history_items - 1  # -1 for first item

		# EN: Assign value to items_to_include.
		# JP: items_to_include に値を代入する。
		items_to_include = [
			self.state.agent_history_items[0].to_string(),  # Keep first item (initialization)
			f'<sys>[... {omitted_count} previous steps omitted...]</sys>',
		]
		# Add most recent items
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		items_to_include.extend([item.to_string() for item in self.state.agent_history_items[-recent_items_count:]])

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		parts.append('\n'.join(items_to_include))
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(parts)

	# EN: Define function `add_new_task`.
	# JP: 関数 `add_new_task` を定義する。
	def add_new_task(self, new_task: str) -> None:
		# EN: Assign value to new_task.
		# JP: new_task に値を代入する。
		new_task = '<follow_up_user_request> ' + new_task.strip() + ' </follow_up_user_request>'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if '<initial_user_request>' not in self.task:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.task = '<initial_user_request>' + self.task + '</initial_user_request>'
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		self.task += '\n' + new_task
		# EN: Assign value to task_update_item.
		# JP: task_update_item に値を代入する。
		task_update_item = HistoryItem(system_message=new_task)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.state.agent_history_items.append(task_update_item)

	# EN: Define function `_update_agent_history_description`.
	# JP: 関数 `_update_agent_history_description` を定義する。
	def _update_agent_history_description(
		self,
		model_output: AgentOutput | None = None,
		result: list[ActionResult] | None = None,
		step_info: AgentStepInfo | None = None,
	) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update the agent history description"""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if result is None:
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = []
		# EN: Assign value to step_number.
		# JP: step_number に値を代入する。
		step_number = step_info.step_number if step_info else None

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.read_state_description = ''

		# EN: Assign value to action_results.
		# JP: action_results に値を代入する。
		action_results = ''
		# EN: Assign value to result_len.
		# JP: result_len に値を代入する。
		result_len = len(result)
		# EN: Assign value to read_state_idx.
		# JP: read_state_idx に値を代入する。
		read_state_idx = 0
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for idx, action_result in enumerate(result):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if action_result.include_extracted_content_only_once and action_result.extracted_content:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				self.state.read_state_description += (
					f'<read_state_{read_state_idx}>\n{action_result.extracted_content}\n</read_state_{read_state_idx}>\n'
				)
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				read_state_idx += 1
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Added extracted_content to read_state_description: {action_result.extracted_content}')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if action_result.long_term_memory:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				action_results += f'{action_result.long_term_memory}\n'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Added long_term_memory to action_results: {action_result.long_term_memory}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif action_result.extracted_content and not action_result.include_extracted_content_only_once:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				action_results += f'{action_result.extracted_content}\n'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Added extracted_content to action_results: {action_result.extracted_content}')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if action_result.error:
				# EN: Assign value to error_text.
				# JP: error_text に値を代入する。
				error_text = action_result.error
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				action_results += f'{error_text}\n'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Added error to action_results: {error_text}')

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.read_state_description = self.state.read_state_description.strip('\n')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if action_results:
			# EN: Assign value to action_results.
			# JP: action_results に値を代入する。
			action_results = f'Result:\n{action_results}'
		# EN: Assign value to action_results.
		# JP: action_results に値を代入する。
		action_results = action_results.strip('\n') if action_results else None

		# Build the history item
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if model_output is None:
			# Add history item for initial actions (step 0) or errors (step > 0)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if step_number is not None:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if step_number == 0 and action_results:
					# Step 0 with initial action results
					# EN: Assign value to history_item.
					# JP: history_item に値を代入する。
					history_item = HistoryItem(step_number=step_number, action_results=action_results)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.state.agent_history_items.append(history_item)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif step_number > 0:
					# Error case for steps > 0
					# EN: Assign value to history_item.
					# JP: history_item に値を代入する。
					history_item = HistoryItem(step_number=step_number, error='Agent failed to output in the right format.')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.state.agent_history_items.append(history_item)
		else:
			# Update persistent notes if provided by the model
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if model_output.persistent_notes:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.state.persistent_notes = model_output.persistent_notes

			# EN: Assign value to history_item.
			# JP: history_item に値を代入する。
			history_item = HistoryItem(
				step_number=step_number,
				evaluation_previous_goal=model_output.current_state.evaluation_previous_goal,
				memory=model_output.current_state.memory,
				next_goal=model_output.current_state.next_goal,
				persistent_notes=model_output.persistent_notes,
				action_results=action_results,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.state.agent_history_items.append(history_item)

	# EN: Define function `_get_sensitive_data_description`.
	# JP: 関数 `_get_sensitive_data_description` を定義する。
	def _get_sensitive_data_description(self, current_page_url) -> str:
		# EN: Assign value to sensitive_data.
		# JP: sensitive_data に値を代入する。
		sensitive_data = self.sensitive_data
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not sensitive_data:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''

		# Collect placeholders for sensitive data
		# EN: Assign annotated value to placeholders.
		# JP: placeholders に型付きの値を代入する。
		placeholders: set[str] = set()

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for key, value in sensitive_data.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(value, dict):
				# New format: {domain: {key: value}}
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if current_page_url and match_url_with_domain_pattern(current_page_url, key, True):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					placeholders.update(value.keys())
			else:
				# Old format: {key: value}
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				placeholders.add(key)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if placeholders:
			# EN: Assign value to placeholder_list.
			# JP: placeholder_list に値を代入する。
			placeholder_list = sorted(list(placeholders))
			# EN: Assign value to info.
			# JP: info に値を代入する。
			info = f'Here are placeholders for sensitive data:\n{placeholder_list}\n'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			info += 'To use them, write <secret>the placeholder name</secret>'
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return info

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

	# EN: Define function `create_state_messages`.
	# JP: 関数 `create_state_messages` を定義する。
	@observe_debug(ignore_input=True, ignore_output=True, name='create_state_messages')
	@time_execution_sync('--create_state_messages')
	def create_state_messages(
		self,
		browser_state_summary: BrowserStateSummary,
		model_output: AgentOutput | None = None,
		result: list[ActionResult] | None = None,
		step_info: AgentStepInfo | None = None,
		use_vision=True,
		page_filtered_actions: str | None = None,
		sensitive_data=None,
		available_file_paths: list[str] | None = None,  # Always pass current available_file_paths
	) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create single state message with all content"""

		# Clear contextual messages from previous steps to prevent accumulation
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.state.history.context_messages.clear()

		# First, update the agent history items with the latest step results
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._update_agent_history_description(model_output, result, step_info)

		# Use the passed sensitive_data parameter, falling back to instance variable
		# EN: Assign value to effective_sensitive_data.
		# JP: effective_sensitive_data に値を代入する。
		effective_sensitive_data = sensitive_data if sensitive_data is not None else self.sensitive_data
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if effective_sensitive_data is not None:
			# Update instance variable to keep it in sync
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.sensitive_data = effective_sensitive_data
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.sensitive_data_description = self._get_sensitive_data_description(browser_state_summary.url)

		# Use only the current screenshot
		# EN: Assign value to screenshots.
		# JP: screenshots に値を代入する。
		screenshots = []
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_state_summary.screenshot:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			screenshots.append(browser_state_summary.screenshot)

		# Create single state message with all content
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert browser_state_summary
		# EN: Assign value to state_message.
		# JP: state_message に値を代入する。
		state_message = AgentMessagePrompt(
			browser_state_summary=browser_state_summary,
			file_system=self.file_system,
			agent_history_description=self.agent_history_description,
			read_state_description=self.state.read_state_description,
			task=self.task,
			include_attributes=self.include_attributes,
			step_info=step_info,
			page_filtered_actions=page_filtered_actions,
			sensitive_data=self.sensitive_data_description,
			available_file_paths=available_file_paths,
			screenshots=screenshots,
			vision_detail_level=self.vision_detail_level,
			include_recent_events=self.include_recent_events,
			sample_images=self.sample_images,
		).get_user_message(use_vision)

		# Set the state message with caching enabled
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._set_message_with_type(state_message, 'state')

	# EN: Define function `_log_history_lines`.
	# JP: 関数 `_log_history_lines` を定義する。
	def _log_history_lines(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Generate a formatted log string of message history for debugging / printing to terminal"""
		# TODO: fix logging

		# try:
		# 	total_input_tokens = 0
		# 	message_lines = []
		# 	terminal_width = shutil.get_terminal_size((80, 20)).columns

		# 	for i, m in enumerate(self.state.history.messages):
		# 		try:
		# 			total_input_tokens += m.metadata.tokens
		# 			is_last_message = i == len(self.state.history.messages) - 1

		# 			# Extract content for logging
		# 			content = _log_extract_message_content(m.message, is_last_message, m.metadata)

		# 			# Format the message line(s)
		# 			lines = _log_format_message_line(m, content, is_last_message, terminal_width)
		# 			message_lines.extend(lines)
		# 		except Exception as e:
		# 			logger.warning(f'Failed to format message {i} for logging: {e}')
		# 			# Add a fallback line for this message
		# 			message_lines.append('❓[   ?]: [Error formatting this message]')

		# 	# Build final log message
		# 	return (
		# 		f'📜 LLM Message history ({len(self.state.history.messages)} messages, {total_input_tokens} tokens):\n'
		# 		+ '\n'.join(message_lines)
		# 	)
		# except Exception as e:
		# 	logger.warning(f'Failed to generate history log: {e}')
		# 	# Return a minimal fallback message
		# 	return f'📜 LLM Message history (error generating log: {e})'

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

	# EN: Define function `get_messages`.
	# JP: 関数 `get_messages` を定義する。
	@time_execution_sync('--get_messages')
	def get_messages(self) -> list[BaseMessage]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get current message list, potentially trimmed to max tokens"""

		# Log message history for debugging
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(self._log_history_lines())
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.last_input_messages = self.state.history.get_messages()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.last_input_messages

	# EN: Define function `_set_message_with_type`.
	# JP: 関数 `_set_message_with_type` を定義する。
	def _set_message_with_type(self, message: BaseMessage, message_type: Literal['system', 'state']) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Replace a specific state message slot with a new message"""
		# Don't filter system and state messages - they should contain placeholder tags or normal conversation
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if message_type == 'system':
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.state.history.system_message = message
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif message_type == 'state':
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.state.history.state_message = message
		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Invalid state message type: {message_type}')

	# EN: Define function `_add_context_message`.
	# JP: 関数 `_add_context_message` を定義する。
	def _add_context_message(self, message: BaseMessage) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Add a contextual message specific to this step (e.g., validation errors, retry instructions, timeout warnings)"""
		# Don't filter context messages - they should contain normal conversation or error messages
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.state.history.context_messages.append(message)

	# EN: Define function `_filter_sensitive_data`.
	# JP: 関数 `_filter_sensitive_data` を定義する。
	@time_execution_sync('--filter_sensitive_data')
	def _filter_sensitive_data(self, message: BaseMessage) -> BaseMessage:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Filter out sensitive data from the message"""

		# EN: Define function `replace_sensitive`.
		# JP: 関数 `replace_sensitive` を定義する。
		def replace_sensitive(value: str) -> str:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.sensitive_data:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return value

			# Collect all sensitive values, immediately converting old format to new format
			# EN: Assign annotated value to sensitive_values.
			# JP: sensitive_values に型付きの値を代入する。
			sensitive_values: dict[str, str] = {}

			# Process all sensitive data entries
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for key_or_domain, content in self.sensitive_data.items():
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(content, dict):
					# Already in new format: {domain: {key: value}}
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for key, val in content.items():
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if val:  # Skip empty values
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							sensitive_values[key] = val
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif content:  # Old format: {key: value} - convert to new format internally
					# We treat this as if it was {'http*://*': {key_or_domain: content}}
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					sensitive_values[key_or_domain] = content

			# If there are no valid sensitive data entries, just return the original value
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not sensitive_values:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.warning('No valid entries found in sensitive_data dictionary')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return value

			# Replace all valid sensitive data values with their placeholder tags
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for key, val in sensitive_values.items():
				# EN: Assign value to value.
				# JP: value に値を代入する。
				value = value.replace(val, f'<secret>{key}</secret>')

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return value

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(message.content, str):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			message.content = replace_sensitive(message.content)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(message.content, list):
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, item in enumerate(message.content):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(item, ContentPartTextParam):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					item.text = replace_sensitive(item.text)
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					message.content[i] = item
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return message

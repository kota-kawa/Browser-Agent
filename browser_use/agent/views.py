# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import traceback
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, Generic, Literal

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai import RateLimitError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model, model_validator
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing_extensions import TypeVar
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.message_manager.views import MessageManagerState
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.scratchpad import Scratchpad
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserStateHistory
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import DEFAULT_INCLUDE_ATTRIBUTES, DOMInteractedElement, DOMSelectorMap

# from browser_use.dom.history_tree_processor.service import (
# 	DOMElementNode,
# 	DOMHistoryElement,
# 	HistoryTreeProcessor,
# )
# from browser_use.dom.views import SelectorMap
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystemState
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tokens.views import UsageSummary
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.registry.views import ActionModel

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define class `AgentSettings`.
# JP: クラス `AgentSettings` を定義する。
class AgentSettings(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Configuration options for the Agent"""

	# EN: Assign annotated value to use_vision.
	# JP: use_vision に型付きの値を代入する。
	use_vision: bool = True
	# EN: Assign annotated value to vision_detail_level.
	# JP: vision_detail_level に型付きの値を代入する。
	vision_detail_level: Literal['auto', 'low', 'high'] = 'auto'
	# EN: Assign annotated value to save_conversation_path.
	# JP: save_conversation_path に型付きの値を代入する。
	save_conversation_path: str | Path | None = None
	# EN: Assign annotated value to save_conversation_path_encoding.
	# JP: save_conversation_path_encoding に型付きの値を代入する。
	save_conversation_path_encoding: str | None = 'utf-8'
	# EN: Assign annotated value to max_failures.
	# JP: max_failures に型付きの値を代入する。
	max_failures: int = 3
	# EN: Assign annotated value to generate_gif.
	# JP: generate_gif に型付きの値を代入する。
	generate_gif: bool | str = False
	# EN: Assign annotated value to override_system_message.
	# JP: override_system_message に型付きの値を代入する。
	override_system_message: str | None = None
	# EN: Assign annotated value to extend_system_message.
	# JP: extend_system_message に型付きの値を代入する。
	extend_system_message: str | None = None
	# EN: Assign annotated value to include_attributes.
	# JP: include_attributes に型付きの値を代入する。
	include_attributes: list[str] | None = DEFAULT_INCLUDE_ATTRIBUTES
	# EN: Assign annotated value to max_actions_per_step.
	# JP: max_actions_per_step に型付きの値を代入する。
	max_actions_per_step: int = 4
	# EN: Assign annotated value to use_thinking.
	# JP: use_thinking に型付きの値を代入する。
	use_thinking: bool = True
	# EN: Assign annotated value to flash_mode.
	# JP: flash_mode に型付きの値を代入する。
	flash_mode: bool = False  # If enabled, disables evaluation_previous_goal and next_goal, and sets use_thinking = False
	# EN: Assign annotated value to max_history_items.
	# JP: max_history_items に型付きの値を代入する。
	max_history_items: int | None = None

	# EN: Assign annotated value to page_extraction_llm.
	# JP: page_extraction_llm に型付きの値を代入する。
	page_extraction_llm: BaseChatModel | None = None
	# EN: Assign annotated value to calculate_cost.
	# JP: calculate_cost に型付きの値を代入する。
	calculate_cost: bool = False
	# EN: Assign annotated value to include_tool_call_examples.
	# JP: include_tool_call_examples に型付きの値を代入する。
	include_tool_call_examples: bool = False
	# EN: Assign annotated value to llm_timeout.
	# JP: llm_timeout に型付きの値を代入する。
	llm_timeout: int = 60  # Timeout in seconds for LLM calls
	# Timeout in seconds for each step. Set to None to disable step-level timeouts entirely.
	# EN: Assign annotated value to step_timeout.
	# JP: step_timeout に型付きの値を代入する。
	step_timeout: int | None = 120
	# EN: Assign annotated value to final_response_after_failure.
	# JP: final_response_after_failure に型付きの値を代入する。
	final_response_after_failure: bool = True  # If True, attempt one final recovery call after max_failures


# EN: Define class `AgentState`.
# JP: クラス `AgentState` を定義する。
class AgentState(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Holds all state information for an Agent"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True)

	# EN: Assign annotated value to agent_id.
	# JP: agent_id に型付きの値を代入する。
	agent_id: str = Field(default_factory=uuid7str)
	# EN: Assign annotated value to n_steps.
	# JP: n_steps に型付きの値を代入する。
	n_steps: int = 1
	# EN: Assign annotated value to step_offset.
	# JP: step_offset に型付きの値を代入する。
	step_offset: int = 0
	# EN: Assign annotated value to consecutive_failures.
	# JP: consecutive_failures に型付きの値を代入する。
	consecutive_failures: int = 0
	# EN: Assign annotated value to last_result.
	# JP: last_result に型付きの値を代入する。
	last_result: list[ActionResult] | None = None
	# EN: Assign annotated value to last_plan.
	# JP: last_plan に型付きの値を代入する。
	last_plan: str | None = None
	# EN: Assign annotated value to last_model_output.
	# JP: last_model_output に型付きの値を代入する。
	last_model_output: AgentOutput | None = None

	# Pause/resume state (kept serialisable for checkpointing)
	# EN: Assign annotated value to paused.
	# JP: paused に型付きの値を代入する。
	paused: bool = False
	# EN: Assign annotated value to stopped.
	# JP: stopped に型付きの値を代入する。
	stopped: bool = False
	# EN: Assign annotated value to session_initialized.
	# JP: session_initialized に型付きの値を代入する。
	session_initialized: bool = False  # Track if session events have been dispatched
	# EN: Assign annotated value to follow_up_task.
	# JP: follow_up_task に型付きの値を代入する。
	follow_up_task: bool = False  # Track if the agent is a follow-up task

	# EN: Assign annotated value to message_manager_state.
	# JP: message_manager_state に型付きの値を代入する。
	message_manager_state: MessageManagerState = Field(default_factory=MessageManagerState)
	# EN: Assign annotated value to file_system_state.
	# JP: file_system_state に型付きの値を代入する。
	file_system_state: FileSystemState | None = None

	# Scratchpad - 外部メモ機能（構造化データの一時保存）
	# EN: Assign annotated value to scratchpad.
	# JP: scratchpad に型付きの値を代入する。
	scratchpad: Scratchpad = Field(default_factory=Scratchpad)


# EN: Define class `AgentStepInfo`.
# JP: クラス `AgentStepInfo` を定義する。
@dataclass
class AgentStepInfo:
	# EN: Assign annotated value to step_number.
	# JP: step_number に型付きの値を代入する。
	step_number: int
	# EN: Assign annotated value to max_steps.
	# JP: max_steps に型付きの値を代入する。
	max_steps: int

	# EN: Define function `is_last_step`.
	# JP: 関数 `is_last_step` を定義する。
	def is_last_step(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if this is the last step"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.step_number >= self.max_steps - 1


# EN: Define class `ActionResult`.
# JP: クラス `ActionResult` を定義する。
class ActionResult(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Result of executing an action"""

	# For done action
	# EN: Assign annotated value to is_done.
	# JP: is_done に型付きの値を代入する。
	is_done: bool | None = False
	# EN: Assign annotated value to success.
	# JP: success に型付きの値を代入する。
	success: bool | None = None

	# Error handling - always include in long term memory
	# EN: Assign annotated value to error.
	# JP: error に型付きの値を代入する。
	error: str | None = None

	# Files
	# EN: Assign annotated value to attachments.
	# JP: attachments に型付きの値を代入する。
	attachments: list[str] | None = None  # Files to display in the done message

	# Always include in long term memory
	# EN: Assign annotated value to long_term_memory.
	# JP: long_term_memory に型付きの値を代入する。
	long_term_memory: str | None = None  # Memory of this action

	# if update_only_read_state is True we add the extracted_content to the agent context only once for the next step
	# if update_only_read_state is False we add the extracted_content to the agent long term memory if no long_term_memory is provided
	# EN: Assign annotated value to extracted_content.
	# JP: extracted_content に型付きの値を代入する。
	extracted_content: str | None = None
	# EN: Assign annotated value to include_extracted_content_only_once.
	# JP: include_extracted_content_only_once に型付きの値を代入する。
	include_extracted_content_only_once: bool = False  # Whether the extracted content should be used to update the read_state

	# Metadata for observability (e.g., click coordinates)
	# EN: Assign annotated value to metadata.
	# JP: metadata に型付きの値を代入する。
	metadata: dict | None = None

	# Deprecated
	# EN: Assign annotated value to include_in_memory.
	# JP: include_in_memory に型付きの値を代入する。
	include_in_memory: bool = False  # whether to include in extracted_content inside long_term_memory

	# EN: Define function `validate_success_requires_done`.
	# JP: 関数 `validate_success_requires_done` を定義する。
	@model_validator(mode='after')
	def validate_success_requires_done(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Ensure success=True can only be set when is_done=True"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.success is True and self.is_done is not True:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(
				'success=True can only be set when is_done=True. '
				'For regular actions that succeed, leave success as None. '
				'Use success=False only for actions that fail.'
			)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self


# EN: Define class `StepMetadata`.
# JP: クラス `StepMetadata` を定義する。
class StepMetadata(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Metadata for a single step including timing and token information"""

	# EN: Assign annotated value to step_start_time.
	# JP: step_start_time に型付きの値を代入する。
	step_start_time: float
	# EN: Assign annotated value to step_end_time.
	# JP: step_end_time に型付きの値を代入する。
	step_end_time: float
	# EN: Assign annotated value to step_number.
	# JP: step_number に型付きの値を代入する。
	step_number: int
	# EN: Assign annotated value to absolute_step_number.
	# JP: absolute_step_number に型付きの値を代入する。
	absolute_step_number: int | None = None

	# EN: Define function `duration_seconds`.
	# JP: 関数 `duration_seconds` を定義する。
	@property
	def duration_seconds(self) -> float:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Calculate step duration in seconds"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.step_end_time - self.step_start_time


# EN: Define class `AgentBrain`.
# JP: クラス `AgentBrain` を定義する。
class AgentBrain(BaseModel):
	# EN: Assign annotated value to thinking.
	# JP: thinking に型付きの値を代入する。
	thinking: str | None = None
	# EN: Assign annotated value to evaluation_previous_goal.
	# JP: evaluation_previous_goal に型付きの値を代入する。
	evaluation_previous_goal: str
	# EN: Assign annotated value to memory.
	# JP: memory に型付きの値を代入する。
	memory: str
	# EN: Assign annotated value to next_goal.
	# JP: next_goal に型付きの値を代入する。
	next_goal: str
	# EN: Assign annotated value to current_status.
	# JP: current_status に型付きの値を代入する。
	current_status: str
	# EN: Assign annotated value to persistent_notes.
	# JP: persistent_notes に型付きの値を代入する。
	persistent_notes: str | None = None


# EN: Define class `AgentOutput`.
# JP: クラス `AgentOutput` を定義する。
class AgentOutput(BaseModel):
	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')

	# EN: Assign annotated value to thinking.
	# JP: thinking に型付きの値を代入する。
	thinking: str | None = None
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
	# EN: Assign annotated value to action.
	# JP: action に型付きの値を代入する。
	action: list[ActionModel] = Field(
		...,
		description='List of actions to execute',
		json_schema_extra={'min_items': 1},  # Ensure at least one action is provided
	)

	# EN: Define function `model_json_schema`.
	# JP: 関数 `model_json_schema` を定義する。
	@classmethod
	def model_json_schema(cls, **kwargs):
		# EN: Assign value to schema.
		# JP: schema に値を代入する。
		schema = super().model_json_schema(**kwargs)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		schema['required'] = ['evaluation_previous_goal', 'memory', 'next_goal', 'current_status', 'action']
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return schema

	# EN: Define function `current_state`.
	# JP: 関数 `current_state` を定義する。
	@property
	def current_state(self) -> AgentBrain:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""For backward compatibility - returns an AgentBrain with the flattened properties"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return AgentBrain(
			thinking=self.thinking,
			evaluation_previous_goal=self.evaluation_previous_goal if self.evaluation_previous_goal else '',
			memory=self.memory if self.memory else '',
			next_goal=self.next_goal if self.next_goal else '',
			current_status=self.current_status if self.current_status else '',
			persistent_notes=self.persistent_notes,
		)

	# EN: Define function `type_with_custom_actions`.
	# JP: 関数 `type_with_custom_actions` を定義する。
	@staticmethod
	def type_with_custom_actions(custom_actions: type[ActionModel]) -> type[AgentOutput]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extend actions with custom actions"""

		# EN: Assign value to model_.
		# JP: model_ に値を代入する。
		model_ = create_model(
			'AgentOutput',
			__base__=AgentOutput,
			action=(
				list[custom_actions],  # type: ignore
				Field(..., description='List of actions to execute', json_schema_extra={'min_items': 1}),
			),
			__module__=AgentOutput.__module__,
		)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		model_.__doc__ = 'AgentOutput model with custom actions'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return model_

	# EN: Define function `type_with_custom_actions_no_thinking`.
	# JP: 関数 `type_with_custom_actions_no_thinking` を定義する。
	@staticmethod
	def type_with_custom_actions_no_thinking(custom_actions: type[ActionModel]) -> type[AgentOutput]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extend actions with custom actions and exclude thinking field"""

		# EN: Define class `AgentOutputNoThinking`.
		# JP: クラス `AgentOutputNoThinking` を定義する。
		class AgentOutputNoThinking(AgentOutput):
			# EN: Define function `model_json_schema`.
			# JP: 関数 `model_json_schema` を定義する。
			@classmethod
			def model_json_schema(cls, **kwargs):
				# EN: Assign value to schema.
				# JP: schema に値を代入する。
				schema = super().model_json_schema(**kwargs)
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del schema['properties']['thinking']
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				schema['required'] = ['evaluation_previous_goal', 'memory', 'next_goal', 'current_status', 'action']
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return schema

		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = create_model(
			'AgentOutput',
			__base__=AgentOutputNoThinking,
			action=(
				list[custom_actions],  # type: ignore
				Field(..., description='List of actions to execute', json_schema_extra={'min_items': 1}),
			),
			__module__=AgentOutputNoThinking.__module__,
		)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		model.__doc__ = 'AgentOutput model with custom actions'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return model

	# EN: Define function `type_with_custom_actions_flash_mode`.
	# JP: 関数 `type_with_custom_actions_flash_mode` を定義する。
	@staticmethod
	def type_with_custom_actions_flash_mode(custom_actions: type[ActionModel]) -> type[AgentOutput]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extend actions with custom actions for flash mode - memory and action fields only"""

		# EN: Define class `AgentOutputFlashMode`.
		# JP: クラス `AgentOutputFlashMode` を定義する。
		class AgentOutputFlashMode(AgentOutput):
			# EN: Define function `model_json_schema`.
			# JP: 関数 `model_json_schema` を定義する。
			@classmethod
			def model_json_schema(cls, **kwargs):
				# EN: Assign value to schema.
				# JP: schema に値を代入する。
				schema = super().model_json_schema(**kwargs)
				# Remove thinking, evaluation_previous_goal, and next_goal fields
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del schema['properties']['thinking']
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del schema['properties']['evaluation_previous_goal']
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del schema['properties']['next_goal']
				# Update required fields to only include remaining properties
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				schema['required'] = ['memory', 'action']
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return schema

		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = create_model(
			'AgentOutput',
			__base__=AgentOutputFlashMode,
			action=(
				list[custom_actions],  # type: ignore
				Field(..., description='List of actions to execute', json_schema_extra={'min_items': 1}),
			),
			__module__=AgentOutputFlashMode.__module__,
		)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		model.__doc__ = 'AgentOutput model with custom actions'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return model


# EN: Define class `AgentHistory`.
# JP: クラス `AgentHistory` を定義する。
class AgentHistory(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""History item for agent actions"""

	# EN: Assign annotated value to model_output.
	# JP: model_output に型付きの値を代入する。
	model_output: AgentOutput | None
	# EN: Assign annotated value to result.
	# JP: result に型付きの値を代入する。
	result: list[ActionResult]
	# EN: Assign annotated value to state.
	# JP: state に型付きの値を代入する。
	state: BrowserStateHistory
	# EN: Assign annotated value to metadata.
	# JP: metadata に型付きの値を代入する。
	metadata: StepMetadata | None = None

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())

	# EN: Define function `get_interacted_element`.
	# JP: 関数 `get_interacted_element` を定義する。
	@staticmethod
	def get_interacted_element(model_output: AgentOutput, selector_map: DOMSelectorMap) -> list[DOMInteractedElement | None]:
		# EN: Assign value to elements.
		# JP: elements に値を代入する。
		elements = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for action in model_output.action:
			# EN: Assign value to index.
			# JP: index に値を代入する。
			index = action.get_index()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if index is not None and index in selector_map:
				# EN: Assign value to el.
				# JP: el に値を代入する。
				el = selector_map[index]
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				elements.append(DOMInteractedElement.load_from_enhanced_dom_tree(el))
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				elements.append(None)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return elements

	# EN: Define function `_filter_sensitive_data_from_string`.
	# JP: 関数 `_filter_sensitive_data_from_string` を定義する。
	def _filter_sensitive_data_from_string(self, value: str, sensitive_data: dict[str, str | dict[str, str]] | None) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Filter out sensitive data from a string value"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not sensitive_data:
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
		for key_or_domain, content in sensitive_data.items():
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

	# EN: Define function `_filter_sensitive_data_from_dict`.
	# JP: 関数 `_filter_sensitive_data_from_dict` を定義する。
	def _filter_sensitive_data_from_dict(
		self, data: dict[str, Any], sensitive_data: dict[str, str | dict[str, str]] | None
	) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Recursively filter sensitive data from a dictionary"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not sensitive_data:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return data

		# EN: Assign value to filtered_data.
		# JP: filtered_data に値を代入する。
		filtered_data = {}
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for key, value in data.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(value, str):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				filtered_data[key] = self._filter_sensitive_data_from_string(value, sensitive_data)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(value, dict):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				filtered_data[key] = self._filter_sensitive_data_from_dict(value, sensitive_data)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(value, list):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				filtered_data[key] = [
					self._filter_sensitive_data_from_string(item, sensitive_data)
					if isinstance(item, str)
					else self._filter_sensitive_data_from_dict(item, sensitive_data)
					if isinstance(item, dict)
					else item
					for item in value
				]
			else:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				filtered_data[key] = value
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return filtered_data

	# EN: Define function `model_dump`.
	# JP: 関数 `model_dump` を定義する。
	def model_dump(self, sensitive_data: dict[str, str | dict[str, str]] | None = None, **kwargs) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Custom serialization handling circular references and filtering sensitive data"""

		# Handle action serialization
		# EN: Assign value to model_output_dump.
		# JP: model_output_dump に値を代入する。
		model_output_dump = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.model_output:
			# EN: Assign value to action_dump.
			# JP: action_dump に値を代入する。
			action_dump = [action.model_dump(exclude_none=True) for action in self.model_output.action]

			# Filter sensitive data only from input_text action parameters if sensitive_data is provided
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if sensitive_data:
				# EN: Assign value to action_dump.
				# JP: action_dump に値を代入する。
				action_dump = [
					self._filter_sensitive_data_from_dict(action, sensitive_data)
					if action.get('name') == 'input_text'
					else action
					for action in action_dump
				]

			# EN: Assign value to model_output_dump.
			# JP: model_output_dump に値を代入する。
			model_output_dump = {
				'evaluation_previous_goal': self.model_output.evaluation_previous_goal,
				'memory': self.model_output.memory,
				'next_goal': self.model_output.next_goal,
				'action': action_dump,  # This preserves the actual action data
			}
			# Only include thinking if it's present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.model_output.thinking is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_output_dump['thinking'] = self.model_output.thinking
			# Only include persistent_notes if it's present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.model_output.persistent_notes is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_output_dump['persistent_notes'] = self.model_output.persistent_notes

		# Handle result serialization - don't filter ActionResult data
		# as it should contain meaningful information for the agent
		# EN: Assign value to result_dump.
		# JP: result_dump に値を代入する。
		result_dump = [r.model_dump(exclude_none=True) for r in self.result]

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'model_output': model_output_dump,
			'result': result_dump,
			'state': self.state.to_dict(),
			'metadata': self.metadata.model_dump() if self.metadata else None,
		}


# EN: Assign value to AgentStructuredOutput.
# JP: AgentStructuredOutput に値を代入する。
AgentStructuredOutput = TypeVar('AgentStructuredOutput', bound=BaseModel)


# EN: Define class `AgentHistoryList`.
# JP: クラス `AgentHistoryList` を定義する。
class AgentHistoryList(BaseModel, Generic[AgentStructuredOutput]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""List of AgentHistory messages, i.e. the history of the agent's actions and thoughts."""

	# EN: Assign annotated value to history.
	# JP: history に型付きの値を代入する。
	history: list[AgentHistory]
	# EN: Assign annotated value to usage.
	# JP: usage に型付きの値を代入する。
	usage: UsageSummary | None = None

	# EN: Assign annotated value to _output_model_schema.
	# JP: _output_model_schema に型付きの値を代入する。
	_output_model_schema: type[AgentStructuredOutput] | None = None

	# EN: Define function `total_duration_seconds`.
	# JP: 関数 `total_duration_seconds` を定義する。
	def total_duration_seconds(self) -> float:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get total duration of all steps in seconds"""
		# EN: Assign value to total.
		# JP: total に値を代入する。
		total = 0.0
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for h in self.history:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if h.metadata:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				total += h.metadata.duration_seconds
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return total

	# EN: Define function `__len__`.
	# JP: 関数 `__len__` を定義する。
	def __len__(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return the number of history items"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return len(self.history)

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Representation of the AgentHistoryList object"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'AgentHistoryList(all_results={self.action_results()}, all_model_outputs={self.model_actions()})'

	# EN: Define function `add_item`.
	# JP: 関数 `add_item` を定義する。
	def add_item(self, history_item: AgentHistory) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Add a history item to the list"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.history.append(history_item)

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Representation of the AgentHistoryList object"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.__str__()

	# EN: Define function `save_to_file`.
	# JP: 関数 `save_to_file` を定義する。
	def save_to_file(self, filepath: str | Path, sensitive_data: dict[str, str | dict[str, str]] | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Save history to JSON file with proper serialization and optional sensitive data filtering"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			Path(filepath).parent.mkdir(parents=True, exist_ok=True)
			# EN: Assign value to data.
			# JP: data に値を代入する。
			data = self.model_dump(sensitive_data=sensitive_data)
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with open(filepath, 'w', encoding='utf-8') as f:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				json.dump(data, f, indent=2)
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise e

	# def save_as_playwright_script(
	# 	self,
	# 	output_path: str | Path,
	# 	sensitive_data_keys: list[str] | None = None,
	# 	browser_config: BrowserConfig | None = None,
	# 	context_config: BrowserContextConfig | None = None,
	# ) -> None:
	# 	"""
	# 	Generates a Playwright script based on the agent's history and saves it to a file.
	# 	Args:
	# 		output_path: The path where the generated Python script will be saved.
	# 		sensitive_data_keys: A list of keys used as placeholders for sensitive data
	# 							 (e.g., ['username_placeholder', 'password_placeholder']).
	# 							 These will be loaded from environment variables in the
	# 							 generated script.
	# 		browser_config: Configuration of the original Browser instance.
	# 		context_config: Configuration of the original BrowserContext instance.
	# 	"""
	# 	from browser_use.agent.playwright_script_generator import PlaywrightScriptGenerator

	# 	try:
	# 		serialized_history = self.model_dump()['history']
	# 		generator = PlaywrightScriptGenerator(serialized_history, sensitive_data_keys, browser_config, context_config)

	# 		script_content = generator.generate_script_content()
	# 		path_obj = Path(output_path)
	# 		path_obj.parent.mkdir(parents=True, exist_ok=True)
	# 		with open(path_obj, 'w', encoding='utf-8') as f:
	# 			f.write(script_content)
	# 	except Exception as e:
	# 		raise e

	# EN: Define function `model_dump`.
	# JP: 関数 `model_dump` を定義する。
	def model_dump(self, **kwargs) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Custom serialization that properly uses AgentHistory's model_dump"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'history': [h.model_dump(**kwargs) for h in self.history],
		}

	# EN: Define function `load_from_file`.
	# JP: 関数 `load_from_file` を定義する。
	@classmethod
	def load_from_file(cls, filepath: str | Path, output_model: type[AgentOutput]) -> AgentHistoryList:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load history from JSON file"""
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(filepath, encoding='utf-8') as f:
			# EN: Assign value to data.
			# JP: data に値を代入する。
			data = json.load(f)
		# loop through history and validate output_model actions to enrich with custom actions
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for h in data['history']:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if h['model_output']:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(h['model_output'], dict):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					h['model_output'] = output_model.model_validate(h['model_output'])
				else:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					h['model_output'] = None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'interacted_element' not in h['state']:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				h['state']['interacted_element'] = None
		# EN: Assign value to history.
		# JP: history に値を代入する。
		history = cls.model_validate(data)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return history

	# EN: Define function `last_action`.
	# JP: 関数 `last_action` を定義する。
	def last_action(self) -> None | dict:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Last action in history"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history and self.history[-1].model_output:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.history[-1].model_output.action[-1].model_dump(exclude_none=True)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `errors`.
	# JP: 関数 `errors` を定義する。
	def errors(self) -> list[str | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all errors from history, with None for steps without errors"""
		# EN: Assign value to errors.
		# JP: errors に値を代入する。
		errors = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for h in self.history:
			# EN: Assign value to step_errors.
			# JP: step_errors に値を代入する。
			step_errors = [r.error for r in h.result if r.error]

			# each step can have only one error
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			errors.append(step_errors[0] if step_errors else None)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return errors

	# EN: Define function `final_result`.
	# JP: 関数 `final_result` を定義する。
	def final_result(self) -> None | str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Final result from history"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history and len(self.history[-1].result) > 0 and self.history[-1].result[-1].extracted_content:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.history[-1].result[-1].extracted_content
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `is_done`.
	# JP: 関数 `is_done` を定義する。
	def is_done(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the agent is done"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history and len(self.history[-1].result) > 0:
			# EN: Assign value to last_result.
			# JP: last_result に値を代入する。
			last_result = self.history[-1].result[-1]
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return last_result.is_done is True
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `is_successful`.
	# JP: 関数 `is_successful` を定義する。
	def is_successful(self) -> bool | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the agent completed successfully - the agent decides in the last step if it was successful or not. None if not done yet."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history and len(self.history[-1].result) > 0:
			# EN: Assign value to last_result.
			# JP: last_result に値を代入する。
			last_result = self.history[-1].result[-1]
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if last_result.is_done is True:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return last_result.success if last_result.success is not None else True
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `has_errors`.
	# JP: 関数 `has_errors` を定義する。
	def has_errors(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the agent has any non-None errors"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return any(error is not None for error in self.errors())

	# EN: Define function `urls`.
	# JP: 関数 `urls` を定義する。
	def urls(self) -> list[str | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all unique URLs from history"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [h.state.url if h.state.url is not None else None for h in self.history]

	# EN: Define function `screenshot_paths`.
	# JP: 関数 `screenshot_paths` を定義する。
	def screenshot_paths(self, n_last: int | None = None, return_none_if_not_screenshot: bool = True) -> list[str | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all screenshot paths from history"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if n_last == 0:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if n_last is None:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if return_none_if_not_screenshot:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [h.state.screenshot_path if h.state.screenshot_path is not None else None for h in self.history]
			else:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [h.state.screenshot_path for h in self.history if h.state.screenshot_path is not None]
		else:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if return_none_if_not_screenshot:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [h.state.screenshot_path if h.state.screenshot_path is not None else None for h in self.history[-n_last:]]
			else:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [h.state.screenshot_path for h in self.history[-n_last:] if h.state.screenshot_path is not None]

	# EN: Define function `screenshots`.
	# JP: 関数 `screenshots` を定義する。
	def screenshots(self, n_last: int | None = None, return_none_if_not_screenshot: bool = True) -> list[str | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all screenshots from history as base64 strings"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if n_last == 0:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []

		# EN: Assign value to history_items.
		# JP: history_items に値を代入する。
		history_items = self.history if n_last is None else self.history[-n_last:]
		# EN: Assign value to screenshots.
		# JP: screenshots に値を代入する。
		screenshots = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for item in history_items:
			# EN: Assign value to screenshot_b64.
			# JP: screenshot_b64 に値を代入する。
			screenshot_b64 = item.state.get_screenshot()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if screenshot_b64:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				screenshots.append(screenshot_b64)
			else:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if return_none_if_not_screenshot:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					screenshots.append(None)
				# If return_none_if_not_screenshot is False, we skip None values

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return screenshots

	# EN: Define function `action_names`.
	# JP: 関数 `action_names` を定義する。
	def action_names(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all action names from history"""
		# EN: Assign value to action_names.
		# JP: action_names に値を代入する。
		action_names = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for action in self.model_actions():
			# EN: Assign value to actions.
			# JP: actions に値を代入する。
			actions = list(action.keys())
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if actions:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				action_names.append(actions[0])
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return action_names

	# EN: Define function `model_thoughts`.
	# JP: 関数 `model_thoughts` を定義する。
	def model_thoughts(self) -> list[AgentBrain]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all thoughts from history"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [h.model_output.current_state for h in self.history if h.model_output]

	# EN: Define function `model_outputs`.
	# JP: 関数 `model_outputs` を定義する。
	def model_outputs(self) -> list[AgentOutput]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all model outputs from history"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [h.model_output for h in self.history if h.model_output]

	# get all actions with params
	# EN: Define function `model_actions`.
	# JP: 関数 `model_actions` を定義する。
	def model_actions(self) -> list[dict]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all actions from history"""
		# EN: Assign value to outputs.
		# JP: outputs に値を代入する。
		outputs = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for h in self.history:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if h.model_output:
				# Guard against None interacted_element before zipping
				# EN: Assign value to interacted_elements.
				# JP: interacted_elements に値を代入する。
				interacted_elements = h.state.interacted_element or [None] * len(h.model_output.action)
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for action, interacted_element in zip(h.model_output.action, interacted_elements):
					# EN: Assign value to output.
					# JP: output に値を代入する。
					output = action.model_dump(exclude_none=True)
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					output['interacted_element'] = interacted_element
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					outputs.append(output)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return outputs

	# EN: Define function `action_history`.
	# JP: 関数 `action_history` を定義する。
	def action_history(self) -> list[list[dict]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get truncated action history with only essential fields"""
		# EN: Assign value to step_outputs.
		# JP: step_outputs に値を代入する。
		step_outputs = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for h in self.history:
			# EN: Assign value to step_actions.
			# JP: step_actions に値を代入する。
			step_actions = []
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if h.model_output:
				# Guard against None interacted_element before zipping
				# EN: Assign value to interacted_elements.
				# JP: interacted_elements に値を代入する。
				interacted_elements = h.state.interacted_element or [None] * len(h.model_output.action)
				# Zip actions with interacted elements and results
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for action, interacted_element, result in zip(h.model_output.action, interacted_elements, h.result):
					# EN: Assign value to action_output.
					# JP: action_output に値を代入する。
					action_output = action.model_dump(exclude_none=True)
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					action_output['interacted_element'] = interacted_element
					# Only keep long_term_memory from result
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					action_output['result'] = result.long_term_memory if result and result.long_term_memory else None
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					step_actions.append(action_output)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			step_outputs.append(step_actions)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return step_outputs

	# EN: Define function `action_results`.
	# JP: 関数 `action_results` を定義する。
	def action_results(self) -> list[ActionResult]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all results from history"""
		# EN: Assign value to results.
		# JP: results に値を代入する。
		results = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for h in self.history:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			results.extend([r for r in h.result if r])
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return results

	# EN: Define function `extracted_content`.
	# JP: 関数 `extracted_content` を定義する。
	def extracted_content(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all extracted content from history"""
		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for h in self.history:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			content.extend([r.extracted_content for r in h.result if r.extracted_content])
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return content

	# EN: Define function `model_actions_filtered`.
	# JP: 関数 `model_actions_filtered` を定義する。
	def model_actions_filtered(self, include: list[str] | None = None) -> list[dict]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all model actions from history as JSON"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if include is None:
			# EN: Assign value to include.
			# JP: include に値を代入する。
			include = []
		# EN: Assign value to outputs.
		# JP: outputs に値を代入する。
		outputs = self.model_actions()
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for o in outputs:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i in include:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if i == list(o.keys())[0]:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					result.append(o)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result

	# EN: Define function `number_of_steps`.
	# JP: 関数 `number_of_steps` を定義する。
	def number_of_steps(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the number of steps in the history"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return len(self.history)

	# EN: Define function `structured_output`.
	# JP: 関数 `structured_output` を定義する。
	@property
	def structured_output(self) -> AgentStructuredOutput | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the structured output from the history

		Returns:
			The structured output if both final_result and _output_model_schema are available,
			otherwise None
		"""
		# EN: Assign value to final_result.
		# JP: final_result に値を代入する。
		final_result = self.final_result()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if final_result is not None and self._output_model_schema is not None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._output_model_schema.model_validate_json(final_result)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None


# EN: Define class `AgentError`.
# JP: クラス `AgentError` を定義する。
class AgentError:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Container for agent error handling"""

	# EN: Assign value to VALIDATION_ERROR.
	# JP: VALIDATION_ERROR に値を代入する。
	VALIDATION_ERROR = 'Invalid model output format. Please follow the correct schema.'
	# EN: Assign value to RATE_LIMIT_ERROR.
	# JP: RATE_LIMIT_ERROR に値を代入する。
	RATE_LIMIT_ERROR = 'Rate limit reached. Waiting before retry.'
	# EN: Assign value to NO_VALID_ACTION.
	# JP: NO_VALID_ACTION に値を代入する。
	NO_VALID_ACTION = 'No valid action found'

	# EN: Define function `format_error`.
	# JP: 関数 `format_error` を定義する。
	@staticmethod
	def format_error(error: Exception, include_trace: bool = False) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Format error message based on error type and optionally include trace"""
		# EN: Assign value to message.
		# JP: message に値を代入する。
		message = ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(error, ValidationError):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'{AgentError.VALIDATION_ERROR}\nDetails: {str(error)}'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(error, RateLimitError):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return AgentError.RATE_LIMIT_ERROR
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if include_trace:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'{str(error)}\nStacktrace:\n{traceback.format_exc()}'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'{str(error)}'

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import gc
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import inspect
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import tempfile
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Awaitable, Callable
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, ClassVar, Generic, Literal, TypeVar
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.parse import urlparse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import EventBus

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.cloud_events import (
	CreateAgentOutputFileEvent,
	CreateAgentSessionEvent,
	CreateAgentStepEvent,
	CreateAgentTaskEvent,
	UpdateAgentTaskEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.eventbus import EventBusFactory
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.message_manager.utils import save_conversation
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.env_loader import load_secrets_env
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.google.chat import ChatGoogle
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage, ContentPartImageParam, ContentPartTextParam, UserMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tokens.service import TokenCost

# EN: Evaluate an expression.
# JP: 式を評価する。
load_secrets_env()

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, ValidationError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use import Browser, BrowserProfile, BrowserSession

# Lazy import for gif to avoid heavy agent.views import at startup
# from browser_use.agent.gif import create_history_gif
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.message_manager.service import (
	MessageManager,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.prompts import SystemPrompt
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import (
	ActionResult,
	AgentError,
	AgentHistory,
	AgentHistoryList,
	AgentOutput,
	AgentSettings,
	AgentState,
	AgentStepInfo,
	AgentStructuredOutput,
	BrowserStateHistory,
	StepMetadata,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.constants import DEFAULT_NEW_TAB_URL
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.session import DEFAULT_BROWSER_PROFILE
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import PLACEHOLDER_4PX_SCREENSHOT, BrowserStateSummary
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import DOMInteractedElement
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystem
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe, observe_debug
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.sync import CloudSync
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.telemetry.service import ProductTelemetry
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.telemetry.views import AgentTelemetryEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.registry.views import ActionModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.service import Tools
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import (
	URL_PATTERN,
	_log_pretty_path,
	get_browser_use_version,
	get_git_info,
	time_execution_async,
	time_execution_sync,
)

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define function `log_response`.
# JP: 関数 `log_response` を定義する。
def log_response(response: AgentOutput, registry=None, logger=None) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Utility function to log the model's response."""

	# Use module logger if no logger provided
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if logger is None:
		# EN: Assign value to logger.
		# JP: logger に値を代入する。
		logger = logging.getLogger(__name__)

	# Only log thinking if it's present
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if response.current_state.thinking:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'💡 Thinking:\n{response.current_state.thinking}')

	# Only log evaluation if it's not empty
	# EN: Assign value to eval_goal.
	# JP: eval_goal に値を代入する。
	eval_goal = response.current_state.evaluation_previous_goal
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if eval_goal:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'success' in eval_goal.lower():
			# EN: Assign value to emoji.
			# JP: emoji に値を代入する。
			emoji = '👍'
			# Green color for success
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'  \033[32m{emoji} Eval: {eval_goal}\033[0m')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif 'failure' in eval_goal.lower():
			# EN: Assign value to emoji.
			# JP: emoji に値を代入する。
			emoji = '⚠️'
			# Red color for failure
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'  \033[31m{emoji} Eval: {eval_goal}\033[0m')
		else:
			# EN: Assign value to emoji.
			# JP: emoji に値を代入する。
			emoji = '❔'
			# No color for unknown/neutral
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'  {emoji} Eval: {eval_goal}')

	# Always log memory if present
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if response.current_state.memory:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'🧠 Memory: {response.current_state.memory}')

	# Only log next goal if it's not empty
	# EN: Assign value to next_goal.
	# JP: next_goal に値を代入する。
	next_goal = response.current_state.next_goal
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if next_goal:
		# Blue color for next goal
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'  \033[34m🎯 Next goal: {next_goal}\033[0m')
	else:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info('')  # Add empty line for spacing


# EN: Assign value to Context.
# JP: Context に値を代入する。
Context = TypeVar('Context')


# EN: Assign value to AgentHookFunc.
# JP: AgentHookFunc に値を代入する。
AgentHookFunc = Callable[['Agent'], Awaitable[None]]


# EN: Define class `Agent`.
# JP: クラス `Agent` を定義する。
class Agent(Generic[Context, AgentStructuredOutput]):
	# EN: Assign annotated value to _WATCHDOG_ATTR_NAMES.
	# JP: _WATCHDOG_ATTR_NAMES に型付きの値を代入する。
	_WATCHDOG_ATTR_NAMES: ClassVar[tuple[str, ...]] = (
		'_downloads_watchdog',
		'_storage_state_watchdog',
		'_local_browser_watchdog',
		'_security_watchdog',
		'_aboutblank_watchdog',
		'_popups_watchdog',
		'_permissions_watchdog',
		'_default_action_watchdog',
		'_screenshot_watchdog',
		'_dom_watchdog',
		'_recording_watchdog',
		'_crash_watchdog',
	)

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	@time_execution_sync('--init')
	def __init__(
		self,
		task: str,
		llm: BaseChatModel | None = None,
		# Optional parameters
		browser_profile: BrowserProfile | None = None,
		browser_session: BrowserSession | None = None,
		browser: Browser | None = None,  # Alias for browser_session
		tools: Tools[Context] | None = None,
		controller: Tools[Context] | None = None,  # Alias for tools
		# Initial agent run parameters
		sensitive_data: dict[str, str | dict[str, str]] | None = None,
		initial_actions: list[dict[str, dict[str, Any]]] | None = None,
		# Cloud Callbacks
		register_new_step_callback: (
			Callable[['BrowserStateSummary', 'AgentOutput', int], None]  # Sync callback
			| Callable[['BrowserStateSummary', 'AgentOutput', int], Awaitable[None]]  # Async callback
			| None
		) = None,
		register_done_callback: (
			Callable[['AgentHistoryList'], Awaitable[None]]  # Async Callback
			| Callable[['AgentHistoryList'], None]  # Sync Callback
			| None
		) = None,
		register_external_agent_status_raise_error_callback: Callable[[], Awaitable[bool]] | None = None,
		# Agent settings
		output_model_schema: type[AgentStructuredOutput] | None = None,
		use_vision: bool = True,
		save_conversation_path: str | Path | None = None,
		save_conversation_path_encoding: str | None = 'utf-8',
		max_failures: int = 3,
		override_system_message: str | None = None,
		extend_system_message: str | None = None,
		generate_gif: bool | str = False,
		available_file_paths: list[str] | None = None,
		include_attributes: list[str] | None = None,
		max_actions_per_step: int = 10,
		use_thinking: bool = True,
		flash_mode: bool = False,
		max_history_items: int | None = None,
		page_extraction_llm: BaseChatModel | None = None,
		injected_agent_state: AgentState | None = None,
		source: str | None = None,
		file_system_path: str | None = None,
		task_id: str | None = None,
		cloud_sync: CloudSync | None = None,
		calculate_cost: bool = False,
		display_files_in_done_text: bool = True,
		include_tool_call_examples: bool = False,
		vision_detail_level: Literal['auto', 'low', 'high'] = 'auto',
		llm_timeout: int = 90,
		step_timeout: int | None = 120,
		directly_open_url: bool = True,
		include_recent_events: bool = False,
		sample_images: list[ContentPartTextParam | ContentPartImageParam] | None = None,
		final_response_after_failure: bool = True,
		_url_shortening_limit: int = 25,
		**kwargs,
	):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if llm is None:
			# EN: Assign value to default_llm_name.
			# JP: default_llm_name に値を代入する。
			default_llm_name = CONFIG.DEFAULT_LLM
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if default_llm_name:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Import required modules.
					# JP: 必要なモジュールをインポートする。
					from browser_use.llm.models import get_llm_by_name

					# EN: Assign value to llm.
					# JP: llm に値を代入する。
					llm = get_llm_by_name(default_llm_name)
				except (ImportError, ValueError) as e:
					# Use the logger that's already imported at the top of the module
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.warning(
						f'Failed to create default LLM "{default_llm_name}": {e}. '
						'Falling back to ChatGoogle(model="gemini-2.5-flash")'
					)
					# EN: Assign value to llm.
					# JP: llm に値を代入する。
					llm = ChatGoogle(model='gemini-2.5-flash')
			else:
				# No default LLM specified, use the Gemini flash model
				# EN: Assign value to llm.
				# JP: llm に値を代入する。
				llm = ChatGoogle(model='gemini-2.5-flash')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if page_extraction_llm is None:
			# EN: Assign value to page_extraction_llm.
			# JP: page_extraction_llm に値を代入する。
			page_extraction_llm = llm
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if available_file_paths is None:
			# EN: Assign value to available_file_paths.
			# JP: available_file_paths に値を代入する。
			available_file_paths = []

		# EN: Assign value to raw_task_id.
		# JP: raw_task_id に値を代入する。
		raw_task_id = task_id or uuid7str()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.original_task_id: str = str(raw_task_id)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.id = self._normalise_identifier(self.original_task_id)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.id != self.original_task_id:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(
				'Normalised agent task identifier from %r to %s to satisfy identifier safety checks',
				self.original_task_id,
				self.id,
			)
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.task_id: str = self.id
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.session_id: str = uuid7str()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.running: bool = False
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._pending_eventbus_refresh: bool = False
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.last_response_time: float = 0.0
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._reserved_eventbus_name: str | None = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._eventbus_cleanup_tasks: set[asyncio.Task[None]] = set()

		# EN: Assign value to browser_profile.
		# JP: browser_profile に値を代入する。
		browser_profile = browser_profile or DEFAULT_BROWSER_PROFILE

		# Handle browser vs browser_session parameter (browser takes precedence)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser and browser_session:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError('Cannot specify both "browser" and "browser_session" parameters. Use "browser" for the cleaner API.')
		# EN: Assign value to browser_session.
		# JP: browser_session に値を代入する。
		browser_session = browser or browser_session

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.browser_session = browser_session or BrowserSession(
			browser_profile=browser_profile,
			id=uuid7str()[:-4] + self.id[-4:],  # re-use the same 4-char suffix so they show up together in logs
		)

		# Initialize available file paths as direct attribute
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.available_file_paths = available_file_paths

		# Core components
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.task = task
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.llm = llm
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.directly_open_url = directly_open_url
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.include_recent_events = include_recent_events
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._url_shortening_limit = _url_shortening_limit
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tools is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.tools = tools
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif controller is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.tools = controller
		else:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.tools = Tools(display_files_in_done_text=display_files_in_done_text)

		# Structured output
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.output_model_schema = output_model_schema
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.output_model_schema is not None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.tools.use_structured_output_action(self.output_model_schema)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.sensitive_data = sensitive_data

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.sample_images = sample_images

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.settings = AgentSettings(
			use_vision=use_vision,
			vision_detail_level=vision_detail_level,
			save_conversation_path=save_conversation_path,
			save_conversation_path_encoding=save_conversation_path_encoding,
			max_failures=max_failures,
			override_system_message=override_system_message,
			extend_system_message=extend_system_message,
			generate_gif=generate_gif,
			include_attributes=include_attributes,
			max_actions_per_step=max_actions_per_step,
			use_thinking=use_thinking,
			flash_mode=flash_mode,
			max_history_items=max_history_items,
			page_extraction_llm=page_extraction_llm,
			calculate_cost=calculate_cost,
			include_tool_call_examples=include_tool_call_examples,
			llm_timeout=llm_timeout,
			step_timeout=step_timeout,
			final_response_after_failure=final_response_after_failure,
		)

		# Token cost service
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.token_cost_service = TokenCost(include_cost=calculate_cost)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.token_cost_service.register_llm(llm)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.token_cost_service.register_llm(page_extraction_llm)

		# Initialize state
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state = injected_agent_state or AgentState()

		# Initialize history
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.history = AgentHistoryList(history=[], usage=None)

		# Initialize agent directory
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import time

		# EN: Assign value to timestamp.
		# JP: timestamp に値を代入する。
		timestamp = int(time.time())
		# EN: Assign value to base_tmp.
		# JP: base_tmp に値を代入する。
		base_tmp = Path(tempfile.gettempdir())
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.agent_directory = base_tmp / f'browser_use_agent_{self.id}_{timestamp}'

		# Initialize file system and screenshot service
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._set_file_system(file_system_path)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._set_screenshot_service()

		# Action setup
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._setup_action_models()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._set_browser_use_version_and_source(source)

		# EN: Assign value to initial_url.
		# JP: initial_url に値を代入する。
		initial_url = None

		# only load url if no initial actions are provided
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.state.follow_up_task and not initial_actions:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.directly_open_url:
				# EN: Assign value to initial_url.
				# JP: initial_url に値を代入する。
				initial_url = self._extract_url_from_task(self.task)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if initial_url:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.info(f'🔗 Found URL in task: {initial_url}, adding as initial action...')
					# EN: Assign value to initial_actions.
					# JP: initial_actions に値を代入する。
					initial_actions = [{'go_to_url': {'url': initial_url, 'new_tab': False}}]
				else:
					# EN: Assign value to initial_url.
					# JP: initial_url に値を代入する。
					initial_url = DEFAULT_NEW_TAB_URL
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.info('🌐 No URL found in task, starting from https://www.yahoo.co.jp by default...')
					# EN: Assign value to initial_actions.
					# JP: initial_actions に値を代入する。
					initial_actions = [{'go_to_url': {'url': initial_url, 'new_tab': False}}]

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.initial_url = initial_url

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.initial_actions = self._convert_initial_actions(initial_actions) if initial_actions else None
		# Verify we can connect to the model
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._verify_and_setup_llm()

		# TODO: move this logic to the LLMs
		# Handle users trying to use use_vision=True with DeepSeek models
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'deepseek' in self.llm.model.lower():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('⚠️ DeepSeek models do not support use_vision=True yet. Setting use_vision=False for now...')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.settings.use_vision = False

		# Handle users trying to use use_vision=True with XAI models
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'grok' in self.llm.model.lower():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('⚠️ XAI models do not support use_vision=True yet. Setting use_vision=False for now...')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.settings.use_vision = False

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(
			f'{" +vision" if self.settings.use_vision else ""}'
			f' extraction_model={self.settings.page_extraction_llm.model if self.settings.page_extraction_llm else "Unknown"}'
			f'{" +file_system" if self.file_system else ""}'
		)

		# Initialize available actions for system prompt (only non-filtered actions)
		# These will be used for the system prompt to maintain caching
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.unfiltered_actions = self.tools.registry.get_prompt_description()

		# Initialize message manager with state
		# Initial system prompt with all actions - will be updated during each step
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._message_manager = MessageManager(
			task=task,
			system_message=SystemPrompt(
				action_description=self.unfiltered_actions,
				max_actions_per_step=self.settings.max_actions_per_step,
				override_system_message=override_system_message,
				extend_system_message=extend_system_message,
				use_thinking=self.settings.use_thinking,
				flash_mode=self.settings.flash_mode,
			).get_system_message(),
			file_system=self.file_system,
			state=self.state.message_manager_state,
			use_thinking=self.settings.use_thinking,
			# Settings that were previously in MessageManagerSettings
			include_attributes=self.settings.include_attributes,
			sensitive_data=sensitive_data,
			max_history_items=self.settings.max_history_items,
			vision_detail_level=self.settings.vision_detail_level,
			include_tool_call_examples=self.settings.include_tool_call_examples,
			include_recent_events=self.include_recent_events,
			sample_images=self.sample_images,
		)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.sensitive_data:
			# Check if sensitive_data has domain-specific credentials
			# EN: Assign value to has_domain_specific_credentials.
			# JP: has_domain_specific_credentials に値を代入する。
			has_domain_specific_credentials = any(isinstance(v, dict) for v in self.sensitive_data.values())

			# If no allowed_domains are configured, show a security warning
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.browser_profile.allowed_domains:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(
					'⚠️ Agent(sensitive_data=••••••••) was provided but Browser(allowed_domains=[...]) is not locked down! ⚠️\n'
					'          ☠️ If the agent visits a malicious website and encounters a prompt-injection attack, your sensitive_data may be exposed!\n\n'
					'   \n'
				)

			# If we're using domain-specific credentials, validate domain patterns
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif has_domain_specific_credentials:
				# For domain-specific format, ensure all domain patterns are included in allowed_domains
				# EN: Assign value to domain_patterns.
				# JP: domain_patterns に値を代入する。
				domain_patterns = [k for k, v in self.sensitive_data.items() if isinstance(v, dict)]

				# Validate each domain pattern against allowed_domains
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for domain_pattern in domain_patterns:
					# EN: Assign value to is_allowed.
					# JP: is_allowed に値を代入する。
					is_allowed = False
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for allowed_domain in self.browser_profile.allowed_domains:
						# Special cases that don't require URL matching
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if domain_pattern == allowed_domain or allowed_domain == '*':
							# EN: Assign value to is_allowed.
							# JP: is_allowed に値を代入する。
							is_allowed = True
							# EN: Exit the current loop.
							# JP: 現在のループを終了する。
							break

						# Need to create example URLs to compare the patterns
						# Extract the domain parts, ignoring scheme
						# EN: Assign value to pattern_domain.
						# JP: pattern_domain に値を代入する。
						pattern_domain = domain_pattern.split('://')[-1] if '://' in domain_pattern else domain_pattern
						# EN: Assign value to allowed_domain_part.
						# JP: allowed_domain_part に値を代入する。
						allowed_domain_part = allowed_domain.split('://')[-1] if '://' in allowed_domain else allowed_domain

						# Check if pattern is covered by an allowed domain
						# Example: "google.com" is covered by "*.google.com"
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if pattern_domain == allowed_domain_part or (
							allowed_domain_part.startswith('*.')
							and (
								pattern_domain == allowed_domain_part[2:]
								or pattern_domain.endswith('.' + allowed_domain_part[2:])
							)
						):
							# EN: Assign value to is_allowed.
							# JP: is_allowed に値を代入する。
							is_allowed = True
							# EN: Exit the current loop.
							# JP: 現在のループを終了する。
							break

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if not is_allowed:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.warning(
							f'⚠️ Domain pattern "{domain_pattern}" in sensitive_data is not covered by any pattern in allowed_domains={self.browser_profile.allowed_domains}\n'
							f'   This may be a security risk as credentials could be used on unintended domains.'
						)

		# Callbacks
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.register_new_step_callback = register_new_step_callback
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.register_done_callback = register_done_callback
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.register_external_agent_status_raise_error_callback = register_external_agent_status_raise_error_callback

		# Telemetry
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.telemetry = ProductTelemetry()

		# Event bus with WAL persistence
		# Default to ~/.config/browseruse/events/{agent_session_id}.jsonl
		# wal_path = CONFIG.BROWSER_USE_CONFIG_DIR / 'events' / f'{self.session_id}.jsonl'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.eventbus, self._reserved_eventbus_name = self._create_eventbus()

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._refresh_browser_session_eventbus()

		# Cloud sync service
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.enable_cloud_sync = CONFIG.BROWSER_USE_CLOUD_SYNC
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.enable_cloud_sync or cloud_sync is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.cloud_sync = cloud_sync or CloudSync()
			# Register cloud sync handler
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.eventbus.on('*', self.cloud_sync.handle_event)
		else:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.cloud_sync = None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.settings.save_conversation_path:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.settings.save_conversation_path = Path(self.settings.save_conversation_path).expanduser().resolve()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'💬 Saving conversation to {_log_pretty_path(self.settings.save_conversation_path)}')

		# Initialize download tracking
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session is not None, 'BrowserSession is not set up'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.has_downloads_path = self.browser_session.browser_profile.downloads_path is not None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.has_downloads_path:
			# EN: Assign annotated value to target variable.
			# JP: target variable に型付きの値を代入する。
			self._last_known_downloads: list[str] = []
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('📁 Initialized download tracking for agent')

		# Event-based pause control (kept out of AgentState for serialization)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._external_pause_event = asyncio.Event()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._external_pause_event.set()

	# EN: Define function `_normalise_identifier`.
	# JP: 関数 `_normalise_identifier` を定義する。
	@staticmethod
	def _normalise_identifier(identifier: str | None) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return an alphanumeric identifier safe for internal agent bookkeeping."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if identifier is None:
			# EN: Assign value to identifier.
			# JP: identifier に値を代入する。
			identifier = ''

		# EN: Assign value to normalised.
		# JP: normalised に値を代入する。
		normalised = ''.join(ch for ch in str(identifier) if ch.isalnum())

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if normalised:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return normalised

		# EN: Assign value to fallback.
		# JP: fallback に値を代入する。
		fallback = uuid7str().replace('-', '')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(
			'Generated fallback agent identifier %s because the provided value %r contained no alphanumeric characters',
			fallback,
			identifier,
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return fallback

	# EN: Define function `_create_eventbus`.
	# JP: 関数 `_create_eventbus` を定義する。
	def _create_eventbus(self, *, force_random: bool = False) -> tuple[EventBus, str | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create a new :class:`EventBus` instance with graceful fallback."""

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			bus, reserved_name = EventBusFactory.create(
				agent_id=self.id,
				force_random=force_random,
				logger=logger,
			)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return bus, reserved_name
		except AssertionError as exc:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(
				'Failed to create named EventBus for agent %s (force_random=%s): %s. Falling back to anonymous EventBus.',
				self.id,
				force_random,
				exc,
			)
		except Exception as exc:  # pragma: no cover - defensive logging
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.exception(
				'Unexpected error while creating EventBus for agent %s (force_random=%s); falling back to anonymous EventBus.',
				self.id,
				force_random,
			)

		# EN: Assign value to fallback_bus.
		# JP: fallback_bus に値を代入する。
		fallback_bus = EventBus()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return fallback_bus, None

	# EN: Define function `_refresh_browser_session_eventbus`.
	# JP: 関数 `_refresh_browser_session_eventbus` を定義する。
	def _refresh_browser_session_eventbus(self, *, reset_watchdogs: bool = True) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Keep the browser session's EventBus aligned with the agent's EventBus."""

		# EN: Assign value to session.
		# JP: session に値を代入する。
		session = getattr(self, 'browser_session', None)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if session is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			session.event_bus = self.eventbus
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(
				'Failed to synchronise browser session event bus with agent event bus',
				exc_info=True,
			)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to fallback_triggered.
		# JP: fallback_triggered に値を代入する。
		fallback_triggered = False

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			session.model_post_init(None)
		except Exception as exc:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(
				'Failed to re-register browser session event handlers on refreshed event bus: %s. '
				'Attempting to rotate the event bus and retry once.',
				exc,
				exc_info=True,
			)

			# EN: Assign value to previous_bus.
			# JP: previous_bus に値を代入する。
			previous_bus = getattr(self, 'eventbus', None)
			# EN: Assign value to previous_name.
			# JP: previous_name に値を代入する。
			previous_name = getattr(self, '_reserved_eventbus_name', None)

			# EN: Assign value to rotated_bus.
			# JP: rotated_bus に値を代入する。
			rotated_bus = False

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				new_bus, new_name = self._create_eventbus(force_random=True)
			except Exception:  # pragma: no cover - defensive logging
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.exception('Failed to create fallback EventBus during browser session refresh')
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				new_bus, new_name = None, None

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if new_bus is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.eventbus = new_bus
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._reserved_eventbus_name = new_name
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					session.event_bus = new_bus
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.exception('Failed to assign rotated EventBus to browser session')
				else:
					# EN: Assign value to rotated_bus.
					# JP: rotated_bus に値を代入する。
					rotated_bus = True
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if previous_name:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						EventBusFactory.release(previous_name)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if previous_bus is not None and previous_bus is not new_bus:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self._schedule_eventbus_stop(previous_bus)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not rotated_bus:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.eventbus.handlers.clear()
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.exception('Failed to clear handlers on browser session EventBus during fallback')
				else:
					# EN: Assign value to rotated_bus.
					# JP: rotated_bus に値を代入する。
					rotated_bus = True

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if rotated_bus and getattr(self, 'cloud_sync', None) and getattr(self, 'enable_cloud_sync', False):
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.eventbus.on('*', self.cloud_sync.handle_event)
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.exception('Failed to re-register cloud sync handler on rotated EventBus')

			# EN: Assign value to fallback_triggered.
			# JP: fallback_triggered に値を代入する。
			fallback_triggered = rotated_bus

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				session.model_post_init(None)
			except Exception as second_exc:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.warning(
					'Second attempt to register browser session event handlers failed: %s',
					second_exc,
					exc_info=True,
				)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if fallback_triggered:
			# EN: Assign value to start_handlers.
			# JP: start_handlers に値を代入する。
			start_handlers = session.event_bus.handlers.get('BrowserStartEvent', [])
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not start_handlers:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError('Browser session EventBus has no BrowserStartEvent handlers after fallback rotation')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not reset_watchdogs:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(session, '_watchdogs_attached'):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				session._watchdogs_attached = False
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(
					'Failed to mark browser session watchdogs for reattachment',
					exc_info=True,
				)

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for attr in self._WATCHDOG_ATTR_NAMES:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(session, attr):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				setattr(session, attr, None)

	# EN: Define function `_reset_eventbus`.
	# JP: 関数 `_reset_eventbus` を定義する。
	def _reset_eventbus(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Replace the current :class:`EventBus` with a fresh instance."""

		# EN: Assign value to previous_bus.
		# JP: previous_bus に値を代入する。
		previous_bus = getattr(self, 'eventbus', None)
		# EN: Assign value to previous_name.
		# JP: previous_name に値を代入する。
		previous_name = self._reserved_eventbus_name
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if previous_name:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			EventBusFactory.release(previous_name)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._reserved_eventbus_name = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.eventbus, self._reserved_eventbus_name = self._create_eventbus(force_random=True)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._refresh_browser_session_eventbus()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if previous_bus is not None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._schedule_eventbus_stop(previous_bus)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, 'cloud_sync') and self.cloud_sync and self.enable_cloud_sync:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.eventbus.on('*', self.cloud_sync.handle_event)
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					'☁️ Re-registered cloud sync handler on EventBus %s',
					self.eventbus.name,
				)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(
					'☁️ Re-registered cloud sync handler on EventBus %s',
					self.eventbus.name,
				)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._pending_eventbus_refresh = False

	# EN: Define function `_schedule_eventbus_stop`.
	# JP: 関数 `_schedule_eventbus_stop` を定義する。
	def _schedule_eventbus_stop(self, bus: EventBus, *, timeout: float = 3.0) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Schedule ``bus.stop`` and fall back to synchronous execution when needed."""

		# EN: Define async function `_stop_bus`.
		# JP: 非同期関数 `_stop_bus` を定義する。
		async def _stop_bus() -> None:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await bus.stop(timeout=timeout)
			except Exception:  # pragma: no cover - defensive logging path
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.exception('Failed to stop EventBus %s cleanly', getattr(bus, 'name', '<anonymous>'))

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to loop.
			# JP: loop に値を代入する。
			loop = asyncio.get_running_loop()
		except RuntimeError:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				asyncio.run(_stop_bus())
			except RuntimeError:
				# If we're already inside a running loop but couldn't obtain it (unlikely),
				# fall back to a dedicated event loop for cleanup.
				# EN: Assign value to new_loop.
				# JP: new_loop に値を代入する。
				new_loop = asyncio.new_event_loop()
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					new_loop.run_until_complete(_stop_bus())
				finally:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					new_loop.close()
			except Exception:  # pragma: no cover - defensive logging path
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.exception('Unexpected error while stopping EventBus %s', getattr(bus, 'name', '<anonymous>'))
		else:
			# EN: Assign value to task.
			# JP: task に値を代入する。
			task = loop.create_task(_stop_bus())
			# EN: Assign value to cleanup_tasks.
			# JP: cleanup_tasks に値を代入する。
			cleanup_tasks = getattr(self, '_eventbus_cleanup_tasks', None)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cleanup_tasks is not None:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				cleanup_tasks.add(task)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				task.add_done_callback(cleanup_tasks.discard)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				task.add_done_callback(lambda _t: None)

	# EN: Define function `logger`.
	# JP: 関数 `logger` を定義する。
	@property
	def logger(self) -> logging.Logger:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get instance-specific logger with task ID in the name"""

		# EN: Assign value to _browser_session_id.
		# JP: _browser_session_id に値を代入する。
		_browser_session_id = self.browser_session.id if self.browser_session else '----'
		# EN: Assign value to _current_target_id.
		# JP: _current_target_id に値を代入する。
		_current_target_id = (
			self.browser_session.agent_focus.target_id[-2:]
			if self.browser_session and self.browser_session.agent_focus and self.browser_session.agent_focus.target_id
			else '--'
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return logging.getLogger(f'browser_use.Agent🅰 {self.task_id[-4:]} ⇢ 🅑 {_browser_session_id[-4:]} 🅣 {_current_target_id}')

	# EN: Define function `browser_profile`.
	# JP: 関数 `browser_profile` を定義する。
	@property
	def browser_profile(self) -> BrowserProfile:
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session is not None, 'BrowserSession is not set up'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.browser_session.browser_profile

	# EN: Define async function `_check_and_update_downloads`.
	# JP: 非同期関数 `_check_and_update_downloads` を定義する。
	async def _check_and_update_downloads(self, context: str = '') -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check for new downloads and update available file paths."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.has_downloads_path:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session is not None, 'BrowserSession is not set up'

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to current_downloads.
			# JP: current_downloads に値を代入する。
			current_downloads = self.browser_session.downloaded_files
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_downloads != self._last_known_downloads:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._update_available_file_paths(current_downloads)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._last_known_downloads = current_downloads
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if context:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'📁 {context}: Updated available files')
		except Exception as e:
			# EN: Assign value to error_context.
			# JP: error_context に値を代入する。
			error_context = f' {context}' if context else ''
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📁 Failed to check for downloads{error_context}: {type(e).__name__}: {e}')

	# EN: Define function `_update_available_file_paths`.
	# JP: 関数 `_update_available_file_paths` を定義する。
	def _update_available_file_paths(self, downloads: list[str]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update available_file_paths with downloaded files."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.has_downloads_path:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to current_files.
		# JP: current_files に値を代入する。
		current_files = set(self.available_file_paths or [])
		# EN: Assign value to new_files.
		# JP: new_files に値を代入する。
		new_files = set(downloads) - current_files

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if new_files:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.available_file_paths = list(current_files | new_files)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(
				f'📁 Added {len(new_files)} downloaded files to available_file_paths (total: {len(self.available_file_paths)} files)'
			)
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for file_path in new_files:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'📄 New file available: {file_path}')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📁 No new downloads detected (tracking {len(current_files)} files)')

	# EN: Define function `_set_file_system`.
	# JP: 関数 `_set_file_system` を定義する。
	def _set_file_system(self, file_system_path: str | None = None) -> None:
		# Check for conflicting parameters
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.file_system_state and file_system_path:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(
				'Cannot provide both file_system_state (from agent state) and file_system_path. '
				'Either restore from existing state or create new file system at specified path, not both.'
			)

		# Check if we should restore from existing state first
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.file_system_state:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Restore file system from state at the exact same location
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.file_system = FileSystem.from_state(self.state.file_system_state)
				# The parent directory of base_dir is the original file_system_path
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.file_system_path = str(self.file_system.base_dir)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'💾 File system restored from state to: {self.file_system_path}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'💾 Failed to restore file system from state: {e}')
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise e

		# Initialize new file system
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if file_system_path:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.file_system = FileSystem(file_system_path)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.file_system_path = file_system_path
			else:
				# Use the agent directory for file system
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.file_system = FileSystem(self.agent_directory)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.file_system_path = str(self.agent_directory)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'💾 Failed to initialize file system: {e}.')
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise e

		# Save file system state to agent state
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.file_system_state = self.file_system.get_state()

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'💾 File system path: {self.file_system_path}')

	# EN: Define function `_set_screenshot_service`.
	# JP: 関数 `_set_screenshot_service` を定義する。
	def _set_screenshot_service(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize screenshot service using agent directory"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from browser_use.screenshots.service import ScreenshotService

			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.screenshot_service = ScreenshotService(self.agent_directory)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'📸 Screenshot service initialized in: {self.agent_directory}/screenshots')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'📸 Failed to initialize screenshot service: {e}.')
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise e

	# EN: Define function `save_file_system_state`.
	# JP: 関数 `save_file_system_state` を定義する。
	def save_file_system_state(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Save current file system state to agent state"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.file_system:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.state.file_system_state = self.file_system.get_state()
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error('💾 File system is not set up. Cannot save state.')
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError('File system is not set up. Cannot save state.')

	# EN: Define function `_set_browser_use_version_and_source`.
	# JP: 関数 `_set_browser_use_version_and_source` を定義する。
	def _set_browser_use_version_and_source(self, source_override: str | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the version from pyproject.toml and determine the source of the browser-use package"""
		# Use the helper function for version detection
		# EN: Assign value to version.
		# JP: version に値を代入する。
		version = get_browser_use_version()

		# Determine source
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to package_root.
			# JP: package_root に値を代入する。
			package_root = Path(__file__).parent.parent.parent
			# EN: Assign value to repo_files.
			# JP: repo_files に値を代入する。
			repo_files = ['.git', 'README.md', 'docs', 'examples']
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if all(Path(package_root / file).exists() for file in repo_files):
				# EN: Assign value to source.
				# JP: source に値を代入する。
				source = 'git'
			else:
				# EN: Assign value to source.
				# JP: source に値を代入する。
				source = 'pip'
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Error determining source: {e}')
			# EN: Assign value to source.
			# JP: source に値を代入する。
			source = 'unknown'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if source_override is not None:
			# EN: Assign value to source.
			# JP: source に値を代入する。
			source = source_override
		# self.logger.debug(f'Version: {version}, Source: {source}')  # moved later to _log_agent_run so that people are more likely to include it in copy-pasted support ticket logs
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.version = version
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.source = source

	# EN: Define function `_setup_action_models`.
	# JP: 関数 `_setup_action_models` を定義する。
	def _setup_action_models(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Setup dynamic action models from tools registry"""
		# Initially only include actions with no filters
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.ActionModel = self.tools.registry.create_action_model()
		# Create output model with the dynamic actions
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.settings.flash_mode:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.AgentOutput = AgentOutput.type_with_custom_actions_flash_mode(self.ActionModel)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.settings.use_thinking:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.AgentOutput = AgentOutput.type_with_custom_actions(self.ActionModel)
		else:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.AgentOutput = AgentOutput.type_with_custom_actions_no_thinking(self.ActionModel)

		# used to force the done action when max_steps is reached
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.DoneActionModel = self.tools.registry.create_action_model(include_actions=['done'])
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.settings.flash_mode:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.DoneAgentOutput = AgentOutput.type_with_custom_actions_flash_mode(self.DoneActionModel)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.settings.use_thinking:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.DoneAgentOutput = AgentOutput.type_with_custom_actions(self.DoneActionModel)
		else:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.DoneAgentOutput = AgentOutput.type_with_custom_actions_no_thinking(self.DoneActionModel)

	# EN: Define function `_is_legacy_eventbus_name`.
	# JP: 関数 `_is_legacy_eventbus_name` を定義する。
	@staticmethod
	def _is_legacy_eventbus_name(name: str | None) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return ``True`` when *name* cannot be used as an identifier."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not name:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return not str(name).isidentifier()

	# EN: Define function `_refresh_legacy_eventbus_state`.
	# JP: 関数 `_refresh_legacy_eventbus_state` を定義する。
	def _refresh_legacy_eventbus_state(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Upgrade legacy EventBus instances with invalid identifiers.

		Older agent runs created ``EventBus`` objects using identifiers that
		are no longer accepted by ``bubus`` (e.g. names containing ``-``).
		When those agents receive follow-up tasks, attempting to reuse the
		legacy identifier raises an ``AssertionError`` before any recovery
		logic can run.  By pro-actively detecting these legacy identifiers
		and rotating the EventBus to a fresh, sanitised name we guarantee
		that follow-up tasks continue executing without forcing the
		controller to recreate the entire agent.

		Returns ``True`` when a migration was performed.
		"""

		# EN: Assign value to eventbus.
		# JP: eventbus に値を代入する。
		eventbus = getattr(self, 'eventbus', None)
		# EN: Assign value to reserved_name.
		# JP: reserved_name に値を代入する。
		reserved_name = getattr(self, '_reserved_eventbus_name', None)

		# EN: Assign value to needs_refresh.
		# JP: needs_refresh に値を代入する。
		needs_refresh = self._is_legacy_eventbus_name(getattr(eventbus, 'name', None))
		# EN: Assign value to needs_refresh.
		# JP: needs_refresh に値を代入する。
		needs_refresh = needs_refresh or self._is_legacy_eventbus_name(reserved_name)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not needs_refresh:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.running:
			# Follow-up requests can arrive while the agent is still executing the
			# previous task. In that case attempt an immediate rotation so that
			# the pending instructions are applied without surfacing an error to
			# the user.
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._pending_eventbus_refresh = True
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🚌 Detected legacy EventBus while running; refreshing immediately')
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('🚌 Detected legacy EventBus while running; refreshing immediately')

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._reset_eventbus()
			except AssertionError:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise
			except Exception:
				# If the refresh fails we fall back to the deferred behaviour to
				# avoid interrupting the active run.
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('🚌 Immediate EventBus refresh failed; will retry after run completes', exc_info=True)
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug('🚌 Immediate EventBus refresh failed; will retry after run completes', exc_info=True)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return False

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				'♻️ Refreshing legacy EventBus %r (reserved=%r) before follow-up task',
				getattr(eventbus, 'name', None),
				reserved_name,
			)
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(
				'♻️ Refreshing legacy EventBus %r (reserved=%r) before follow-up task',
				getattr(eventbus, 'name', None),
				reserved_name,
			)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._reset_eventbus()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Define function `reset_completion_state`.
	# JP: 関数 `reset_completion_state` を定義する。
	def reset_completion_state(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear completion flags so follow-up runs can execute new steps."""

		# EN: Assign value to cleared.
		# JP: cleared に値を代入する。
		cleared = False

		# EN: Define function `_clear_flag`.
		# JP: 関数 `_clear_flag` を定義する。
		def _clear_flag(results: list[ActionResult] | None) -> None:
			# EN: Execute this statement.
			# JP: この文を実行する。
			nonlocal cleared
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not results:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to final_result.
				# JP: final_result に値を代入する。
				final_result = results[-1]
			except IndexError:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if getattr(final_result, 'is_done', None):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				final_result.is_done = False
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if getattr(final_result, 'success', None) is not None:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					final_result.success = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(final_result, 'error'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					final_result.error = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(final_result, 'long_term_memory'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					final_result.long_term_memory = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(final_result, 'extracted_content'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					final_result.extracted_content = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(final_result, 'metadata'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					final_result.metadata = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(final_result, 'attachments'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					final_result.attachments = []
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(final_result, 'include_extracted_content_only_once'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					final_result.include_extracted_content_only_once = False
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(final_result, 'include_in_memory'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					final_result.include_in_memory = False
				# EN: Assign value to cleared.
				# JP: cleared に値を代入する。
				cleared = True

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_clear_flag(self.state.last_result)

		# EN: Assign value to history_items.
		# JP: history_items に値を代入する。
		history_items = getattr(self.history, 'history', None)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if history_items:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_clear_flag(getattr(history_items[-1], 'result', None))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cleared

	# EN: Define function `add_new_task`.
	# JP: 関数 `add_new_task` を定義する。
	def add_new_task(self, new_task: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Add a new task to the agent, keeping the same task_id as tasks are continuous"""
		# Simply delegate to message manager - no need for new task_id or events
		# The task continues with new instructions, it doesn't end and start a new one
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.task = new_task
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._message_manager.add_new_task(new_task)
		# Mark as follow-up task so we preserve state-specific behaviours like skipping initial actions
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.follow_up_task = True

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.reset_completion_state()

		# Ensure follow-up runs never reuse the previous EventBus identifier.
		# EN: Assign value to identifier_changed.
		# JP: identifier_changed に値を代入する。
		identifier_changed = False
		# EN: Assign value to normalised_id.
		# JP: normalised_id に値を代入する。
		normalised_id = self._normalise_identifier(self.id)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if normalised_id != self.id:
			# EN: Assign value to identifier_changed.
			# JP: identifier_changed に値を代入する。
			identifier_changed = True
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					'Normalised agent identifier from %r to %s before refreshing EventBus',
					self.id,
					normalised_id,
				)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(
					'Normalised agent identifier from %r to %s before refreshing EventBus',
					self.id,
					normalised_id,
				)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.id = normalised_id
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.task_id = normalised_id

		# EN: Assign value to legacy_rotated.
		# JP: legacy_rotated に値を代入する。
		legacy_rotated = self._refresh_legacy_eventbus_state()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not legacy_rotated and identifier_changed and getattr(self, '_reserved_eventbus_name', None):
			# Release names that are no longer valid so the new EventBus can
			# claim a fresh, sanitised identifier.
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			EventBusFactory.release(self._reserved_eventbus_name)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._reserved_eventbus_name = None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.running:
			# Defer recreation until the active run finishes shutting down its EventBus.
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._pending_eventbus_refresh = True
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🚌 Deferring EventBus reset until run shutdown completes')
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('🚌 Deferring EventBus reset until run shutdown completes')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif not legacy_rotated:
			# Create the new EventBus immediately when the agent is idle or after
			# migrating away from a legacy identifier.
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._reset_eventbus()

	# EN: Define function `_current_step_number`.
	# JP: 関数 `_current_step_number` を定義する。
	def _current_step_number(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return the current step number relative to the latest run."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not hasattr(self.state, 'step_offset'):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.state.n_steps

		# EN: Assign value to current_step.
		# JP: current_step に値を代入する。
		current_step = self.state.n_steps - self.state.step_offset
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return current_step if current_step > 0 else 1

	# EN: Define function `current_step_number`.
	# JP: 関数 `current_step_number` を定義する。
	@property
	def current_step_number(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Public accessor for the current step number within the active run."""

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._current_step_number()

	# EN: Define function `_compute_steps_completed_in_current_run`.
	# JP: 関数 `_compute_steps_completed_in_current_run` を定義する。
	def _compute_steps_completed_in_current_run(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Internal helper to calculate completed steps for the current run."""

		# EN: Assign value to current_step.
		# JP: current_step に値を代入する。
		current_step = self._current_step_number()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return current_step - 1 if current_step > 0 else 0

	# EN: Define function `steps_completed_in_current_run`.
	# JP: 関数 `steps_completed_in_current_run` を定義する。
	@property
	def steps_completed_in_current_run(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Number of steps completed during the most recent run."""

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._compute_steps_completed_in_current_run()

	# EN: Define async function `_raise_if_stopped_or_paused`.
	# JP: 非同期関数 `_raise_if_stopped_or_paused` を定義する。
	async def _raise_if_stopped_or_paused(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Utility function that raises an InterruptedError if the agent is stopped or paused."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.register_external_agent_status_raise_error_callback:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if await self.register_external_agent_status_raise_error_callback():
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise InterruptedError

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.stopped:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise InterruptedError

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.paused:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise InterruptedError

	# EN: Define async function `step`.
	# JP: 非同期関数 `step` を定義する。
	@observe(name='agent.step', ignore_output=True, ignore_input=True)
	@time_execution_async('--step')
	async def step(self, step_info: AgentStepInfo | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute one step of the task"""
		# Initialize timing first, before any exceptions can occur

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.step_start_time = time.time()

		# EN: Assign value to browser_state_summary.
		# JP: browser_state_summary に値を代入する。
		browser_state_summary = None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Phase 1: Prepare context and timing
			# EN: Assign value to browser_state_summary.
			# JP: browser_state_summary に値を代入する。
			browser_state_summary = await self._prepare_context(step_info)

			# Phase 2: Get model output and execute actions
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._get_next_action(browser_state_summary)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._execute_actions()

			# Phase 3: Post-processing
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._post_process()

		except Exception as e:
			# Handle ALL exceptions in one place
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._handle_step_error(e)

		finally:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._finalize(browser_state_summary)

	# EN: Define async function `_prepare_context`.
	# JP: 非同期関数 `_prepare_context` を定義する。
	async def _prepare_context(self, step_info: AgentStepInfo | None = None) -> BrowserStateSummary:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Prepare the context for the step: browser state, action models, page actions"""
		# step_start_time is now set in step() method

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session is not None, 'BrowserSession is not set up'

		# EN: Assign value to current_step.
		# JP: current_step に値を代入する。
		current_step = self._current_step_number()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🌐 Step {current_step}: Getting browser state...')
		# Always take screenshots for all steps
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('📸 Requesting browser state with include_screenshot=True')
		# EN: Assign value to browser_state_summary.
		# JP: browser_state_summary に値を代入する。
		browser_state_summary = await self.browser_session.get_browser_state_summary(
			cache_clickable_elements_hashes=True,
			include_screenshot=True,  # always capture even if use_vision=False so that cloud sync is useful (it's fast now anyway)
			include_recent_events=self.include_recent_events,
		)

		# Retry once if the DOM snapshot unexpectedly comes back empty on a normal page.
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._should_retry_browser_state(browser_state_summary):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔁 Empty DOM on loaded page detected, retrying browser state after short wait')
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.6)
				# EN: Assign value to browser_state_summary.
				# JP: browser_state_summary に値を代入する。
				browser_state_summary = await self.browser_session.get_browser_state_summary(
					cache_clickable_elements_hashes=True,
					include_screenshot=True,
					include_recent_events=self.include_recent_events,
				)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🔁 Browser state retry failed', exc_info=True)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_state_summary.screenshot:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📸 Got browser state WITH screenshot, length: {len(browser_state_summary.screenshot)}')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('📸 Got browser state WITHOUT screenshot')

		# Check for new downloads after getting browser state (catches PDF auto-downloads and previous step downloads)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._check_and_update_downloads(f'Step {current_step}: after getting browser state')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._log_step_context(browser_state_summary)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._raise_if_stopped_or_paused()

		# Update action models with page-specific actions
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'📝 Step {current_step}: Updating action models...')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._update_action_models_for_page(browser_state_summary.url)

		# Get page-specific filtered actions
		# EN: Assign value to page_filtered_actions.
		# JP: page_filtered_actions に値を代入する。
		page_filtered_actions = self.tools.registry.get_prompt_description(browser_state_summary.url)

		# Page-specific actions will be included directly in the browser_state message
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'💬 Step {current_step}: Creating state messages for context...')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._message_manager.create_state_messages(
			browser_state_summary=browser_state_summary,
			model_output=self.state.last_model_output,
			result=self.state.last_result,
			step_info=step_info,
			use_vision=self.settings.use_vision,
			page_filtered_actions=page_filtered_actions if page_filtered_actions else None,
			sensitive_data=self.sensitive_data,
			available_file_paths=self.available_file_paths,  # Always pass current available_file_paths
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._force_done_after_last_step(step_info)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._force_done_after_failure()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return browser_state_summary

	# EN: Define function `_should_retry_browser_state`.
	# JP: 関数 `_should_retry_browser_state` を定義する。
	@staticmethod
	def _should_retry_browser_state(state: BrowserStateSummary | None) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Decide whether to retry fetching browser state when the DOM is unexpectedly empty."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if state is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Skip retry for non-web pages, PDFs, or when errors are already reported.
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if state.is_pdf_viewer or state.browser_errors:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not state.url or not state.url.startswith(('http://', 'https://')):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# If we already have interactive elements, no need to retry.
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if state.dom_state and state.dom_state.selector_map:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# about:blank placeholder screenshot indicates the page truly is empty.
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if state.screenshot == PLACEHOLDER_4PX_SCREENSHOT:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Define async function `_get_next_action`.
	# JP: 非同期関数 `_get_next_action` を定義する。
	@observe_debug(ignore_input=True, name='get_next_action')
	async def _get_next_action(self, browser_state_summary: BrowserStateSummary) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute LLM interaction with retry logic and handle callbacks"""
		# EN: Assign value to input_messages.
		# JP: input_messages に値を代入する。
		input_messages = self._message_manager.get_messages()
		# EN: Assign value to current_step.
		# JP: current_step に値を代入する。
		current_step = self._current_step_number()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🤖 Step {current_step}: Calling LLM with {len(input_messages)} messages (model: {self.llm.model})...')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to model_output.
			# JP: model_output に値を代入する。
			model_output = await asyncio.wait_for(
				self._get_model_output_with_retry(input_messages), timeout=self.settings.llm_timeout
			)
		except TimeoutError:

			# EN: Define async function `_log_model_input_to_lmnr`.
			# JP: 非同期関数 `_log_model_input_to_lmnr` を定義する。
			@observe(name='_llm_call_timed_out_with_input')
			async def _log_model_input_to_lmnr(input_messages: list[BaseMessage]) -> None:
				# EN: Describe this block with a docstring.
				# JP: このブロックの説明をドキュメント文字列で記述する。
				"""Log the model input"""
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await _log_model_input_to_lmnr(input_messages)

			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise TimeoutError(
				f'LLM call timed out after {self.settings.llm_timeout} seconds. Keep your thinking and output short.'
			)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.last_model_output = model_output

		# Check again for paused/stopped state after getting model output
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._raise_if_stopped_or_paused()

		# Handle callbacks and conversation saving
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._handle_post_llm_processing(browser_state_summary, input_messages)

		# check again if Ctrl+C was pressed before we commit the output to history
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._raise_if_stopped_or_paused()

	# EN: Define async function `_execute_actions`.
	# JP: 非同期関数 `_execute_actions` を定義する。
	async def _execute_actions(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute the actions from model output"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.last_model_output is None:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError('No model output to execute actions from')

		# EN: Assign value to current_step.
		# JP: current_step に値を代入する。
		current_step = self._current_step_number()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'⚡ Step {current_step}: Executing {len(self.state.last_model_output.action)} actions...')
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = await self.multi_act(self.state.last_model_output.action)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'✅ Step {current_step}: Actions completed')

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.last_result = result

	# EN: Define async function `_post_process`.
	# JP: 非同期関数 `_post_process` を定義する。
	async def _post_process(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle post-action processing like download tracking and result logging"""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session is not None, 'BrowserSession is not set up'

		# Check for new downloads after executing actions
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._check_and_update_downloads('after executing actions')

		# check for action errors  and len more than 1
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.last_result and len(self.state.last_result) == 1 and self.state.last_result[-1].error:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.state.consecutive_failures += 1
			# EN: Assign value to current_step.
			# JP: current_step に値を代入する。
			current_step = self._current_step_number()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'🔄 Step {current_step}: Consecutive failures: {self.state.consecutive_failures}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.consecutive_failures = 0
		# EN: Assign value to current_step.
		# JP: current_step に値を代入する。
		current_step = self._current_step_number()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🔄 Step {current_step}: Consecutive failures reset to: {self.state.consecutive_failures}')

		# Log completion results
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.last_result and len(self.state.last_result) > 0 and self.state.last_result[-1].is_done:
			# EN: Assign value to success.
			# JP: success に値を代入する。
			success = self.state.last_result[-1].success
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if success:
				# Green color for success
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'\n📄 \033[32m Final Result:\033[0m \n{self.state.last_result[-1].extracted_content}\n\n')
			else:
				# Red color for failure
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'\n📄 \033[31m Final Result:\033[0m \n{self.state.last_result[-1].extracted_content}\n\n')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.state.last_result[-1].attachments:
				# EN: Assign value to total_attachments.
				# JP: total_attachments に値を代入する。
				total_attachments = len(self.state.last_result[-1].attachments)
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for i, file_path in enumerate(self.state.last_result[-1].attachments):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.info(f'👉 Attachment {i + 1 if total_attachments > 1 else ""}: {file_path}')

	# EN: Define async function `_handle_step_error`.
	# JP: 非同期関数 `_handle_step_error` を定義する。
	async def _handle_step_error(self, error: Exception) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle all types of errors that can occur during a step"""

		# Handle all other exceptions
		# EN: Assign value to include_trace.
		# JP: include_trace に値を代入する。
		include_trace = self.logger.isEnabledFor(logging.DEBUG)
		# EN: Assign value to error_msg.
		# JP: error_msg に値を代入する。
		error_msg = AgentError.format_error(error, include_trace=include_trace)
		# EN: Assign value to prefix.
		# JP: prefix に値を代入する。
		prefix = f'❌ Result failed {self.state.consecutive_failures + 1}/{self.settings.max_failures + int(self.settings.final_response_after_failure)} times:\n '
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		self.state.consecutive_failures += 1

		# Handle InterruptedError specially
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(error, InterruptedError):
			# EN: Assign value to error_msg.
			# JP: error_msg に値を代入する。
			error_msg = 'The agent was interrupted mid-step' + (f' - {error}' if error else '')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'{prefix}{error_msg}')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif 'Could not parse response' in error_msg or 'tool_use_failed' in error_msg:
			# give model a hint how output should look like
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Model: {self.llm.model} failed')
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			error_msg += '\n\nReturn a valid JSON object with the required fields.'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'{prefix}{error_msg}')
			# Add context message to help model fix parsing errors
			# EN: Assign value to parse_hint.
			# JP: parse_hint に値を代入する。
			parse_hint = 'Your response could not be parsed. Return a valid JSON object with the required fields.'
			# self._message_manager._add_context_message(UserMessage(content=parse_hint))
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif 'messages[1].content' in error_msg and 'invalid' in error_msg.lower():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'{prefix}{error_msg}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('⚠️ API rejected message content (likely image). Disabling vision for future steps to recover.')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.settings.use_vision = False
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif 'validation errors for AgentOutput' in error_msg and 'input_value' in error_msg and "'error':" in error_msg:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'{prefix}{error_msg}')

			# Try to extract the actual error message from the input_value
			# Pattern: input_value={'error': {'message': 'ACTUAL_ERROR_MESSAGE', ...}}
			# Handle both standard and escaped quotes in the error message
			# EN: Assign value to match.
			# JP: match に値を代入する。
			match = re.search(r"(?:\\)?'message(?:\\)?':\s*(?:\\)?'([^']+)(?:\\)?'", error_msg)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if match:
				# EN: Assign value to extracted_error.
				# JP: extracted_error に値を代入する。
				extracted_error = match.group(1)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(f'🔍 Extracted API Error: {extracted_error}')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'messages[1].content' in extracted_error:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning('⚠️ Disabling vision based on extracted API error.')
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.settings.use_vision = False
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif 'messages[1].content' in error_msg:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning('⚠️ Disabling vision based on error content (fallback).')
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.settings.use_vision = False
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'{prefix}{error_msg}')

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.last_result = [ActionResult(error=error_msg)]
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `_finalize`.
	# JP: 非同期関数 `_finalize` を定義する。
	async def _finalize(self, browser_state_summary: BrowserStateSummary | None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Finalize the step with history, logging, and events"""
		# EN: Assign value to step_end_time.
		# JP: step_end_time に値を代入する。
		step_end_time = time.time()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.state.last_result:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_state_summary:
			# EN: Assign value to current_step.
			# JP: current_step に値を代入する。
			current_step = self._current_step_number()
			# EN: Assign value to metadata.
			# JP: metadata に値を代入する。
			metadata = StepMetadata(
				step_number=current_step,
				absolute_step_number=self.state.n_steps,
				step_start_time=self.step_start_time,
				step_end_time=step_end_time,
			)

			# Use _make_history_item like main branch
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._make_history_item(self.state.last_model_output, browser_state_summary, self.state.last_result, metadata)

		# Log step completion summary
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._log_step_completion_summary(self.step_start_time, self.state.last_result)

		# Save file system state after step completion
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.save_file_system_state()

		# Emit both step created and executed events
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_state_summary and self.state.last_model_output:
			# Extract key step data for the event
			# EN: Assign value to actions_data.
			# JP: actions_data に値を代入する。
			actions_data = []
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.state.last_model_output.action:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for action in self.state.last_model_output.action:
					# EN: Assign value to action_dict.
					# JP: action_dict に値を代入する。
					action_dict = action.model_dump() if hasattr(action, 'model_dump') else {}
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					actions_data.append(action_dict)

			# Emit CreateAgentStepEvent only if cloud sync is enabled
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.enable_cloud_sync:
				# EN: Assign value to step_event.
				# JP: step_event に値を代入する。
				step_event = CreateAgentStepEvent.from_agent_step(
					self,
					self.state.last_model_output,
					self.state.last_result,
					actions_data,
					browser_state_summary,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.eventbus.dispatch(step_event)

		# Increment step counter only if the step was successful
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not (self.state.last_result and len(self.state.last_result) == 1 and self.state.last_result[-1].error):
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.state.n_steps += 1

	# EN: Define async function `_force_done_after_last_step`.
	# JP: 非同期関数 `_force_done_after_last_step` を定義する。
	async def _force_done_after_last_step(self, step_info: AgentStepInfo | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle special processing for the last step"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if step_info and step_info.is_last_step():
			# Add last step warning if needed
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = 'Now comes your last step. Use only the "done" action now. No other actions - so here your action sequence must have length 1.'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			msg += '\nIf you have found ANY useful information, set success in "done" to true, even if it is incomplete.'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			msg += '\nOnly set success to false if you found absolutely nothing.'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			msg += '\nInclude everything you found out for the ultimate task in the done text.'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('Last step finishing up')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._message_manager._add_context_message(UserMessage(content=msg))
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.AgentOutput = self.DoneAgentOutput

	# EN: Define async function `_force_done_after_failure`.
	# JP: 非同期関数 `_force_done_after_failure` を定義する。
	async def _force_done_after_failure(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Force done after failure"""
		# Create recovery message
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.state.consecutive_failures >= self.settings.max_failures and self.settings.final_response_after_failure:
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = f'You have failed {self.settings.max_failures} consecutive times. This is your final step to complete the task or provide what you found. '
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			msg += 'Use only the "done" action now. No other actions - so here your action sequence must have length 1.'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			msg += '\nIf you have found ANY useful information, set success in "done" to true, even if it is incomplete.'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			msg += '\nOnly set success to false if you found absolutely nothing.'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			msg += '\nInclude everything you found out for the task in the done text.'

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('Force done action, because we reached max_failures.')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._message_manager._add_context_message(UserMessage(content=msg))
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.AgentOutput = self.DoneAgentOutput

	# EN: Define async function `_get_model_output_with_retry`.
	# JP: 非同期関数 `_get_model_output_with_retry` を定義する。
	async def _get_model_output_with_retry(self, input_messages: list[BaseMessage]) -> AgentOutput:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get model output with retry logic for empty actions and JSON parse errors"""
		# EN: Assign value to max_json_retries.
		# JP: max_json_retries に値を代入する。
		max_json_retries = 2
		# EN: Assign annotated value to last_error.
		# JP: last_error に型付きの値を代入する。
		last_error: Exception | None = None

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for attempt in range(max_json_retries + 1):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if attempt > 0:
					# Add JSON correction hint for retry attempts
					# EN: Assign value to json_correction_message.
					# JP: json_correction_message に値を代入する。
					json_correction_message = UserMessage(
						content=(
							'あなたの前回の出力はJSONとして解析できませんでした。\n'
							'以下の点に注意して、正しいJSONのみを出力してください：\n'
							'1. 文字列内の改行は \\n でエスケープする\n'
							'2. 文字列内のダブルクォートは \\" でエスケープする\n'
							'3. 制御文字（タブ等）は適切にエスケープする\n'
							'4. JSONの構文（カンマ、括弧の対応）を正しくする\n'
							'5. 説明やマークダウンは含めず、純粋なJSONのみを出力する'
						)
					)
					# EN: Assign value to retry_messages.
					# JP: retry_messages に値を代入する。
					retry_messages = input_messages + [json_correction_message]
					# EN: Assign value to model_output.
					# JP: model_output に値を代入する。
					model_output = await self.get_model_output(retry_messages)
				else:
					# EN: Assign value to model_output.
					# JP: model_output に値を代入する。
					model_output = await self.get_model_output(input_messages)

				# EN: Assign value to current_step.
				# JP: current_step に値を代入する。
				current_step = self._current_step_number()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'✅ Step {current_step}: Got LLM response with {len(model_output.action) if model_output.action else 0} actions'
				)
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break  # Success - exit retry loop

			except (ValidationError, ValueError, json.JSONDecodeError) as e:
				# EN: Assign value to last_error.
				# JP: last_error に値を代入する。
				last_error = e
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if attempt < max_json_retries:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'⚠️ JSON parse error (attempt {attempt + 1}/{max_json_retries + 1}): {str(e)[:200]}')
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'❌ JSON parse failed after {max_json_retries + 1} attempts: {str(e)[:200]}')
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise
		else:
			# All retries exhausted
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if last_error:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise last_error
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError('Failed to get model output after retries')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if (
			not model_output.action
			or not isinstance(model_output.action, list)
			or all(action.model_dump() == {} for action in model_output.action)
		):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('Model returned empty action. Retrying...')

			# EN: Assign value to clarification_message.
			# JP: clarification_message に値を代入する。
			clarification_message = UserMessage(
				content='You forgot to return an action. Please respond with a valid JSON action according to the expected schema with your assessment and next actions.'
			)

			# EN: Assign value to retry_messages.
			# JP: retry_messages に値を代入する。
			retry_messages = input_messages + [clarification_message]
			# EN: Assign value to model_output.
			# JP: model_output に値を代入する。
			model_output = await self.get_model_output(retry_messages)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not model_output.action or all(action.model_dump() == {} for action in model_output.action):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning('Model still returned empty after retry. Inserting safe noop action.')
				# EN: Assign value to action_instance.
				# JP: action_instance に値を代入する。
				action_instance = self.ActionModel()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				setattr(
					action_instance,
					'done',
					{
						'success': False,
						'text': 'No next action returned by LLM!',
					},
				)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_output.action = [action_instance]

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return model_output

	# EN: Define async function `_handle_post_llm_processing`.
	# JP: 非同期関数 `_handle_post_llm_processing` を定義する。
	async def _handle_post_llm_processing(
		self,
		browser_state_summary: BrowserStateSummary,
		input_messages: list[BaseMessage],
	) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle callbacks and conversation saving after LLM interaction"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.register_new_step_callback and self.state.last_model_output:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if inspect.iscoroutinefunction(self.register_new_step_callback):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.register_new_step_callback(
					browser_state_summary,
					self.state.last_model_output,
					self.state.n_steps,
				)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.register_new_step_callback(
					browser_state_summary,
					self.state.last_model_output,
					self.state.n_steps,
				)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.settings.save_conversation_path and self.state.last_model_output:
			# Treat save_conversation_path as a directory (consistent with other recording paths)
			# EN: Assign value to conversation_dir.
			# JP: conversation_dir に値を代入する。
			conversation_dir = Path(self.settings.save_conversation_path)
			# EN: Assign value to conversation_filename.
			# JP: conversation_filename に値を代入する。
			conversation_filename = f'conversation_{self.id}_{self.state.n_steps}.txt'
			# EN: Assign value to target.
			# JP: target に値を代入する。
			target = conversation_dir / conversation_filename
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await save_conversation(
				input_messages,
				self.state.last_model_output,
				target,
				self.settings.save_conversation_path_encoding,
			)

	# EN: Define async function `_make_history_item`.
	# JP: 非同期関数 `_make_history_item` を定義する。
	async def _make_history_item(
		self,
		model_output: AgentOutput | None,
		browser_state_summary: BrowserStateSummary,
		result: list[ActionResult],
		metadata: StepMetadata | None = None,
	) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create and store history item"""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if model_output:
			# EN: Assign value to interacted_elements.
			# JP: interacted_elements に値を代入する。
			interacted_elements = AgentHistory.get_interacted_element(model_output, browser_state_summary.dom_state.selector_map)
		else:
			# EN: Assign value to interacted_elements.
			# JP: interacted_elements に値を代入する。
			interacted_elements = [None]

		# Store screenshot and get path
		# EN: Assign value to screenshot_path.
		# JP: screenshot_path に値を代入する。
		screenshot_path = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_state_summary.screenshot:
			# EN: Assign value to current_step.
			# JP: current_step に値を代入する。
			current_step = metadata.step_number if metadata and metadata.step_number is not None else self._current_step_number()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'📸 Storing screenshot for step {current_step}, screenshot length: {len(browser_state_summary.screenshot)}'
			)
			# EN: Assign value to storage_step.
			# JP: storage_step に値を代入する。
			storage_step = (
				metadata.absolute_step_number if metadata and metadata.absolute_step_number is not None else self.state.n_steps
			)
			# EN: Assign value to screenshot_path.
			# JP: screenshot_path に値を代入する。
			screenshot_path = await self.screenshot_service.store_screenshot(browser_state_summary.screenshot, storage_step)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📸 Screenshot stored at: {screenshot_path}')
		else:
			# EN: Assign value to current_step.
			# JP: current_step に値を代入する。
			current_step = metadata.step_number if metadata and metadata.step_number is not None else self._current_step_number()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📸 No screenshot in browser_state_summary for step {current_step}')

		# EN: Assign value to state_history.
		# JP: state_history に値を代入する。
		state_history = BrowserStateHistory(
			url=browser_state_summary.url,
			title=browser_state_summary.title,
			tabs=browser_state_summary.tabs,
			interacted_element=interacted_elements,
			screenshot_path=screenshot_path,
		)

		# EN: Assign value to history_item.
		# JP: history_item に値を代入する。
		history_item = AgentHistory(
			model_output=model_output,
			result=result,
			state=state_history,
			metadata=metadata,
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.history.add_item(history_item)

	# EN: Define function `_remove_think_tags`.
	# JP: 関数 `_remove_think_tags` を定義する。
	def _remove_think_tags(self, text: str) -> str:
		# EN: Assign value to THINK_TAGS.
		# JP: THINK_TAGS に値を代入する。
		THINK_TAGS = re.compile(r'<think>.*?</think>', re.DOTALL)
		# EN: Assign value to STRAY_CLOSE_TAG.
		# JP: STRAY_CLOSE_TAG に値を代入する。
		STRAY_CLOSE_TAG = re.compile(r'.*?</think>', re.DOTALL)
		# Step 1: Remove well-formed <think>...</think>
		# EN: Assign value to text.
		# JP: text に値を代入する。
		text = re.sub(THINK_TAGS, '', text)
		# Step 2: If there's an unmatched closing tag </think>,
		#         remove everything up to and including that.
		# EN: Assign value to text.
		# JP: text に値を代入する。
		text = re.sub(STRAY_CLOSE_TAG, '', text)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return text.strip()

	# region - URL replacement
	# EN: Define function `_replace_urls_in_text`.
	# JP: 関数 `_replace_urls_in_text` を定義する。
	def _replace_urls_in_text(self, text: str) -> tuple[str, dict[str, str]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Replace URLs in a text string"""

		# EN: Assign annotated value to replaced_urls.
		# JP: replaced_urls に型付きの値を代入する。
		replaced_urls: dict[str, str] = {}

		# EN: Define function `replace_url`.
		# JP: 関数 `replace_url` を定義する。
		def replace_url(match: re.Match) -> str:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Url can only have 1 query and 1 fragment"""
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import hashlib

			# EN: Assign value to original_url.
			# JP: original_url に値を代入する。
			original_url = match.group(0)

			# Find where the query/fragment starts
			# EN: Assign value to query_start.
			# JP: query_start に値を代入する。
			query_start = original_url.find('?')
			# EN: Assign value to fragment_start.
			# JP: fragment_start に値を代入する。
			fragment_start = original_url.find('#')

			# Find the earliest position of query or fragment
			# EN: Assign value to after_path_start.
			# JP: after_path_start に値を代入する。
			after_path_start = len(original_url)  # Default: no query/fragment
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if query_start != -1:
				# EN: Assign value to after_path_start.
				# JP: after_path_start に値を代入する。
				after_path_start = min(after_path_start, query_start)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if fragment_start != -1:
				# EN: Assign value to after_path_start.
				# JP: after_path_start に値を代入する。
				after_path_start = min(after_path_start, fragment_start)

			# Split URL into base (up to path) and after_path (query + fragment)
			# EN: Assign value to base_url.
			# JP: base_url に値を代入する。
			base_url = original_url[:after_path_start]
			# EN: Assign value to after_path.
			# JP: after_path に値を代入する。
			after_path = original_url[after_path_start:]

			# If after_path is within the limit, don't shorten
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(after_path) <= self._url_shortening_limit:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return original_url

			# If after_path is too long, truncate and add hash
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if after_path:
				# EN: Assign value to truncated_after_path.
				# JP: truncated_after_path に値を代入する。
				truncated_after_path = after_path[: self._url_shortening_limit]
				# Create a short hash of the full after_path content
				# EN: Assign value to hash_obj.
				# JP: hash_obj に値を代入する。
				hash_obj = hashlib.md5(after_path.encode('utf-8'))
				# EN: Assign value to short_hash.
				# JP: short_hash に値を代入する。
				short_hash = hash_obj.hexdigest()[:7]
				# Create shortened URL
				# EN: Assign value to shortened.
				# JP: shortened に値を代入する。
				shortened = f'{base_url}{truncated_after_path}...{short_hash}'
				# Only use shortened URL if it's actually shorter than the original
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if len(shortened) < len(original_url):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					replaced_urls[shortened] = original_url
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return shortened

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return original_url

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return URL_PATTERN.sub(replace_url, text), replaced_urls

	# EN: Define function `_process_messsages_and_replace_long_urls_shorter_ones`.
	# JP: 関数 `_process_messsages_and_replace_long_urls_shorter_ones` を定義する。
	def _process_messsages_and_replace_long_urls_shorter_ones(self, input_messages: list[BaseMessage]) -> dict[str, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Replace long URLs with shorter ones
		? @dev edits input_messages in place

		returns:
			tuple[filtered_input_messages, urls we replaced {shorter_url: original_url}]
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.llm.messages import AssistantMessage, UserMessage

		# EN: Assign annotated value to urls_replaced.
		# JP: urls_replaced に型付きの値を代入する。
		urls_replaced: dict[str, str] = {}

		# Process each message, in place
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for message in input_messages:
			# no need to process SystemMessage, we have control over that anyway
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(message, (UserMessage, AssistantMessage)):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(message.content, str):
					# Simple string content
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					message.content, replaced_urls = self._replace_urls_in_text(message.content)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					urls_replaced.update(replaced_urls)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(message.content, list):
					# List of content parts
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for part in message.content:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if isinstance(part, ContentPartTextParam):
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							part.text, replaced_urls = self._replace_urls_in_text(part.text)
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							urls_replaced.update(replaced_urls)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return urls_replaced

	# EN: Define function `_recursive_process_all_strings_inside_pydantic_model`.
	# JP: 関数 `_recursive_process_all_strings_inside_pydantic_model` を定義する。
	@staticmethod
	def _recursive_process_all_strings_inside_pydantic_model(model: BaseModel, url_replacements: dict[str, str]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Recursively process all strings inside a Pydantic model, replacing shortened URLs with originals in place."""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for field_name, field_value in model.__dict__.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(field_value, str):
				# Replace shortened URLs with original URLs in string
				# EN: Assign value to processed_string.
				# JP: processed_string に値を代入する。
				processed_string = Agent._replace_shortened_urls_in_string(field_value, url_replacements)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				setattr(model, field_name, processed_string)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(field_value, BaseModel):
				# Recursively process nested Pydantic models
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				Agent._recursive_process_all_strings_inside_pydantic_model(field_value, url_replacements)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(field_value, dict):
				# Process dictionary values in place
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				Agent._recursive_process_dict(field_value, url_replacements)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(field_value, (list, tuple)):
				# EN: Assign value to processed_value.
				# JP: processed_value に値を代入する。
				processed_value = Agent._recursive_process_list_or_tuple(field_value, url_replacements)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				setattr(model, field_name, processed_value)

	# EN: Define function `_recursive_process_dict`.
	# JP: 関数 `_recursive_process_dict` を定義する。
	@staticmethod
	def _recursive_process_dict(dictionary: dict, url_replacements: dict[str, str]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Helper method to process dictionaries."""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for k, v in dictionary.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(v, str):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				dictionary[k] = Agent._replace_shortened_urls_in_string(v, url_replacements)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(v, BaseModel):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				Agent._recursive_process_all_strings_inside_pydantic_model(v, url_replacements)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(v, dict):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				Agent._recursive_process_dict(v, url_replacements)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(v, (list, tuple)):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				dictionary[k] = Agent._recursive_process_list_or_tuple(v, url_replacements)

	# EN: Define function `_recursive_process_list_or_tuple`.
	# JP: 関数 `_recursive_process_list_or_tuple` を定義する。
	@staticmethod
	def _recursive_process_list_or_tuple(container: list | tuple, url_replacements: dict[str, str]) -> list | tuple:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Helper method to process lists and tuples."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(container, tuple):
			# For tuples, create a new tuple with processed items
			# EN: Assign value to processed_items.
			# JP: processed_items に値を代入する。
			processed_items = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for item in container:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(item, str):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					processed_items.append(Agent._replace_shortened_urls_in_string(item, url_replacements))
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(item, BaseModel):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					Agent._recursive_process_all_strings_inside_pydantic_model(item, url_replacements)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					processed_items.append(item)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(item, dict):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					Agent._recursive_process_dict(item, url_replacements)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					processed_items.append(item)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(item, (list, tuple)):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					processed_items.append(Agent._recursive_process_list_or_tuple(item, url_replacements))
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					processed_items.append(item)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return tuple(processed_items)
		else:
			# For lists, modify in place
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, item in enumerate(container):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(item, str):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					container[i] = Agent._replace_shortened_urls_in_string(item, url_replacements)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(item, BaseModel):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					Agent._recursive_process_all_strings_inside_pydantic_model(item, url_replacements)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(item, dict):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					Agent._recursive_process_dict(item, url_replacements)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(item, (list, tuple)):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					container[i] = Agent._recursive_process_list_or_tuple(item, url_replacements)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return container

	# EN: Define function `_replace_shortened_urls_in_string`.
	# JP: 関数 `_replace_shortened_urls_in_string` を定義する。
	@staticmethod
	def _replace_shortened_urls_in_string(text: str, url_replacements: dict[str, str]) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Replace all shortened URLs in a string with their original URLs."""
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = text
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for shortened_url, original_url in url_replacements.items():
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = result.replace(shortened_url, original_url)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result

	# endregion - URL replacement

	# EN: Define async function `get_model_output`.
	# JP: 非同期関数 `get_model_output` を定義する。
	@time_execution_async('--get_next_action')
	@observe_debug(ignore_input=True, ignore_output=True, name='get_model_output')
	async def get_model_output(self, input_messages: list[BaseMessage]) -> AgentOutput:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get next action from LLM based on current state"""

		# EN: Assign value to urls_replaced.
		# JP: urls_replaced に値を代入する。
		urls_replaced = self._process_messsages_and_replace_long_urls_shorter_ones(input_messages)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to response.
			# JP: response に値を代入する。
			response = await self.llm.ainvoke(input_messages, output_format=self.AgentOutput)
			# EN: Assign value to parsed.
			# JP: parsed に値を代入する。
			parsed = response.completion

			# Replace any shortened URLs in the LLM response back to original URLs
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if urls_replaced:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._recursive_process_all_strings_inside_pydantic_model(parsed, urls_replaced)

			# cut the number of actions to max_actions_per_step if needed
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(parsed.action) > self.settings.max_actions_per_step:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				parsed.action = parsed.action[: self.settings.max_actions_per_step]

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not (hasattr(self.state, 'paused') and (self.state.paused or self.state.stopped)):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				log_response(parsed, self.tools.registry.registry, self.logger)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._log_next_action_summary(parsed)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return parsed
		except ValidationError:
			# Just re-raise - Pydantic's validation errors are already descriptive
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define function `_log_agent_run`.
	# JP: 関数 `_log_agent_run` を定義する。
	def _log_agent_run(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log the agent run"""
		# Blue color for task
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.info(f'\033[34m🚀 Task: {self.task}\033[0m')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🤖 Browser-Use Library Version {self.version} ({self.source})')

	# EN: Define function `_log_first_step_startup`.
	# JP: 関数 `_log_first_step_startup` を定義する。
	def _log_first_step_startup(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log startup message only on the first step"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(self.history.history) == 0:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'🧠 Starting a browser-use version {self.version} with model={self.llm.model}')

	# EN: Define function `_log_step_context`.
	# JP: 関数 `_log_step_context` を定義する。
	def _log_step_context(self, browser_state_summary: BrowserStateSummary) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log step context information"""
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = browser_state_summary.url if browser_state_summary else ''
		# EN: Assign value to url_short.
		# JP: url_short に値を代入する。
		url_short = url[:50] + '...' if len(url) > 50 else url
		# EN: Assign value to interactive_count.
		# JP: interactive_count に値を代入する。
		interactive_count = len(browser_state_summary.dom_state.selector_map) if browser_state_summary else 0
		# EN: Assign value to current_step.
		# JP: current_step に値を代入する。
		current_step = self._current_step_number()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.info('\n')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.info(f'📍 Step {current_step}:')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'Evaluating page with {interactive_count} interactive elements on: {url_short}')

	# EN: Define function `_log_next_action_summary`.
	# JP: 関数 `_log_next_action_summary` を定義する。
	def _log_next_action_summary(self, parsed: 'AgentOutput') -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log a comprehensive summary of the next action(s)"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not (self.logger.isEnabledFor(logging.DEBUG) and parsed.action):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to action_count.
		# JP: action_count に値を代入する。
		action_count = len(parsed.action)

		# Collect action details
		# EN: Assign value to action_details.
		# JP: action_details に値を代入する。
		action_details = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, action in enumerate(parsed.action):
			# EN: Assign value to action_data.
			# JP: action_data に値を代入する。
			action_data = action.model_dump(exclude_unset=True)
			# EN: Assign value to action_name.
			# JP: action_name に値を代入する。
			action_name = next(iter(action_data.keys())) if action_data else 'unknown'
			# EN: Assign value to action_params.
			# JP: action_params に値を代入する。
			action_params = action_data.get(action_name, {}) if action_data else {}

			# Format key parameters concisely
			# EN: Assign value to param_summary.
			# JP: param_summary に値を代入する。
			param_summary = []
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(action_params, dict):
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for key, value in action_params.items():
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if key == 'index':
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						param_summary.append(f'#{value}')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key == 'text' and isinstance(value, str):
						# EN: Assign value to text_preview.
						# JP: text_preview に値を代入する。
						text_preview = value[:30] + '...' if len(value) > 30 else value
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						param_summary.append(f'text="{text_preview}"')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key == 'url':
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						param_summary.append(f'url="{value}"')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key == 'success':
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						param_summary.append(f'success={value}')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif isinstance(value, (str, int, bool)):
						# EN: Assign value to val_str.
						# JP: val_str に値を代入する。
						val_str = str(value)[:30] + '...' if len(str(value)) > 30 else str(value)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						param_summary.append(f'{key}={val_str}')

			# EN: Assign value to param_str.
			# JP: param_str に値を代入する。
			param_str = f'({", ".join(param_summary)})' if param_summary else ''
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			action_details.append(f'{action_name}{param_str}')

		# Create summary based on single vs multi-action
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if action_count == 1:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'☝️ Decided next action: {action_name}{param_str}')
		else:
			# EN: Assign value to summary_lines.
			# JP: summary_lines に値を代入する。
			summary_lines = [f'✌️ Decided next {action_count} multi-actions:']
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, detail in enumerate(action_details):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				summary_lines.append(f'          {i + 1}. {detail}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info('\n'.join(summary_lines))

	# EN: Define function `_log_step_completion_summary`.
	# JP: 関数 `_log_step_completion_summary` を定義する。
	def _log_step_completion_summary(self, step_start_time: float, result: list[ActionResult]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log step completion summary with action count, timing, and success/failure stats"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not result:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to step_duration.
		# JP: step_duration に値を代入する。
		step_duration = time.time() - step_start_time
		# EN: Assign value to action_count.
		# JP: action_count に値を代入する。
		action_count = len(result)

		# Count success and failures
		# EN: Assign value to success_count.
		# JP: success_count に値を代入する。
		success_count = sum(1 for r in result if not r.error)
		# EN: Assign value to failure_count.
		# JP: failure_count に値を代入する。
		failure_count = action_count - success_count

		# Format success/failure indicators
		# EN: Assign value to success_indicator.
		# JP: success_indicator に値を代入する。
		success_indicator = f'✅ {success_count}' if success_count > 0 else ''
		# EN: Assign value to failure_indicator.
		# JP: failure_indicator に値を代入する。
		failure_indicator = f'❌ {failure_count}' if failure_count > 0 else ''
		# EN: Assign value to status_parts.
		# JP: status_parts に値を代入する。
		status_parts = [part for part in [success_indicator, failure_indicator] if part]
		# EN: Assign value to status_str.
		# JP: status_str に値を代入する。
		status_str = ' | '.join(status_parts) if status_parts else '✅ 0'

		# EN: Assign value to current_step.
		# JP: current_step に値を代入する。
		current_step = self._current_step_number()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(
			f'📍 Step {current_step}: Ran {action_count} action{"" if action_count == 1 else "s"} in {step_duration:.2f}s: {status_str}'
		)

	# EN: Define function `_log_agent_event`.
	# JP: 関数 `_log_agent_event` を定義する。
	def _log_agent_event(self, max_steps: int, agent_run_error: str | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Sent the agent event for this run to telemetry"""

		# EN: Assign value to token_summary.
		# JP: token_summary に値を代入する。
		token_summary = self.token_cost_service.get_usage_tokens_for_model(self.llm.model)

		# Prepare action_history data correctly
		# EN: Assign value to action_history_data.
		# JP: action_history_data に値を代入する。
		action_history_data = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for item in self.history.history:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if item.model_output and item.model_output.action:
				# Convert each ActionModel in the step to its dictionary representation
				# EN: Assign value to step_actions.
				# JP: step_actions に値を代入する。
				step_actions = [
					action.model_dump(exclude_unset=True)
					for action in item.model_output.action
					if action  # Ensure action is not None if list allows it
				]
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				action_history_data.append(step_actions)
			else:
				# Append None or [] if a step had no actions or no model output
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				action_history_data.append(None)

		# EN: Assign value to final_res.
		# JP: final_res に値を代入する。
		final_res = self.history.final_result()
		# EN: Assign value to final_result_str.
		# JP: final_result_str に値を代入する。
		final_result_str = json.dumps(final_res) if final_res is not None else None

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.telemetry.capture(
			AgentTelemetryEvent(
				task=self.task,
				model=self.llm.model,
				model_provider=self.llm.provider,
				max_steps=max_steps,
				max_actions_per_step=self.settings.max_actions_per_step,
				use_vision=self.settings.use_vision,
				version=self.version,
				source=self.source,
				cdp_url=urlparse(self.browser_session.cdp_url).hostname
				if self.browser_session and self.browser_session.cdp_url
				else None,
				action_errors=self.history.errors(),
				action_history=action_history_data,
				urls_visited=self.history.urls(),
				steps=self.steps_completed_in_current_run,
				total_input_tokens=token_summary.prompt_tokens,
				total_duration_seconds=self.history.total_duration_seconds(),
				success=self.history.is_successful(),
				final_result_response=final_result_str,
				error_message=agent_run_error,
			)
		)

	# EN: Define async function `take_step`.
	# JP: 非同期関数 `take_step` を定義する。
	async def take_step(self, step_info: AgentStepInfo | None = None) -> tuple[bool, bool]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Take a step

		Returns:
			Tuple[bool, bool]: (is_done, is_valid)
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if step_info is not None and step_info.step_number == 0:
			# First step
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._log_first_step_startup()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._execute_initial_actions()

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.step(step_info)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history.is_done():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.log_completion()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.register_done_callback:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if inspect.iscoroutinefunction(self.register_done_callback):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.register_done_callback(self.history)
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.register_done_callback(self.history)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True, True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False, False

	# EN: Define function `_extract_url_from_task`.
	# JP: 関数 `_extract_url_from_task` を定義する。
	def _extract_url_from_task(self, task: str) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract URL from task string using naive pattern matching."""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import re

		# Remove email addresses from task before looking for URLs
		# EN: Assign value to task_without_emails.
		# JP: task_without_emails に値を代入する。
		task_without_emails = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', task)

		# Look for common URL patterns
		# EN: Assign value to patterns.
		# JP: patterns に値を代入する。
		patterns = [
			r'https?://[^\s<>"\']+',  # Full URLs with http/https
			r'(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}(?:/[^\s<>"\']*)?',  # Domain names with subdomains and optional paths
		]

		# EN: Assign value to found_urls.
		# JP: found_urls に値を代入する。
		found_urls = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for pattern in patterns:
			# EN: Assign value to matches.
			# JP: matches に値を代入する。
			matches = re.finditer(pattern, task_without_emails)
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for match in matches:
				# EN: Assign value to url.
				# JP: url に値を代入する。
				url = match.group(0)

				# Remove trailing punctuation that's not part of URLs
				# EN: Assign value to url.
				# JP: url に値を代入する。
				url = re.sub(r'[.,;:!?()\[\]]+$', '', url)
				# Add https:// if missing
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not url.startswith(('http://', 'https://')):
					# EN: Assign value to url.
					# JP: url に値を代入する。
					url = 'https://' + url
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				found_urls.append(url)

		# EN: Assign value to unique_urls.
		# JP: unique_urls に値を代入する。
		unique_urls = list(set(found_urls))
		# If multiple URLs found, skip directly_open_urling
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(unique_urls) > 1:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Multiple URLs found ({len(found_urls)}), skipping directly_open_url to avoid ambiguity')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# If exactly one URL found, return it
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(unique_urls) == 1:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return unique_urls[0]

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `run`.
	# JP: 非同期関数 `run` を定義する。
	@observe(name='agent.run', metadata={'task': '{{task}}', 'debug': '{{debug}}'})
	@time_execution_async('--run')
	async def run(
		self,
		max_steps: int = 100,
		on_step_start: AgentHookFunc | None = None,
		on_step_end: AgentHookFunc | None = None,
	) -> AgentHistoryList[AgentStructuredOutput]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute the task with maximum number of steps"""

		# EN: Assign value to loop.
		# JP: loop に値を代入する。
		loop = asyncio.get_event_loop()
		# EN: Assign annotated value to agent_run_error.
		# JP: agent_run_error に型付きの値を代入する。
		agent_run_error: str | None = None  # Initialize error tracking variable
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._force_exit_telemetry_logged = False  # ADDED: Flag for custom telemetry on force exit

		# Set up the  signal handler with callbacks specific to this agent
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.utils import SignalHandler

		# Define the custom exit callback function for second CTRL+C
		# EN: Define function `on_force_exit_log_telemetry`.
		# JP: 関数 `on_force_exit_log_telemetry` を定義する。
		def on_force_exit_log_telemetry():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._log_agent_event(max_steps=max_steps, agent_run_error='SIGINT: Cancelled by user')
			# NEW: Call the flush method on the telemetry instance
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(self, 'telemetry') and self.telemetry:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.telemetry.flush()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._force_exit_telemetry_logged = True  # Set the flag

		# EN: Assign value to signal_handler.
		# JP: signal_handler に値を代入する。
		signal_handler = SignalHandler(
			loop=loop,
			pause_callback=self.pause,
			resume_callback=self.resume,
			custom_exit_callback=on_force_exit_log_telemetry,  # Pass the new telemetrycallback
			exit_on_second_int=True,
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		signal_handler.register()

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.running = True
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.state.step_offset = max(0, self.state.n_steps - 1)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.state.consecutive_failures = 0

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._log_agent_run()

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'🔧 Agent setup: Agent Session ID {self.session_id[-4:]}, Task ID {self.task_id[-4:]}, Browser Session ID {self.browser_session.id[-4:] if self.browser_session else "None"} {"(connecting via CDP)" if (self.browser_session and self.browser_session.cdp_url) else "(launching local browser)"}'
			)

			# Initialize timing for session and task
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._session_start_time = time.time()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._task_start_time = self._session_start_time  # Initialize task start time

			# Only dispatch session events if this is the first run
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.state.session_initialized:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.enable_cloud_sync:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('📡 Dispatching CreateAgentSessionEvent...')
					# Emit CreateAgentSessionEvent at the START of run()
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.eventbus.dispatch(CreateAgentSessionEvent.from_agent(self))

					# Brief delay to ensure session is created in backend before sending task
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(0.2)

				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.state.session_initialized = True

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.enable_cloud_sync:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('📡 Dispatching CreateAgentTaskEvent...')
				# Emit CreateAgentTaskEvent at the START of run()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.eventbus.dispatch(CreateAgentTaskEvent.from_agent(self))

			# Start browser session and attach watchdogs
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.browser_session.start()

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._execute_initial_actions()
			# Log startup message on first step (only if we haven't already done steps)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._log_first_step_startup()

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'🔄 Starting main execution loop with max {max_steps} steps...')
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for step in range(max_steps):
				# Use the consolidated pause state management
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.state.paused:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'⏸️ Step {step}: Agent paused, waiting to resume...')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._external_pause_event.wait()
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					signal_handler.reset()

				# Check if we should stop due to too many failures, if final_response_after_failure is True, we try one last time
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if (self.state.consecutive_failures) >= self.settings.max_failures + int(
					self.settings.final_response_after_failure
				):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'❌ Stopping due to {self.settings.max_failures} consecutive failures')
					# EN: Assign value to agent_run_error.
					# JP: agent_run_error に値を代入する。
					agent_run_error = f'Stopped due to {self.settings.max_failures} consecutive failures'
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

				# Check control flags before each step
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.state.stopped:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.info('🛑 Agent stopped')
					# EN: Assign value to agent_run_error.
					# JP: agent_run_error に値を代入する。
					agent_run_error = 'Agent stopped programmatically'
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if on_step_start is not None:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await on_step_start(self)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'🚶 Starting step {step + 1}/{max_steps}...')
				# EN: Assign value to step_info.
				# JP: step_info に値を代入する。
				step_info = AgentStepInfo(step_number=step, max_steps=max_steps)

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# When step_timeout is None or <=0, allow the step to run indefinitely.
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if not self.settings.step_timeout or self.settings.step_timeout <= 0:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self.step(step_info)
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.wait_for(
							self.step(step_info),
							timeout=self.settings.step_timeout,
						)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'✅ Completed step {step + 1}/{max_steps}')
				except TimeoutError:
					# Handle step timeout gracefully
					# EN: Assign value to timeout_seconds.
					# JP: timeout_seconds に値を代入する。
					timeout_seconds = self.settings.step_timeout
					# EN: Assign value to error_msg.
					# JP: error_msg に値を代入する。
					error_msg = (
						f'Step {step + 1} timed out after {timeout_seconds} seconds'
						if timeout_seconds
						else f'Step {step + 1} timed out'
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'⏰ {error_msg}')
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					self.state.consecutive_failures += 1
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.state.last_result = [ActionResult(error=error_msg)]

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if on_step_end is not None:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await on_step_end(self)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.history.is_done():
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'🎯 Task completed after {step + 1} steps!')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.log_completion()

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self.register_done_callback:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if inspect.iscoroutinefunction(self.register_done_callback):
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await self.register_done_callback(self.history)
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.register_done_callback(self.history)

					# Task completed
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break
			else:
				# EN: Assign value to agent_run_error.
				# JP: agent_run_error に値を代入する。
				agent_run_error = 'Failed to complete task in maximum steps'

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.history.add_item(
					AgentHistory(
						model_output=None,
						result=[ActionResult(error=agent_run_error, include_in_memory=True)],
						state=BrowserStateHistory(
							url='',
							title='',
							tabs=[],
							interacted_element=[],
							screenshot_path=None,
						),
						metadata=None,
					)
				)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'❌ {agent_run_error}')

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('📊 Collecting usage summary...')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.history.usage = await self.token_cost_service.get_usage_summary()

			# set the model output schema and call it on the fly
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.history._output_model_schema is None and self.output_model_schema is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.history._output_model_schema = self.output_model_schema

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🏁 Agent.run() completed successfully')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.history

		except KeyboardInterrupt:
			# Already handled by our signal handler, but catch any direct KeyboardInterrupt as well
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('Got KeyboardInterrupt during execution, returning current history')
			# EN: Assign value to agent_run_error.
			# JP: agent_run_error に値を代入する。
			agent_run_error = 'KeyboardInterrupt'

			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.history.usage = await self.token_cost_service.get_usage_summary()

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.history

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'Agent run failed with exception: {e}', exc_info=True)
			# EN: Assign value to agent_run_error.
			# JP: agent_run_error に値を代入する。
			agent_run_error = str(e)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise e

		finally:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.running = False
			# Log token usage summary
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.token_cost_service.log_usage_summary()

			# Unregister signal handlers before cleanup
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			signal_handler.unregister()

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self._force_exit_telemetry_logged:  # MODIFIED: Check the flag
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._log_agent_event(max_steps=max_steps, agent_run_error=agent_run_error)
				except Exception as log_e:  # Catch potential errors during logging itself
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'Failed to log telemetry event: {log_e}', exc_info=True)
			else:
				# ADDED: Info message when custom telemetry for SIGINT was already logged
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('Telemetry for force exit (SIGINT) was logged by custom exit callback.')

			# NOTE: CreateAgentSessionEvent and CreateAgentTaskEvent are now emitted at the START of run()
			# to match backend requirements for CREATE events to be fired when entities are created,
			# not when they are completed

			# Emit UpdateAgentTaskEvent at the END of run() with final task state
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.enable_cloud_sync:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.eventbus.dispatch(UpdateAgentTaskEvent.from_agent(self))

			# Generate GIF if needed before stopping event bus
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.settings.generate_gif:
				# EN: Assign annotated value to output_path.
				# JP: output_path に型付きの値を代入する。
				output_path: str = 'agent_history.gif'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(self.settings.generate_gif, str):
					# EN: Assign value to output_path.
					# JP: output_path に値を代入する。
					output_path = self.settings.generate_gif

				# Lazy import gif module to avoid heavy startup cost
				# EN: Import required modules.
				# JP: 必要なモジュールをインポートする。
				from browser_use.agent.gif import create_history_gif

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				create_history_gif(task=self.task, history=self.history, output_path=output_path)

				# Only emit output file event if GIF was actually created
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if Path(output_path).exists():
					# EN: Assign value to output_event.
					# JP: output_event に値を代入する。
					output_event = await CreateAgentOutputFileEvent.from_agent_and_file(self, output_path)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.eventbus.dispatch(output_event)

			# Wait briefly for cloud auth to start and print the URL, but don't block for completion
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.enable_cloud_sync and hasattr(self, 'cloud_sync') and self.cloud_sync is not None:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.cloud_sync.auth_task and not self.cloud_sync.auth_task.done():
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# Wait up to 1 second for auth to start and print URL
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.wait_for(self.cloud_sync.auth_task, timeout=1.0)
					except TimeoutError:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.debug('Cloud authentication started - continuing in background')
					except Exception as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.debug(f'Cloud authentication error: {e}')

			# Stop the event bus gracefully, waiting for all events to be processed
			# Use longer timeout to avoid deadlocks in tests with multiple agents
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.eventbus.stop(timeout=3.0)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._reset_eventbus()

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.close()

	# EN: Define async function `multi_act`.
	# JP: 非同期関数 `multi_act` を定義する。
	@observe_debug(ignore_input=True, ignore_output=True)
	@time_execution_async('--multi_act')
	async def multi_act(
		self,
		actions: list[ActionModel],
		check_for_new_elements: bool = True,
	) -> list[ActionResult]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute multiple actions"""
		# EN: Assign annotated value to results.
		# JP: results に型付きの値を代入する。
		results: list[ActionResult] = []
		# EN: Assign value to time_elapsed.
		# JP: time_elapsed に値を代入する。
		time_elapsed = 0
		# EN: Assign value to total_actions.
		# JP: total_actions に値を代入する。
		total_actions = len(actions)

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session is not None, 'BrowserSession is not set up'
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				self.browser_session._cached_browser_state_summary is not None
				and self.browser_session._cached_browser_state_summary.dom_state is not None
			):
				# EN: Assign value to cached_selector_map.
				# JP: cached_selector_map に値を代入する。
				cached_selector_map = dict(self.browser_session._cached_browser_state_summary.dom_state.selector_map)
				# EN: Assign value to cached_element_hashes.
				# JP: cached_element_hashes に値を代入する。
				cached_element_hashes = {e.parent_branch_hash() for e in cached_selector_map.values()}
			else:
				# EN: Assign value to cached_selector_map.
				# JP: cached_selector_map に値を代入する。
				cached_selector_map = {}
				# EN: Assign value to cached_element_hashes.
				# JP: cached_element_hashes に値を代入する。
				cached_element_hashes = set()
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'Error getting cached selector map: {e}')
			# EN: Assign value to cached_selector_map.
			# JP: cached_selector_map に値を代入する。
			cached_selector_map = {}
			# EN: Assign value to cached_element_hashes.
			# JP: cached_element_hashes に値を代入する。
			cached_element_hashes = set()

		# await self.browser_session.remove_highlights()

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, action in enumerate(actions):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if i > 0:
				# ONLY ALLOW TO CALL `done` IF IT IS A SINGLE ACTION
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if action.model_dump(exclude_unset=True).get('done') is not None:
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f'Done action is allowed only as a single action - stopped after action {i} / {total_actions}.'
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(msg)
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

			# DOM synchronization check - verify element indexes are still valid AFTER first action
			# This prevents stale element detection but doesn't refresh before execution
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if action.get_index() is not None and i != 0:
				# EN: Assign value to new_browser_state_summary.
				# JP: new_browser_state_summary に値を代入する。
				new_browser_state_summary = await self.browser_session.get_browser_state_summary(
					cache_clickable_elements_hashes=False,
					include_screenshot=False,
				)
				# EN: Assign value to new_selector_map.
				# JP: new_selector_map に値を代入する。
				new_selector_map = new_browser_state_summary.dom_state.selector_map

				# Detect index change after previous action
				# EN: Assign value to orig_target.
				# JP: orig_target に値を代入する。
				orig_target = cached_selector_map.get(action.get_index())
				# EN: Assign value to orig_target_hash.
				# JP: orig_target_hash に値を代入する。
				orig_target_hash = orig_target.parent_branch_hash() if orig_target else None

				# EN: Assign value to new_target.
				# JP: new_target に値を代入する。
				new_target = new_selector_map.get(action.get_index())  # type: ignore
				# EN: Assign value to new_target_hash.
				# JP: new_target_hash に値を代入する。
				new_target_hash = new_target.parent_branch_hash() if new_target else None

				# EN: Define function `get_remaining_actions_str`.
				# JP: 関数 `get_remaining_actions_str` を定義する。
				def get_remaining_actions_str(actions: list[ActionModel], index: int) -> str:
					# EN: Assign value to remaining_actions.
					# JP: remaining_actions に値を代入する。
					remaining_actions = []
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for remaining_action in actions[index:]:
						# EN: Assign value to action_data.
						# JP: action_data に値を代入する。
						action_data = remaining_action.model_dump(exclude_unset=True)
						# EN: Assign value to action_name.
						# JP: action_name に値を代入する。
						action_name = next(iter(action_data.keys())) if action_data else 'unknown'
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						remaining_actions.append(action_name)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ', '.join(remaining_actions)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if orig_target_hash != new_target_hash:
					# Get names of remaining actions that won't be executed
					# EN: Assign value to remaining_actions_str.
					# JP: remaining_actions_str に値を代入する。
					remaining_actions_str = get_remaining_actions_str(actions, i)
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f'Page changed after action: actions {remaining_actions_str} are not yet executed'
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info(msg)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					results.append(
						ActionResult(
							extracted_content=msg,
							include_in_memory=True,
							long_term_memory=msg,
						)
					)
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

				# Check for new elements that appeared
				# EN: Assign value to new_element_hashes.
				# JP: new_element_hashes に値を代入する。
				new_element_hashes = {e.parent_branch_hash() for e in new_selector_map.values()}
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if check_for_new_elements and not new_element_hashes.issubset(cached_element_hashes):
					# next action requires index but there are new elements on the page
					# log difference in len debug
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'New elements: {abs(len(new_element_hashes) - len(cached_element_hashes))}')
					# EN: Assign value to remaining_actions_str.
					# JP: remaining_actions_str に値を代入する。
					remaining_actions_str = get_remaining_actions_str(actions, i)
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f'Something new appeared after action {i} / {total_actions}: actions {remaining_actions_str} were not executed'
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info(msg)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					results.append(
						ActionResult(
							extracted_content=msg,
							include_in_memory=True,
							long_term_memory=msg,
						)
					)
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

			# wait between actions (only after first action)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if i > 0:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(self.browser_profile.wait_between_actions)

			# EN: Assign value to red.
			# JP: red に値を代入する。
			red = '\033[91m'
			# EN: Assign value to green.
			# JP: green に値を代入する。
			green = '\033[92m'
			# EN: Assign value to cyan.
			# JP: cyan に値を代入する。
			cyan = '\033[96m'
			# EN: Assign value to blue.
			# JP: blue に値を代入する。
			blue = '\033[34m'
			# EN: Assign value to reset.
			# JP: reset に値を代入する。
			reset = '\033[0m'

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._raise_if_stopped_or_paused()
				# Get action name from the action model
				# EN: Assign value to action_data.
				# JP: action_data に値を代入する。
				action_data = action.model_dump(exclude_unset=True)
				# EN: Assign value to action_name.
				# JP: action_name に値を代入する。
				action_name = next(iter(action_data.keys())) if action_data else 'unknown'
				# EN: Assign value to action_params.
				# JP: action_params に値を代入する。
				action_params = getattr(action, action_name, '') or str(action.model_dump(mode='json'))[:140].replace(
					'"', ''
				).replace('{', '').replace('}', '').replace("'", '').strip().strip(',')
				# Ensure action_params is always a string before checking length
				# EN: Assign value to action_params.
				# JP: action_params に値を代入する。
				action_params = str(action_params)
				# EN: Assign value to action_params.
				# JP: action_params に値を代入する。
				action_params = f'{action_params[:522]}...' if len(action_params) > 528 else action_params
				# EN: Assign value to time_start.
				# JP: time_start に値を代入する。
				time_start = time.time()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'  🦾 {blue}[ACTION {i + 1}/{total_actions}]{reset} {action_params}')

				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await self.tools.act(
					action=action,
					browser_session=self.browser_session,
					file_system=self.file_system,
					page_extraction_llm=self.settings.page_extraction_llm,
					sensitive_data=self.sensitive_data,
					available_file_paths=self.available_file_paths,
					scratchpad=self.state.scratchpad,
				)

				# EN: Assign value to time_end.
				# JP: time_end に値を代入する。
				time_end = time.time()
				# EN: Assign value to time_elapsed.
				# JP: time_elapsed に値を代入する。
				time_elapsed = time_end - time_start
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(result)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'☑️ Executed action {i + 1}/{total_actions}: {green}{action_params}{reset} in {time_elapsed:.2f}s'
				)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if results[-1].is_done or results[-1].error or i == total_actions - 1:
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

			except Exception as e:
				# Handle any exceptions during action execution
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(
					f'❌ Executing action {i + 1} failed in {time_elapsed:.2f}s {red}({action_params}) -> {type(e).__name__}: {e}{reset}'
				)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise e

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return results

	# EN: Define async function `log_completion`.
	# JP: 非同期関数 `log_completion` を定義する。
	async def log_completion(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log the completion of the task"""
		# self._task_end_time = time.time()
		# self._task_duration = self._task_end_time - self._task_start_time TODO: this is not working when using take_step
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history.is_successful():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info('✅ Task completed successfully')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info('❌ Task completed without success')

	# EN: Define async function `rerun_history`.
	# JP: 非同期関数 `rerun_history` を定義する。
	async def rerun_history(
		self,
		history: AgentHistoryList,
		max_retries: int = 3,
		skip_failures: bool = True,
		delay_between_actions: float = 2.0,
	) -> list[ActionResult]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Rerun a saved history of actions with error handling and retry logic.

		Args:
				history: The history to replay
				max_retries: Maximum number of retries per action
				skip_failures: Whether to skip failed actions or stop execution
				delay_between_actions: Delay between actions in seconds

		Returns:
				List of action results
		"""
		# Skip cloud sync session events for rerunning (we're replaying, not starting new)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.session_initialized = True

		# Initialize browser session
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.browser_session.start()

		# EN: Assign value to results.
		# JP: results に値を代入する。
		results = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, history_item in enumerate(history.history):
			# EN: Assign value to goal.
			# JP: goal に値を代入する。
			goal = history_item.model_output.current_state.next_goal if history_item.model_output else ''
			# EN: Assign value to step_num.
			# JP: step_num に値を代入する。
			step_num = history_item.metadata.step_number if history_item.metadata else i
			# EN: Assign value to step_name.
			# JP: step_name に値を代入する。
			step_name = 'Initial actions' if step_num == 0 else f'Step {step_num}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'Replaying {step_name} ({i + 1}/{len(history.history)}): {goal}')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				not history_item.model_output
				or not history_item.model_output.action
				or history_item.model_output.action == [None]
			):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'{step_name}: No action to replay, skipping')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(ActionResult(error='No action to replay'))
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Assign value to retry_count.
			# JP: retry_count に値を代入する。
			retry_count = 0
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while retry_count < max_retries:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = await self._execute_history_step(history_item, delay_between_actions)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					results.extend(result)
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

				except Exception as e:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					retry_count += 1
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if retry_count == max_retries:
						# EN: Assign value to error_msg.
						# JP: error_msg に値を代入する。
						error_msg = f'{step_name} failed after {max_retries} attempts: {str(e)}'
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.error(error_msg)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if not skip_failures:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							results.append(ActionResult(error=error_msg))
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise RuntimeError(error_msg)
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.warning(f'{step_name} failed (attempt {retry_count}/{max_retries}), retrying...')
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.sleep(delay_between_actions)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.close()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return results

	# EN: Define async function `_execute_initial_actions`.
	# JP: 非同期関数 `_execute_initial_actions` を定義する。
	async def _execute_initial_actions(self) -> None:
		# Execute initial actions if provided
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.initial_actions and not self.state.follow_up_task:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'⚡ Executing {len(self.initial_actions)} initial actions...')
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await self.multi_act(self.initial_actions, check_for_new_elements=False)
			# update result 1 to mention that its was automatically loaded
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if result and self.initial_url and result[0].long_term_memory:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				result[0].long_term_memory = f'Found initial url and automatically loaded it. {result[0].long_term_memory}'
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.state.last_result = result

			# Save initial actions to history as step 0 for rerun capability
			# Skip browser state capture for initial actions (usually just URL navigation)
			# EN: Assign value to model_output.
			# JP: model_output に値を代入する。
			model_output = self.AgentOutput(
				evaluation_previous_goal='Starting agent with initial actions',
				memory='',
				next_goal='Execute initial navigation or setup actions',
				action=self.initial_actions,
			)

			# EN: Assign value to metadata.
			# JP: metadata に値を代入する。
			metadata = StepMetadata(
				step_number=0,
				absolute_step_number=0,
				step_start_time=time.time(),
				step_end_time=time.time(),
			)

			# Create minimal browser state history for initial actions
			# EN: Assign value to state_history.
			# JP: state_history に値を代入する。
			state_history = BrowserStateHistory(
				url=self.initial_url or '',
				title='Initial Actions',
				tabs=[],
				interacted_element=[None] * len(self.initial_actions),  # No DOM elements needed
				screenshot_path=None,
			)

			# EN: Assign value to history_item.
			# JP: history_item に値を代入する。
			history_item = AgentHistory(
				model_output=model_output,
				result=result,
				state=state_history,
				metadata=metadata,
			)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.history.add_item(history_item)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('📝 Saved initial actions to history as step 0')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('Initial actions completed')

	# EN: Define async function `_execute_history_step`.
	# JP: 非同期関数 `_execute_history_step` を定義する。
	async def _execute_history_step(self, history_item: AgentHistory, delay: float) -> list[ActionResult]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute a single step from history with element validation"""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session is not None, 'BrowserSession is not set up'
		# EN: Assign value to state.
		# JP: state に値を代入する。
		state = await self.browser_session.get_browser_state_summary(
			cache_clickable_elements_hashes=False, include_screenshot=False
		)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not state or not history_item.model_output:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError('Invalid state or model output')
		# EN: Assign value to updated_actions.
		# JP: updated_actions に値を代入する。
		updated_actions = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, action in enumerate(history_item.model_output.action):
			# EN: Assign value to updated_action.
			# JP: updated_action に値を代入する。
			updated_action = await self._update_action_indices(
				history_item.state.interacted_element[i],
				action,
				state,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			updated_actions.append(updated_action)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if updated_action is None:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f'Could not find matching element {i} in current page')

		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = await self.multi_act(updated_actions)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await asyncio.sleep(delay)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result

	# EN: Define async function `_update_action_indices`.
	# JP: 非同期関数 `_update_action_indices` を定義する。
	async def _update_action_indices(
		self,
		historical_element: DOMInteractedElement | None,
		action: ActionModel,  # Type this properly based on your action model
		browser_state_summary: BrowserStateSummary,
	) -> ActionModel | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Update action indices based on current page state.
		Returns updated action or None if element cannot be found.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not historical_element or not browser_state_summary.dom_state.selector_map:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return action

		# selector_hash_map = {hash(e): e for e in browser_state_summary.dom_state.selector_map.values()}

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		highlight_index, current_element = next(
			(
				(highlight_index, element)
				for highlight_index, element in browser_state_summary.dom_state.selector_map.items()
				if element.element_hash == historical_element.element_hash
			),
			(None, None),
		)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not current_element or highlight_index is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to old_index.
		# JP: old_index に値を代入する。
		old_index = action.get_index()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if old_index != highlight_index:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			action.set_index(highlight_index)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'Element moved in DOM, updated index from {old_index} to {highlight_index}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return action

	# EN: Define async function `load_and_rerun`.
	# JP: 非同期関数 `load_and_rerun` を定義する。
	async def load_and_rerun(self, history_file: str | Path | None = None, **kwargs) -> list[ActionResult]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Load history from file and rerun it.

		Args:
				history_file: Path to the history file
				**kwargs: Additional arguments passed to rerun_history
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not history_file:
			# EN: Assign value to history_file.
			# JP: history_file に値を代入する。
			history_file = 'AgentHistory.json'
		# EN: Assign value to history.
		# JP: history に値を代入する。
		history = AgentHistoryList.load_from_file(history_file, self.AgentOutput)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await self.rerun_history(history, **kwargs)

	# EN: Define function `save_history`.
	# JP: 関数 `save_history` を定義する。
	def save_history(self, file_path: str | Path | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Save the history to a file with sensitive data filtering"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not file_path:
			# EN: Assign value to file_path.
			# JP: file_path に値を代入する。
			file_path = 'AgentHistory.json'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.history.save_to_file(file_path, sensitive_data=self.sensitive_data)

	# EN: Define function `pause`.
	# JP: 関数 `pause` を定義する。
	def pause(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Pause the agent before the next step"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\n\n⏸️ Paused the agent and left the browser open.\n\tPress [Enter] to resume or [Ctrl+C] again to quit.')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.paused = True
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._external_pause_event.clear()

	# EN: Define function `resume`.
	# JP: 関数 `resume` を定義する。
	def resume(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Resume the agent"""
		# TODO: Locally the browser got closed
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('----------------------------------------------------------------------')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('▶️  Resuming agent execution where it left off...\n')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.paused = False
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._external_pause_event.set()

	# EN: Define function `stop`.
	# JP: 関数 `stop` を定義する。
	def stop(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Stop the agent"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.info('⏹️ Agent stopping')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.state.stopped = True

		# Signal pause event to unblock any waiting code so it can check the stopped state
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._external_pause_event.set()

		# Task stopped

	# EN: Define function `_convert_initial_actions`.
	# JP: 関数 `_convert_initial_actions` を定義する。
	def _convert_initial_actions(self, actions: list[dict[str, dict[str, Any]]]) -> list[ActionModel]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert dictionary-based actions to ActionModel instances"""
		# EN: Assign value to converted_actions.
		# JP: converted_actions に値を代入する。
		converted_actions = []
		# EN: Assign value to action_model.
		# JP: action_model に値を代入する。
		action_model = self.ActionModel
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for action_dict in actions:
			# Each action_dict should have a single key-value pair
			# EN: Assign value to action_name.
			# JP: action_name に値を代入する。
			action_name = next(iter(action_dict))
			# EN: Assign value to params.
			# JP: params に値を代入する。
			params = action_dict[action_name]

			# Get the parameter model for this action from registry
			# EN: Assign value to action_info.
			# JP: action_info に値を代入する。
			action_info = self.tools.registry.registry.actions[action_name]
			# EN: Assign value to param_model.
			# JP: param_model に値を代入する。
			param_model = action_info.param_model

			# Create validated parameters using the appropriate param model
			# EN: Assign value to validated_params.
			# JP: validated_params に値を代入する。
			validated_params = param_model(**params)

			# Create ActionModel instance with the validated parameters
			# EN: Assign value to action_model.
			# JP: action_model に値を代入する。
			action_model = self.ActionModel(**{action_name: validated_params})
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			converted_actions.append(action_model)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return converted_actions

	# EN: Define function `_verify_and_setup_llm`.
	# JP: 関数 `_verify_and_setup_llm` を定義する。
	def _verify_and_setup_llm(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Verify that the LLM API keys are setup and the LLM API is responding properly.
		Also handles tool calling method detection if in auto mode.
		"""

		# Skip verification if already done
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if getattr(self.llm, '_verified_api_keys', None) is True or CONFIG.SKIP_LLM_API_KEY_VERIFICATION:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			setattr(self.llm, '_verified_api_keys', True)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

	# EN: Define function `message_manager`.
	# JP: 関数 `message_manager` を定義する。
	@property
	def message_manager(self) -> MessageManager:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._message_manager

	# EN: Define async function `close`.
	# JP: 非同期関数 `close` を定義する。
	async def close(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close all resources"""
		# EN: Assign value to eventbus_stop_timeout.
		# JP: eventbus_stop_timeout に値を代入する。
		eventbus_stop_timeout = 3.0

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Only close browser if keep_alive is False (or not set)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session is not None:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not self.browser_session.browser_profile.keep_alive:
					# Kill the browser session - this dispatches BrowserStopEvent,
					# stops the EventBus with clear=True, and recreates a fresh EventBus
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.browser_session.kill()

			# EN: Assign value to eventbus.
			# JP: eventbus に値を代入する。
			eventbus = getattr(self, 'eventbus', None)
			# EN: Assign value to cleanup_tasks.
			# JP: cleanup_tasks に値を代入する。
			cleanup_tasks = getattr(self, '_eventbus_cleanup_tasks', None)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if eventbus is not None:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await eventbus.stop(timeout=eventbus_stop_timeout)
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(
						'Failed to stop EventBus %s cleanly',
						getattr(eventbus, 'name', '<anonymous>'),
						exc_info=True,
					)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cleanup_tasks is not None:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for task in list(cleanup_tasks):
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.wait_for(asyncio.shield(task), timeout=eventbus_stop_timeout)
					except Exception:
						# EN: Assign value to task_name.
						# JP: task_name に値を代入する。
						task_name = task.get_name() if hasattr(task, 'get_name') else repr(task)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.warning(
							'EventBus cleanup task %s did not finish cleanly',
							task_name,
							exc_info=True,
						)
					finally:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						cleanup_tasks.discard(task)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				cleanup_tasks.clear()

			# EN: Assign value to reserved_name.
			# JP: reserved_name に値を代入する。
			reserved_name = getattr(self, '_reserved_eventbus_name', None)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if reserved_name:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					EventBusFactory.release(reserved_name)
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(
						'Failed to release EventBus name %s',
						reserved_name,
						exc_info=True,
					)
				finally:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._reserved_eventbus_name = None
			else:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._reserved_eventbus_name = None

			# Force garbage collection
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			gc.collect()

			# Debug: Log remaining threads and asyncio tasks
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import threading

			# EN: Assign value to threads.
			# JP: threads に値を代入する。
			threads = threading.enumerate()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'🧵 Remaining threads ({len(threads)}): {[t.name for t in threads]}')

			# Get all asyncio tasks
			# EN: Assign value to tasks.
			# JP: tasks に値を代入する。
			tasks = asyncio.all_tasks(asyncio.get_event_loop())
			# Filter out the current task (this close() coroutine)
			# EN: Assign value to other_tasks.
			# JP: other_tasks に値を代入する。
			other_tasks = [t for t in tasks if t != asyncio.current_task()]
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if other_tasks:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'⚡ Remaining asyncio tasks ({len(other_tasks)}):')
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for task in other_tasks[:10]:  # Limit to first 10 to avoid spam
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'  - {task.get_name()}: {task}')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('⚡ No remaining asyncio tasks')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'Error during cleanup: {e}')

	# EN: Define async function `_update_action_models_for_page`.
	# JP: 非同期関数 `_update_action_models_for_page` を定義する。
	async def _update_action_models_for_page(self, page_url: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update action models with page-specific actions"""
		# Create new action model with current page's filtered actions
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.ActionModel = self.tools.registry.create_action_model(page_url=page_url)
		# Update output model with the new actions
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.settings.flash_mode:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.AgentOutput = AgentOutput.type_with_custom_actions_flash_mode(self.ActionModel)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.settings.use_thinking:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.AgentOutput = AgentOutput.type_with_custom_actions(self.ActionModel)
		else:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.AgentOutput = AgentOutput.type_with_custom_actions_no_thinking(self.ActionModel)

		# Update done action model too
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.DoneActionModel = self.tools.registry.create_action_model(include_actions=['done'], page_url=page_url)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.settings.flash_mode:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.DoneAgentOutput = AgentOutput.type_with_custom_actions_flash_mode(self.DoneActionModel)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.settings.use_thinking:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.DoneAgentOutput = AgentOutput.type_with_custom_actions(self.DoneActionModel)
		else:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.DoneAgentOutput = AgentOutput.type_with_custom_actions_no_thinking(self.DoneActionModel)

	# EN: Define function `get_trace_object`.
	# JP: 関数 `get_trace_object` を定義する。
	def get_trace_object(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the trace and trace_details objects for the agent"""

		# EN: Define function `extract_task_website`.
		# JP: 関数 `extract_task_website` を定義する。
		def extract_task_website(task_text: str) -> str | None:
			# EN: Assign value to url_pattern.
			# JP: url_pattern に値を代入する。
			url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|[^\s<>"\']+\.[a-z]{2,}(?:/[^\s<>"\']*)?'
			# EN: Assign value to match.
			# JP: match に値を代入する。
			match = re.search(url_pattern, task_text, re.IGNORECASE)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return match.group(0) if match else None

		# EN: Define function `_get_complete_history_without_screenshots`.
		# JP: 関数 `_get_complete_history_without_screenshots` を定義する。
		def _get_complete_history_without_screenshots(history_data: dict[str, Any]) -> str:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'history' in history_data:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for item in history_data['history']:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'state' in item and 'screenshot' in item['state']:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						item['state']['screenshot'] = None

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return json.dumps(history_data)

		# Generate autogenerated fields
		# EN: Assign value to trace_id.
		# JP: trace_id に値を代入する。
		trace_id = uuid7str()
		# EN: Assign value to timestamp.
		# JP: timestamp に値を代入する。
		timestamp = datetime.now().isoformat()

		# Only declare variables that are used multiple times
		# EN: Assign value to structured_output.
		# JP: structured_output に値を代入する。
		structured_output = self.history.structured_output
		# EN: Assign value to structured_output_json.
		# JP: structured_output_json に値を代入する。
		structured_output_json = json.dumps(structured_output.model_dump()) if structured_output else None
		# EN: Assign value to final_result.
		# JP: final_result に値を代入する。
		final_result = self.history.final_result()
		# EN: Assign value to git_info.
		# JP: git_info に値を代入する。
		git_info = get_git_info()
		# EN: Assign value to action_history.
		# JP: action_history に値を代入する。
		action_history = self.history.action_history()
		# EN: Assign value to action_errors.
		# JP: action_errors に値を代入する。
		action_errors = self.history.errors()
		# EN: Assign value to urls.
		# JP: urls に値を代入する。
		urls = self.history.urls()
		# EN: Assign value to usage.
		# JP: usage に値を代入する。
		usage = self.history.usage

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'trace': {
				# Autogenerated fields
				'trace_id': trace_id,
				'timestamp': timestamp,
				'browser_use_version': get_browser_use_version(),
				'git_info': json.dumps(git_info) if git_info else None,
				# Direct agent properties
				'model': self.llm.model,
				'settings': json.dumps(self.settings.model_dump()) if self.settings else None,
				'task_id': self.task_id,
				'task_truncated': self.task[:20000] if len(self.task) > 20000 else self.task,
				'task_website': extract_task_website(self.task),
				# AgentHistoryList methods
				'structured_output_truncated': (
					structured_output_json[:20000]
					if structured_output_json and len(structured_output_json) > 20000
					else structured_output_json
				),
				'action_history_truncated': json.dumps(action_history) if action_history else None,
				'action_errors': json.dumps(action_errors) if action_errors else None,
				'urls': json.dumps(urls) if urls else None,
				'final_result_response_truncated': (
					final_result[:20000] if final_result and len(final_result) > 20000 else final_result
				),
				'self_report_completed': 1 if self.history.is_done() else 0,
				'self_report_success': 1 if self.history.is_successful() else 0,
				'duration': self.history.total_duration_seconds(),
				'steps_taken': self.history.number_of_steps(),
				'usage': json.dumps(usage.model_dump()) if usage else None,
			},
			'trace_details': {
				# Autogenerated fields (ensure same as trace)
				'trace_id': trace_id,
				'timestamp': timestamp,
				# Direct agent properties
				'task': self.task,
				# AgentHistoryList methods
				'structured_output': structured_output_json,
				'final_result_response': final_result,
				'complete_history': _get_complete_history_without_screenshots(
					self.history.model_dump(sensitive_data=self.sensitive_data)
				),
			},
		}

	# EN: Define async function `authenticate_cloud_sync`.
	# JP: 非同期関数 `authenticate_cloud_sync` を定義する。
	async def authenticate_cloud_sync(self, show_instructions: bool = True) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Authenticate with cloud service for future runs.

		This is useful when users want to authenticate after a task has completed
		so that future runs will sync to the cloud.

		Args:
			show_instructions: Whether to show authentication instructions to user

		Returns:
			bool: True if authentication was successful
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not hasattr(self, 'cloud_sync') or self.cloud_sync is None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('Cloud sync is not available for this agent')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await self.cloud_sync.authenticate(show_instructions=show_instructions)

	# EN: Define function `run_sync`.
	# JP: 関数 `run_sync` を定義する。
	def run_sync(
		self,
		max_steps: int = 100,
		on_step_start: AgentHookFunc | None = None,
		on_step_end: AgentHookFunc | None = None,
	) -> AgentHistoryList[AgentStructuredOutput]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Synchronous wrapper around the async run method for easier usage without asyncio."""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import asyncio

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return asyncio.run(self.run(max_steps=max_steps, on_step_start=on_step_start, on_step_end=on_step_end))

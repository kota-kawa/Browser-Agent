# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import inspect
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.logging_config import setup_logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.model_selection import apply_model_selection

# Ensure DEFAULT_LLM and OpenAI env vars reflect Multi-Agent-Platform settings
# EN: Evaluate an expression.
# JP: 式を評価する。
apply_model_selection('browser')

# Only set up logging if not in MCP mode or if explicitly requested
# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if os.environ.get('BROWSER_USE_SETUP_LOGGING', 'true').lower() != 'false':
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.config import CONFIG

	# Get log file paths from config/environment
	# EN: Assign value to debug_log_file.
	# JP: debug_log_file に値を代入する。
	debug_log_file = getattr(CONFIG, 'BROWSER_USE_DEBUG_LOG_FILE', None)
	# EN: Assign value to info_log_file.
	# JP: info_log_file に値を代入する。
	info_log_file = getattr(CONFIG, 'BROWSER_USE_INFO_LOG_FILE', None)

	# Set up logging with file handlers if specified
	# EN: Assign value to logger.
	# JP: logger に値を代入する。
	logger = setup_logging(debug_log_file=debug_log_file, info_log_file=info_log_file)
else:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import logging

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger('browser_use')

# Relax EventBus recursion guard for long nested handler chains (e.g., CloudSync)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import EventBus
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus.service import get_handler_id, get_handler_name
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus.service import logger as eventbus_logger


# EN: Define function `_patch_eventbus_recursion_limits`.
# JP: 関数 `_patch_eventbus_recursion_limits` を定義する。
def _patch_eventbus_recursion_limits() -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Allow deeper re-entrancy for safe handlers to avoid false loop errors.

	The default bubus limit raises at depth>2 which breaks long event chains when
	CloudSync listens to every event. We raise the ceiling (default 5) and skip
	depth checks for known side-effect-only handlers.
	"""

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if getattr(EventBus, '_browser_use_recursion_patched', False):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# EN: Assign value to max_depth.
	# JP: max_depth に値を代入する。
	max_depth = int(os.environ.get('BROWSER_USE_EVENTBUS_RECURSION_DEPTH', '5'))
	# EN: Assign value to warn_depth.
	# JP: warn_depth に値を代入する。
	warn_depth = max(1, max_depth - 1)
	# EN: Assign value to ignore_handlers.
	# JP: ignore_handlers に値を代入する。
	ignore_handlers = {'CloudSync.handle_event'}

	# EN: Define function `_patched_would_create_loop`.
	# JP: 関数 `_patched_would_create_loop` を定義する。
	def _patched_would_create_loop(self, event, handler):  # type: ignore[override]
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert inspect.isfunction(handler) or inspect.iscoroutinefunction(handler) or inspect.ismethod(handler), (
			f'Handler {get_handler_name(handler)} must be a sync or async function, got: {type(handler)}'
		)

		# Forwarding loop check (unchanged)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(handler, '__self__') and isinstance(handler.__self__, EventBus) and handler.__name__ == 'dispatch':
			# EN: Assign value to target_bus.
			# JP: target_bus に値を代入する。
			target_bus = handler.__self__
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target_bus.name in event.event_path:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				eventbus_logger.debug(
					f'⚠️ {self} handler {get_handler_name(handler)}#{str(id(handler))[-4:]}({event}) skipped to prevent infinite forwarding loop with {target_bus.name}'
				)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

		# EN: Assign value to handler_id.
		# JP: handler_id に値を代入する。
		handler_id = get_handler_id(handler, self)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if handler_id in event.event_results:
			# EN: Assign value to existing_result.
			# JP: existing_result に値を代入する。
			existing_result = event.event_results[handler_id]
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if existing_result.status in ('pending', 'started'):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				eventbus_logger.debug(
					f'⚠️ {self} handler {get_handler_name(handler)}#{str(id(handler))[-4:]}({event}) is already {existing_result.status} for event {event.event_id} (preventing recursive call)'
				)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif existing_result.completed_at is not None:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				eventbus_logger.debug(
					f'⚠️ {self} handler {get_handler_name(handler)}#{str(id(handler))[-4:]}({event}) already completed @ {existing_result.completed_at} for event {event.event_id} (will not re-run)'
				)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

		# EN: Assign value to is_forwarding_handler.
		# JP: is_forwarding_handler に値を代入する。
		is_forwarding_handler = (
			inspect.ismethod(handler) and isinstance(handler.__self__, EventBus) and handler.__name__ == 'dispatch'
		)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not is_forwarding_handler:
			# EN: Assign value to handler_name.
			# JP: handler_name に値を代入する。
			handler_name = get_handler_name(handler)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if handler_name not in ignore_handlers:
				# EN: Assign value to recursion_depth.
				# JP: recursion_depth に値を代入する。
				recursion_depth = self._handler_dispatched_ancestor(event, handler_id)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if recursion_depth > max_depth:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise RuntimeError(
						f'Infinite loop detected: Handler {get_handler_name(handler)}#{str(id(handler))[-4:]} '
						f'has recursively processed {recursion_depth} levels of events (max {max_depth}). '
						f'Current event: {event}, Handler: {handler_id}'
					)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif recursion_depth >= warn_depth:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					eventbus_logger.warning(
						f'⚠️ {self} handler {get_handler_name(handler)}#{str(id(handler))[-4:]} '
						f'at recursion depth {recursion_depth}/{max_depth} - deeper nesting will raise'
					)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	EventBus._would_create_loop = _patched_would_create_loop  # type: ignore[assignment]
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	EventBus._browser_use_recursion_patched = True


# EN: Evaluate an expression.
# JP: 式を評価する。
_patch_eventbus_recursion_limits()

# Monkeypatch BaseSubprocessTransport.__del__ to handle closed event loops gracefully
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from asyncio import base_subprocess

# EN: Assign value to _original_del.
# JP: _original_del に値を代入する。
_original_del = base_subprocess.BaseSubprocessTransport.__del__


# EN: Define function `_patched_del`.
# JP: 関数 `_patched_del` を定義する。
def _patched_del(self):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Patched __del__ that handles closed event loops without throwing noisy red-herring errors like RuntimeError: Event loop is closed"""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Check if the event loop is closed before calling the original
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, '_loop') and self._loop and self._loop.is_closed():
			# Event loop is closed, skip cleanup that requires the loop
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_original_del(self)
	except RuntimeError as e:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'Event loop is closed' in str(e):
			# Silently ignore this specific error
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass
		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise


# EN: Assign value to target variable.
# JP: target variable に値を代入する。
base_subprocess.BaseSubprocessTransport.__del__ = _patched_del

# Type stubs for lazy imports - fixes linter warnings
# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.agent.prompts import SystemPrompt
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.agent.service import Agent
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.agent.views import ActionModel, ActionResult, AgentHistoryList
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser import BrowserProfile, BrowserSession
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser import BrowserSession as Browser
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.dom.service import DomService
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm import models
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.anthropic.chat import ChatAnthropic
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.azure.chat import ChatAzureOpenAI
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.google.chat import ChatGoogle
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.groq.chat import ChatGroq
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.ollama.chat import ChatOllama
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.openai.chat import ChatOpenAI
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.tools.service import Controller, Tools


# Lazy imports mapping - only import when actually accessed
# EN: Assign value to _LAZY_IMPORTS.
# JP: _LAZY_IMPORTS に値を代入する。
_LAZY_IMPORTS = {
	# Agent service (heavy due to dependencies)
	'Agent': ('browser_use.agent.service', 'Agent'),
	# System prompt (moderate weight due to agent.views imports)
	'SystemPrompt': ('browser_use.agent.prompts', 'SystemPrompt'),
	# Agent views (very heavy - over 1 second!)
	'ActionModel': ('browser_use.agent.views', 'ActionModel'),
	'ActionResult': ('browser_use.agent.views', 'ActionResult'),
	'AgentHistoryList': ('browser_use.agent.views', 'AgentHistoryList'),
	'BrowserSession': ('browser_use.browser', 'BrowserSession'),
	'Browser': ('browser_use.browser', 'BrowserSession'),  # Alias for BrowserSession
	'BrowserProfile': ('browser_use.browser', 'BrowserProfile'),
	# Tools (moderate weight)
	'Tools': ('browser_use.tools.service', 'Tools'),
	'Controller': ('browser_use.tools.service', 'Controller'),  # alias
	# DOM service (moderate weight)
	'DomService': ('browser_use.dom.service', 'DomService'),
	# Chat models (very heavy imports)
	'ChatOpenAI': ('browser_use.llm.openai.chat', 'ChatOpenAI'),
	'ChatGoogle': ('browser_use.llm.google.chat', 'ChatGoogle'),
	'ChatAnthropic': ('browser_use.llm.anthropic.chat', 'ChatAnthropic'),
	'ChatGroq': ('browser_use.llm.groq.chat', 'ChatGroq'),
	'ChatAzureOpenAI': ('browser_use.llm.azure.chat', 'ChatAzureOpenAI'),
	'ChatOllama': ('browser_use.llm.ollama.chat', 'ChatOllama'),
	# LLM models module
	'models': ('browser_use.llm.models', None),
}


# EN: Define function `__getattr__`.
# JP: 関数 `__getattr__` を定義する。
def __getattr__(name: str):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Lazy import mechanism - only import modules when they're actually accessed."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if name in _LAZY_IMPORTS:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		module_path, attr_name = _LAZY_IMPORTS[name]
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from importlib import import_module

			# EN: Assign value to module.
			# JP: module に値を代入する。
			module = import_module(module_path)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if attr_name is None:
				# For modules like 'models', return the module itself
				# EN: Assign value to attr.
				# JP: attr に値を代入する。
				attr = module
			else:
				# EN: Assign value to attr.
				# JP: attr に値を代入する。
				attr = getattr(module, attr_name)
			# Cache the imported attribute in the module's globals
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			globals()[name] = attr
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return attr
		except ImportError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ImportError(f'Failed to import {name} from {module_path}: {e}') from e

	# EN: Raise an exception.
	# JP: 例外を送出する。
	raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# EN: Assign value to __all__.
# JP: __all__ に値を代入する。
__all__ = [
	'Agent',
	'BrowserSession',
	'Browser',  # Alias for BrowserSession
	'BrowserProfile',
	'Controller',
	'DomService',
	'SystemPrompt',
	'ActionResult',
	'ActionModel',
	'AgentHistoryList',
	# Chat models
	'ChatOpenAI',
	'ChatGoogle',
	'ChatAnthropic',
	'ChatGroq',
	'ChatAzureOpenAI',
	'ChatOllama',
	'Tools',
	'Controller',
	# LLM models module
	'models',
]

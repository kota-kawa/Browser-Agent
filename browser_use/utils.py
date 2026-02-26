# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import platform
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import signal
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Callable, Coroutine
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fnmatch import fnmatch
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from functools import cache, wraps
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from sys import stderr
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, ParamSpec, TypeVar
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.parse import urlparse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.constants import DEFAULT_NEW_TAB_URL
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.env_loader import load_secrets_env

# EN: Evaluate an expression.
# JP: 式を評価する。
load_secrets_env()

# Pre-compiled regex for URL detection - used in URL shortening
# EN: Assign value to URL_PATTERN.
# JP: URL_PATTERN に値を代入する。
URL_PATTERN = re.compile(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|[^\s<>"\']+\.[a-z]{2,}(?:/[^\s<>"\']*)?', re.IGNORECASE)


# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)

# Import error types - these may need to be adjusted based on actual import paths
# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from openai import BadRequestError as OpenAIBadRequestError
except ImportError:
	# EN: Assign value to OpenAIBadRequestError.
	# JP: OpenAIBadRequestError に値を代入する。
	OpenAIBadRequestError = None

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from groq import BadRequestError as GroqBadRequestError  # type: ignore[import-not-found]
except ImportError:
	# EN: Assign value to GroqBadRequestError.
	# JP: GroqBadRequestError に値を代入する。
	GroqBadRequestError = None


# Global flag to prevent duplicate exit messages
# EN: Assign value to _exiting.
# JP: _exiting に値を代入する。
_exiting = False

# Define generic type variables for return type and parameters
# EN: Assign value to R.
# JP: R に値を代入する。
R = TypeVar('R')
# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T')
# EN: Assign value to P.
# JP: P に値を代入する。
P = ParamSpec('P')


# EN: Define class `SignalHandler`.
# JP: クラス `SignalHandler` を定義する。
class SignalHandler:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A modular and reusable signal handling system for managing SIGINT (Ctrl+C), SIGTERM,
	and other signals in asyncio applications.

	This class provides:
	- Configurable signal handling for SIGINT and SIGTERM
	- Support for custom pause/resume callbacks
	- Management of event loop state across signals
	- Standardized handling of first and second Ctrl+C presses
	- Cross-platform compatibility (with simplified behavior on Windows)
	"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		loop: asyncio.AbstractEventLoop | None = None,
		pause_callback: Callable[[], None] | None = None,
		resume_callback: Callable[[], None] | None = None,
		custom_exit_callback: Callable[[], None] | None = None,
		exit_on_second_int: bool = True,
		interruptible_task_patterns: list[str] | None = None,
	):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Initialize the signal handler.

		Args:
			loop: The asyncio event loop to use. Defaults to current event loop.
			pause_callback: Function to call when system is paused (first Ctrl+C)
			resume_callback: Function to call when system is resumed
			custom_exit_callback: Function to call on exit (second Ctrl+C or SIGTERM)
			exit_on_second_int: Whether to exit on second SIGINT (Ctrl+C)
			interruptible_task_patterns: List of patterns to match task names that should be
										 canceled on first Ctrl+C (default: ['step', 'multi_act', 'get_next_action'])
		"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.loop = loop or asyncio.get_event_loop()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.pause_callback = pause_callback
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.resume_callback = resume_callback
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.custom_exit_callback = custom_exit_callback
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.exit_on_second_int = exit_on_second_int
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.interruptible_task_patterns = interruptible_task_patterns or ['step', 'multi_act', 'get_next_action']
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.is_windows = platform.system() == 'Windows'

		# Initialize loop state attributes
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._initialize_loop_state()

		# Store original signal handlers to restore them later if needed
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.original_sigint_handler = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.original_sigterm_handler = None

	# EN: Define function `_initialize_loop_state`.
	# JP: 関数 `_initialize_loop_state` を定義する。
	def _initialize_loop_state(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize loop state attributes used for signal handling."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		setattr(self.loop, 'ctrl_c_pressed', False)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		setattr(self.loop, 'waiting_for_input', False)

	# EN: Define function `register`.
	# JP: 関数 `register` を定義する。
	def register(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Register signal handlers for SIGINT and SIGTERM."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.is_windows:
				# On Windows, use simple signal handling with immediate exit on Ctrl+C
				# EN: Define function `windows_handler`.
				# JP: 関数 `windows_handler` を定義する。
				def windows_handler(sig, frame):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					print('\n\n🛑 Got Ctrl+C. Exiting immediately on Windows...\n', file=stderr)
					# Run the custom exit callback if provided
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self.custom_exit_callback:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.custom_exit_callback()
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					os._exit(0)

				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.original_sigint_handler = signal.signal(signal.SIGINT, windows_handler)
			else:
				# On Unix-like systems, use asyncio's signal handling for smoother experience
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.original_sigint_handler = self.loop.add_signal_handler(signal.SIGINT, lambda: self.sigint_handler())
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.original_sigterm_handler = self.loop.add_signal_handler(signal.SIGTERM, lambda: self.sigterm_handler())

		except Exception:
			# there are situations where signal handlers are not supported, e.g.
			# - when running in a thread other than the main thread
			# - some operating systems
			# - inside jupyter notebooks
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass

	# EN: Define function `unregister`.
	# JP: 関数 `unregister` を定義する。
	def unregister(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Unregister signal handlers and restore original handlers if possible."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.is_windows:
				# On Windows, just restore the original SIGINT handler
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.original_sigint_handler:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					signal.signal(signal.SIGINT, self.original_sigint_handler)
			else:
				# On Unix-like systems, use asyncio's signal handler removal
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.loop.remove_signal_handler(signal.SIGINT)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.loop.remove_signal_handler(signal.SIGTERM)

				# Restore original handlers if available
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.original_sigint_handler:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					signal.signal(signal.SIGINT, self.original_sigint_handler)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.original_sigterm_handler:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					signal.signal(signal.SIGTERM, self.original_sigterm_handler)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(f'Error while unregistering signal handlers: {e}')

	# EN: Define function `_handle_second_ctrl_c`.
	# JP: 関数 `_handle_second_ctrl_c` を定義する。
	def _handle_second_ctrl_c(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Handle a second Ctrl+C press by performing cleanup and exiting.
		This is shared logic used by both sigint_handler and wait_for_resume.
		"""
		# EN: Execute this statement.
		# JP: この文を実行する。
		global _exiting

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not _exiting:
			# EN: Assign value to _exiting.
			# JP: _exiting に値を代入する。
			_exiting = True

			# Call custom exit callback if provided
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.custom_exit_callback:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.custom_exit_callback()
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(f'Error in exit callback: {e}')

		# Force immediate exit - more reliable than sys.exit()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\n\n🛑  Got second Ctrl+C. Exiting immediately...\n', file=stderr)

		# Reset terminal to a clean state by sending multiple escape sequences
		# Order matters for terminal resets - we try different approaches

		# Reset terminal modes for both stdout and stderr
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\033[?25h', end='', flush=True, file=stderr)  # Show cursor
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\033[?25h', end='', flush=True)  # Show cursor

		# Reset text attributes and terminal modes
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\033[0m', end='', flush=True, file=stderr)  # Reset text attributes
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\033[0m', end='', flush=True)  # Reset text attributes

		# Disable special input modes that may cause arrow keys to output control chars
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\033[?1l', end='', flush=True, file=stderr)  # Reset cursor keys to normal mode
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\033[?1l', end='', flush=True)  # Reset cursor keys to normal mode

		# Disable bracketed paste mode
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\033[?2004l', end='', flush=True, file=stderr)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\033[?2004l', end='', flush=True)

		# Carriage return helps ensure a clean line
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\r', end='', flush=True, file=stderr)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\r', end='', flush=True)

		# these ^^ attempts dont work as far as we can tell
		# we still dont know what causes the broken input, if you know how to fix it, please let us know
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('(tip: press [Enter] once to fix escape codes appearing after chrome exit)', file=stderr)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		os._exit(0)

	# EN: Define function `sigint_handler`.
	# JP: 関数 `sigint_handler` を定義する。
	def sigint_handler(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		SIGINT (Ctrl+C) handler.

		First Ctrl+C: Cancel current step and pause.
		Second Ctrl+C: Exit immediately if exit_on_second_int is True.
		"""
		# EN: Execute this statement.
		# JP: この文を実行する。
		global _exiting

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if _exiting:
			# Already exiting, force exit immediately
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			os._exit(0)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if getattr(self.loop, 'ctrl_c_pressed', False):
			# If we're in the waiting for input state, let the pause method handle it
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if getattr(self.loop, 'waiting_for_input', False):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Second Ctrl+C - exit immediately if configured to do so
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.exit_on_second_int:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._handle_second_ctrl_c()

		# Mark that Ctrl+C was pressed
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		setattr(self.loop, 'ctrl_c_pressed', True)

		# Cancel current tasks that should be interruptible - this is crucial for immediate pausing
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._cancel_interruptible_tasks()

		# Call pause callback if provided - this sets the paused flag
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.pause_callback:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.pause_callback()
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Error in pause callback: {e}')

		# Log pause message after pause_callback is called (not before)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('----------------------------------------------------------------------', file=stderr)

	# EN: Define function `sigterm_handler`.
	# JP: 関数 `sigterm_handler` を定義する。
	def sigterm_handler(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		SIGTERM handler.

		Always exits the program completely.
		"""
		# EN: Execute this statement.
		# JP: この文を実行する。
		global _exiting
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not _exiting:
			# EN: Assign value to _exiting.
			# JP: _exiting に値を代入する。
			_exiting = True
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('\n\n🛑 SIGTERM received. Exiting immediately...\n\n', file=stderr)

			# Call custom exit callback if provided
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.custom_exit_callback:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.custom_exit_callback()

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		os._exit(0)

	# EN: Define function `_cancel_interruptible_tasks`.
	# JP: 関数 `_cancel_interruptible_tasks` を定義する。
	def _cancel_interruptible_tasks(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Cancel current tasks that should be interruptible."""
		# EN: Assign value to current_task.
		# JP: current_task に値を代入する。
		current_task = asyncio.current_task(self.loop)
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for task in asyncio.all_tasks(self.loop):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if task != current_task and not task.done():
				# EN: Assign value to task_name.
				# JP: task_name に値を代入する。
				task_name = task.get_name() if hasattr(task, 'get_name') else str(task)
				# Cancel tasks that match certain patterns
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if any(pattern in task_name for pattern in self.interruptible_task_patterns):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug(f'Cancelling task: {task_name}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					task.cancel()
					# Add exception handler to silence "Task exception was never retrieved" warnings
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					task.add_done_callback(lambda t: t.exception() if t.cancelled() else None)

		# Also cancel the current task if it's interruptible
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if current_task and not current_task.done():
			# EN: Assign value to task_name.
			# JP: task_name に値を代入する。
			task_name = current_task.get_name() if hasattr(current_task, 'get_name') else str(current_task)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if any(pattern in task_name for pattern in self.interruptible_task_patterns):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Cancelling current task: {task_name}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				current_task.cancel()

	# EN: Define function `wait_for_resume`.
	# JP: 関数 `wait_for_resume` を定義する。
	def wait_for_resume(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Wait for user input to resume or exit.

		This method should be called after handling the first Ctrl+C.
		It temporarily restores default signal handling to allow catching
		a second Ctrl+C directly.
		"""
		# Set flag to indicate we're waiting for input
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		setattr(self.loop, 'waiting_for_input', True)

		# Temporarily restore default signal handling for SIGINT
		# This ensures KeyboardInterrupt will be raised during input()
		# EN: Assign value to original_handler.
		# JP: original_handler に値を代入する。
		original_handler = signal.getsignal(signal.SIGINT)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			signal.signal(signal.SIGINT, signal.default_int_handler)
		except ValueError:
			# we are running in a thread other than the main thread
			# or signal handlers are not supported for some other reason
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass

		# EN: Assign value to green.
		# JP: green に値を代入する。
		green = '\x1b[32;1m'
		# EN: Assign value to red.
		# JP: red に値を代入する。
		red = '\x1b[31m'
		# EN: Assign value to blink.
		# JP: blink に値を代入する。
		blink = '\033[33;5m'
		# EN: Assign value to unblink.
		# JP: unblink に値を代入する。
		unblink = '\033[0m'
		# EN: Assign value to reset.
		# JP: reset に値を代入する。
		reset = '\x1b[0m'

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:  # escape code is to blink the ...
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(
				f'➡️  Press {green}[Enter]{reset} to resume or {red}[Ctrl+C]{reset} again to exit{blink}...{unblink} ',
				end='',
				flush=True,
				file=stderr,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			input()  # This will raise KeyboardInterrupt on Ctrl+C

			# Call resume callback if provided
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.resume_callback:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.resume_callback()
		except KeyboardInterrupt:
			# Use the shared method to handle second Ctrl+C
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._handle_second_ctrl_c()
		finally:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Restore our signal handler
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				signal.signal(signal.SIGINT, original_handler)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				setattr(self.loop, 'waiting_for_input', False)
			except Exception:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass

	# EN: Define function `reset`.
	# JP: 関数 `reset` を定義する。
	def reset(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Reset state after resuming."""
		# Clear the flags
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self.loop, 'ctrl_c_pressed'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			setattr(self.loop, 'ctrl_c_pressed', False)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self.loop, 'waiting_for_input'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			setattr(self.loop, 'waiting_for_input', False)


# EN: Define function `time_execution_sync`.
# JP: 関数 `time_execution_sync` を定義する。
def time_execution_sync(additional_text: str = '') -> Callable[[Callable[P, R]], Callable[P, R]]:
	# EN: Define function `decorator`.
	# JP: 関数 `decorator` を定義する。
	def decorator(func: Callable[P, R]) -> Callable[P, R]:
		# EN: Define function `wrapper`.
		# JP: 関数 `wrapper` を定義する。
		@wraps(func)
		def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
			# EN: Assign value to start_time.
			# JP: start_time に値を代入する。
			start_time = time.time()
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = func(*args, **kwargs)
			# EN: Assign value to execution_time.
			# JP: execution_time に値を代入する。
			execution_time = time.time() - start_time
			# Only log if execution takes more than 0.25 seconds
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if execution_time > 0.25:
				# EN: Assign value to self_has_logger.
				# JP: self_has_logger に値を代入する。
				self_has_logger = args and getattr(args[0], 'logger', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self_has_logger:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = getattr(args[0], 'logger')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif 'agent' in kwargs:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = getattr(kwargs['agent'], 'logger')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif 'browser_session' in kwargs:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = getattr(kwargs['browser_session'], 'logger')
				else:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = logging.getLogger(__name__)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'⏳ {additional_text.strip("-")}() took {execution_time:.2f}s')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return result

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return wrapper

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return decorator


# EN: Define function `time_execution_async`.
# JP: 関数 `time_execution_async` を定義する。
def time_execution_async(
	additional_text: str = '',
) -> Callable[[Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]]:
	# EN: Define function `decorator`.
	# JP: 関数 `decorator` を定義する。
	def decorator(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
		# EN: Define async function `wrapper`.
		# JP: 非同期関数 `wrapper` を定義する。
		@wraps(func)
		async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
			# EN: Assign value to start_time.
			# JP: start_time に値を代入する。
			start_time = time.time()
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await func(*args, **kwargs)
			# EN: Assign value to execution_time.
			# JP: execution_time に値を代入する。
			execution_time = time.time() - start_time
			# Only log if execution takes more than 0.25 seconds to avoid spamming the logs
			# you can lower this threshold locally when you're doing dev work to performance optimize stuff
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if execution_time > 0.25:
				# EN: Assign value to self_has_logger.
				# JP: self_has_logger に値を代入する。
				self_has_logger = args and getattr(args[0], 'logger', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self_has_logger:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = getattr(args[0], 'logger')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif 'agent' in kwargs:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = getattr(kwargs['agent'], 'logger')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif 'browser_session' in kwargs:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = getattr(kwargs['browser_session'], 'logger')
				else:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = logging.getLogger(__name__)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'⏳ {additional_text.strip("-")}() took {execution_time:.2f}s')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return result

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return wrapper

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return decorator


# EN: Define function `singleton`.
# JP: 関数 `singleton` を定義する。
def singleton(cls):
	# EN: Assign value to instance.
	# JP: instance に値を代入する。
	instance = [None]

	# EN: Define function `wrapper`.
	# JP: 関数 `wrapper` を定義する。
	def wrapper(*args, **kwargs):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if instance[0] is None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			instance[0] = cls(*args, **kwargs)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return instance[0]

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return wrapper


# EN: Define function `check_env_variables`.
# JP: 関数 `check_env_variables` を定義する。
def check_env_variables(keys: list[str], any_or_all=all) -> bool:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Check if all required environment variables are set"""
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return any_or_all(os.getenv(key, '').strip() for key in keys)


# EN: Define function `is_unsafe_pattern`.
# JP: 関数 `is_unsafe_pattern` を定義する。
def is_unsafe_pattern(pattern: str) -> bool:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Check if a domain pattern has complex wildcards that could match too many domains.

	Args:
		pattern: The domain pattern to check

	Returns:
		bool: True if the pattern has unsafe wildcards, False otherwise
	"""
	# Extract domain part if there's a scheme
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if '://' in pattern:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		_, pattern = pattern.split('://', 1)

	# Remove safe patterns (*.domain and domain.*)
	# EN: Assign value to bare_domain.
	# JP: bare_domain に値を代入する。
	bare_domain = pattern.replace('.*', '').replace('*.', '')

	# If there are still wildcards, it's potentially unsafe
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return '*' in bare_domain


# EN: Define function `_normalize_new_tab_candidate`.
# JP: 関数 `_normalize_new_tab_candidate` を定義する。
def _normalize_new_tab_candidate(url: str) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Normalize a URL candidate for new tab comparisons."""

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not url:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

	# EN: Assign value to normalized.
	# JP: normalized に値を代入する。
	normalized = url.strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not normalized:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

	# Normalize case for comparisons and remove a single trailing slash so
	# ``https://example.com`` and ``https://example.com/`` are treated the same.
	# EN: Assign value to normalized.
	# JP: normalized に値を代入する。
	normalized = normalized.rstrip('/')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return normalized.lower()


# EN: Define function `is_default_new_tab_url`.
# JP: 関数 `is_default_new_tab_url` を定義する。
def is_default_new_tab_url(url: str) -> bool:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return True if *url* matches the configured default new tab URL."""

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return _normalize_new_tab_candidate(url) == _normalize_new_tab_candidate(DEFAULT_NEW_TAB_URL)


# EN: Define function `is_new_tab_page`.
# JP: 関数 `is_new_tab_page` を定義する。
def is_new_tab_page(url: str) -> bool:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return True if *url* should be treated as a browser new tab page."""

	# EN: Assign value to normalized.
	# JP: normalized に値を代入する。
	normalized = _normalize_new_tab_candidate(url)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return normalized in (
		_normalize_new_tab_candidate(DEFAULT_NEW_TAB_URL),
		'about:blank',
		'chrome://new-tab-page',
		'chrome://newtab',
	)


# EN: Define function `match_url_with_domain_pattern`.
# JP: 関数 `match_url_with_domain_pattern` を定義する。
def match_url_with_domain_pattern(url: str, domain_pattern: str, log_warnings: bool = False) -> bool:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Check if a URL matches a domain pattern. SECURITY CRITICAL.

	Supports optional glob patterns and schemes:
	- *.example.com will match sub.example.com and example.com
	- *google.com will match google.com, agoogle.com, and www.google.com
	- http*://example.com will match http://example.com, https://example.com
	- chrome-extension://* will match chrome-extension://aaaaaaaaaaaa and chrome-extension://bbbbbbbbbbbbb

	When no scheme is specified, https is used by default for security.
	For example, 'example.com' will match 'https://example.com' but not 'http://example.com'.

	Note: New tab pages (about:blank, chrome://new-tab-page) must be handled at the callsite, not inside this function.

	Args:
		url: The URL to check
		domain_pattern: Domain pattern to match against
		log_warnings: Whether to log warnings about unsafe patterns

	Returns:
		bool: True if the URL matches the pattern, False otherwise
	"""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Note: new tab pages should be handled at the callsite, not here
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_new_tab_page(url):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Assign value to parsed_url.
		# JP: parsed_url に値を代入する。
		parsed_url = urlparse(url)

		# Extract only the hostname and scheme components
		# EN: Assign value to scheme.
		# JP: scheme に値を代入する。
		scheme = parsed_url.scheme.lower() if parsed_url.scheme else ''
		# EN: Assign value to domain.
		# JP: domain に値を代入する。
		domain = parsed_url.hostname.lower() if parsed_url.hostname else ''

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not scheme or not domain:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Normalize the domain pattern
		# EN: Assign value to domain_pattern.
		# JP: domain_pattern に値を代入する。
		domain_pattern = domain_pattern.lower()

		# Handle pattern with scheme
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if '://' in domain_pattern:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			pattern_scheme, pattern_domain = domain_pattern.split('://', 1)
		else:
			# EN: Assign value to pattern_scheme.
			# JP: pattern_scheme に値を代入する。
			pattern_scheme = 'https'  # Default to matching only https for security
			# EN: Assign value to pattern_domain.
			# JP: pattern_domain に値を代入する。
			pattern_domain = domain_pattern

		# Handle port in pattern (we strip ports from patterns since we already
		# extracted only the hostname from the URL)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ':' in pattern_domain and not pattern_domain.startswith(':'):
			# EN: Assign value to pattern_domain.
			# JP: pattern_domain に値を代入する。
			pattern_domain = pattern_domain.split(':', 1)[0]

		# If scheme doesn't match, return False
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not fnmatch(scheme, pattern_scheme):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Check for exact match
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if pattern_domain == '*' or domain == pattern_domain:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Handle glob patterns
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if '*' in pattern_domain:
			# Check for unsafe glob patterns
			# First, check for patterns like *.*.domain which are unsafe
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if pattern_domain.count('*.') > 1 or pattern_domain.count('.*') > 1:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if log_warnings:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = logging.getLogger(__name__)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(f'⛔️ Multiple wildcards in pattern=[{domain_pattern}] are not supported')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return False  # Don't match unsafe patterns

			# Check for wildcards in TLD part (example.*)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if pattern_domain.endswith('.*'):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if log_warnings:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = logging.getLogger(__name__)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(f'⛔️ Wildcard TLDs like in pattern=[{domain_pattern}] are not supported for security')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return False  # Don't match unsafe patterns

			# Then check for embedded wildcards
			# EN: Assign value to bare_domain.
			# JP: bare_domain に値を代入する。
			bare_domain = pattern_domain.replace('*.', '')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if '*' in bare_domain:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if log_warnings:
					# EN: Assign value to logger.
					# JP: logger に値を代入する。
					logger = logging.getLogger(__name__)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(f'⛔️ Only *.domain style patterns are supported, ignoring pattern=[{domain_pattern}]')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return False  # Don't match unsafe patterns

			# Special handling so that *.google.com also matches bare google.com
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if pattern_domain.startswith('*.'):
				# EN: Assign value to parent_domain.
				# JP: parent_domain に値を代入する。
				parent_domain = pattern_domain[2:]
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if domain == parent_domain or fnmatch(domain, parent_domain):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True

			# Normal case: match domain against pattern
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if fnmatch(domain, pattern_domain):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False
	except Exception as e:
		# EN: Assign value to logger.
		# JP: logger に値を代入する。
		logger = logging.getLogger(__name__)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'⛔️ Error matching URL {url} with pattern {domain_pattern}: {type(e).__name__}: {e}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False


# EN: Define function `merge_dicts`.
# JP: 関数 `merge_dicts` を定義する。
def merge_dicts(a: dict, b: dict, path: tuple[str, ...] = ()):
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for key in b:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if key in a:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(a[key], dict) and isinstance(b[key], dict):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				merge_dicts(a[key], b[key], path + (str(key),))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(a[key], list) and isinstance(b[key], list):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				a[key] = a[key] + b[key]
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif a[key] != b[key]:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise Exception('Conflict at ' + '.'.join(path + (str(key),)))
		else:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			a[key] = b[key]
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return a


# EN: Define function `get_browser_use_version`.
# JP: 関数 `get_browser_use_version` を定義する。
@cache
def get_browser_use_version() -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get the browser-use package version using the same logic as Agent._set_browser_use_version_and_source"""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to package_root.
		# JP: package_root に値を代入する。
		package_root = Path(__file__).parent.parent
		# EN: Assign value to pyproject_path.
		# JP: pyproject_path に値を代入する。
		pyproject_path = package_root / 'pyproject.toml'

		# Try to read version from pyproject.toml
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if pyproject_path.exists():
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import re

			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with open(pyproject_path, encoding='utf-8') as f:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = f.read()
				# EN: Assign value to match.
				# JP: match に値を代入する。
				match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if match:
					# EN: Assign value to version.
					# JP: version に値を代入する。
					version = f'{match.group(1)}'
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					os.environ['LIBRARY_VERSION'] = version  # used by bubus event_schema so all Event schemas include versioning
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return version

		# If pyproject.toml doesn't exist, try getting version from pip
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from importlib.metadata import version as get_version

		# EN: Assign value to version.
		# JP: version に値を代入する。
		version = str(get_version('browser-use'))
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		os.environ['LIBRARY_VERSION'] = version
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return version

	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Error detecting browser-use version: {type(e).__name__}: {e}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'unknown'


# EN: Define function `get_git_info`.
# JP: 関数 `get_git_info` を定義する。
@cache
def get_git_info() -> dict[str, str] | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get git information if installed from git repository"""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import subprocess

		# EN: Assign value to package_root.
		# JP: package_root に値を代入する。
		package_root = Path(__file__).parent.parent
		# EN: Assign value to git_dir.
		# JP: git_dir に値を代入する。
		git_dir = package_root / '.git'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not git_dir.exists():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Get git commit hash
		# EN: Assign value to commit_hash.
		# JP: commit_hash に値を代入する。
		commit_hash = (
			subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=package_root, stderr=subprocess.DEVNULL).decode().strip()
		)

		# Get git branch
		# EN: Assign value to branch.
		# JP: branch に値を代入する。
		branch = (
			subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=package_root, stderr=subprocess.DEVNULL)
			.decode()
			.strip()
		)

		# Get remote URL
		# EN: Assign value to remote_url.
		# JP: remote_url に値を代入する。
		remote_url = (
			subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=package_root, stderr=subprocess.DEVNULL)
			.decode()
			.strip()
		)

		# Get commit timestamp
		# EN: Assign value to commit_timestamp.
		# JP: commit_timestamp に値を代入する。
		commit_timestamp = (
			subprocess.check_output(['git', 'show', '-s', '--format=%ci', 'HEAD'], cwd=package_root, stderr=subprocess.DEVNULL)
			.decode()
			.strip()
		)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {'commit_hash': commit_hash, 'branch': branch, 'remote_url': remote_url, 'commit_timestamp': commit_timestamp}
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Error getting git info: {type(e).__name__}: {e}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None


# EN: Define function `_log_pretty_path`.
# JP: 関数 `_log_pretty_path` を定義する。
def _log_pretty_path(path: str | Path | None) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Pretty-print a path, shorten home dir to ~ and cwd to ."""

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not path or not str(path).strip():
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''  # always falsy in -> falsy out so it can be used in ternaries

	# dont print anything thats not a path
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not isinstance(path, (str, Path)):
		# no other types are safe to just str(path) and log to terminal unless we know what they are
		# e.g. what if we get storage_date=dict | Path and the dict version could contain real cookies
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'<{type(path).__name__}>'

	# replace home dir and cwd with ~ and .
	# EN: Assign value to pretty_path.
	# JP: pretty_path に値を代入する。
	pretty_path = str(path).replace(str(Path.home()), '~').replace(str(Path.cwd().resolve()), '.')

	# wrap in quotes if it contains spaces
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if pretty_path.strip() and ' ' in pretty_path:
		# EN: Assign value to pretty_path.
		# JP: pretty_path に値を代入する。
		pretty_path = f'"{pretty_path}"'

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return pretty_path


# EN: Define function `_log_pretty_url`.
# JP: 関数 `_log_pretty_url` を定義する。
def _log_pretty_url(s: str, max_len: int | None = 22) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Truncate/pretty-print a URL with a maximum length, removing the protocol and www. prefix"""
	# EN: Assign value to s.
	# JP: s に値を代入する。
	s = s.replace('https://', '').replace('http://', '').replace('www.', '')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if max_len is not None and len(s) > max_len:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return s[:max_len] + '…'
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return s

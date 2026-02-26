# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import sys
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.env_loader import load_secrets_env

# EN: Evaluate an expression.
# JP: 式を評価する。
load_secrets_env()

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG


# EN: Define function `addLoggingLevel`.
# JP: 関数 `addLoggingLevel` を定義する。
def addLoggingLevel(levelName, levelNum, methodName=None):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Comprehensively adds a new logging level to the `logging` module and the
	currently configured logging class.

	`levelName` becomes an attribute of the `logging` module with the value
	`levelNum`. `methodName` becomes a convenience method for both `logging`
	itself and the class returned by `logging.getLoggerClass()` (usually just
	`logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
	used.

	To avoid accidental clobberings of existing attributes, this method will
	raise an `AttributeError` if the level name is already an attribute of the
	`logging` module or if the method name is already present

	Example
	-------
	>>> addLoggingLevel('TRACE', logging.DEBUG - 5)
	>>> logging.getLogger(__name__).setLevel('TRACE')
	>>> logging.getLogger(__name__).trace('that worked')
	>>> logging.trace('so did this')
	>>> logging.TRACE
	5

	"""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not methodName:
		# EN: Assign value to methodName.
		# JP: methodName に値を代入する。
		methodName = levelName.lower()

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if hasattr(logging, levelName):
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AttributeError(f'{levelName} already defined in logging module')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if hasattr(logging, methodName):
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AttributeError(f'{methodName} already defined in logging module')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if hasattr(logging.getLoggerClass(), methodName):
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AttributeError(f'{methodName} already defined in logger class')

	# This method was inspired by the answers to Stack Overflow post
	# http://stackoverflow.com/q/2183233/2988730, especially
	# http://stackoverflow.com/a/13638084/2988730
	# EN: Define function `logForLevel`.
	# JP: 関数 `logForLevel` を定義する。
	def logForLevel(self, message, *args, **kwargs):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.isEnabledFor(levelNum):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._log(levelNum, message, args, **kwargs)

	# EN: Define function `logToRoot`.
	# JP: 関数 `logToRoot` を定義する。
	def logToRoot(message, *args, **kwargs):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logging.log(levelNum, message, *args, **kwargs)

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logging.addLevelName(levelNum, levelName)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	setattr(logging, levelName, levelNum)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	setattr(logging.getLoggerClass(), methodName, logForLevel)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	setattr(logging, methodName, logToRoot)


# EN: Define function `setup_logging`.
# JP: 関数 `setup_logging` を定義する。
def setup_logging(stream=None, log_level=None, force_setup=False, debug_log_file=None, info_log_file=None):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Setup logging configuration for browser-use.

	Args:
		stream: Output stream for logs (default: sys.stdout). Can be sys.stderr for MCP mode.
		log_level: Override log level (default: uses CONFIG.BROWSER_USE_LOGGING_LEVEL)
		force_setup: Force reconfiguration even if handlers already exist
		debug_log_file: Path to log file for debug level logs only
		info_log_file: Path to log file for info level logs only
	"""
	# Try to add RESULT level, but ignore if it already exists
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		addLoggingLevel('RESULT', 35)  # This allows ERROR, FATAL and CRITICAL
	except AttributeError:
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass  # Level already exists, which is fine

	# EN: Assign value to log_type.
	# JP: log_type に値を代入する。
	log_type = log_level or CONFIG.BROWSER_USE_LOGGING_LEVEL

	# Check if handlers are already set up
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if logging.getLogger().hasHandlers() and not force_setup:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return logging.getLogger('browser_use')

	# Clear existing handlers
	# EN: Assign value to root.
	# JP: root に値を代入する。
	root = logging.getLogger()
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	root.handlers = []

	# EN: Define class `BrowserUseFormatter`.
	# JP: クラス `BrowserUseFormatter` を定義する。
	class BrowserUseFormatter(logging.Formatter):
		# EN: Define function `__init__`.
		# JP: 関数 `__init__` を定義する。
		def __init__(self, fmt, log_level):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			super().__init__(fmt)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.log_level = log_level

		# EN: Define function `format`.
		# JP: 関数 `format` を定義する。
		def format(self, record):
			# Only clean up names in INFO mode, keep everything in DEBUG mode
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.log_level > logging.DEBUG and isinstance(record.name, str) and record.name.startswith('browser_use.'):
				# Extract clean component names from logger names
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'Agent' in record.name:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					record.name = 'Agent'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif 'BrowserSession' in record.name:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					record.name = 'BrowserSession'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif 'tools' in record.name:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					record.name = 'tools'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif 'dom' in record.name:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					record.name = 'dom'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif record.name.startswith('browser_use.'):
					# For other browser_use modules, use the last part
					# EN: Assign value to parts.
					# JP: parts に値を代入する。
					parts = record.name.split('.')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if len(parts) >= 2:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						record.name = parts[-1]
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return super().format(record)

	# Setup single handler for all loggers
	# EN: Assign value to console.
	# JP: console に値を代入する。
	console = logging.StreamHandler(stream or sys.stdout)

	# Determine the log level to use first
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if log_type == 'result':
		# EN: Assign value to log_level.
		# JP: log_level に値を代入する。
		log_level = 35  # RESULT level value
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif log_type == 'debug':
		# EN: Assign value to log_level.
		# JP: log_level に値を代入する。
		log_level = logging.DEBUG
	else:
		# EN: Assign value to log_level.
		# JP: log_level に値を代入する。
		log_level = logging.INFO

	# adittional setLevel here to filter logs
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if log_type == 'result':
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		console.setLevel('RESULT')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		console.setFormatter(BrowserUseFormatter('%(message)s', log_level))
	else:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		console.setLevel(log_level)  # Keep console at original log level (e.g., INFO)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		console.setFormatter(BrowserUseFormatter('%(levelname)-8s [%(name)s] %(message)s', log_level))

	# Configure root logger only
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	root.addHandler(console)

	# Add file handlers if specified
	# EN: Assign value to file_handlers.
	# JP: file_handlers に値を代入する。
	file_handlers = []

	# Create debug log file handler
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if debug_log_file:
		# EN: Assign value to debug_handler.
		# JP: debug_handler に値を代入する。
		debug_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		debug_handler.setLevel(logging.DEBUG)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		debug_handler.setFormatter(BrowserUseFormatter('%(asctime)s - %(levelname)-8s [%(name)s] %(message)s', logging.DEBUG))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		file_handlers.append(debug_handler)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		root.addHandler(debug_handler)

	# Create info log file handler
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if info_log_file:
		# EN: Assign value to info_handler.
		# JP: info_handler に値を代入する。
		info_handler = logging.FileHandler(info_log_file, encoding='utf-8')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		info_handler.setLevel(logging.INFO)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		info_handler.setFormatter(BrowserUseFormatter('%(asctime)s - %(levelname)-8s [%(name)s] %(message)s', logging.INFO))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		file_handlers.append(info_handler)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		root.addHandler(info_handler)

	# Configure root logger - use DEBUG if debug file logging is enabled
	# EN: Assign value to effective_log_level.
	# JP: effective_log_level に値を代入する。
	effective_log_level = logging.DEBUG if debug_log_file else log_level
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	root.setLevel(effective_log_level)

	# Configure browser_use logger
	# EN: Assign value to browser_use_logger.
	# JP: browser_use_logger に値を代入する。
	browser_use_logger = logging.getLogger('browser_use')
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	browser_use_logger.propagate = False  # Don't propagate to root logger
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	browser_use_logger.addHandler(console)
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for handler in file_handlers:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		browser_use_logger.addHandler(handler)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	browser_use_logger.setLevel(effective_log_level)

	# Configure bubus logger to allow INFO level logs
	# EN: Assign value to bubus_logger.
	# JP: bubus_logger に値を代入する。
	bubus_logger = logging.getLogger('bubus')
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	bubus_logger.propagate = False  # Don't propagate to root logger
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	bubus_logger.addHandler(console)
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for handler in file_handlers:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		bubus_logger.addHandler(handler)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	bubus_logger.setLevel(logging.INFO if log_type == 'result' else effective_log_level)

	# Configure CDP logging using cdp_use's setup function
	# This enables the formatted CDP output using CDP_LOGGING_LEVEL environment variable
	# Convert CDP_LOGGING_LEVEL string to logging level
	# EN: Assign value to cdp_level_str.
	# JP: cdp_level_str に値を代入する。
	cdp_level_str = CONFIG.CDP_LOGGING_LEVEL.upper()
	# EN: Assign value to cdp_level.
	# JP: cdp_level に値を代入する。
	cdp_level = getattr(logging, cdp_level_str, logging.WARNING)

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from cdp_use.logging import setup_cdp_logging  # type: ignore

		# Use the CDP-specific logging level
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		setup_cdp_logging(
			level=cdp_level,
			stream=stream or sys.stdout,
			format_string='%(levelname)-8s [%(name)s] %(message)s' if log_type != 'result' else '%(message)s',
		)
	except ImportError:
		# If cdp_use doesn't have the new logging module, fall back to manual config
		# EN: Assign value to cdp_loggers.
		# JP: cdp_loggers に値を代入する。
		cdp_loggers = [
			'websockets.client',
			'cdp_use',
			'cdp_use.client',
			'cdp_use.cdp',
			'cdp_use.cdp.registry',
		]
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for logger_name in cdp_loggers:
			# EN: Assign value to cdp_logger.
			# JP: cdp_logger に値を代入する。
			cdp_logger = logging.getLogger(logger_name)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cdp_logger.setLevel(cdp_level)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cdp_logger.addHandler(console)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			cdp_logger.propagate = False

	# EN: Assign value to logger.
	# JP: logger に値を代入する。
	logger = logging.getLogger('browser_use')
	# logger.debug('BrowserUse logging setup complete with level %s', log_type)

	# Silence third-party loggers (but not CDP ones which we configured above)
	# EN: Assign value to third_party_loggers.
	# JP: third_party_loggers に値を代入する。
	third_party_loggers = [
		'WDM',
		'httpx',
		'selenium',
		'playwright',
		'urllib3',
		'asyncio',
		'langsmith',
		'langsmith.client',
		'openai',
		'httpcore',
		'charset_normalizer',
		'anthropic._base_client',
		'PIL.PngImagePlugin',
		'trafilatura.htmlprocessing',
		'trafilatura',
		'groq',
		'portalocker',
		'google_genai',
		'portalocker.utils',
		'websockets',  # General websockets (but not websockets.client which we need)
	]
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for logger_name in third_party_loggers:
		# EN: Assign value to third_party.
		# JP: third_party に値を代入する。
		third_party = logging.getLogger(logger_name)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		third_party.setLevel(logging.ERROR)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		third_party.propagate = False

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return logger


# EN: Define class `FIFOHandler`.
# JP: クラス `FIFOHandler` を定義する。
class FIFOHandler(logging.Handler):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Non-blocking handler that writes to a named pipe."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, fifo_path: str):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.fifo_path = fifo_path
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		Path(fifo_path).parent.mkdir(parents=True, exist_ok=True)

		# Create FIFO if it doesn't exist
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.path.exists(fifo_path):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			os.mkfifo(fifo_path)

		# Don't open the FIFO yet - will open on first write
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.fd = None

	# EN: Define function `emit`.
	# JP: 関数 `emit` を定義する。
	def emit(self, record):
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Open FIFO on first write if not already open
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.fd is None:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.fd = os.open(self.fifo_path, os.O_WRONLY | os.O_NONBLOCK)
				except OSError:
					# No reader connected yet, skip this message
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return

			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = f'{self.format(record)}\n'.encode()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			os.write(self.fd, msg)
		except (OSError, BrokenPipeError):
			# Reader disconnected, close and reset
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.fd is not None:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					os.close(self.fd)
				except Exception:
					# EN: Keep a placeholder statement.
					# JP: プレースホルダー文を維持する。
					pass
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.fd = None

	# EN: Define function `close`.
	# JP: 関数 `close` を定義する。
	def close(self):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, 'fd') and self.fd is not None:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				os.close(self.fd)
			except Exception:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().close()


# EN: Define function `setup_log_pipes`.
# JP: 関数 `setup_log_pipes` を定義する。
def setup_log_pipes(session_id: str, base_dir: str | None = None):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Setup named pipes for log streaming.

	Usage:
		# In browser-use:
		setup_log_pipes(session_id="abc123")

		# In consumer process:
		tail -f {temp_dir}/buagent.c123/agent.pipe
	"""
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import tempfile

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if base_dir is None:
		# EN: Assign value to base_dir.
		# JP: base_dir に値を代入する。
		base_dir = tempfile.gettempdir()

	# EN: Assign value to suffix.
	# JP: suffix に値を代入する。
	suffix = session_id[-4:]
	# EN: Assign value to pipe_dir.
	# JP: pipe_dir に値を代入する。
	pipe_dir = Path(base_dir) / f'buagent.{suffix}'

	# Agent logs
	# EN: Assign value to agent_handler.
	# JP: agent_handler に値を代入する。
	agent_handler = FIFOHandler(str(pipe_dir / 'agent.pipe'))
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	agent_handler.setLevel(logging.DEBUG)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	agent_handler.setFormatter(logging.Formatter('%(levelname)-8s [%(name)s] %(message)s'))
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for name in ['browser_use.agent', 'browser_use.tools']:
		# EN: Assign value to logger.
		# JP: logger に値を代入する。
		logger = logging.getLogger(name)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.addHandler(agent_handler)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.setLevel(logging.DEBUG)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		logger.propagate = True

	# CDP logs
	# EN: Assign value to cdp_handler.
	# JP: cdp_handler に値を代入する。
	cdp_handler = FIFOHandler(str(pipe_dir / 'cdp.pipe'))
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	cdp_handler.setLevel(logging.DEBUG)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	cdp_handler.setFormatter(logging.Formatter('%(levelname)-8s [%(name)s] %(message)s'))
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for name in ['websockets.client', 'cdp_use.client']:
		# EN: Assign value to logger.
		# JP: logger に値を代入する。
		logger = logging.getLogger(name)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.addHandler(cdp_handler)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.setLevel(logging.DEBUG)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		logger.propagate = True

	# Event logs
	# EN: Assign value to event_handler.
	# JP: event_handler に値を代入する。
	event_handler = FIFOHandler(str(pipe_dir / 'events.pipe'))
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	event_handler.setLevel(logging.INFO)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	event_handler.setFormatter(logging.Formatter('%(levelname)-8s [%(name)s] %(message)s'))
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for name in ['bubus', 'browser_use.browser.session']:
		# EN: Assign value to logger.
		# JP: logger に値を代入する。
		logger = logging.getLogger(name)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.addHandler(event_handler)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.setLevel(logging.INFO)  # Enable INFO for event bus
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		logger.propagate = True

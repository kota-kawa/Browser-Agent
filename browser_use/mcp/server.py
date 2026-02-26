# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""MCP Server for browser-use - exposes browser automation capabilities via Model Context Protocol.

This server provides tools for:
- Running autonomous browser tasks with an AI agent
- Direct browser control (navigation, clicking, typing, etc.)
- Content extraction from web pages
- File system operations

Usage:
    uvx browser-use --mcp

Or as an MCP server in Claude Desktop or other MCP clients:
    {
        "mcpServers": {
            "browser-use": {
                "command": "uvx",
                "args": ["browser-use[cli]", "--mcp"],
                "env": {
                    "OPENAI_API_KEY": "sk-proj-1234567890",
                }
            }
        }
    }
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import sys

# Set environment variables BEFORE any browser_use imports to prevent early logging
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'critical'
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# Configure logging for MCP mode - redirect to stderr but preserve critical diagnostics
# EN: Evaluate an expression.
# JP: 式を評価する。
logging.basicConfig(
	stream=sys.stderr, level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', force=True
)

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import psutil

	# EN: Assign value to PSUTIL_AVAILABLE.
	# JP: PSUTIL_AVAILABLE に値を代入する。
	PSUTIL_AVAILABLE = True
except ImportError:
	# EN: Assign value to PSUTIL_AVAILABLE.
	# JP: PSUTIL_AVAILABLE に値を代入する。
	PSUTIL_AVAILABLE = False

# Add browser-use to path if running from source
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and configure logging to use stderr before other imports
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.logging_config import setup_logging


# EN: Define function `_configure_mcp_server_logging`.
# JP: 関数 `_configure_mcp_server_logging` を定義する。
def _configure_mcp_server_logging():
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Configure logging for MCP server mode - redirect all logs to stderr to prevent JSON RPC interference."""
	# Set environment to suppress browser-use logging during server mode
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'warning'
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'  # Prevent automatic logging setup

	# Configure logging to stderr for MCP mode - preserve warnings and above for troubleshooting
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	setup_logging(stream=sys.stderr, log_level='warning', force_setup=True)

	# Also configure the root logger and all existing loggers to use stderr
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	logging.root.handlers = []
	# EN: Assign value to stderr_handler.
	# JP: stderr_handler に値を代入する。
	stderr_handler = logging.StreamHandler(sys.stderr)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	stderr_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logging.root.addHandler(stderr_handler)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logging.root.setLevel(logging.CRITICAL)

	# Configure all existing loggers to use stderr and CRITICAL level
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for name in list(logging.root.manager.loggerDict.keys()):
		# EN: Assign value to logger_obj.
		# JP: logger_obj に値を代入する。
		logger_obj = logging.getLogger(name)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		logger_obj.handlers = []
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger_obj.setLevel(logging.CRITICAL)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger_obj.addHandler(stderr_handler)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		logger_obj.propagate = False


# Configure MCP server logging before any browser_use imports to capture early log lines
# EN: Evaluate an expression.
# JP: 式を評価する。
_configure_mcp_server_logging()

# Additional suppression - disable all logging completely for MCP mode
# EN: Evaluate an expression.
# JP: 式を評価する。
logging.disable(logging.CRITICAL)

# Import browser_use modules
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use import ActionModel, Agent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser import BrowserProfile, BrowserSession
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import get_default_llm, get_default_profile, load_browser_use_config
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystem
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.openai.chat import ChatOpenAI
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.service import Tools

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define function `_ensure_all_loggers_use_stderr`.
# JP: 関数 `_ensure_all_loggers_use_stderr` を定義する。
def _ensure_all_loggers_use_stderr():
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Ensure ALL loggers only output to stderr, not stdout."""
	# Get the stderr handler
	# EN: Assign value to stderr_handler.
	# JP: stderr_handler に値を代入する。
	stderr_handler = None
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for handler in logging.root.handlers:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(handler, 'stream') and handler.stream == sys.stderr:  # type: ignore
			# EN: Assign value to stderr_handler.
			# JP: stderr_handler に値を代入する。
			stderr_handler = handler
			# EN: Exit the current loop.
			# JP: 現在のループを終了する。
			break

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not stderr_handler:
		# EN: Assign value to stderr_handler.
		# JP: stderr_handler に値を代入する。
		stderr_handler = logging.StreamHandler(sys.stderr)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		stderr_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

	# Configure root logger
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	logging.root.handlers = [stderr_handler]
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logging.root.setLevel(logging.CRITICAL)

	# Configure all existing loggers
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for name in list(logging.root.manager.loggerDict.keys()):
		# EN: Assign value to logger_obj.
		# JP: logger_obj に値を代入する。
		logger_obj = logging.getLogger(name)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		logger_obj.handlers = [stderr_handler]
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger_obj.setLevel(logging.CRITICAL)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		logger_obj.propagate = False


# Ensure stderr logging after all imports
# EN: Evaluate an expression.
# JP: 式を評価する。
_ensure_all_loggers_use_stderr()


# Try to import MCP SDK
# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import mcp.server.stdio
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import mcp.types as types
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from mcp.server import NotificationOptions, Server
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from mcp.server.models import InitializationOptions

	# EN: Assign value to MCP_AVAILABLE.
	# JP: MCP_AVAILABLE に値を代入する。
	MCP_AVAILABLE = True

	# Configure MCP SDK logging to stderr as well
	# EN: Assign value to mcp_logger.
	# JP: mcp_logger に値を代入する。
	mcp_logger = logging.getLogger('mcp')
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	mcp_logger.handlers = []
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	mcp_logger.addHandler(logging.root.handlers[0] if logging.root.handlers else logging.StreamHandler(sys.stderr))
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	mcp_logger.setLevel(logging.ERROR)
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	mcp_logger.propagate = False
except ImportError:
	# EN: Assign value to MCP_AVAILABLE.
	# JP: MCP_AVAILABLE に値を代入する。
	MCP_AVAILABLE = False
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.error('MCP SDK not installed. Install with: pip install mcp')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	sys.exit(1)

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.telemetry import MCPServerTelemetryEvent, ProductTelemetry
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import get_browser_use_version


# EN: Define function `get_parent_process_cmdline`.
# JP: 関数 `get_parent_process_cmdline` を定義する。
def get_parent_process_cmdline() -> str | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get the command line of all parent processes up the chain."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not PSUTIL_AVAILABLE:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to cmdlines.
		# JP: cmdlines に値を代入する。
		cmdlines = []
		# EN: Assign value to current_process.
		# JP: current_process に値を代入する。
		current_process = psutil.Process()
		# EN: Assign value to parent.
		# JP: parent に値を代入する。
		parent = current_process.parent()

		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while parent:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to cmdline.
				# JP: cmdline に値を代入する。
				cmdline = parent.cmdline()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if cmdline:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					cmdlines.append(' '.join(cmdline))
			except (psutil.AccessDenied, psutil.NoSuchProcess):
				# Skip processes we can't access (like system processes)
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to parent.
				# JP: parent に値を代入する。
				parent = parent.parent()
			except (psutil.AccessDenied, psutil.NoSuchProcess):
				# Can't go further up the chain
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ';'.join(cmdlines) if cmdlines else None
	except Exception:
		# If we can't get parent process info, just return None
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None


# EN: Define class `BrowserUseServer`.
# JP: クラス `BrowserUseServer` を定義する。
class BrowserUseServer:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""MCP Server for browser-use capabilities."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, session_timeout_minutes: int = 10):
		# Ensure all logging goes to stderr (in case new loggers were created)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_ensure_all_loggers_use_stderr()

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.server = Server('browser-use')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.config = load_browser_use_config()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.agent: Agent | None = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.browser_session: BrowserSession | None = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.tools: Tools | None = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.llm: ChatOpenAI | None = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.file_system: FileSystem | None = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._telemetry = ProductTelemetry()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._start_time = time.time()

		# Session management
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.active_sessions: dict[str, dict[str, Any]] = {}  # session_id -> session info
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.session_timeout_minutes = session_timeout_minutes
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._cleanup_task: Any = None

		# Setup handlers
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._setup_handlers()

	# EN: Define function `_setup_handlers`.
	# JP: 関数 `_setup_handlers` を定義する。
	def _setup_handlers(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Setup MCP server handlers."""

		# EN: Define async function `handle_list_tools`.
		# JP: 非同期関数 `handle_list_tools` を定義する。
		@self.server.list_tools()
		async def handle_list_tools() -> list[types.Tool]:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""List all available browser-use tools."""
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return [
				# Agent tools
				# Direct browser control tools
				types.Tool(
					name='browser_navigate',
					description='Navigate to a URL in the browser',
					inputSchema={
						'type': 'object',
						'properties': {
							'url': {'type': 'string', 'description': 'The URL to navigate to'},
							'new_tab': {'type': 'boolean', 'description': 'Whether to open in a new tab', 'default': False},
						},
						'required': ['url'],
					},
				),
				types.Tool(
					name='browser_click',
					description='Click an element on the page by its index',
					inputSchema={
						'type': 'object',
						'properties': {
							'index': {
								'type': 'integer',
								'description': 'The index of the link or element to click (from browser_get_state)',
							},
							'new_tab': {
								'type': 'boolean',
								'description': 'Whether to open any resulting navigation in a new tab',
								'default': False,
							},
						},
						'required': ['index'],
					},
				),
				types.Tool(
					name='browser_type',
					description='Type text into an input field',
					inputSchema={
						'type': 'object',
						'properties': {
							'index': {
								'type': 'integer',
								'description': 'The index of the input element (from browser_get_state)',
							},
							'text': {'type': 'string', 'description': 'The text to type'},
						},
						'required': ['index', 'text'],
					},
				),
				types.Tool(
					name='browser_get_state',
					description='Get the current state of the page including all interactive elements',
					inputSchema={
						'type': 'object',
						'properties': {
							'include_screenshot': {
								'type': 'boolean',
								'description': 'Whether to include a screenshot of the current page',
								'default': False,
							}
						},
					},
				),
				types.Tool(
					name='browser_extract_content',
					description='Extract structured content from the current page based on a query',
					inputSchema={
						'type': 'object',
						'properties': {
							'query': {'type': 'string', 'description': 'What information to extract from the page'},
							'extract_links': {
								'type': 'boolean',
								'description': 'Whether to include links in the extraction',
								'default': False,
							},
						},
						'required': ['query'],
					},
				),
				types.Tool(
					name='browser_scroll',
					description='Scroll the page',
					inputSchema={
						'type': 'object',
						'properties': {
							'direction': {
								'type': 'string',
								'enum': ['up', 'down'],
								'description': 'Direction to scroll',
								'default': 'down',
							}
						},
					},
				),
				types.Tool(
					name='browser_go_back',
					description='Go back to the previous page',
					inputSchema={'type': 'object', 'properties': {}},
				),
				# Tab management
				types.Tool(
					name='browser_list_tabs', description='List all open tabs', inputSchema={'type': 'object', 'properties': {}}
				),
				types.Tool(
					name='browser_switch_tab',
					description='Switch to a different tab',
					inputSchema={
						'type': 'object',
						'properties': {'tab_id': {'type': 'string', 'description': '4 Character Tab ID of the tab to switch to'}},
						'required': ['tab_id'],
					},
				),
				types.Tool(
					name='browser_close_tab',
					description='Close a tab',
					inputSchema={
						'type': 'object',
						'properties': {'tab_id': {'type': 'string', 'description': '4 Character Tab ID of the tab to close'}},
						'required': ['tab_id'],
					},
				),
				# types.Tool(
				# 	name="browser_close",
				# 	description="Close the browser session",
				# 	inputSchema={
				# 		"type": "object",
				# 		"properties": {}
				# 	}
				# ),
				types.Tool(
					name='retry_with_browser_use_agent',
					description='Retry a task using the browser-use agent. Only use this as a last resort if you fail to interact with a page multiple times.',
					inputSchema={
						'type': 'object',
						'properties': {
							'task': {
								'type': 'string',
								'description': 'The high-level goal and detailed step-by-step description of the task the AI browser agent needs to attempt, along with any relevant data needed to complete the task and info about previous attempts.',
							},
							'max_steps': {
								'type': 'integer',
								'description': 'Maximum number of steps an agent can take.',
								'default': 100,
							},
							'model': {
								'type': 'string',
								'description': 'LLM model to use (e.g., gpt-4o, claude-3-opus-20240229)',
								'default': 'gpt-4o',
							},
							'allowed_domains': {
								'type': 'array',
								'items': {'type': 'string'},
								'description': 'List of domains the agent is allowed to visit (security feature)',
								'default': [],
							},
							'use_vision': {
								'type': 'boolean',
								'description': 'Whether to use vision capabilities (screenshots) for the agent',
								'default': True,
							},
						},
						'required': ['task'],
					},
				),
				# Browser session management tools
				types.Tool(
					name='browser_list_sessions',
					description='List all active browser sessions with their details and last activity time',
					inputSchema={'type': 'object', 'properties': {}},
				),
				types.Tool(
					name='browser_close_session',
					description='Close a specific browser session by its ID',
					inputSchema={
						'type': 'object',
						'properties': {
							'session_id': {
								'type': 'string',
								'description': 'The browser session ID to close (get from browser_list_sessions)',
							}
						},
						'required': ['session_id'],
					},
				),
				types.Tool(
					name='browser_close_all',
					description='Close all active browser sessions and clean up resources',
					inputSchema={'type': 'object', 'properties': {}},
				),
			]

		# EN: Define async function `handle_list_resources`.
		# JP: 非同期関数 `handle_list_resources` を定義する。
		@self.server.list_resources()
		async def handle_list_resources() -> list[types.Resource]:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""List available resources (none for browser-use)."""
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []

		# EN: Define async function `handle_list_prompts`.
		# JP: 非同期関数 `handle_list_prompts` を定義する。
		@self.server.list_prompts()
		async def handle_list_prompts() -> list[types.Prompt]:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""List available prompts (none for browser-use)."""
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []

		# EN: Define async function `handle_call_tool`.
		# JP: 非同期関数 `handle_call_tool` を定義する。
		@self.server.call_tool()
		async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Handle tool execution."""
			# EN: Assign value to start_time.
			# JP: start_time に値を代入する。
			start_time = time.time()
			# EN: Assign value to error_msg.
			# JP: error_msg に値を代入する。
			error_msg = None
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await self._execute_tool(name, arguments or {})
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [types.TextContent(type='text', text=result)]
			except Exception as e:
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = str(e)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Tool execution failed: {e}', exc_info=True)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [types.TextContent(type='text', text=f'Error: {str(e)}')]
			finally:
				# Capture telemetry for tool calls
				# EN: Assign value to duration.
				# JP: duration に値を代入する。
				duration = time.time() - start_time
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._telemetry.capture(
					MCPServerTelemetryEvent(
						version=get_browser_use_version(),
						action='tool_call',
						tool_name=name,
						duration_seconds=duration,
						error_message=error_msg,
					)
				)

	# EN: Define async function `_execute_tool`.
	# JP: 非同期関数 `_execute_tool` を定義する。
	async def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute a browser-use tool."""

		# Agent-based tools
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tool_name == 'retry_with_browser_use_agent':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return await self._retry_with_browser_use_agent(
				task=arguments['task'],
				max_steps=arguments.get('max_steps', 100),
				model=arguments.get('model', 'gpt-4o'),
				allowed_domains=arguments.get('allowed_domains', []),
				use_vision=arguments.get('use_vision', True),
			)

		# Browser session management tools (don't require active session)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tool_name == 'browser_list_sessions':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return await self._list_sessions()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif tool_name == 'browser_close_session':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return await self._close_session(arguments['session_id'])

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif tool_name == 'browser_close_all':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return await self._close_all_sessions()

		# Direct browser control tools (require active session)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif tool_name.startswith('browser_'):
			# Ensure browser session exists
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.browser_session:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._init_browser_session()

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if tool_name == 'browser_navigate':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._navigate(arguments['url'], arguments.get('new_tab', False))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_click':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._click(arguments['index'], arguments.get('new_tab', False))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_type':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._type_text(arguments['index'], arguments['text'])

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_get_state':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._get_browser_state(arguments.get('include_screenshot', False))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_extract_content':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._extract_content(arguments['query'], arguments.get('extract_links', False))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_scroll':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._scroll(arguments.get('direction', 'down'))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_go_back':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._go_back()

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_close':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._close_browser()

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_list_tabs':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._list_tabs()

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_switch_tab':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._switch_tab(arguments['tab_id'])

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif tool_name == 'browser_close_tab':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self._close_tab(arguments['tab_id'])

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Unknown tool: {tool_name}'

	# EN: Define async function `_init_browser_session`.
	# JP: 非同期関数 `_init_browser_session` を定義する。
	async def _init_browser_session(self, allowed_domains: list[str] | None = None, **kwargs):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize browser session using config"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Ensure all logging goes to stderr before browser initialization
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_ensure_all_loggers_use_stderr()

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Initializing browser session...')

		# Get profile config
		# EN: Assign value to profile_config.
		# JP: profile_config に値を代入する。
		profile_config = get_default_profile(self.config)

		# Merge profile config with defaults and overrides
		# EN: Assign value to profile_data.
		# JP: profile_data に値を代入する。
		profile_data = {
			'downloads_path': str(Path.home() / 'Downloads' / 'browser-use-mcp'),
			'wait_between_actions': 0.5,
			'keep_alive': True,
			'user_data_dir': '~/.config/browseruse/profiles/default',
			'device_scale_factor': 1.0,
			'disable_security': False,
			'headless': False,
			**profile_config,  # Config values override defaults
		}

		# Tool parameter overrides (highest priority)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if allowed_domains is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			profile_data['allowed_domains'] = allowed_domains

		# Merge any additional kwargs that are valid BrowserProfile fields
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for key, value in kwargs.items():
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			profile_data[key] = value

		# Create browser profile
		# EN: Assign value to profile.
		# JP: profile に値を代入する。
		profile = BrowserProfile(**profile_data)

		# Create browser session
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.browser_session = BrowserSession(browser_profile=profile)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.browser_session.start()

		# Track the session for management
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._track_session(self.browser_session)

		# Create tools for direct actions
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.tools = Tools()

		# Initialize LLM from config
		# EN: Assign value to llm_config.
		# JP: llm_config に値を代入する。
		llm_config = get_default_llm(self.config)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if api_key := llm_config.get('api_key'):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.llm = ChatOpenAI(
				model=llm_config.get('model', 'gpt-4o-mini'),
				api_key=api_key,
				temperature=llm_config.get('temperature', 0.7),
				# max_tokens=llm_config.get('max_tokens'),
			)

		# Initialize FileSystem for extraction actions
		# EN: Assign value to file_system_path.
		# JP: file_system_path に値を代入する。
		file_system_path = profile_config.get('file_system_path', '~/.browser-use-mcp')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.file_system = FileSystem(base_dir=Path(file_system_path).expanduser())

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Browser session initialized')

	# EN: Define async function `_retry_with_browser_use_agent`.
	# JP: 非同期関数 `_retry_with_browser_use_agent` を定義する。
	async def _retry_with_browser_use_agent(
		self,
		task: str,
		max_steps: int = 100,
		model: str = 'gpt-4o',
		allowed_domains: list[str] | None = None,
		use_vision: bool = True,
	) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Run an autonomous agent task."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Running agent task: {task}')

		# Get LLM config
		# EN: Assign value to llm_config.
		# JP: llm_config に値を代入する。
		llm_config = get_default_llm(self.config)
		# EN: Assign value to api_key.
		# JP: api_key に値を代入する。
		api_key = llm_config.get('api_key') or os.getenv('OPENAI_API_KEY')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not api_key:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: OPENAI_API_KEY not set in config or environment'

		# Override model if provided in tool call
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if model != llm_config.get('model', 'gpt-4o'):
			# EN: Assign value to llm_model.
			# JP: llm_model に値を代入する。
			llm_model = model
		else:
			# EN: Assign value to llm_model.
			# JP: llm_model に値を代入する。
			llm_model = llm_config.get('model', 'gpt-4o')

		# EN: Assign value to llm.
		# JP: llm に値を代入する。
		llm = ChatOpenAI(
			model=llm_model,
			api_key=api_key,
			temperature=llm_config.get('temperature', 0.7),
		)

		# Get profile config and merge with tool parameters
		# EN: Assign value to profile_config.
		# JP: profile_config に値を代入する。
		profile_config = get_default_profile(self.config)

		# Override allowed_domains if provided in tool call
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if allowed_domains is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			profile_config['allowed_domains'] = allowed_domains

		# Create browser profile using config
		# EN: Assign value to profile.
		# JP: profile に値を代入する。
		profile = BrowserProfile(**profile_config)

		# Create and run agent
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(
			task=task,
			llm=llm,
			browser_profile=profile,
			use_vision=use_vision,
		)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to history.
			# JP: history に値を代入する。
			history = await agent.run(max_steps=max_steps)

			# Format results
			# EN: Assign value to results.
			# JP: results に値を代入する。
			results = []
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			results.append(f'Task completed in {len(history.history)} steps')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			results.append(f'Success: {history.is_successful()}')

			# Get final result if available
			# EN: Assign value to final_result.
			# JP: final_result に値を代入する。
			final_result = history.final_result()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if final_result:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(f'\nFinal result:\n{final_result}')

			# Include any errors
			# EN: Assign value to errors.
			# JP: errors に値を代入する。
			errors = history.errors()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if errors:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				results.append(f'\nErrors encountered:\n{json.dumps(errors, indent=2)}')

			# Include URLs visited
			# EN: Assign value to urls.
			# JP: urls に値を代入する。
			urls = history.urls()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if urls:
				# Filter out None values and convert to strings
				# EN: Assign value to valid_urls.
				# JP: valid_urls に値を代入する。
				valid_urls = [str(url) for url in urls if url is not None]
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if valid_urls:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					results.append(f'\nURLs visited: {", ".join(valid_urls)}')

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '\n'.join(results)

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Agent task failed: {e}', exc_info=True)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Agent task failed: {str(e)}'
		finally:
			# Clean up
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await agent.close()

	# EN: Define async function `_navigate`.
	# JP: 非同期関数 `_navigate` を定義する。
	async def _navigate(self, url: str, new_tab: bool = False) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Navigate to a URL."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# Update session activity
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._update_session_activity(self.browser_session.id)

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import NavigateToUrlEvent

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if new_tab:
			# EN: Assign value to event.
			# JP: event に値を代入する。
			event = self.browser_session.event_bus.dispatch(NavigateToUrlEvent(url=url, new_tab=True))
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await event
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Opened new tab with URL: {url}'
		else:
			# EN: Assign value to event.
			# JP: event に値を代入する。
			event = self.browser_session.event_bus.dispatch(NavigateToUrlEvent(url=url))
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await event
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Navigated to: {url}'

	# EN: Define async function `_click`.
	# JP: 非同期関数 `_click` を定義する。
	async def _click(self, index: int, new_tab: bool = False) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Click an element by index."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# Update session activity
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._update_session_activity(self.browser_session.id)

		# Get the element
		# EN: Assign value to element.
		# JP: element に値を代入する。
		element = await self.browser_session.get_dom_element_by_index(index)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not element:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Element with index {index} not found'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if new_tab:
			# For links, extract href and open in new tab
			# EN: Assign value to href.
			# JP: href に値を代入する。
			href = element.attributes.get('href')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if href:
				# Convert relative href to absolute URL
				# EN: Assign value to state.
				# JP: state に値を代入する。
				state = await self.browser_session.get_browser_state_summary()
				# EN: Assign value to current_url.
				# JP: current_url に値を代入する。
				current_url = state.url
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if href.startswith('/'):
					# Relative URL - construct full URL
					# EN: Import required modules.
					# JP: 必要なモジュールをインポートする。
					from urllib.parse import urlparse

					# EN: Assign value to parsed.
					# JP: parsed に値を代入する。
					parsed = urlparse(current_url)
					# EN: Assign value to full_url.
					# JP: full_url に値を代入する。
					full_url = f'{parsed.scheme}://{parsed.netloc}{href}'
				else:
					# EN: Assign value to full_url.
					# JP: full_url に値を代入する。
					full_url = href

				# Open link in new tab
				# EN: Import required modules.
				# JP: 必要なモジュールをインポートする。
				from browser_use.browser.events import NavigateToUrlEvent

				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = self.browser_session.event_bus.dispatch(NavigateToUrlEvent(url=full_url, new_tab=True))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return f'Clicked element {index} and opened in new tab {full_url[:20]}...'
			else:
				# For non-link elements, just do a normal click
				# Opening in new tab without href is not reliably supported
				# EN: Import required modules.
				# JP: 必要なモジュールをインポートする。
				from browser_use.browser.events import ClickElementEvent

				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = self.browser_session.event_bus.dispatch(ClickElementEvent(node=element))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return f'Clicked element {index} (new tab not supported for non-link elements)'
		else:
			# Normal click
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from browser_use.browser.events import ClickElementEvent

			# EN: Assign value to event.
			# JP: event に値を代入する。
			event = self.browser_session.event_bus.dispatch(ClickElementEvent(node=element))
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await event
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Clicked element {index}'

	# EN: Define async function `_type_text`.
	# JP: 非同期関数 `_type_text` を定義する。
	async def _type_text(self, index: int, text: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Type text into an element."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# EN: Assign value to element.
		# JP: element に値を代入する。
		element = await self.browser_session.get_dom_element_by_index(index)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not element:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Element with index {index} not found'

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import TypeTextEvent

		# Conservative heuristic to detect potentially sensitive data
		# Only flag very obvious patterns to minimize false positives
		# EN: Assign value to is_potentially_sensitive.
		# JP: is_potentially_sensitive に値を代入する。
		is_potentially_sensitive = len(text) >= 6 and (
			# Email pattern: contains @ and a domain-like suffix
			('@' in text and '.' in text.split('@')[-1] if '@' in text else False)
			# Mixed alphanumeric with reasonable complexity (likely API keys/tokens)
			or (
				len(text) >= 16
				and any(char.isdigit() for char in text)
				and any(char.isalpha() for char in text)
				and any(char in '.-_' for char in text)
			)
		)

		# Use generic key names to avoid information leakage about detection patterns
		# EN: Assign value to sensitive_key_name.
		# JP: sensitive_key_name に値を代入する。
		sensitive_key_name = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_potentially_sensitive:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if '@' in text and '.' in text.split('@')[-1]:
				# EN: Assign value to sensitive_key_name.
				# JP: sensitive_key_name に値を代入する。
				sensitive_key_name = 'email'
			else:
				# EN: Assign value to sensitive_key_name.
				# JP: sensitive_key_name に値を代入する。
				sensitive_key_name = 'credential'

		# EN: Assign value to event.
		# JP: event に値を代入する。
		event = self.browser_session.event_bus.dispatch(
			TypeTextEvent(node=element, text=text, is_sensitive=is_potentially_sensitive, sensitive_key_name=sensitive_key_name)
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await event

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_potentially_sensitive:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if sensitive_key_name:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return f'Typed <{sensitive_key_name}> into element {index}'
			else:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return f'Typed <sensitive> into element {index}'
		else:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"Typed '{text}' into element {index}"

	# EN: Define async function `_get_browser_state`.
	# JP: 非同期関数 `_get_browser_state` を定義する。
	async def _get_browser_state(self, include_screenshot: bool = False) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get current browser state."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# EN: Assign value to state.
		# JP: state に値を代入する。
		state = await self.browser_session.get_browser_state_summary(cache_clickable_elements_hashes=False)

		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = {
			'url': state.url,
			'title': state.title,
			'tabs': [{'url': tab.url, 'title': tab.title} for tab in state.tabs],
			'interactive_elements': [],
		}

		# Add interactive elements with their indices
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for index, element in state.dom_state.selector_map.items():
			# EN: Assign value to elem_info.
			# JP: elem_info に値を代入する。
			elem_info = {
				'index': index,
				'tag': element.tag_name,
				'text': element.get_all_children_text(max_depth=2)[:100],
			}
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if element.attributes.get('placeholder'):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				elem_info['placeholder'] = element.attributes['placeholder']
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if element.attributes.get('href'):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				elem_info['href'] = element.attributes['href']
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			result['interactive_elements'].append(elem_info)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if include_screenshot and state.screenshot:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			result['screenshot'] = state.screenshot

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return json.dumps(result, indent=2)

	# EN: Define async function `_extract_content`.
	# JP: 非同期関数 `_extract_content` を定義する。
	async def _extract_content(self, query: str, extract_links: bool = False) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract content from current page."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.llm:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: LLM not initialized (set OPENAI_API_KEY)'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.file_system:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: FileSystem not initialized'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.tools:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: Tools not initialized'

		# EN: Assign value to state.
		# JP: state に値を代入する。
		state = await self.browser_session.get_browser_state_summary()

		# Use the extract_structured_data action
		# Create a dynamic action model that matches the tools's expectations
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from pydantic import create_model

		# Create action model dynamically
		# EN: Assign value to ExtractAction.
		# JP: ExtractAction に値を代入する。
		ExtractAction = create_model(
			'ExtractAction',
			__base__=ActionModel,
			extract_structured_data=(dict[str, Any], {'query': query, 'extract_links': extract_links}),
		)

		# EN: Assign value to action.
		# JP: action に値を代入する。
		action = ExtractAction()
		# EN: Assign value to action_result.
		# JP: action_result に値を代入する。
		action_result = await self.tools.act(
			action=action,
			browser_session=self.browser_session,
			page_extraction_llm=self.llm,
			file_system=self.file_system,
		)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return action_result.extracted_content or 'No content extracted'

	# EN: Define async function `_scroll`.
	# JP: 非同期関数 `_scroll` を定義する。
	async def _scroll(self, direction: str = 'down') -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Scroll the page."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import ScrollEvent

		# Scroll by a standard amount (500 pixels)
		# EN: Assign value to event.
		# JP: event に値を代入する。
		event = self.browser_session.event_bus.dispatch(
			ScrollEvent(
				direction=direction,  # type: ignore
				amount=500,
			)
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await event
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Scrolled {direction}'

	# EN: Define async function `_go_back`.
	# JP: 非同期関数 `_go_back` を定義する。
	async def _go_back(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Go back in browser history."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import GoBackEvent

		# EN: Assign value to event.
		# JP: event に値を代入する。
		event = self.browser_session.event_bus.dispatch(GoBackEvent())
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await event
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'Navigated back'

	# EN: Define async function `_close_browser`.
	# JP: 非同期関数 `_close_browser` を定義する。
	async def _close_browser(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close the browser session."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from browser_use.browser.events import BrowserStopEvent

			# EN: Assign value to event.
			# JP: event に値を代入する。
			event = self.browser_session.event_bus.dispatch(BrowserStopEvent())
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await event
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.browser_session = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.tools = None
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Browser closed'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'No browser session to close'

	# EN: Define async function `_list_tabs`.
	# JP: 非同期関数 `_list_tabs` を定義する。
	async def _list_tabs(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""List all open tabs."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# EN: Assign value to tabs_info.
		# JP: tabs_info に値を代入する。
		tabs_info = await self.browser_session.get_tabs()
		# EN: Assign value to tabs.
		# JP: tabs に値を代入する。
		tabs = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, tab in enumerate(tabs_info):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			tabs.append({'tab_id': tab.target_id[-4:], 'url': tab.url, 'title': tab.title or ''})
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return json.dumps(tabs, indent=2)

	# EN: Define async function `_switch_tab`.
	# JP: 非同期関数 `_switch_tab` を定義する。
	async def _switch_tab(self, tab_id: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Switch to a different tab."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import SwitchTabEvent

		# EN: Assign value to target_id.
		# JP: target_id に値を代入する。
		target_id = await self.browser_session.get_target_id_from_tab_id(tab_id)
		# EN: Assign value to event.
		# JP: event に値を代入する。
		event = self.browser_session.event_bus.dispatch(SwitchTabEvent(target_id=target_id))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await event
		# EN: Assign value to state.
		# JP: state に値を代入する。
		state = await self.browser_session.get_browser_state_summary()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Switched to tab {tab_id}: {state.url}'

	# EN: Define async function `_close_tab`.
	# JP: 非同期関数 `_close_tab` を定義する。
	async def _close_tab(self, tab_id: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close a specific tab."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: No browser session active'

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import CloseTabEvent

		# EN: Assign value to target_id.
		# JP: target_id に値を代入する。
		target_id = await self.browser_session.get_target_id_from_tab_id(tab_id)
		# EN: Assign value to event.
		# JP: event に値を代入する。
		event = self.browser_session.event_bus.dispatch(CloseTabEvent(target_id=target_id))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await event
		# EN: Assign value to current_url.
		# JP: current_url に値を代入する。
		current_url = await self.browser_session.get_current_page_url()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Closed tab # {tab_id}, now on {current_url}'

	# EN: Define function `_track_session`.
	# JP: 関数 `_track_session` を定義する。
	def _track_session(self, session: BrowserSession) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Track a browser session for management."""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.active_sessions[session.id] = {
			'session': session,
			'created_at': time.time(),
			'last_activity': time.time(),
			'url': getattr(session, 'current_url', None),
		}

	# EN: Define function `_update_session_activity`.
	# JP: 関数 `_update_session_activity` を定義する。
	def _update_session_activity(self, session_id: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update the last activity time for a session."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if session_id in self.active_sessions:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.active_sessions[session_id]['last_activity'] = time.time()

	# EN: Define async function `_list_sessions`.
	# JP: 非同期関数 `_list_sessions` を定義する。
	async def _list_sessions(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""List all active browser sessions."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.active_sessions:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'No active browser sessions'

		# EN: Assign value to sessions_info.
		# JP: sessions_info に値を代入する。
		sessions_info = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for session_id, session_data in self.active_sessions.items():
			# EN: Assign value to session.
			# JP: session に値を代入する。
			session = session_data['session']
			# EN: Assign value to created_at.
			# JP: created_at に値を代入する。
			created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session_data['created_at']))
			# EN: Assign value to last_activity.
			# JP: last_activity に値を代入する。
			last_activity = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session_data['last_activity']))

			# Check if session is still active
			# EN: Assign value to is_active.
			# JP: is_active に値を代入する。
			is_active = hasattr(session, 'cdp_client') and session.cdp_client is not None

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			sessions_info.append(
				{
					'session_id': session_id,
					'created_at': created_at,
					'last_activity': last_activity,
					'active': is_active,
					'current_url': session_data.get('url', 'Unknown'),
					'age_minutes': (time.time() - session_data['created_at']) / 60,
				}
			)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return json.dumps(sessions_info, indent=2)

	# EN: Define async function `_close_session`.
	# JP: 非同期関数 `_close_session` を定義する。
	async def _close_session(self, session_id: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close a specific browser session."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if session_id not in self.active_sessions:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Session {session_id} not found'

		# EN: Assign value to session_data.
		# JP: session_data に値を代入する。
		session_data = self.active_sessions[session_id]
		# EN: Assign value to session.
		# JP: session に値を代入する。
		session = session_data['session']

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Close the session
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(session, 'kill'):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.kill()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif hasattr(session, 'close'):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.close()

			# Remove from tracking
			# EN: Delete referenced values.
			# JP: 参照される値を削除する。
			del self.active_sessions[session_id]

			# If this was the current session, clear it
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session and self.browser_session.id == session_id:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.browser_session = None
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.tools = None

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Successfully closed session {session_id}'
		except Exception as e:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Error closing session {session_id}: {str(e)}'

	# EN: Define async function `_close_all_sessions`.
	# JP: 非同期関数 `_close_all_sessions` を定義する。
	async def _close_all_sessions(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close all active browser sessions."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.active_sessions:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'No active sessions to close'

		# EN: Assign value to closed_count.
		# JP: closed_count に値を代入する。
		closed_count = 0
		# EN: Assign value to errors.
		# JP: errors に値を代入する。
		errors = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for session_id in list(self.active_sessions.keys()):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await self._close_session(session_id)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'Successfully closed' in result:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					closed_count += 1
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					errors.append(f'{session_id}: {result}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				errors.append(f'{session_id}: {str(e)}')

		# Clear current session references
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.browser_session = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.tools = None

		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = f'Closed {closed_count} sessions'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if errors:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			result += f'. Errors: {"; ".join(errors)}'

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result

	# EN: Define async function `_cleanup_expired_sessions`.
	# JP: 非同期関数 `_cleanup_expired_sessions` を定義する。
	async def _cleanup_expired_sessions(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Background task to clean up expired sessions."""
		# EN: Assign value to current_time.
		# JP: current_time に値を代入する。
		current_time = time.time()
		# EN: Assign value to timeout_seconds.
		# JP: timeout_seconds に値を代入する。
		timeout_seconds = self.session_timeout_minutes * 60

		# EN: Assign value to expired_sessions.
		# JP: expired_sessions に値を代入する。
		expired_sessions = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for session_id, session_data in self.active_sessions.items():
			# EN: Assign value to last_activity.
			# JP: last_activity に値を代入する。
			last_activity = session_data['last_activity']
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_time - last_activity > timeout_seconds:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				expired_sessions.append(session_id)

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for session_id in expired_sessions:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._close_session(session_id)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'Auto-closed expired session {session_id}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Error auto-closing session {session_id}: {e}')

	# EN: Define async function `_start_cleanup_task`.
	# JP: 非同期関数 `_start_cleanup_task` を定義する。
	async def _start_cleanup_task(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Start the background cleanup task."""

		# EN: Define async function `cleanup_loop`.
		# JP: 非同期関数 `cleanup_loop` を定義する。
		async def cleanup_loop():
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while True:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._cleanup_expired_sessions()
					# Check every 2 minutes
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(120)
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(f'Error in cleanup task: {e}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(120)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cleanup_task = asyncio.create_task(cleanup_loop())

	# EN: Define async function `run`.
	# JP: 非同期関数 `run` を定義する。
	async def run(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Run the MCP server."""
		# Start the cleanup task
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._start_cleanup_task()

		# EN: Execute async logic with managed resources.
		# JP: リソース管理付きで非同期処理を実行する。
		async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.server.run(
				read_stream,
				write_stream,
				InitializationOptions(
					server_name='browser-use',
					server_version='0.1.0',
					capabilities=self.server.get_capabilities(
						notification_options=NotificationOptions(),
						experimental_capabilities={},
					),
				),
			)


# EN: Define async function `main`.
# JP: 非同期関数 `main` を定義する。
async def main(session_timeout_minutes: int = 10):
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not MCP_AVAILABLE:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('MCP SDK is required. Install with: pip install mcp', file=sys.stderr)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(1)

	# EN: Assign value to server.
	# JP: server に値を代入する。
	server = BrowserUseServer(session_timeout_minutes=session_timeout_minutes)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	server._telemetry.capture(
		MCPServerTelemetryEvent(
			version=get_browser_use_version(),
			action='start',
			parent_process_cmdline=get_parent_process_cmdline(),
		)
	)

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await server.run()
	finally:
		# EN: Assign value to duration.
		# JP: duration に値を代入する。
		duration = time.time() - server._start_time
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		server._telemetry.capture(
			MCPServerTelemetryEvent(
				version=get_browser_use_version(),
				action='stop',
				duration_seconds=duration,
				parent_process_cmdline=get_parent_process_cmdline(),
			)
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		server._telemetry.flush()


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(main())

# pyright: reportMissingImports=false

# Check for MCP mode early to prevent logging initialization
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import sys

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if '--mcp' in sys.argv:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import logging
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import os

	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'critical'
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logging.disable(logging.CRITICAL)

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
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.env_loader import load_secrets_env
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.anthropic.chat import ChatAnthropic
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.google.chat import ChatGoogle
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.openai.chat import ChatOpenAI

# EN: Evaluate an expression.
# JP: 式を評価する。
load_secrets_env()

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use import Agent, Controller
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import AgentSettings
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser import BrowserProfile, BrowserSession
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.logging_config import addLoggingLevel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.telemetry import CLITelemetryEvent, ProductTelemetry
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import get_browser_use_version

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import click
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from textual import events
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from textual.app import App, ComposeResult
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from textual.binding import Binding
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from textual.containers import Container, HorizontalGroup, VerticalScroll
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from textual.widgets import Footer, Header, Input, Label, Link, RichLog, Static
except ImportError:
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('⚠️ CLI addon is not installed. Please install it with: `pip install "browser-use[cli]"` and try again.')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	sys.exit(1)


# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import readline

	# EN: Assign value to READLINE_AVAILABLE.
	# JP: READLINE_AVAILABLE に値を代入する。
	READLINE_AVAILABLE = True
except ImportError:
	# readline not available on Windows by default
	# EN: Assign value to READLINE_AVAILABLE.
	# JP: READLINE_AVAILABLE に値を代入する。
	READLINE_AVAILABLE = False


# EN: Assign value to target variable.
# JP: target variable に値を代入する。
os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'result'

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG

# Set USER_DATA_DIR now that CONFIG is imported
# EN: Assign value to USER_DATA_DIR.
# JP: USER_DATA_DIR に値を代入する。
USER_DATA_DIR = CONFIG.BROWSER_USE_PROFILES_DIR / 'cli'

# Ensure directories exist
# EN: Evaluate an expression.
# JP: 式を評価する。
CONFIG.BROWSER_USE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
# EN: Evaluate an expression.
# JP: 式を評価する。
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default User settings
# EN: Assign value to MAX_HISTORY_LENGTH.
# JP: MAX_HISTORY_LENGTH に値を代入する。
MAX_HISTORY_LENGTH = 100

# Directory setup will happen in functions that need CONFIG


# Logo components with styling for rich panels
# EN: Assign value to BROWSER_LOGO.
# JP: BROWSER_LOGO に値を代入する。
BROWSER_LOGO = """
				   [white]   ++++++   +++++++++   [/]                                
				   [white] +++     +++++     +++  [/]                                
				   [white] ++    ++++   ++    ++  [/]                                
				   [white] ++  +++       +++  ++  [/]                                
				   [white]   ++++          +++    [/]                                
				   [white]  +++             +++   [/]                                
				   [white] +++               +++  [/]                                
				   [white] ++   +++      +++  ++  [/]                                
				   [white] ++    ++++   ++    ++  [/]                                
				   [white] +++     ++++++    +++  [/]                                
				   [white]   ++++++    +++++++    [/]                                

[white]██████╗ ██████╗  ██████╗ ██╗    ██╗███████╗███████╗██████╗[/]     [darkorange]██╗   ██╗███████╗███████╗[/]
[white]██╔══██╗██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔════╝██╔══██╗[/]    [darkorange]██║   ██║██╔════╝██╔════╝[/]
[white]██████╔╝██████╔╝██║   ██║██║ █╗ ██║███████╗█████╗  ██████╔╝[/]    [darkorange]██║   ██║███████╗█████╗[/]  
[white]██╔══██╗██╔══██╗██║   ██║██║███╗██║╚════██║██╔══╝  ██╔══██╗[/]    [darkorange]██║   ██║╚════██║██╔══╝[/]  
[white]██████╔╝██║  ██║╚██████╔╝╚███╔███╔╝███████║███████╗██║  ██║[/]    [darkorange]╚██████╔╝███████║███████╗[/]
[white]╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝[/]     [darkorange]╚═════╝ ╚══════╝╚══════╝[/]
"""


# Common UI constants
# EN: Assign value to TEXTUAL_BORDER_STYLES.
# JP: TEXTUAL_BORDER_STYLES に値を代入する。
TEXTUAL_BORDER_STYLES = {'logo': 'blue', 'info': 'blue', 'input': 'orange3', 'working': 'yellow', 'completion': 'green'}


# EN: Define function `get_default_config`.
# JP: 関数 `get_default_config` を定義する。
def get_default_config() -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return default configuration dictionary using the new config system."""
	# Load config from the new config system
	# EN: Assign value to config_data.
	# JP: config_data に値を代入する。
	config_data = CONFIG.load_config()

	# Extract browser profile, llm, and agent configs
	# EN: Assign value to browser_profile.
	# JP: browser_profile に値を代入する。
	browser_profile = config_data.get('browser_profile', {})
	# EN: Assign value to llm_config.
	# JP: llm_config に値を代入する。
	llm_config = config_data.get('llm', {})
	# EN: Assign value to agent_config.
	# JP: agent_config に値を代入する。
	agent_config = config_data.get('agent', {})

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return {
		'model': {
			'name': llm_config.get('model'),
			'temperature': llm_config.get('temperature', 0.0),
			'api_keys': {
				'OPENAI_API_KEY': llm_config.get('api_key', CONFIG.OPENAI_API_KEY),
				'ANTHROPIC_API_KEY': CONFIG.ANTHROPIC_API_KEY,
				'GOOGLE_API_KEY': CONFIG.GOOGLE_API_KEY,
				'DEEPSEEK_API_KEY': CONFIG.DEEPSEEK_API_KEY,
				'GROK_API_KEY': CONFIG.GROK_API_KEY,
			},
		},
		'agent': agent_config,
		'browser': {
			'headless': browser_profile.get('headless', True),
			'keep_alive': browser_profile.get('keep_alive', True),
			'ignore_https_errors': browser_profile.get('ignore_https_errors', False),
			'user_data_dir': browser_profile.get('user_data_dir'),
			'allowed_domains': browser_profile.get('allowed_domains'),
			'wait_between_actions': browser_profile.get('wait_between_actions'),
			'is_mobile': browser_profile.get('is_mobile'),
			'device_scale_factor': browser_profile.get('device_scale_factor'),
			'disable_security': browser_profile.get('disable_security'),
		},
		'command_history': [],
	}


# EN: Define function `load_user_config`.
# JP: 関数 `load_user_config` を定義する。
def load_user_config() -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Load user configuration using the new config system."""
	# Just get the default config which already loads from the new system
	# EN: Assign value to config.
	# JP: config に値を代入する。
	config = get_default_config()

	# Load command history from a separate file if it exists
	# EN: Assign value to history_file.
	# JP: history_file に値を代入する。
	history_file = CONFIG.BROWSER_USE_CONFIG_DIR / 'command_history.json'
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if history_file.exists():
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with open(history_file) as f:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				config['command_history'] = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['command_history'] = []

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return config


# EN: Define function `save_user_config`.
# JP: 関数 `save_user_config` を定義する。
def save_user_config(config: dict[str, Any]) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Save command history only (config is saved via the new system)."""
	# Only save command history to a separate file
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if 'command_history' in config and isinstance(config['command_history'], list):
		# Ensure command history doesn't exceed maximum length
		# EN: Assign value to history.
		# JP: history に値を代入する。
		history = config['command_history']
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(history) > MAX_HISTORY_LENGTH:
			# EN: Assign value to history.
			# JP: history に値を代入する。
			history = history[-MAX_HISTORY_LENGTH:]

		# Save to separate history file
		# EN: Assign value to history_file.
		# JP: history_file に値を代入する。
		history_file = CONFIG.BROWSER_USE_CONFIG_DIR / 'command_history.json'
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(history_file, 'w') as f:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			json.dump(history, f, indent=2)


# EN: Define function `update_config_with_click_args`.
# JP: 関数 `update_config_with_click_args` を定義する。
def update_config_with_click_args(config: dict[str, Any], ctx: click.Context) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Update configuration with command-line arguments."""
	# Ensure required sections exist
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if 'model' not in config:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['model'] = {}
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if 'browser' not in config:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['browser'] = {}

	# Update configuration with command-line args if provided
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('model'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['model']['name'] = ctx.params['model']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('headless') is not None:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['browser']['headless'] = ctx.params['headless']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('window_width'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['browser']['window_width'] = ctx.params['window_width']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('window_height'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['browser']['window_height'] = ctx.params['window_height']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('user_data_dir'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['browser']['user_data_dir'] = ctx.params['user_data_dir']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('profile_directory'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['browser']['profile_directory'] = ctx.params['profile_directory']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('cdp_url'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['browser']['cdp_url'] = ctx.params['cdp_url']

	# Consolidated proxy dict
	# EN: Assign annotated value to proxy.
	# JP: proxy に型付きの値を代入する。
	proxy: dict[str, str] = {}
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('proxy_url'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		proxy['server'] = ctx.params['proxy_url']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('no_proxy'):
		# Store as comma-separated list string to match Chrome flag
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		proxy['bypass'] = ','.join([p.strip() for p in ctx.params['no_proxy'].split(',') if p.strip()])
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('proxy_username'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		proxy['username'] = ctx.params['proxy_username']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.params.get('proxy_password'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		proxy['password'] = ctx.params['proxy_password']
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if proxy:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		config['browser']['proxy'] = proxy

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return config


# EN: Define function `setup_readline_history`.
# JP: 関数 `setup_readline_history` を定義する。
def setup_readline_history(history: list[str]) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Set up readline with command history."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not READLINE_AVAILABLE:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# Add history items to readline
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for item in history:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		readline.add_history(item)


# EN: Define function `get_llm`.
# JP: 関数 `get_llm` を定義する。
def get_llm(config: dict[str, Any]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get the language model based on config and available API keys."""
	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = config.get('model', {})
	# EN: Assign value to model_name.
	# JP: model_name に値を代入する。
	model_name = model_config.get('name')
	# EN: Assign value to temperature.
	# JP: temperature に値を代入する。
	temperature = model_config.get('temperature', 0.0)

	# Get API key from config or environment
	# EN: Assign value to api_key.
	# JP: api_key に値を代入する。
	api_key = model_config.get('api_keys', {}).get('OPENAI_API_KEY') or CONFIG.OPENAI_API_KEY

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if model_name:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if model_name.startswith('gpt'):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not api_key and not CONFIG.OPENAI_API_KEY:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('⚠️  OpenAI API key not found. Please update your config or set OPENAI_API_KEY environment variable.')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				sys.exit(1)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key or CONFIG.OPENAI_API_KEY)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif model_name.startswith('claude'):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not CONFIG.ANTHROPIC_API_KEY:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('⚠️  Anthropic API key not found. Please update your config or set ANTHROPIC_API_KEY environment variable.')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				sys.exit(1)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ChatAnthropic(model=model_name, temperature=temperature)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif model_name.startswith('gemini'):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not CONFIG.GOOGLE_API_KEY:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('⚠️  Google API key not found. Please update your config or set GOOGLE_API_KEY environment variable.')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				sys.exit(1)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ChatGoogle(model=model_name, temperature=temperature)

	# Auto-detect based on available API keys
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if api_key or CONFIG.OPENAI_API_KEY:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatOpenAI(model='gpt-5-mini', temperature=temperature, api_key=api_key or CONFIG.OPENAI_API_KEY)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif CONFIG.ANTHROPIC_API_KEY:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatAnthropic(model='claude-4-sonnet', temperature=temperature)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif CONFIG.GOOGLE_API_KEY:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatGoogle(model='gemini-2.5-pro', temperature=temperature)
	else:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(
			'⚠️  No API keys found. Please update your config or set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY.'
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(1)


# EN: Define class `RichLogHandler`.
# JP: クラス `RichLogHandler` を定義する。
class RichLogHandler(logging.Handler):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Custom logging handler that redirects logs to a RichLog widget."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, rich_log: RichLog):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.rich_log = rich_log

	# EN: Define function `emit`.
	# JP: 関数 `emit` を定義する。
	def emit(self, record):
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = self.format(record)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.rich_log.write(msg)
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.handleError(record)


# EN: Define class `BrowserUseApp`.
# JP: クラス `BrowserUseApp` を定義する。
class BrowserUseApp(App):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Browser-use TUI application."""

	# Make it an inline app instead of fullscreen
	# MODES = {"light"}  # Ensure app is inline, not fullscreen

	# EN: Assign value to CSS.
	# JP: CSS に値を代入する。
	CSS = """
	#main-container {
		height: 100%;
		layout: vertical;
	}
	
	#logo-panel, #links-panel, #paths-panel, #info-panels {
		border: solid $primary;
		margin: 0 0 0 0; 
		padding: 0;
	}
	
	#info-panels {
		display: none;
		layout: vertical;
		height: auto;
		min-height: 5;
		margin: 0 0 1 0;
	}
	
	#top-panels {
		layout: horizontal;
		height: auto;
		width: 100%;
	}
	
	#browser-panel, #model-panel {
		width: 1fr;
		height: 100%;
		padding: 1;
		border-right: solid $primary;
	}
	
	#model-panel {
		border-right: none;
	}
	
	#tasks-panel {
		height: auto;
		max-height: 10;
		overflow-y: scroll;
		padding: 1;
		border-top: solid $primary;
	}
	
	#browser-info, #model-info, #tasks-info {
		height: auto;
		margin: 0;
		padding: 0;
		background: transparent;
		overflow-y: auto;
		min-height: 3;
	}
	
	#three-column-container {
		height: 1fr;
		layout: horizontal;
		width: 100%;
		display: none;
	}
	
	#main-output-column {
		width: 1fr;
		height: 100%;
		border: solid $primary;
		padding: 0;
		margin: 0 1 0 0;
	}
	
	#events-column {
		width: 1fr;
		height: 100%;
		border: solid $warning;
		padding: 0;
		margin: 0 1 0 0;
	}
	
	#cdp-column {
		width: 1fr;
		height: 100%;
		border: solid $accent;
		padding: 0;
		margin: 0;
	}
	
	#main-output-log, #events-log, #cdp-log {
		height: 100%;
		overflow-y: scroll;
		background: $surface;
		color: $text;
		width: 100%;
		padding: 1;
	}
	
	#events-log {
		color: $warning;
	}
	
	#cdp-log {
		color: $accent-lighten-2;
	}
	
	#logo-panel {
		width: 100%;
		height: auto;
		content-align: center middle;
		text-align: center;
	}
	
	#links-panel {
		width: 100%;
		padding: 1;
		border: solid $primary;
		height: auto;
	}
	
	.link-white {
		color: white;
	}
	
	.link-purple {
		color: purple;
	}
	
	.link-magenta {
		color: magenta;
	}
	
	.link-green {
		color: green;
	}

	HorizontalGroup {
		height: auto;
	}
	
	.link-label {
		width: auto;
	}
	
	.link-url {
		width: auto;
	}
	
	.link-row {
		width: 100%;
		height: auto;
	}
	
	#paths-panel {
		color: $text-muted;
	}
	
	#task-input-container {
		border: solid $accent;
		padding: 1;
		margin-bottom: 1;
		height: auto;
		dock: bottom;
	}
	
	#task-label {
		color: $accent;
		padding-bottom: 1;
	}
	
	#task-input {
		width: 100%;
	}
	"""

	# EN: Assign value to BINDINGS.
	# JP: BINDINGS に値を代入する。
	BINDINGS = [
		Binding('ctrl+c', 'quit', 'Quit', priority=True, show=True),
		Binding('ctrl+q', 'quit', 'Quit', priority=True),
		Binding('ctrl+d', 'quit', 'Quit', priority=True),
		Binding('up', 'input_history_prev', 'Previous command', show=False),
		Binding('down', 'input_history_next', 'Next command', show=False),
	]

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, config: dict[str, Any], *args, **kwargs):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__(*args, **kwargs)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.config = config
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.browser_session: BrowserSession | None = None  # Will be set before app.run_async()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.controller: Controller | None = None  # Will be set before app.run_async()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.agent: Agent | None = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.llm: Any | None = None  # Will be set before app.run_async()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.task_history = config.get('command_history', [])
		# Track current position in history for up/down navigation
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.history_index = len(self.task_history)
		# Initialize telemetry
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._telemetry = ProductTelemetry()
		# Store for event bus handler
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._event_bus_handler_id = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._event_bus_handler_func = None
		# Timer for info panel updates
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._info_panel_timer = None

	# EN: Define function `setup_richlog_logging`.
	# JP: 関数 `setup_richlog_logging` を定義する。
	def setup_richlog_logging(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set up logging to redirect to RichLog widget instead of stdout."""
		# Try to add RESULT level if it doesn't exist
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			addLoggingLevel('RESULT', 35)
		except AttributeError:
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass  # Level already exists, which is fine

		# Get the main output RichLog widget
		# EN: Assign value to rich_log.
		# JP: rich_log に値を代入する。
		rich_log = self.query_one('#main-output-log', RichLog)

		# Create and set up the custom handler
		# EN: Assign value to log_handler.
		# JP: log_handler に値を代入する。
		log_handler = RichLogHandler(rich_log)
		# EN: Assign value to log_type.
		# JP: log_type に値を代入する。
		log_type = os.getenv('BROWSER_USE_LOGGING_LEVEL', 'result').lower()

		# EN: Define class `BrowserUseFormatter`.
		# JP: クラス `BrowserUseFormatter` を定義する。
		class BrowserUseFormatter(logging.Formatter):
			# EN: Define function `format`.
			# JP: 関数 `format` を定義する。
			def format(self, record):
				# if isinstance(record.name, str) and record.name.startswith('browser_use.'):
				# 	record.name = record.name.split('.')[-2]
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return super().format(record)

		# Set up the formatter based on log type
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if log_type == 'result':
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			log_handler.setLevel('RESULT')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			log_handler.setFormatter(BrowserUseFormatter('%(message)s'))
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			log_handler.setFormatter(BrowserUseFormatter('%(levelname)-8s [%(name)s] %(message)s'))

		# Configure root logger - Replace ALL handlers, not just stdout handlers
		# EN: Assign value to root.
		# JP: root に値を代入する。
		root = logging.getLogger()

		# Clear all existing handlers to prevent output to stdout/stderr
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		root.handlers = []
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		root.addHandler(log_handler)

		# Set log level based on environment variable
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if log_type == 'result':
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			root.setLevel('RESULT')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif log_type == 'debug':
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			root.setLevel(logging.DEBUG)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			root.setLevel(logging.INFO)

		# Configure browser_use logger and all its sub-loggers
		# EN: Assign value to browser_use_logger.
		# JP: browser_use_logger に値を代入する。
		browser_use_logger = logging.getLogger('browser_use')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		browser_use_logger.propagate = False  # Don't propagate to root logger
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		browser_use_logger.handlers = [log_handler]  # Replace any existing handlers
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		browser_use_logger.setLevel(root.level)

		# Also ensure agent loggers go to the main output
		# Use a wildcard pattern to catch all agent-related loggers
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for logger_name in ['browser_use.Agent', 'browser_use.controller', 'browser_use.agent', 'browser_use.agent.service']:
			# EN: Assign value to agent_logger.
			# JP: agent_logger に値を代入する。
			agent_logger = logging.getLogger(logger_name)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent_logger.propagate = False
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent_logger.handlers = [log_handler]
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			agent_logger.setLevel(root.level)

		# Also catch any dynamically created agent loggers with task IDs
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for name, logger in logging.Logger.manager.loggerDict.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(name, str) and 'browser_use.Agent' in name:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(logger, logging.Logger):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					logger.propagate = False
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					logger.handlers = [log_handler]
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.setLevel(root.level)

		# Silence third-party loggers but keep them using our handler
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for logger_name in [
			'WDM',
			'httpx',
			'selenium',
			'playwright',
			'urllib3',
			'asyncio',
			'openai',
			'httpcore',
			'charset_normalizer',
			'anthropic._base_client',
			'PIL.PngImagePlugin',
			'trafilatura.htmlprocessing',
			'trafilatura',
			'groq',
			'portalocker',
			'portalocker.utils',
		]:
			# EN: Assign value to third_party.
			# JP: third_party に値を代入する。
			third_party = logging.getLogger(logger_name)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			third_party.setLevel(logging.ERROR)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			third_party.propagate = False
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			third_party.handlers = [log_handler]  # Use our handler to prevent stdout/stderr leakage

	# EN: Define function `on_mount`.
	# JP: 関数 `on_mount` を定義する。
	def on_mount(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set up components when app is mounted."""
		# We'll use a file logger since stdout is now controlled by Textual
		# EN: Assign value to logger.
		# JP: logger に値を代入する。
		logger = logging.getLogger('browser_use.on_mount')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('on_mount() method started')

		# Step 1: Set up custom logging to RichLog
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Setting up RichLog logging...')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.setup_richlog_logging()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('RichLog logging set up successfully')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Error setting up RichLog logging: {str(e)}', exc_info=True)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError(f'Failed to set up RichLog logging: {str(e)}')

		# Step 2: Set up input history
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Setting up readline history...')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if READLINE_AVAILABLE and self.task_history:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for item in self.task_history:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					readline.add_history(item)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Added {len(self.task_history)} items to readline history')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('No readline history to set up')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Error setting up readline history: {str(e)}', exc_info=False)
			# Non-critical, continue

		# Step 3: Focus the input field
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Focusing input field...')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to input_field.
			# JP: input_field に値を代入する。
			input_field = self.query_one('#task-input', Input)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			input_field.focus()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('Input field focused')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Error focusing input field: {str(e)}', exc_info=True)
			# Non-critical, continue

		# Step 5: Setup CDP logger and event bus listener if browser session is available
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Setting up CDP logging and event bus listener...')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.setup_cdp_logger()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.setup_event_bus_listener()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('CDP logging and event bus setup complete')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Error setting up CDP logging/event bus: {str(e)}', exc_info=True)
			# Non-critical, continue

		# Capture telemetry for CLI start
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._telemetry.capture(
			CLITelemetryEvent(
				version=get_browser_use_version(),
				action='start',
				mode='interactive',
				model=self.llm.model if self.llm and hasattr(self.llm, 'model') else None,
				model_provider=self.llm.provider if self.llm and hasattr(self.llm, 'provider') else None,
			)
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('on_mount() completed successfully')

	# EN: Define function `on_input_key_up`.
	# JP: 関数 `on_input_key_up` を定義する。
	def on_input_key_up(self, event: events.Key) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle up arrow key in the input field."""
		# For textual key events, we need to check focus manually
		# EN: Assign value to input_field.
		# JP: input_field に値を代入する。
		input_field = self.query_one('#task-input', Input)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not input_field.has_focus:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Only process if we have history
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.task_history:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Move back in history if possible
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history_index > 0:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.history_index -= 1
			# EN: Assign value to task_input.
			# JP: task_input に値を代入する。
			task_input = self.query_one('#task-input', Input)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			task_input.value = self.task_history[self.history_index]
			# Move cursor to end of text
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			task_input.cursor_position = len(task_input.value)

		# Prevent default behavior (cursor movement)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		event.prevent_default()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		event.stop()

	# EN: Define function `on_input_key_down`.
	# JP: 関数 `on_input_key_down` を定義する。
	def on_input_key_down(self, event: events.Key) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle down arrow key in the input field."""
		# For textual key events, we need to check focus manually
		# EN: Assign value to input_field.
		# JP: input_field に値を代入する。
		input_field = self.query_one('#task-input', Input)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not input_field.has_focus:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Only process if we have history
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.task_history:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Move forward in history or clear input if at the end
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history_index < len(self.task_history) - 1:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.history_index += 1
			# EN: Assign value to task_input.
			# JP: task_input に値を代入する。
			task_input = self.query_one('#task-input', Input)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			task_input.value = self.task_history[self.history_index]
			# Move cursor to end of text
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			task_input.cursor_position = len(task_input.value)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.history_index == len(self.task_history) - 1:
			# At the end of history, go to "new line" state
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.history_index += 1
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.query_one('#task-input', Input).value = ''

		# Prevent default behavior (cursor movement)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		event.prevent_default()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		event.stop()

	# EN: Define async function `on_key`.
	# JP: 非同期関数 `on_key` を定義する。
	async def on_key(self, event: events.Key) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle key events at the app level to ensure graceful exit."""
		# Handle Ctrl+C, Ctrl+D, and Ctrl+Q for app exit
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.key == 'ctrl+c' or event.key == 'ctrl+d' or event.key == 'ctrl+q':
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.action_quit()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			event.stop()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			event.prevent_default()

	# EN: Define function `on_input_submitted`.
	# JP: 関数 `on_input_submitted` を定義する。
	def on_input_submitted(self, event: Input.Submitted) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle task input submission."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.input.id == 'task-input':
			# EN: Assign value to task.
			# JP: task に値を代入する。
			task = event.input.value
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not task.strip():
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Add to history if it's new
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if task.strip() and (not self.task_history or task != self.task_history[-1]):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.task_history.append(task)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.config['command_history'] = self.task_history
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				save_user_config(self.config)

			# Reset history index to point past the end of history
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.history_index = len(self.task_history)

			# Hide logo, links, and paths panels
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.hide_intro_panels()

			# Process the task
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.run_task(task)

			# Clear the input
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			event.input.value = ''

	# EN: Define function `hide_intro_panels`.
	# JP: 関数 `hide_intro_panels` を定義する。
	def hide_intro_panels(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Hide the intro panels, show info panels and the three-column view."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get the panels
			# EN: Assign value to logo_panel.
			# JP: logo_panel に値を代入する。
			logo_panel = self.query_one('#logo-panel')
			# EN: Assign value to links_panel.
			# JP: links_panel に値を代入する。
			links_panel = self.query_one('#links-panel')
			# EN: Assign value to paths_panel.
			# JP: paths_panel に値を代入する。
			paths_panel = self.query_one('#paths-panel')
			# EN: Assign value to info_panels.
			# JP: info_panels に値を代入する。
			info_panels = self.query_one('#info-panels')
			# EN: Assign value to three_column.
			# JP: three_column に値を代入する。
			three_column = self.query_one('#three-column-container')

			# Hide intro panels if they're visible and show info panels + three-column view
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if logo_panel.display:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logging.debug('Hiding intro panels and showing info panels + three-column view')

				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				logo_panel.display = False
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				links_panel.display = False
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				paths_panel.display = False

				# Show info panels and three-column container
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				info_panels.display = True
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				three_column.display = True

				# Start updating info panels
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.update_info_panels()

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logging.debug('Info panels and three-column view should now be visible')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logging.error(f'Error in hide_intro_panels: {str(e)}')

	# EN: Define function `setup_event_bus_listener`.
	# JP: 関数 `setup_event_bus_listener` を定義する。
	def setup_event_bus_listener(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Setup listener for browser session event bus."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session or not self.browser_session.event_bus:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Clean up any existing handler before registering a new one
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._event_bus_handler_func is not None:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Remove handler from the event bus's internal handlers dict
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(self.browser_session.event_bus, 'handlers'):
					# Find and remove our handler function from all event patterns
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for event_type, handler_list in list(self.browser_session.event_bus.handlers.items()):
						# Remove our specific handler function object
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if self._event_bus_handler_func in handler_list:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							handler_list.remove(self._event_bus_handler_func)
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							logging.debug(f'Removed old handler from event type: {event_type}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logging.debug(f'Error cleaning up event bus handler: {e}')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._event_bus_handler_func = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._event_bus_handler_id = None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get the events log widget
			# EN: Assign value to events_log.
			# JP: events_log に値を代入する。
			events_log = self.query_one('#events-log', RichLog)
		except Exception:
			# Widget not ready yet
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Create handler to log all events
		# EN: Define function `log_event`.
		# JP: 関数 `log_event` を定義する。
		def log_event(event):
			# EN: Assign value to event_name.
			# JP: event_name に値を代入する。
			event_name = event.__class__.__name__
			# Format event data nicely
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(event, 'model_dump'):
					# EN: Assign value to event_data.
					# JP: event_data に値を代入する。
					event_data = event.model_dump(exclude_unset=True)
					# Remove large fields
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'screenshot' in event_data:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						event_data['screenshot'] = '<bytes>'
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'dom_state' in event_data:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						event_data['dom_state'] = '<truncated>'
					# EN: Assign value to event_str.
					# JP: event_str に値を代入する。
					event_str = str(event_data) if event_data else ''
				else:
					# EN: Assign value to event_str.
					# JP: event_str に値を代入する。
					event_str = str(event)

				# Truncate long strings
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if len(event_str) > 200:
					# EN: Assign value to event_str.
					# JP: event_str に値を代入する。
					event_str = event_str[:200] + '...'

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				events_log.write(f'[yellow]→ {event_name}[/] {event_str}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				events_log.write(f'[red]→ {event_name}[/] (error formatting: {e})')

		# Store the handler function before registering it
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._event_bus_handler_func = log_event
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._event_bus_handler_id = id(log_event)

		# Register wildcard handler for all events
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.browser_session.event_bus.on('*', log_event)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logging.debug(f'Registered new event bus handler with id: {self._event_bus_handler_id}')

	# EN: Define function `setup_cdp_logger`.
	# JP: 関数 `setup_cdp_logger` を定義する。
	def setup_cdp_logger(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Setup CDP message logger to capture already-transformed CDP logs."""
		# No need to configure levels - setup_logging() already handles that
		# We just need to capture the transformed logs and route them to the CDP pane

		# Get the CDP log widget
		# EN: Assign value to cdp_log.
		# JP: cdp_log に値を代入する。
		cdp_log = self.query_one('#cdp-log', RichLog)

		# Create custom handler for CDP logging
		# EN: Define class `CDPLogHandler`.
		# JP: クラス `CDPLogHandler` を定義する。
		class CDPLogHandler(logging.Handler):
			# EN: Define function `__init__`.
			# JP: 関数 `__init__` を定義する。
			def __init__(self, rich_log: RichLog):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				super().__init__()
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.rich_log = rich_log

			# EN: Define function `emit`.
			# JP: 関数 `emit` を定義する。
			def emit(self, record):
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = self.format(record)
					# Truncate very long messages
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if len(msg) > 300:
						# EN: Assign value to msg.
						# JP: msg に値を代入する。
						msg = msg[:300] + '...'
					# Color code by level
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if record.levelno >= logging.ERROR:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.rich_log.write(f'[red]{msg}[/]')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif record.levelno >= logging.WARNING:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.rich_log.write(f'[yellow]{msg}[/]')
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.rich_log.write(f'[cyan]{msg}[/]')
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.handleError(record)

		# Setup handler for cdp_use loggers
		# EN: Assign value to cdp_handler.
		# JP: cdp_handler に値を代入する。
		cdp_handler = CDPLogHandler(cdp_log)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		cdp_handler.setFormatter(logging.Formatter('%(message)s'))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		cdp_handler.setLevel(logging.DEBUG)

		# Route CDP logs to the CDP pane
		# These are already transformed by cdp_use and at the right level from setup_logging
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for logger_name in ['websockets.client', 'cdp_use', 'cdp_use.client', 'cdp_use.cdp', 'cdp_use.cdp.registry']:
			# EN: Assign value to logger.
			# JP: logger に値を代入する。
			logger = logging.getLogger(logger_name)
			# Add our handler (don't replace - keep existing console handler too)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cdp_handler not in logger.handlers:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.addHandler(cdp_handler)

	# EN: Define function `scroll_to_input`.
	# JP: 関数 `scroll_to_input` を定義する。
	def scroll_to_input(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Scroll to the input field to ensure it's visible."""
		# EN: Assign value to input_container.
		# JP: input_container に値を代入する。
		input_container = self.query_one('#task-input-container')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		input_container.scroll_visible()

	# EN: Define function `run_task`.
	# JP: 関数 `run_task` を定義する。
	def run_task(self, task: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Launch the task in a background worker."""
		# Create or update the agent
		# EN: Assign value to agent_settings.
		# JP: agent_settings に値を代入する。
		agent_settings = AgentSettings.model_validate(self.config.get('agent', {}))

		# Get the logger
		# EN: Assign value to logger.
		# JP: logger に値を代入する。
		logger = logging.getLogger('browser_use.app')

		# Make sure intro is hidden and log is ready
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.hide_intro_panels()

		# EN: Assign value to created_new_agent.
		# JP: created_new_agent に値を代入する。
		created_new_agent = False
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.agent is None:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.llm:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError('LLM not initialized')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.agent = Agent(
				task=task,
				llm=self.llm,
				controller=self.controller if self.controller else Controller(),
				browser_session=self.browser_session,
				source='cli',
				**agent_settings.model_dump(),
			)
			# EN: Assign value to created_new_agent.
			# JP: created_new_agent に値を代入する。
			created_new_agent = True
			# Update our browser_session reference to point to the agent's
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(self.agent, 'browser_session'):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.browser_session = self.agent.browser_session
				# Set up event bus listener (will clean up any old handler first)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.setup_event_bus_listener()
		else:
			# EN: Assign value to agent_is_running.
			# JP: agent_is_running に値を代入する。
			agent_is_running = getattr(self.agent, 'running', False)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if agent_is_running:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.agent.add_new_task(task)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._telemetry.capture(
					CLITelemetryEvent(
						version=get_browser_use_version(),
						action='message_sent',
						mode='interactive',
						model=self.llm.model if self.llm and hasattr(self.llm, 'model') else None,
						model_provider=self.llm.provider if self.llm and hasattr(self.llm, 'provider') else None,
					)
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'📝 Added follow-up instruction: {task}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

		# Clear the main output log to start fresh for a new run
		# EN: Assign value to rich_log.
		# JP: rich_log に値を代入する。
		rich_log = self.query_one('#main-output-log', RichLog)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		rich_log.clear()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.agent is not None and not created_new_agent:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.agent.add_new_task(task)

		# Let the agent run in the background
		# EN: Define async function `agent_task_worker`.
		# JP: 非同期関数 `agent_task_worker` を定義する。
		async def agent_task_worker() -> None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('\n🚀 Working on task: %s', task)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.agent:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.agent.last_response_time = 0  # type: ignore

			# Panel updates are already happening via the timer in update_info_panels

			# EN: Assign value to task_start_time.
			# JP: task_start_time に値を代入する。
			task_start_time = time.time()
			# EN: Assign value to error_msg.
			# JP: error_msg に値を代入する。
			error_msg = None

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Capture telemetry for message sent
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._telemetry.capture(
					CLITelemetryEvent(
						version=get_browser_use_version(),
						action='message_sent',
						mode='interactive',
						model=self.llm.model if self.llm and hasattr(self.llm, 'model') else None,
						model_provider=self.llm.provider if self.llm and hasattr(self.llm, 'provider') else None,
					)
				)

				# Run the agent task, redirecting output to RichLog through our handler
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.agent:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.agent.run()
			except Exception as e:
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = str(e)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error('\nError running agent: %s', str(e))
			finally:
				# Capture telemetry for task completion
				# EN: Assign value to duration.
				# JP: duration に値を代入する。
				duration = time.time() - task_start_time
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._telemetry.capture(
					CLITelemetryEvent(
						version=get_browser_use_version(),
						action='task_completed' if error_msg is None else 'error',
						mode='interactive',
						model=self.llm.model if self.llm and hasattr(self.llm, 'model') else None,
						model_provider=self.llm.provider if self.llm and hasattr(self.llm, 'provider') else None,
						duration_seconds=duration,
						error_message=error_msg,
					)
				)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('\n✅ Task completed!')

				# Make sure the task input container is visible
				# EN: Assign value to task_input_container.
				# JP: task_input_container に値を代入する。
				task_input_container = self.query_one('#task-input-container')
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				task_input_container.display = True

				# Refocus the input field
				# EN: Assign value to input_field.
				# JP: input_field に値を代入する。
				input_field = self.query_one('#task-input', Input)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				input_field.focus()

				# Ensure the input is visible by scrolling to it
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.call_after_refresh(self.scroll_to_input)

		# Run the worker
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.run_worker(agent_task_worker, name='agent_task')

	# EN: Define function `action_input_history_prev`.
	# JP: 関数 `action_input_history_prev` を定義する。
	def action_input_history_prev(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Navigate to the previous item in command history."""
		# Only process if we have history and input is focused
		# EN: Assign value to input_field.
		# JP: input_field に値を代入する。
		input_field = self.query_one('#task-input', Input)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not input_field.has_focus or not self.task_history:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Move back in history if possible
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history_index > 0:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.history_index -= 1
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			input_field.value = self.task_history[self.history_index]
			# Move cursor to end of text
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			input_field.cursor_position = len(input_field.value)

	# EN: Define function `action_input_history_next`.
	# JP: 関数 `action_input_history_next` を定義する。
	def action_input_history_next(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Navigate to the next item in command history or clear input."""
		# Only process if we have history and input is focused
		# EN: Assign value to input_field.
		# JP: input_field に値を代入する。
		input_field = self.query_one('#task-input', Input)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not input_field.has_focus or not self.task_history:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Move forward in history or clear input if at the end
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.history_index < len(self.task_history) - 1:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.history_index += 1
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			input_field.value = self.task_history[self.history_index]
			# Move cursor to end of text
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			input_field.cursor_position = len(input_field.value)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.history_index == len(self.task_history) - 1:
			# At the end of history, go to "new line" state
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.history_index += 1
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			input_field.value = ''

	# EN: Define async function `action_quit`.
	# JP: 非同期関数 `action_quit` を定義する。
	async def action_quit(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Quit the application and clean up resources."""
		# Note: We don't need to close the browser session here because:
		# 1. If an agent exists, it already called browser_session.stop() in its run() method
		# 2. If keep_alive=True (default), we want to leave the browser running anyway
		# This prevents the duplicate "stop() called" messages in the logs

		# Flush telemetry before exiting
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._telemetry.flush()

		# Exit the application
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.exit()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\nTry running tasks on our cloud: https://browser-use.com')

	# EN: Define function `compose`.
	# JP: 関数 `compose` を定義する。
	def compose(self) -> ComposeResult:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create the UI layout."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		yield Header()

		# Main container for app content
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with Container(id='main-container'):
			# Logo panel
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			yield Static(BROWSER_LOGO, id='logo-panel', markup=True)

			# Links panel with URLs
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with Container(id='links-panel'):
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with HorizontalGroup(classes='link-row'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield Static('Run at scale on cloud:    [blink]☁️[/]  ', markup=True, classes='link-label')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield Link('https://browser-use.com', url='https://browser-use.com', classes='link-white link-url')

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				yield Static('')  # Empty line

				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with HorizontalGroup(classes='link-row'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield Static('Chat & share on Discord:  🚀 ', markup=True, classes='link-label')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield Link(
						'https://discord.gg/ESAUZAdxXY', url='https://discord.gg/ESAUZAdxXY', classes='link-purple link-url'
					)

				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with HorizontalGroup(classes='link-row'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield Static('Get prompt inspiration:   🦸 ', markup=True, classes='link-label')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield Link(
						'https://github.com/browser-use/awesome-prompts',
						url='https://github.com/browser-use/awesome-prompts',
						classes='link-magenta link-url',
					)

				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with HorizontalGroup(classes='link-row'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield Static('[dim]Report any issues:[/]        🐛 ', markup=True, classes='link-label')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield Link(
						'https://github.com/browser-use/browser-use/issues',
						url='https://github.com/browser-use/browser-use/issues',
						classes='link-green link-url',
					)

			# Paths panel
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			yield Static(
				f' ⚙️  Settings saved to:              {str(CONFIG.BROWSER_USE_CONFIG_FILE.resolve()).replace(str(Path.home()), "~")}\n'
				f' 📁 Outputs & recordings saved to:  {str(Path(".").resolve()).replace(str(Path.home()), "~")}',
				id='paths-panel',
				markup=True,
			)

			# Info panels (hidden by default, shown when task starts)
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with Container(id='info-panels'):
				# Top row with browser and model panels side by side
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with Container(id='top-panels'):
					# Browser panel
					# EN: Execute logic with managed resources.
					# JP: リソース管理付きで処理を実行する。
					with Container(id='browser-panel'):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						yield RichLog(id='browser-info', markup=True, highlight=True, wrap=True)

					# Model panel
					# EN: Execute logic with managed resources.
					# JP: リソース管理付きで処理を実行する。
					with Container(id='model-panel'):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						yield RichLog(id='model-info', markup=True, highlight=True, wrap=True)

				# Tasks panel (full width, below browser and model)
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with VerticalScroll(id='tasks-panel'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield RichLog(id='tasks-info', markup=True, highlight=True, wrap=True, auto_scroll=True)

			# Three-column container (hidden by default)
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with Container(id='three-column-container'):
				# Column 1: Main output
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with VerticalScroll(id='main-output-column'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield RichLog(highlight=True, markup=True, id='main-output-log', wrap=True, auto_scroll=True)

				# Column 2: Event bus events
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with VerticalScroll(id='events-column'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield RichLog(highlight=True, markup=True, id='events-log', wrap=True, auto_scroll=True)

				# Column 3: CDP messages
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with VerticalScroll(id='cdp-column'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					yield RichLog(highlight=True, markup=True, id='cdp-log', wrap=True, auto_scroll=True)

			# Task input container (now at the bottom)
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with Container(id='task-input-container'):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				yield Label('🔍 What would you like me to do on the web?', id='task-label')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				yield Input(placeholder='Enter your task...', id='task-input')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		yield Footer()

	# EN: Define function `update_info_panels`.
	# JP: 関数 `update_info_panels` を定義する。
	def update_info_panels(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update all information panels with current state."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Update actual content
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.update_browser_panel()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.update_model_panel()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.update_tasks_panel()
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logging.error(f'Error in update_info_panels: {str(e)}')
		finally:
			# Always schedule the next update - will update at 1-second intervals
			# This ensures continuous updates even if agent state changes
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.set_timer(1.0, self.update_info_panels)

	# EN: Define function `update_browser_panel`.
	# JP: 関数 `update_browser_panel` を定義する。
	def update_browser_panel(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update browser information panel with details about the browser."""
		# EN: Assign value to browser_info.
		# JP: browser_info に値を代入する。
		browser_info = self.query_one('#browser-info', RichLog)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		browser_info.clear()

		# Try to use the agent's browser session if available
		# EN: Assign value to browser_session.
		# JP: browser_session に値を代入する。
		browser_session = self.browser_session
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, 'agent') and self.agent and hasattr(self.agent, 'browser_session'):
			# EN: Assign value to browser_session.
			# JP: browser_session に値を代入する。
			browser_session = self.agent.browser_session

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_session:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Check if browser session has a CDP client
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not hasattr(browser_session, 'cdp_client') or browser_session.cdp_client is None:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					browser_info.write('[yellow]Browser session created, waiting for browser to launch...[/]')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return

				# Update our reference if we're using the agent's session
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if browser_session != self.browser_session:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.browser_session = browser_session

				# Get basic browser info from browser_profile
				# EN: Assign value to browser_type.
				# JP: browser_type に値を代入する。
				browser_type = 'Chromium'
				# EN: Assign value to headless.
				# JP: headless に値を代入する。
				headless = browser_session.browser_profile.headless

				# Determine connection type based on config
				# EN: Assign value to connection_type.
				# JP: connection_type に値を代入する。
				connection_type = 'playwright'  # Default
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if browser_session.cdp_url:
					# EN: Assign value to connection_type.
					# JP: connection_type に値を代入する。
					connection_type = 'CDP'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif browser_session.browser_profile.executable_path:
					# EN: Assign value to connection_type.
					# JP: connection_type に値を代入する。
					connection_type = 'user-provided'

				# Get window size details from browser_profile
				# EN: Assign value to window_width.
				# JP: window_width に値を代入する。
				window_width = None
				# EN: Assign value to window_height.
				# JP: window_height に値を代入する。
				window_height = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if browser_session.browser_profile.viewport:
					# EN: Assign value to window_width.
					# JP: window_width に値を代入する。
					window_width = browser_session.browser_profile.viewport.width
					# EN: Assign value to window_height.
					# JP: window_height に値を代入する。
					window_height = browser_session.browser_profile.viewport.height

				# Try to get browser PID
				# EN: Assign value to browser_pid.
				# JP: browser_pid に値を代入する。
				browser_pid = 'Unknown'
				# EN: Assign value to connected.
				# JP: connected に値を代入する。
				connected = False
				# EN: Assign value to browser_status.
				# JP: browser_status に値を代入する。
				browser_status = '[red]Disconnected[/]'

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# Check if browser PID is available
					# Check if we have a CDP client
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if browser_session.cdp_client is not None:
						# EN: Assign value to connected.
						# JP: connected に値を代入する。
						connected = True
						# EN: Assign value to browser_status.
						# JP: browser_status に値を代入する。
						browser_status = '[green]Connected[/]'
						# EN: Assign value to browser_pid.
						# JP: browser_pid に値を代入する。
						browser_pid = 'N/A'
				except Exception as e:
					# EN: Assign value to browser_pid.
					# JP: browser_pid に値を代入する。
					browser_pid = f'Error: {str(e)}'

				# Display browser information
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				browser_info.write(f'[bold cyan]Chromium[/] Browser ({browser_status})')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				browser_info.write(
					f'Type: [yellow]{connection_type}[/] [{"green" if not headless else "red"}]{" (headless)" if headless else ""}[/]'
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				browser_info.write(f'PID: [dim]{browser_pid}[/]')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				browser_info.write(f'CDP Port: {browser_session.cdp_url}')

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if window_width and window_height:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					browser_info.write(f'Window: [blue]{window_width}[/] × [blue]{window_height}[/]')

				# Include additional information about the browser if needed
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if connected and hasattr(self, 'agent') and self.agent:
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# Show when the browser was connected
						# EN: Assign value to timestamp.
						# JP: timestamp に値を代入する。
						timestamp = int(time.time())
						# EN: Assign value to current_time.
						# JP: current_time に値を代入する。
						current_time = time.strftime('%H:%M:%S', time.localtime(timestamp))
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						browser_info.write(f'Last updated: [dim]{current_time}[/]')
					except Exception:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

					# Show the agent's current page URL if available
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if browser_session.agent_focus:
						# EN: Assign value to current_url.
						# JP: current_url に値を代入する。
						current_url = (
							browser_session.agent_focus.url.replace('https://', '')
							.replace('http://', '')
							.replace('www.', '')[:36]
							+ '…'
						)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						browser_info.write(f'👁️  [green]{current_url}[/]')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				browser_info.write(f'[red]Error updating browser info: {str(e)}[/]')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			browser_info.write('[red]Browser not initialized[/]')

	# EN: Define function `update_model_panel`.
	# JP: 関数 `update_model_panel` を定義する。
	def update_model_panel(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update model information panel with details about the LLM."""
		# EN: Assign value to model_info.
		# JP: model_info に値を代入する。
		model_info = self.query_one('#model-info', RichLog)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		model_info.clear()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.llm:
			# Get model details
			# EN: Assign value to model_name.
			# JP: model_name に値を代入する。
			model_name = 'Unknown'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(self.llm, 'model_name'):
				# EN: Assign value to model_name.
				# JP: model_name に値を代入する。
				model_name = self.llm.model_name
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif hasattr(self.llm, 'model'):
				# EN: Assign value to model_name.
				# JP: model_name に値を代入する。
				model_name = self.llm.model

			# Show model name
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.agent:
				# EN: Assign value to temp_str.
				# JP: temp_str に値を代入する。
				temp_str = f'{self.llm.temperature}ºC ' if self.llm.temperature else ''
				# EN: Assign value to vision_str.
				# JP: vision_str に値を代入する。
				vision_str = '+ vision ' if self.agent.settings.use_vision else ''
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				model_info.write(
					f'[white]LLM:[/] [blue]{self.llm.__class__.__name__} [yellow]{model_name}[/] {temp_str}{vision_str}'
				)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				model_info.write(f'[white]LLM:[/] [blue]{self.llm.__class__.__name__} [yellow]{model_name}[/]')

			# Show token usage statistics if agent exists and has history
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.agent and hasattr(self.agent, 'state') and hasattr(self.agent.state, 'history'):
				# Calculate tokens per step
				# EN: Assign value to num_steps.
				# JP: num_steps に値を代入する。
				num_steps = len(self.agent.history.history)

				# Get the last step metadata to show the most recent LLM response time
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if num_steps > 0 and self.agent.history.history[-1].metadata:
					# EN: Assign value to last_step.
					# JP: last_step に値を代入する。
					last_step = self.agent.history.history[-1]
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if last_step.metadata:
						# EN: Assign value to step_duration.
						# JP: step_duration に値を代入する。
						step_duration = last_step.metadata.duration_seconds
					else:
						# EN: Assign value to step_duration.
						# JP: step_duration に値を代入する。
						step_duration = 0

				# Show total duration
				# EN: Assign value to total_duration.
				# JP: total_duration に値を代入する。
				total_duration = self.agent.history.total_duration_seconds()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if total_duration > 0:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					model_info.write(f'[white]Total Duration:[/] [magenta]{total_duration:.2f}s[/]')

					# Calculate response time metrics
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					model_info.write(f'[white]Last Step Duration:[/] [magenta]{step_duration:.2f}s[/]')

				# Add current state information
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(self.agent, 'running'):
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if getattr(self.agent, 'running', False):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						model_info.write('[yellow]LLM is thinking[blink]...[/][/]')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif hasattr(self.agent, 'state') and hasattr(self.agent.state, 'paused') and self.agent.state.paused:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						model_info.write('[orange]LLM paused[/]')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			model_info.write('[red]Model not initialized[/]')

	# EN: Define function `update_tasks_panel`.
	# JP: 関数 `update_tasks_panel` を定義する。
	def update_tasks_panel(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update tasks information panel with details about the tasks and steps hierarchy."""
		# EN: Assign value to tasks_info.
		# JP: tasks_info に値を代入する。
		tasks_info = self.query_one('#tasks-info', RichLog)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		tasks_info.clear()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.agent:
			# Check if agent has tasks
			# EN: Assign value to task_history.
			# JP: task_history に値を代入する。
			task_history = []
			# EN: Assign value to message_history.
			# JP: message_history に値を代入する。
			message_history = []

			# Try to extract tasks by looking at message history
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(self.agent, '_message_manager') and self.agent._message_manager:
				# EN: Assign value to message_history.
				# JP: message_history に値を代入する。
				message_history = self.agent._message_manager.state.history.get_messages()

				# Extract original task(s)
				# EN: Assign value to original_tasks.
				# JP: original_tasks に値を代入する。
				original_tasks = []
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for msg in message_history:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if hasattr(msg, 'content'):
						# EN: Assign value to content.
						# JP: content に値を代入する。
						content = msg.content
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if isinstance(content, str) and 'Your ultimate task is:' in content:
							# EN: Assign value to task_text.
							# JP: task_text に値を代入する。
							task_text = content.split('"""')[1].strip()
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							original_tasks.append(task_text)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if original_tasks:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					tasks_info.write('[bold green]TASK:[/]')
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for i, task in enumerate(original_tasks, 1):
						# Only show latest task if multiple task changes occurred
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if i == len(original_tasks):
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							tasks_info.write(f'[white]{task}[/]')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					tasks_info.write('')

			# Get current state information
			# EN: Assign value to current_step.
			# JP: current_step に値を代入する。
			current_step = self.agent.state.n_steps if hasattr(self.agent, 'state') else 0

			# Get all agent history items
			# EN: Assign value to history_items.
			# JP: history_items に値を代入する。
			history_items = []
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(self.agent, 'state') and hasattr(self.agent.state, 'history'):
				# EN: Assign value to history_items.
				# JP: history_items に値を代入する。
				history_items = self.agent.history.history

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if history_items:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					tasks_info.write('[bold yellow]STEPS:[/]')

					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for idx, item in enumerate(history_items, 1):
						# Determine step status
						# EN: Assign value to step_style.
						# JP: step_style に値を代入する。
						step_style = '[green]✓[/]'

						# For the current step, show it as in progress
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if idx == current_step:
							# EN: Assign value to step_style.
							# JP: step_style に値を代入する。
							step_style = '[yellow]⟳[/]'

						# Check if this step had an error
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if item.result and any(result.error for result in item.result):
							# EN: Assign value to step_style.
							# JP: step_style に値を代入する。
							step_style = '[red]✗[/]'

						# Show step number
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						tasks_info.write(f'{step_style} Step {idx}/{current_step}')

						# Show goal if available
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if item.model_output and hasattr(item.model_output, 'current_state'):
							# Show goal for this step
							# EN: Assign value to goal.
							# JP: goal に値を代入する。
							goal = item.model_output.current_state.next_goal
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if goal:
								# Take just the first line for display
								# EN: Assign value to goal_lines.
								# JP: goal_lines に値を代入する。
								goal_lines = goal.strip().split('\n')
								# EN: Assign value to goal_summary.
								# JP: goal_summary に値を代入する。
								goal_summary = goal_lines[0]
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								tasks_info.write(f'   [cyan]Goal:[/] {goal_summary}')

							# Show evaluation of previous goal (feedback)
							# EN: Assign value to eval_prev.
							# JP: eval_prev に値を代入する。
							eval_prev = item.model_output.current_state.evaluation_previous_goal
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if eval_prev and idx > 1:  # Only show for steps after the first
								# EN: Assign value to eval_lines.
								# JP: eval_lines に値を代入する。
								eval_lines = eval_prev.strip().split('\n')
								# EN: Assign value to eval_summary.
								# JP: eval_summary に値を代入する。
								eval_summary = eval_lines[0]
								# EN: Assign value to eval_summary.
								# JP: eval_summary に値を代入する。
								eval_summary = eval_summary.replace('Success', '✅ ').replace('Failed', '❌ ').strip()
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								tasks_info.write(f'   [tan]Evaluation:[/] {eval_summary}')

						# Show actions taken in this step
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if item.model_output and item.model_output.action:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							tasks_info.write('   [purple]Actions:[/]')
							# EN: Iterate over items in a loop.
							# JP: ループで要素を順に処理する。
							for action_idx, action in enumerate(item.model_output.action, 1):
								# EN: Assign value to action_type.
								# JP: action_type に値を代入する。
								action_type = action.__class__.__name__
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if hasattr(action, 'model_dump'):
									# For proper actions, show the action type
									# EN: Assign value to action_dict.
									# JP: action_dict に値を代入する。
									action_dict = action.model_dump(exclude_unset=True)
									# EN: Branch logic based on a condition.
									# JP: 条件に応じて処理を分岐する。
									if action_dict:
										# EN: Assign value to action_name.
										# JP: action_name に値を代入する。
										action_name = list(action_dict.keys())[0]
										# EN: Evaluate an expression.
										# JP: 式を評価する。
										tasks_info.write(f'     {action_idx}. [blue]{action_name}[/]')

						# Show results or errors from this step
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if item.result:
							# EN: Iterate over items in a loop.
							# JP: ループで要素を順に処理する。
							for result in item.result:
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if result.error:
									# EN: Assign value to error_text.
									# JP: error_text に値を代入する。
									error_text = result.error
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									tasks_info.write(f'   [red]Error:[/] {error_text}')
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								elif result.extracted_content:
									# EN: Assign value to content.
									# JP: content に値を代入する。
									content = result.extracted_content
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									tasks_info.write(f'   [green]Result:[/] {content}')

						# Add a space between steps for readability
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						tasks_info.write('')

			# If agent is actively running, show a status indicator
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(self.agent, 'running') and getattr(self.agent, 'running', False):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				tasks_info.write('[yellow]Agent is actively working[blink]...[/][/]')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif hasattr(self.agent, 'state') and hasattr(self.agent.state, 'paused') and self.agent.state.paused:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				tasks_info.write('[orange]Agent is paused (press Enter to resume)[/]')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			tasks_info.write('[dim]Agent not initialized[/]')

		# Force scroll to bottom
		# EN: Assign value to tasks_panel.
		# JP: tasks_panel に値を代入する。
		tasks_panel = self.query_one('#tasks-panel')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		tasks_panel.scroll_end(animate=False)


# EN: Define async function `run_prompt_mode`.
# JP: 非同期関数 `run_prompt_mode` を定義する。
async def run_prompt_mode(prompt: str, ctx: click.Context, debug: bool = False):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Run browser-use in non-interactive mode with a single prompt."""
	# Import and call setup_logging to ensure proper initialization
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.logging_config import setup_logging

	# Set up logging to only show results by default
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'result'

	# Re-run setup_logging to apply the new log level
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	setup_logging()

	# The logging is now properly configured by setup_logging()
	# No need to manually configure handlers since setup_logging() handles it

	# Initialize telemetry
	# EN: Assign value to telemetry.
	# JP: telemetry に値を代入する。
	telemetry = ProductTelemetry()
	# EN: Assign value to start_time.
	# JP: start_time に値を代入する。
	start_time = time.time()
	# EN: Assign value to error_msg.
	# JP: error_msg に値を代入する。
	error_msg = None

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Load config
		# EN: Assign value to config.
		# JP: config に値を代入する。
		config = load_user_config()
		# EN: Assign value to config.
		# JP: config に値を代入する。
		config = update_config_with_click_args(config, ctx)

		# Get LLM
		# EN: Assign value to llm.
		# JP: llm に値を代入する。
		llm = get_llm(config)

		# Capture telemetry for CLI start in oneshot mode
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		telemetry.capture(
			CLITelemetryEvent(
				version=get_browser_use_version(),
				action='start',
				mode='oneshot',
				model=llm.model if hasattr(llm, 'model') else None,
				model_provider=llm.__class__.__name__ if llm else None,
			)
		)

		# Get agent settings from config
		# EN: Assign value to agent_settings.
		# JP: agent_settings に値を代入する。
		agent_settings = AgentSettings.model_validate(config.get('agent', {}))

		# Create browser session with config parameters
		# EN: Assign value to browser_config.
		# JP: browser_config に値を代入する。
		browser_config = config.get('browser', {})
		# Remove None values from browser_config
		# EN: Assign value to browser_config.
		# JP: browser_config に値を代入する。
		browser_config = {k: v for k, v in browser_config.items() if v is not None}
		# Create BrowserProfile with user_data_dir
		# EN: Assign value to profile.
		# JP: profile に値を代入する。
		profile = BrowserProfile(user_data_dir=str(USER_DATA_DIR), **browser_config)
		# EN: Assign value to browser_session.
		# JP: browser_session に値を代入する。
		browser_session = BrowserSession(
			browser_profile=profile,
		)

		# Create and run agent
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(
			task=prompt,
			llm=llm,
			browser_session=browser_session,
			source='cli',
			**agent_settings.model_dump(),
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await agent.run()

		# Ensure the browser session is fully stopped
		# The agent's close() method only kills the browser if keep_alive=False,
		# but we need to ensure all background tasks are stopped regardless
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_session:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Kill the browser session to stop all background tasks
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await browser_session.kill()
			except Exception:
				# Ignore errors during cleanup
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass

		# Capture telemetry for successful completion
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		telemetry.capture(
			CLITelemetryEvent(
				version=get_browser_use_version(),
				action='task_completed',
				mode='oneshot',
				model=llm.model if hasattr(llm, 'model') else None,
				model_provider=llm.__class__.__name__ if llm else None,
				duration_seconds=time.time() - start_time,
			)
		)

	except Exception as e:
		# EN: Assign value to error_msg.
		# JP: error_msg に値を代入する。
		error_msg = str(e)
		# Capture telemetry for error
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		telemetry.capture(
			CLITelemetryEvent(
				version=get_browser_use_version(),
				action='error',
				mode='oneshot',
				model=llm.model if hasattr(llm, 'model') else None,
				model_provider=llm.__class__.__name__ if llm and 'llm' in locals() else None,
				duration_seconds=time.time() - start_time,
				error_message=error_msg,
			)
		)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if debug:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import traceback

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			traceback.print_exc()
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'Error: {str(e)}', file=sys.stderr)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(1)
	finally:
		# Ensure telemetry is flushed
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		telemetry.flush()

		# Give a brief moment for cleanup to complete
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await asyncio.sleep(0.1)

		# Cancel any remaining tasks to ensure clean exit
		# EN: Assign value to tasks.
		# JP: tasks に値を代入する。
		tasks = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for task in tasks:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			task.cancel()

		# Wait for all tasks to be cancelled
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tasks:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.gather(*tasks, return_exceptions=True)


# EN: Define async function `textual_interface`.
# JP: 非同期関数 `textual_interface` を定義する。
async def textual_interface(config: dict[str, Any]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Run the Textual interface."""
	# Prevent browser_use from setting up logging at import time
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'

	# EN: Assign value to logger.
	# JP: logger に値を代入する。
	logger = logging.getLogger('browser_use.startup')

	# Set up logging for Textual UI - prevent any logging to stdout
	# EN: Define function `setup_textual_logging`.
	# JP: 関数 `setup_textual_logging` を定義する。
	def setup_textual_logging():
		# Replace all handlers with null handler
		# EN: Assign value to root_logger.
		# JP: root_logger に値を代入する。
		root_logger = logging.getLogger()
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for handler in root_logger.handlers:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			root_logger.removeHandler(handler)

		# Add null handler to ensure no output to stdout/stderr
		# EN: Assign value to null_handler.
		# JP: null_handler に値を代入する。
		null_handler = logging.NullHandler()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		root_logger.addHandler(null_handler)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Logging configured for Textual UI')

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Setting up Browser, Controller, and LLM...')

	# Step 1: Initialize BrowserSession with config
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Initializing BrowserSession...')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Get browser config from the config dict
		# EN: Assign value to browser_config.
		# JP: browser_config に値を代入する。
		browser_config = config.get('browser', {})

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info('Browser type: chromium')  # BrowserSession only supports chromium
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_config.get('executable_path'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'Browser binary: {browser_config["executable_path"]}')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_config.get('headless'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('Browser mode: headless')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('Browser mode: visible')

		# Create BrowserSession directly with config parameters
		# Remove None values from browser_config
		# EN: Assign value to browser_config.
		# JP: browser_config に値を代入する。
		browser_config = {k: v for k, v in browser_config.items() if v is not None}
		# Create BrowserProfile with user_data_dir
		# EN: Assign value to profile.
		# JP: profile に値を代入する。
		profile = BrowserProfile(user_data_dir=str(USER_DATA_DIR), **browser_config)
		# EN: Assign value to browser_session.
		# JP: browser_session に値を代入する。
		browser_session = BrowserSession(
			browser_profile=profile,
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('BrowserSession initialized successfully')

		# Set up FIFO logging pipes for streaming logs to UI
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from browser_use.logging_config import setup_log_pipes

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			setup_log_pipes(session_id=browser_session.id)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'FIFO logging pipes set up for session {browser_session.id[-4:]}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Could not set up FIFO logging pipes: {e}')

		# Browser version logging not available with CDP implementation
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Error initializing BrowserSession: {str(e)}', exc_info=True)
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise RuntimeError(f'Failed to initialize BrowserSession: {str(e)}')

	# Step 3: Initialize Controller
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Initializing Controller...')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = Controller()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Controller initialized successfully')
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Error initializing Controller: {str(e)}', exc_info=True)
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise RuntimeError(f'Failed to initialize Controller: {str(e)}')

	# Step 4: Get LLM
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Getting LLM...')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Ensure setup_logging is not called when importing modules
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		os.environ['BROWSER_USE_SETUP_LOGGING'] = 'false'
		# EN: Assign value to llm.
		# JP: llm に値を代入する。
		llm = get_llm(config)
		# Log LLM details
		# EN: Assign value to model_name.
		# JP: model_name に値を代入する。
		model_name = getattr(llm, 'model_name', None) or getattr(llm, 'model', 'Unknown model')
		# EN: Assign value to provider.
		# JP: provider に値を代入する。
		provider = llm.__class__.__name__
		# EN: Assign value to temperature.
		# JP: temperature に値を代入する。
		temperature = getattr(llm, 'temperature', 0.0)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'LLM: {provider} ({model_name}), temperature: {temperature}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'LLM initialized successfully: {provider}')
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Error getting LLM: {str(e)}', exc_info=True)
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise RuntimeError(f'Failed to initialize LLM: {str(e)}')

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Initializing BrowserUseApp instance...')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to app.
		# JP: app に値を代入する。
		app = BrowserUseApp(config)
		# Pass the initialized components to the app
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		app.browser_session = browser_session
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		app.controller = controller
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		app.llm = llm

		# Set up event bus listener now that browser session is available
		# Note: This needs to be called before run_async() but after browser_session is set
		# We'll defer this to on_mount() since it needs the widgets to be available

		# Configure logging for Textual UI before going fullscreen
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		setup_textual_logging()

		# Log browser and model configuration that will be used
		# EN: Assign value to browser_type.
		# JP: browser_type に値を代入する。
		browser_type = 'Chromium'  # BrowserSession only supports Chromium
		# EN: Assign value to model_name.
		# JP: model_name に値を代入する。
		model_name = config.get('model', {}).get('name', 'auto-detected')
		# EN: Assign value to headless.
		# JP: headless に値を代入する。
		headless = config.get('browser', {}).get('headless', False)
		# EN: Assign value to headless_str.
		# JP: headless_str に値を代入する。
		headless_str = 'headless' if headless else 'visible'

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'Preparing {browser_type} browser ({headless_str}) with {model_name} LLM')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Starting Textual app with run_async()...')
		# No more logging after this point as we're in fullscreen mode
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await app.run_async()
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Error in textual_interface: {str(e)}', exc_info=True)
		# Note: We don't close the browser session here to avoid duplicate stop() calls
		# The browser session will be cleaned up by its __del__ method if needed
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise


# EN: Define async function `run_auth_command`.
# JP: 非同期関数 `run_auth_command` を定義する。
async def run_auth_command():
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Run the authentication command with dummy task in UI."""
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import asyncio
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import os

	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.sync.auth import DeviceAuthClient

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('🔐 Browser Use Cloud Authentication')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('=' * 40)

	# Ensure cloud sync is enabled (should be default, but make sure)
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	os.environ['BROWSER_USE_CLOUD_SYNC'] = 'true'

	# EN: Assign value to auth_client.
	# JP: auth_client に値を代入する。
	auth_client = DeviceAuthClient()

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('🔍 Debug: Checking authentication status...')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print(f'    API Token: {"✅ Present" if auth_client.api_token else "❌ Missing"}')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print(f'    User ID: {auth_client.user_id}')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print(f'    Is Authenticated: {auth_client.is_authenticated}')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if auth_client.auth_config.authorized_at:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'    Authorized at: {auth_client.auth_config.authorized_at}')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print()

	# Check if already authenticated
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if auth_client.is_authenticated:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('✅ Already authenticated!')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'   User ID: {auth_client.user_id}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'   Authenticated at: {auth_client.auth_config.authorized_at}')

		# Show cloud URL if possible
		# EN: Assign value to frontend_url.
		# JP: frontend_url に値を代入する。
		frontend_url = CONFIG.BROWSER_USE_CLOUD_UI_URL or auth_client.base_url.replace('//api.', '//cloud.')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'\n🌐 View your runs at: {frontend_url}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('🚀 Starting authentication flow...')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('   This will open a browser window for you to sign in.')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print()

	# Initialize variables for exception handling
	# EN: Assign value to task_id.
	# JP: task_id に値を代入する。
	task_id = None
	# EN: Assign value to sync_service.
	# JP: sync_service に値を代入する。
	sync_service = None

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Create authentication flow with dummy task
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from uuid_extensions import uuid7str

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.agent.cloud_events import (
			CreateAgentSessionEvent,
			CreateAgentStepEvent,
			CreateAgentTaskEvent,
			UpdateAgentTaskEvent,
		)
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.sync.service import CloudSync

		# IDs for our session and task
		# EN: Assign value to session_id.
		# JP: session_id に値を代入する。
		session_id = uuid7str()
		# EN: Assign value to task_id.
		# JP: task_id に値を代入する。
		task_id = uuid7str()

		# Create special sync service that allows auth events
		# EN: Assign value to sync_service.
		# JP: sync_service に値を代入する。
		sync_service = CloudSync(allow_session_events_for_auth=True)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sync_service.set_auth_flow_active()  # Explicitly enable auth flow
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		sync_service.session_id = session_id  # Set session ID for auth context
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		sync_service.auth_client = auth_client  # Use the same auth client instance!

		# 1. Create session (like main branch does at start)
		# EN: Assign value to session_event.
		# JP: session_event に値を代入する。
		session_event = CreateAgentSessionEvent(
			id=session_id,
			user_id=auth_client.temp_user_id,
			browser_session_id=uuid7str(),
			browser_session_live_url='',
			browser_session_cdp_url='',
			device_id=auth_client.device_id,
			browser_state={
				'viewport': {'width': 1280, 'height': 720},
				'user_agent': None,
				'headless': True,
				'initial_url': None,
				'final_url': None,
				'total_pages_visited': 0,
				'session_duration_seconds': 0,
			},
			browser_session_data={
				'cookies': [],
				'secrets': {},
				'allowed_domains': [],
			},
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await sync_service.handle_event(session_event)

		# Brief delay to ensure session is created in backend before sending task
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await asyncio.sleep(0.5)

		# 2. Create task (like main branch does at start)
		# EN: Assign value to task_event.
		# JP: task_event に値を代入する。
		task_event = CreateAgentTaskEvent(
			id=task_id,
			agent_session_id=session_id,
			llm_model='auth-flow',
			task='🔐 Complete authentication and join the browser-use community',
			user_id=auth_client.temp_user_id,
			device_id=auth_client.device_id,
			done_output=None,
			user_feedback_type=None,
			user_comment=None,
			gif_url=None,
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await sync_service.handle_event(task_event)

		# Longer delay to ensure task is created in backend before sending step event
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await asyncio.sleep(1.0)

		# 3. Run authentication with timeout
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('⏳ Waiting for authentication... (this may take up to 2 minutes for testing)')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('   Complete the authentication in your browser, then this will continue automatically.')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print()

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('🔧 Debug: Starting authentication process...')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'    Original auth client authenticated: {auth_client.is_authenticated}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'    Sync service auth client authenticated: {sync_service.auth_client.is_authenticated}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'    Same auth client? {auth_client is sync_service.auth_client}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'    Session ID: {sync_service.session_id}')

			# Create a task to show periodic status updates
			# EN: Define async function `show_auth_progress`.
			# JP: 非同期関数 `show_auth_progress` を定義する。
			async def show_auth_progress():
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for i in range(1, 25):  # Show updates every 5 seconds for 2 minutes
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(5)
					# EN: Assign value to fresh_check.
					# JP: fresh_check に値を代入する。
					fresh_check = DeviceAuthClient()
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					print(f'⏱️  Waiting for authentication... ({i * 5}s elapsed)')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					print(f'    Status: {"✅ Authenticated" if fresh_check.is_authenticated else "⏳ Still waiting"}')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if fresh_check.is_authenticated:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						print('🎉 Authentication detected! Completing...')
						# EN: Exit the current loop.
						# JP: 現在のループを終了する。
						break

			# Run authentication and progress updates concurrently
			# EN: Assign value to auth_start_time.
			# JP: auth_start_time に値を代入する。
			auth_start_time = asyncio.get_event_loop().time()
			# EN: Assign value to auth_task.
			# JP: auth_task に値を代入する。
			auth_task = asyncio.create_task(sync_service.authenticate(show_instructions=True))
			# EN: Assign value to progress_task.
			# JP: progress_task に値を代入する。
			progress_task = asyncio.create_task(show_auth_progress())

			# Wait for authentication to complete, with timeout
			# EN: Assign value to success.
			# JP: success に値を代入する。
			success = await asyncio.wait_for(auth_task, timeout=120.0)  # 2 minutes for initial testing
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			progress_task.cancel()  # Stop the progress updates

			# EN: Assign value to auth_duration.
			# JP: auth_duration に値を代入する。
			auth_duration = asyncio.get_event_loop().time() - auth_start_time
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'🔧 Debug: Authentication returned: {success} (took {auth_duration:.1f}s)')

		except TimeoutError:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('⏱️ Authentication timed out after 2 minutes.')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('   Checking if authentication completed in background...')

			# Create a fresh auth client to check current status
			# EN: Assign value to fresh_auth_client.
			# JP: fresh_auth_client に値を代入する。
			fresh_auth_client = DeviceAuthClient()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('🔧 Debug: Fresh auth client check:')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'    API Token: {"✅ Present" if fresh_auth_client.api_token else "❌ Missing"}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'    Is Authenticated: {fresh_auth_client.is_authenticated}')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if fresh_auth_client.is_authenticated:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('✅ Authentication was successful!')
				# EN: Assign value to success.
				# JP: success に値を代入する。
				success = True
				# Update the sync service's auth client
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				sync_service.auth_client = fresh_auth_client
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('❌ Authentication not completed. Please try again.')
				# EN: Assign value to success.
				# JP: success に値を代入する。
				success = False
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'❌ Authentication error: {type(e).__name__}: {e}')
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import traceback

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'📄 Full traceback: {traceback.format_exc()}')
			# EN: Assign value to success.
			# JP: success に値を代入する。
			success = False

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if success:
			# 4. Send step event to show progress (like main branch during execution)
			# Use the sync service's auth client which has the updated user_id
			# EN: Assign value to step_event.
			# JP: step_event に値を代入する。
			step_event = CreateAgentStepEvent(
				# Remove explicit ID - let it auto-generate to avoid backend validation issues
				user_id=auth_client.temp_user_id,  # Use same temp user_id as task for consistency
				device_id=auth_client.device_id,  # Use consistent device_id
				agent_task_id=task_id,
				step=1,
				actions=[
					{
						'click': {
							'coordinate': [800, 400],
							'description': 'Click on Star button',
							'success': True,
						},
						'done': {
							'success': True,
							'text': '⭐ Starred browser-use/browser-use repository! Welcome to the community!',
						},
					}
				],
				next_goal='⭐ Star browser-use GitHub repository to join the community',
				evaluation_previous_goal='Authentication completed successfully',
				memory='User authenticated with Browser Use Cloud and is now part of the community',
				screenshot_url=None,
				url='https://github.com/browser-use/browser-use',
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('📤 Sending dummy step event...')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await sync_service.handle_event(step_event)

			# Small delay to ensure step is processed before completion
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(0.5)

			# 5. Complete task (like main branch does at end)
			# EN: Assign value to completion_event.
			# JP: completion_event に値を代入する。
			completion_event = UpdateAgentTaskEvent(
				id=task_id,
				user_id=auth_client.temp_user_id,  # Use same temp user_id as task for consistency
				device_id=auth_client.device_id,  # Use consistent device_id
				done_output="🎉 Welcome to Browser Use! You're now authenticated and part of our community. ⭐ Your future tasks will sync to the cloud automatically.",
				user_feedback_type=None,
				user_comment=None,
				gif_url=None,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await sync_service.handle_event(completion_event)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('🎉 Authentication successful!')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('   Future browser-use runs will now sync to the cloud.')
		else:
			# Failed - still complete the task with failure message
			# EN: Assign value to completion_event.
			# JP: completion_event に値を代入する。
			completion_event = UpdateAgentTaskEvent(
				id=task_id,
				user_id=auth_client.temp_user_id,  # Still temp user since auth failed
				device_id=auth_client.device_id,
				done_output='❌ Authentication failed. Please try again.',
				user_feedback_type=None,
				user_comment=None,
				gif_url=None,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await sync_service.handle_event(completion_event)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('❌ Authentication failed.')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('   Please try again or check your internet connection.')

	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'❌ Authentication error: {e}')
		# Still try to complete the task in UI with error message
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if task_id and sync_service:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Import required modules.
				# JP: 必要なモジュールをインポートする。
				from browser_use.agent.cloud_events import UpdateAgentTaskEvent

				# EN: Assign value to completion_event.
				# JP: completion_event に値を代入する。
				completion_event = UpdateAgentTaskEvent(
					id=task_id,
					user_id=auth_client.temp_user_id,
					device_id=auth_client.device_id,
					done_output=f'❌ Authentication error: {e}',
					user_feedback_type=None,
					user_comment=None,
					gif_url=None,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await sync_service.handle_event(completion_event)
			except Exception:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass  # Don't fail if we can't send the error event
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(1)


# EN: Define function `main`.
# JP: 関数 `main` を定義する。
@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Print version and exit')
@click.option('--model', type=str, help='Model to use (e.g., gpt-5-mini, claude-4-sonnet, gemini-2.5-flash)')
@click.option('--debug', is_flag=True, help='Enable verbose startup logging')
@click.option('--headless', is_flag=True, help='Run browser in headless mode', default=None)
@click.option('--window-width', type=int, help='Browser window width')
@click.option('--window-height', type=int, help='Browser window height')
@click.option(
	'--user-data-dir', type=str, help='Path to Chrome user data directory (e.g. ~/Library/Application Support/Google/Chrome)'
)
@click.option('--profile-directory', type=str, help='Chrome profile directory name (e.g. "Default", "Profile 1")')
@click.option('--cdp-url', type=str, help='Connect to existing Chrome via CDP URL (e.g. http://localhost:9222)')
@click.option('--proxy-url', type=str, help='Proxy server for Chromium traffic (e.g. http://host:8080 or socks5://host:1080)')
@click.option('--no-proxy', type=str, help='Comma-separated hosts to bypass proxy (e.g. localhost,127.0.0.1,*.internal)')
@click.option('--proxy-username', type=str, help='Proxy auth username')
@click.option('--proxy-password', type=str, help='Proxy auth password')
@click.option('-p', '--prompt', type=str, help='Run a single task without the TUI (headless mode)')
@click.option('--mcp', is_flag=True, help='Run as MCP server (exposes JSON RPC via stdin/stdout)')
@click.pass_context
def main(ctx: click.Context, debug: bool = False, **kwargs):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Browser Use - AI Agent for Web Automation

	Run without arguments to start the interactive TUI.
	"""

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if ctx.invoked_subcommand is None:
		# No subcommand, run the main interface
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		run_main_interface(ctx, debug, **kwargs)


# EN: Define function `run_main_interface`.
# JP: 関数 `run_main_interface` を定義する。
def run_main_interface(ctx: click.Context, debug: bool = False, **kwargs):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Run the main browser-use interface"""

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if kwargs['version']:
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from importlib.metadata import version

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(version('browser-use'))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(0)

	# Check if MCP server mode is activated
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if kwargs.get('mcp'):
		# Capture telemetry for MCP server mode via CLI (suppress any logging from this)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to telemetry.
			# JP: telemetry に値を代入する。
			telemetry = ProductTelemetry()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			telemetry.capture(
				CLITelemetryEvent(
					version=get_browser_use_version(),
					action='start',
					mode='mcp_server',
				)
			)
		except Exception:
			# Ignore telemetry errors in MCP mode to prevent any stdout contamination
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass
		# Run as MCP server
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.mcp.server import main as mcp_main

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		asyncio.run(mcp_main())
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# Check if prompt mode is activated
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if kwargs.get('prompt'):
		# Set environment variable for prompt mode before running
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'result'
		# Run in non-interactive mode
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		asyncio.run(run_prompt_mode(kwargs['prompt'], ctx, debug))
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# Configure console logging
	# EN: Assign value to console_handler.
	# JP: console_handler に値を代入する。
	console_handler = logging.StreamHandler(sys.stdout)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S'))

	# Configure root logger
	# EN: Assign value to root_logger.
	# JP: root_logger に値を代入する。
	root_logger = logging.getLogger()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	root_logger.setLevel(logging.INFO if not debug else logging.DEBUG)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	root_logger.addHandler(console_handler)

	# EN: Assign value to logger.
	# JP: logger に値を代入する。
	logger = logging.getLogger('browser_use.startup')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.info('Starting Browser-Use initialization')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if debug:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'System info: Python {sys.version.split()[0]}, Platform: {sys.platform}')

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Loading environment variables from secrets.env...')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	load_secrets_env()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Environment variables loaded')

	# Load user configuration
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Loading user configuration...')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to config.
		# JP: config に値を代入する。
		config = load_user_config()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'User configuration loaded from {CONFIG.BROWSER_USE_CONFIG_FILE}')
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Error loading user configuration: {str(e)}', exc_info=True)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'Error loading configuration: {str(e)}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(1)

	# Update config with command-line arguments
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Updating configuration with command line arguments...')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to config.
		# JP: config に値を代入する。
		config = update_config_with_click_args(config, ctx)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Configuration updated')
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Error updating config with command line args: {str(e)}', exc_info=True)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'Error updating configuration: {str(e)}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(1)

	# Save updated config
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Saving user configuration...')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		save_user_config(config)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Configuration saved')
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Error saving user configuration: {str(e)}', exc_info=True)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'Error saving configuration: {str(e)}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(1)

	# Setup handlers for console output before entering Textual UI
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('Setting up handlers for Textual UI...')

	# Log browser and model configuration that will be used
	# EN: Assign value to browser_type.
	# JP: browser_type に値を代入する。
	browser_type = 'Chromium'  # BrowserSession only supports Chromium
	# EN: Assign value to model_name.
	# JP: model_name に値を代入する。
	model_name = config.get('model', {}).get('name', 'auto-detected')
	# EN: Assign value to headless.
	# JP: headless に値を代入する。
	headless = config.get('browser', {}).get('headless', False)
	# EN: Assign value to headless_str.
	# JP: headless_str に値を代入する。
	headless_str = 'headless' if headless else 'visible'

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.info(f'Preparing {browser_type} browser ({headless_str}) with {model_name} LLM')

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Run the Textual UI interface - now all the initialization happens before we go fullscreen
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Starting Textual UI interface...')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		asyncio.run(textual_interface(config))
	except Exception as e:
		# Restore console logging for error reporting
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		root_logger.setLevel(logging.INFO)
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for handler in root_logger.handlers:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			root_logger.removeHandler(handler)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		root_logger.addHandler(console_handler)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Error initializing Browser-Use: {str(e)}', exc_info=debug)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'\nError launching Browser-Use: {str(e)}')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if debug:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import traceback

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			traceback.print_exc()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.exit(1)


# EN: Define function `auth`.
# JP: 関数 `auth` を定義する。
@main.command()
def auth():
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Authenticate with Browser Use Cloud to sync your runs"""
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(run_auth_command())


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	main()

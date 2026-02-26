# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Event-driven browser session with backwards compatibility."""

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
from contextlib import suppress
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from functools import cached_property
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, Literal, Self, cast

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import EventBus
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use import CDPClient
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.fetch import AuthRequiredEvent, RequestPausedEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.network import Cookie
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.target import AttachedToTargetEvent, SessionID, TargetID
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from websockets.exceptions import InvalidStatus

# CDP logging is now handled by setup_logging() in logging_config.py
# It automatically sets CDP logs to the same level as browser_use logs
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.constants import DEFAULT_NEW_TAB_URL
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	AgentFocusChangedEvent,
	BrowserConnectedEvent,
	BrowserErrorEvent,
	BrowserLaunchEvent,
	BrowserLaunchResult,
	BrowserStartEvent,
	BrowserStateRequestEvent,
	BrowserStopEvent,
	BrowserStoppedEvent,
	CloseTabEvent,
	FileDownloadedEvent,
	NavigateToUrlEvent,
	NavigationCompleteEvent,
	NavigationStartedEvent,
	SwitchTabEvent,
	TabClosedEvent,
	TabCreatedEvent,
)

# Connection retry controls for CDP. By default we retry indefinitely with a short delay,
# so long-running jobs keep trying to reconnect instead of failing early.
# EN: Assign value to _CDP_CONNECT_RETRY_DELAY.
# JP: _CDP_CONNECT_RETRY_DELAY に値を代入する。
_CDP_CONNECT_RETRY_DELAY = float(os.environ.get('BROWSER_USE_CDP_CONNECT_RETRY_DELAY', '5.0'))
# EN: Assign value to _CDP_CONNECT_MAX_RETRIES_RAW.
# JP: _CDP_CONNECT_MAX_RETRIES_RAW に値を代入する。
_CDP_CONNECT_MAX_RETRIES_RAW = os.environ.get('BROWSER_USE_CDP_CONNECT_MAX_RETRIES')
# EN: Assign annotated value to _CDP_CONNECT_MAX_RETRIES.
# JP: _CDP_CONNECT_MAX_RETRIES に型付きの値を代入する。
_CDP_CONNECT_MAX_RETRIES: int | None
# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Assign value to _CDP_CONNECT_MAX_RETRIES.
	# JP: _CDP_CONNECT_MAX_RETRIES に値を代入する。
	_CDP_CONNECT_MAX_RETRIES = int(_CDP_CONNECT_MAX_RETRIES_RAW) if _CDP_CONNECT_MAX_RETRIES_RAW else None
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _CDP_CONNECT_MAX_RETRIES is not None and _CDP_CONNECT_MAX_RETRIES <= 0:
		# EN: Assign value to _CDP_CONNECT_MAX_RETRIES.
		# JP: _CDP_CONNECT_MAX_RETRIES に値を代入する。
		_CDP_CONNECT_MAX_RETRIES = None
except ValueError:
	# EN: Assign value to _CDP_CONNECT_MAX_RETRIES.
	# JP: _CDP_CONNECT_MAX_RETRIES に値を代入する。
	_CDP_CONNECT_MAX_RETRIES = None

# Whether newly discovered targets (tabs) should use dedicated WebSocket connections by default.
# Using a dedicated socket per target improves isolation but can exhaust DevTools proxies when many
# tabs are opened in long-running batches. The default is now shared sockets for stability, and can
# be overridden via environment variable when isolation is required.
# EN: Assign value to _CDP_DEDICATED_SOCKET_DEFAULT.
# JP: _CDP_DEDICATED_SOCKET_DEFAULT に値を代入する。
_CDP_DEDICATED_SOCKET_DEFAULT = os.environ.get('BROWSER_USE_DEDICATED_SOCKET_PER_TARGET', 'false').lower() in (
	'1',
	'true',
	'yes',
	'on',
)
# If a dedicated socket fails to open (often due to hub limits like \"Too many websocket connections\"),
# automatically retry once with the shared root socket to keep the agent running.
# EN: Assign value to _CDP_NEW_SOCKET_FALLBACK.
# JP: _CDP_NEW_SOCKET_FALLBACK に値を代入する。
_CDP_NEW_SOCKET_FALLBACK = os.environ.get('BROWSER_USE_NEW_SOCKET_FALLBACK', 'true').lower() in (
	'1',
	'true',
	'yes',
	'on',
)

# Whether newly discovered targets (tabs) should use dedicated WebSocket connections by default.
# Using a dedicated socket per target improves isolation but can exhaust DevTools proxies when many
# tabs are opened in long-running batches. The default is now shared sockets for stability, and can
# be overridden via environment variable when isolation is required.
# EN: Assign value to _CDP_DEDICATED_SOCKET_DEFAULT.
# JP: _CDP_DEDICATED_SOCKET_DEFAULT に値を代入する。
_CDP_DEDICATED_SOCKET_DEFAULT = os.environ.get('BROWSER_USE_DEDICATED_SOCKET_PER_TARGET', 'false').lower() in (
	'1',
	'true',
	'yes',
	'on',
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.profile import BrowserProfile, ProxySettings, ViewportSize
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserStateSummary, TabInfo
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import EnhancedDOMTreeNode, TargetInfo
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe_debug
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import _log_pretty_url, is_default_new_tab_url, is_new_tab_page


# EN: Define async function `ensure_browser_state_handler_registered`.
# JP: 非同期関数 `ensure_browser_state_handler_registered` を定義する。
async def ensure_browser_state_handler_registered(session: 'BrowserSession') -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Ensure the DOM watchdog handler that yields BrowserStateSummary is registered."""

	# EN: Define function `_get_handlers`.
	# JP: 関数 `_get_handlers` を定義する。
	def _get_handlers() -> list[Any]:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return session.event_bus.handlers.get(BrowserStateRequestEvent.__name__, []) or []

	# EN: Define function `_has_summary_handler`.
	# JP: 関数 `_has_summary_handler` を定義する。
	def _has_summary_handler(handlers: list[Any]) -> bool:
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for handler in handlers:
			# EN: Assign value to name.
			# JP: name に値を代入する。
			name = getattr(handler, '__name__', '')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'DOMWatchdog.on_BrowserStateRequestEvent' in name:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True
			# EN: Assign value to watchdog_instance.
			# JP: watchdog_instance に値を代入する。
			watchdog_instance = getattr(handler, '__self__', None)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if getattr(getattr(watchdog_instance, '__class__', None), '__name__', None) == 'DOMWatchdog':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Assign value to handlers.
	# JP: handlers に値を代入する。
	handlers = _get_handlers()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _has_summary_handler(handlers):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	session.logger.debug('BrowserStateRequestEvent handler missing; attaching watchdogs before requesting state summary.')

	# Clear any stale handlers so watchdog reattachment can register a fresh DOM handler
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	session.event_bus.handlers.pop(BrowserStateRequestEvent.__name__, None)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if getattr(session, '_watchdogs_attached', False):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		session._watchdogs_attached = False  # type: ignore[attr-defined]

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	await session.attach_all_watchdogs()

	# EN: Assign value to handlers.
	# JP: handlers に値を代入する。
	handlers = _get_handlers()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not _has_summary_handler(handlers):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		session.logger.warning(
			'BrowserStateRequestEvent handler still missing after reattaching watchdogs; continuing to dispatch for retry path.'
		)


# EN: Assign value to DEFAULT_BROWSER_PROFILE.
# JP: DEFAULT_BROWSER_PROFILE に値を代入する。
DEFAULT_BROWSER_PROFILE = BrowserProfile()

# EN: Assign value to _LOGGED_UNIQUE_SESSION_IDS.
# JP: _LOGGED_UNIQUE_SESSION_IDS に値を代入する。
_LOGGED_UNIQUE_SESSION_IDS = set()  # track unique session IDs that have been logged to make sure we always assign a unique enough id to new sessions and avoid ambiguity in logs
# EN: Assign value to red.
# JP: red に値を代入する。
red = '\033[91m'
# EN: Assign value to reset.
# JP: reset に値を代入する。
reset = '\033[0m'


# EN: Define class `CDPSession`.
# JP: クラス `CDPSession` を定義する。
class CDPSession(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Info about a single CDP session bound to a specific target.

	Can optionally use its own WebSocket connection for better isolation.
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True, revalidate_instances='never')

	# EN: Assign annotated value to cdp_client.
	# JP: cdp_client に型付きの値を代入する。
	cdp_client: CDPClient

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID
	# EN: Assign annotated value to session_id.
	# JP: session_id に型付きの値を代入する。
	session_id: SessionID
	# EN: Assign annotated value to title.
	# JP: title に型付きの値を代入する。
	title: str = 'Unknown title'
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str = DEFAULT_NEW_TAB_URL

	# Track if this session owns its CDP client (for cleanup)
	# EN: Assign annotated value to owns_cdp_client.
	# JP: owns_cdp_client に型付きの値を代入する。
	owns_cdp_client: bool = False

	# EN: Define async function `for_target`.
	# JP: 非同期関数 `for_target` を定義する。
	@classmethod
	async def for_target(
		cls,
		cdp_client: CDPClient,
		target_id: TargetID,
		new_socket: bool = False,
		cdp_url: str | None = None,
		domains: list[str] | None = None,
	):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create a CDP session for a target.

		Args:
		    cdp_client: Existing CDP client to use (or just for reference if creating own)
		    target_id: Target ID to attach to
		    new_socket: If True, create a dedicated WebSocket connection for this target
		    cdp_url: CDP URL (required if new_socket is True)
		    domains: List of CDP domains to enable. If None, enables default domains.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if new_socket:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not cdp_url:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError('cdp_url required when new_socket=True')
			# Create a new CDP client with its own WebSocket connection
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import logging

			# EN: Assign value to logger.
			# JP: logger に値を代入する。
			logger = logging.getLogger(f'browser_use.CDPSession.{target_id[-4:]}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'🔌 Creating new dedicated WebSocket connection for target 🅣 {target_id}')

			# EN: Assign value to target_cdp_client.
			# JP: target_cdp_client に値を代入する。
			target_cdp_client = CDPClient(cdp_url)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await target_cdp_client.start()

			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = cls(
				cdp_client=target_cdp_client,
				target_id=target_id,
				session_id='connecting',
				owns_cdp_client=True,
			)
		else:
			# Use shared CDP client
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = cls(
				cdp_client=cdp_client,
				target_id=target_id,
				session_id='connecting',
				owns_cdp_client=False,
			)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await cdp_session.attach(domains=domains)

	# EN: Define async function `attach`.
	# JP: 非同期関数 `attach` を定義する。
	async def attach(self, domains: list[str] | None = None) -> Self:
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = await self.cdp_client.send.Target.attachToTarget(
			params={
				'targetId': self.target_id,
				'flatten': True,
				'filter': [  # type: ignore
					{'type': 'page', 'exclude': False},
					{'type': 'iframe', 'exclude': False},
				],
			}
		)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.session_id = result['sessionId']

		# Use specified domains or default domains
		# EN: Assign value to domains.
		# JP: domains に値を代入する。
		domains = domains or ['Page', 'DOM', 'DOMSnapshot', 'Accessibility', 'Runtime', 'Inspector']

		# Enable all domains in parallel
		# EN: Assign value to enable_tasks.
		# JP: enable_tasks に値を代入する。
		enable_tasks = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for domain in domains:
			# Get the enable method, e.g. self.cdp_client.send.Page.enable(session_id=self.session_id)
			# EN: Assign value to domain_api.
			# JP: domain_api に値を代入する。
			domain_api = getattr(self.cdp_client.send, domain, None)
			# Browser and Target domains don't use session_id, dont pass it for those
			# EN: Assign value to enable_kwargs.
			# JP: enable_kwargs に値を代入する。
			enable_kwargs = {} if domain in ['Browser', 'Target'] else {'session_id': self.session_id}
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert domain_api and hasattr(domain_api, 'enable'), (
				f'{domain_api} is not a recognized CDP domain with a .enable() method'
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			enable_tasks.append(domain_api.enable(**enable_kwargs))

		# EN: Assign value to results.
		# JP: results に値を代入する。
		results = await asyncio.gather(*enable_tasks, return_exceptions=True)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if any(isinstance(result, Exception) for result in results):
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError(f'Failed to enable requested CDP domain: {results}')

		# in case 'Debugger' domain is enabled, disable breakpoints on the page so it doesnt pause on crashes / debugger statements
		# also covered by Runtime.runIfWaitingForDebugger() calls in get_or_create_cdp_session()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.cdp_client.send.Debugger.setSkipAllPauses(params={'skip': True}, session_id=self.session_id)
			# if 'Debugger' not in domains:
			#     await self.cdp_client.send.Debugger.disable()
			# await cdp_session.cdp_client.send.EventBreakpoints.disable(session_id=cdp_session.session_id)
		except Exception:
			# self.logger.warning(f'Failed to disable page JS breakpoints: {e}')
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass

		# EN: Assign value to target_info.
		# JP: target_info に値を代入する。
		target_info = await self.get_target_info()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.title = target_info['title']
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.url = target_info['url']
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define async function `disconnect`.
	# JP: 非同期関数 `disconnect` を定義する。
	async def disconnect(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Disconnect and cleanup if this session owns its CDP client."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.owns_cdp_client and self.cdp_client:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.cdp_client.stop()
			except Exception:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass  # Ignore errors during cleanup

	# EN: Define async function `get_tab_info`.
	# JP: 非同期関数 `get_tab_info` を定義する。
	async def get_tab_info(self) -> TabInfo:
		# EN: Assign value to target_info.
		# JP: target_info に値を代入する。
		target_info = await self.get_target_info()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return TabInfo(
			target_id=target_info['targetId'],
			url=target_info['url'],
			title=target_info['title'],
		)

	# EN: Define async function `get_target_info`.
	# JP: 非同期関数 `get_target_info` を定義する。
	async def get_target_info(self) -> TargetInfo:
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = await self.cdp_client.send.Target.getTargetInfo(params={'targetId': self.target_id})
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result['targetInfo']


# EN: Define class `BrowserSession`.
# JP: クラス `BrowserSession` を定義する。
class BrowserSession(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Event-driven browser session with backwards compatibility.

	This class provides a 2-layer architecture:
	- High-level event handling for agents/tools
	- Direct CDP/Playwright calls for browser operations

	Supports both event-driven and imperative calling styles.

	Browser configuration is stored in the browser_profile, session identity in direct fields:
	```python
	# Direct settings (recommended for most users)
	session = BrowserSession(headless=True, user_data_dir='./profile')

	# Or use a profile (for advanced use cases)
	session = BrowserSession(browser_profile=BrowserProfile(...))

	# Access session fields directly, browser settings via profile or property
	print(session.id)  # Session field
	```
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(
		arbitrary_types_allowed=True,
		validate_assignment=True,
		extra='forbid',
		revalidate_instances='never',  # resets private attrs on every model rebuild
	)

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		# Core configuration
		id: str | None = None,
		cdp_url: str | None = None,
		is_local: bool = False,
		browser_profile: BrowserProfile | None = None,
		# BrowserProfile fields that can be passed directly
		# From BrowserConnectArgs
		headers: dict[str, str] | None = None,
		# From BrowserLaunchArgs
		env: dict[str, str | float | bool] | None = None,
		executable_path: str | Path | None = None,
		headless: bool | None = None,
		args: list[str] | None = None,
		ignore_default_args: list[str] | Literal[True] | None = None,
		channel: str | None = None,
		chromium_sandbox: bool | None = None,
		devtools: bool | None = None,
		downloads_path: str | Path | None = None,
		traces_dir: str | Path | None = None,
		# From BrowserContextArgs
		accept_downloads: bool | None = None,
		permissions: list[str] | None = None,
		user_agent: str | None = None,
		screen: dict | None = None,
		viewport: dict | None = None,
		no_viewport: bool | None = None,
		device_scale_factor: float | None = None,
		record_har_content: str | None = None,
		record_har_mode: str | None = None,
		record_har_path: str | Path | None = None,
		record_video_dir: str | Path | None = None,
		record_video_framerate: int | None = None,
		record_video_size: dict | None = None,
		# From BrowserLaunchPersistentContextArgs
		user_data_dir: str | Path | None = None,
		# From BrowserNewContextArgs
		storage_state: str | Path | dict[str, Any] | None = None,
		# BrowserProfile specific fields
		disable_security: bool | None = None,
		deterministic_rendering: bool | None = None,
		allowed_domains: list[str] | None = None,
		keep_alive: bool | None = None,
		proxy: ProxySettings | None = None,
		enable_default_extensions: bool | None = None,
		window_size: dict | None = None,
		window_position: dict | None = None,
		minimum_wait_page_load_time: float | None = None,
		wait_for_network_idle_page_load_time: float | None = None,
		wait_between_actions: float | None = None,
		filter_highlight_ids: bool | None = None,
		auto_download_pdfs: bool | None = None,
		profile_directory: str | None = None,
		cookie_whitelist_domains: list[str] | None = None,
		# DOM extraction layer configuration
		cross_origin_iframes: bool | None = None,
		highlight_elements: bool | None = None,
		paint_order_filtering: bool | None = None,
		# Iframe processing limits
		max_iframes: int | None = None,
		max_iframe_depth: int | None = None,
	):
		# Following the same pattern as AgentSettings in service.py
		# Only pass non-None values to avoid validation errors
		# EN: Assign value to profile_kwargs.
		# JP: profile_kwargs に値を代入する。
		profile_kwargs = {k: v for k, v in locals().items() if k not in ['self', 'browser_profile', 'id'] and v is not None}

		# if is_local is False but executable_path is provided, set is_local to True
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_local is False and executable_path is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			profile_kwargs['is_local'] = True
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not cdp_url:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			profile_kwargs['is_local'] = True

		# Create browser profile from direct parameters or use provided one
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_profile is not None:
			# Merge any direct kwargs into the provided browser_profile (direct kwargs take precedence)
			# EN: Assign value to merged_kwargs.
			# JP: merged_kwargs に値を代入する。
			merged_kwargs = {**browser_profile.model_dump(exclude_unset=True), **profile_kwargs}
			# EN: Assign value to resolved_browser_profile.
			# JP: resolved_browser_profile に値を代入する。
			resolved_browser_profile = BrowserProfile(**merged_kwargs)
		else:
			# EN: Assign value to resolved_browser_profile.
			# JP: resolved_browser_profile に値を代入する。
			resolved_browser_profile = BrowserProfile(**profile_kwargs)

		# Initialize the Pydantic model
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__(
			id=id or str(uuid7str()),
			browser_profile=resolved_browser_profile,
		)

	# Session configuration (session identity only)
	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str = Field(default_factory=lambda: str(uuid7str()), description='Unique identifier for this browser session')

	# Browser configuration (reusable profile)
	# EN: Assign annotated value to browser_profile.
	# JP: browser_profile に型付きの値を代入する。
	browser_profile: BrowserProfile = Field(
		default_factory=lambda: DEFAULT_BROWSER_PROFILE,
		description='BrowserProfile() options to use for the session, otherwise a default profile will be used',
	)

	# Convenience properties for common browser settings
	# EN: Define function `cdp_url`.
	# JP: 関数 `cdp_url` を定義する。
	@property
	def cdp_url(self) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""CDP URL from browser profile."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.browser_profile.cdp_url

	# EN: Define function `is_local`.
	# JP: 関数 `is_local` を定義する。
	@property
	def is_local(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Whether this is a local browser instance from browser profile."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.browser_profile.is_local

	# Main shared event bus for all browser session + all watchdogs
	# EN: Assign annotated value to event_bus.
	# JP: event_bus に型付きの値を代入する。
	event_bus: EventBus = Field(default_factory=EventBus)

	# Mutable public state
	# EN: Assign annotated value to agent_focus.
	# JP: agent_focus に型付きの値を代入する。
	agent_focus: CDPSession | None = None

	# Mutable private state shared between watchdogs
	# EN: Assign annotated value to _cdp_client_root.
	# JP: _cdp_client_root に型付きの値を代入する。
	_cdp_client_root: CDPClient | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _cdp_session_pool.
	# JP: _cdp_session_pool に型付きの値を代入する。
	_cdp_session_pool: dict[str, CDPSession] = PrivateAttr(default_factory=dict)
	# EN: Assign annotated value to _cached_browser_state_summary.
	# JP: _cached_browser_state_summary に型付きの値を代入する。
	_cached_browser_state_summary: Any = PrivateAttr(default=None)
	# EN: Assign annotated value to _cached_selector_map.
	# JP: _cached_selector_map に型付きの値を代入する。
	_cached_selector_map: dict[int, EnhancedDOMTreeNode] = PrivateAttr(default_factory=dict)
	# EN: Assign annotated value to _downloaded_files.
	# JP: _downloaded_files に型付きの値を代入する。
	_downloaded_files: list[str] = PrivateAttr(default_factory=list)  # Track files downloaded during this session

	# Watchdogs
	# EN: Assign annotated value to _crash_watchdog.
	# JP: _crash_watchdog に型付きの値を代入する。
	_crash_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _downloads_watchdog.
	# JP: _downloads_watchdog に型付きの値を代入する。
	_downloads_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _aboutblank_watchdog.
	# JP: _aboutblank_watchdog に型付きの値を代入する。
	_aboutblank_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _security_watchdog.
	# JP: _security_watchdog に型付きの値を代入する。
	_security_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _storage_state_watchdog.
	# JP: _storage_state_watchdog に型付きの値を代入する。
	_storage_state_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _local_browser_watchdog.
	# JP: _local_browser_watchdog に型付きの値を代入する。
	_local_browser_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _default_action_watchdog.
	# JP: _default_action_watchdog に型付きの値を代入する。
	_default_action_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _dom_watchdog.
	# JP: _dom_watchdog に型付きの値を代入する。
	_dom_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _screenshot_watchdog.
	# JP: _screenshot_watchdog に型付きの値を代入する。
	_screenshot_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _permissions_watchdog.
	# JP: _permissions_watchdog に型付きの値を代入する。
	_permissions_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _recording_watchdog.
	# JP: _recording_watchdog に型付きの値を代入する。
	_recording_watchdog: Any | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _initial_window_state_applied.
	# JP: _initial_window_state_applied に型付きの値を代入する。
	_initial_window_state_applied: bool = PrivateAttr(default=False)
	# EN: Assign annotated value to _fullscreen_requested.
	# JP: _fullscreen_requested に型付きの値を代入する。
	_fullscreen_requested: bool = PrivateAttr(default=False)
	# EN: Assign annotated value to _logger.
	# JP: _logger に型付きの値を代入する。
	_logger: Any = PrivateAttr(default=None)

	# EN: Define function `logger`.
	# JP: 関数 `logger` を定義する。
	@property
	def logger(self) -> Any:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get instance-specific logger with session ID in the name"""
		# **regenerate it every time** because our id and str(self) can change as browser connection state changes
		# if self._logger is None or not self._cdp_client_root:
		#     self._logger = logging.getLogger(f'browser_use.{self}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return logging.getLogger(f'browser_use.{self}')

	# EN: Define function `_id_for_logs`.
	# JP: 関数 `_id_for_logs` を定義する。
	@cached_property
	def _id_for_logs(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get human-friendly semi-unique identifier for differentiating different BrowserSession instances in logs"""
		# EN: Assign value to str_id.
		# JP: str_id に値を代入する。
		str_id = self.id[-4:]  # default to last 4 chars of truly random uuid, less helpful than cdp port but always unique enough
		# EN: Assign value to port_number.
		# JP: port_number に値を代入する。
		port_number = (self.cdp_url or 'no-cdp').rsplit(':', 1)[-1].split('/', 1)[0].strip()
		# EN: Assign value to port_is_random.
		# JP: port_is_random に値を代入する。
		port_is_random = not port_number.startswith('922')
		# EN: Assign value to port_is_unique_enough.
		# JP: port_is_unique_enough に値を代入する。
		port_is_unique_enough = port_number not in _LOGGED_UNIQUE_SESSION_IDS
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if port_number and port_number.isdigit() and port_is_random and port_is_unique_enough:
			# if cdp port is random/unique enough to identify this session, use it as our id in logs
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_LOGGED_UNIQUE_SESSION_IDS.add(port_number)
			# EN: Assign value to str_id.
			# JP: str_id に値を代入する。
			str_id = port_number
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str_id

	# EN: Define function `_tab_id_for_logs`.
	# JP: 関数 `_tab_id_for_logs` を定義する。
	@property
	def _tab_id_for_logs(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.agent_focus.target_id[-2:] if self.agent_focus and self.agent_focus.target_id else f'{red}--{reset}'

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'BrowserSession🅑 {self._id_for_logs} 🅣 {self._tab_id_for_logs} (cdp_url={self.cdp_url}, profile={self.browser_profile})'

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'BrowserSession🅑 {self._id_for_logs} 🅣 {self._tab_id_for_logs}'

	# EN: Define async function `reset`.
	# JP: 非同期関数 `reset` を定義する。
	async def reset(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear all cached CDP sessions with proper cleanup."""

		# TODO: clear the event bus queue here, implement this helper
		# await self.event_bus.wait_for_idle(timeout=5.0)
		# await self.event_bus.clear()

		# Disconnect sessions that own their WebSocket connections
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for session in self._cdp_session_pool.values():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(session, 'disconnect'):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.disconnect()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._cdp_session_pool.clear()

		# Close the shared CDP client to avoid leaking WebSocket connections
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._cdp_client_root:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with suppress(Exception):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._cdp_client_root.stop()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cdp_client_root = None  # type: ignore
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cached_browser_state_summary = None
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._cached_selector_map.clear()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._downloaded_files.clear()

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.agent_focus = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.is_local:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.browser_profile.cdp_url = None

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._crash_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._downloads_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._aboutblank_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._security_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._storage_state_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._local_browser_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._default_action_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._dom_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._screenshot_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._permissions_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._recording_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._initial_window_state_applied = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._fullscreen_requested = False

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, '_watchdogs_attached'):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._watchdogs_attached = False

	# EN: Define function `_reset_event_bus_state`.
	# JP: 関数 `_reset_event_bus_state` を定義する。
	def _reset_event_bus_state(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Reset watchdog references and re-register core event handlers."""

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._crash_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._downloads_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._aboutblank_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._security_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._storage_state_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._local_browser_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._default_action_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._dom_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._screenshot_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._permissions_watchdog = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._recording_watchdog = None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, '_watchdogs_attached'):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._watchdogs_attached = False

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.event_bus = EventBus()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.model_post_init(None)

	# EN: Define async function `drain_event_bus`.
	# JP: 非同期関数 `drain_event_bus` を定義する。
	async def drain_event_bus(self, *, timeout: float = 5.0) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Wait for the event bus to become idle and clean up history.

		Returns True when the bus drains successfully, False when a timeout
		forces a rotation to a fresh bus. Always keeps the CDP connection
		alive so follow-up runs maintain context.
		"""

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.event_bus.wait_until_idle(timeout=timeout)
		except TimeoutError:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(
				'Event bus failed to drain after %.1fs; rotating for a clean follow-up.',
				timeout,
			)
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with suppress(Exception):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.event_bus.stop(clear=True, timeout=timeout)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._reset_event_bus_state()
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with suppress(Exception):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.cleanup_event_history()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Define function `model_post_init`.
	# JP: 関数 `model_post_init` を定義する。
	def model_post_init(self, __context) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Register event handlers after model initialization."""
		# Check if handlers are already registered to prevent duplicates

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdog_base import BaseWatchdog

		# EN: Assign value to start_handlers.
		# JP: start_handlers に値を代入する。
		start_handlers = self.event_bus.handlers.get('BrowserStartEvent', [])
		# EN: Assign value to start_handler_names.
		# JP: start_handler_names に値を代入する。
		start_handler_names = [getattr(h, '__name__', str(h)) for h in start_handlers]

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if any('on_BrowserStartEvent' in name for name in start_handler_names):
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError(
				'[BrowserSession] Duplicate handler registration attempted! '
				'on_BrowserStartEvent is already registered. '
				'This likely means BrowserSession was initialized multiple times with the same EventBus.'
			)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, BrowserStartEvent, self.on_BrowserStartEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, BrowserStopEvent, self.on_BrowserStopEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, NavigateToUrlEvent, self.on_NavigateToUrlEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, SwitchTabEvent, self.on_SwitchTabEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, TabCreatedEvent, self.on_TabCreatedEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, TabClosedEvent, self.on_TabClosedEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, AgentFocusChangedEvent, self.on_AgentFocusChangedEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, FileDownloadedEvent, self.on_FileDownloadedEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		BaseWatchdog.attach_handler_to_session(self, CloseTabEvent, self.on_CloseTabEvent)

	# EN: Define async function `start`.
	# JP: 非同期関数 `start` を定義する。
	async def start(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Start the browser session."""
		# EN: Assign value to start_event.
		# JP: start_event に値を代入する。
		start_event = self.event_bus.dispatch(BrowserStartEvent())
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await start_event
		# Ensure any exceptions from the event handler are propagated
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await start_event.event_result(raise_if_any=True, raise_if_none=False)

	# EN: Define async function `kill`.
	# JP: 非同期関数 `kill` を定義する。
	async def kill(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Kill the browser session and reset all state."""
		# First save storage state while CDP is still connected
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import SaveStorageStateEvent

		# EN: Assign value to save_event.
		# JP: save_event に値を代入する。
		save_event = self.event_bus.dispatch(SaveStorageStateEvent())
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await save_event

		# Dispatch stop event to kill the browser
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.event_bus.dispatch(BrowserStopEvent(force=True))
		# Stop the event bus
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.event_bus.stop(clear=True, timeout=5)
		# Reset all state
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.reset()
		# Create fresh event bus
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.event_bus = EventBus()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.model_post_init(None)

	# EN: Define async function `stop`.
	# JP: 非同期関数 `stop` を定義する。
	async def stop(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Stop the browser session without killing the browser process.

		This clears event buses and cached state but keeps the browser alive.
		Useful when you want to clean up resources but plan to reconnect later.
		"""
		# First save storage state while CDP is still connected
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import SaveStorageStateEvent

		# EN: Assign value to save_event.
		# JP: save_event に値を代入する。
		save_event = self.event_bus.dispatch(SaveStorageStateEvent())
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await save_event

		# Now dispatch BrowserStopEvent to notify watchdogs
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.event_bus.dispatch(BrowserStopEvent(force=False))

		# Stop the event bus
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.event_bus.stop(clear=True, timeout=5)
		# Reset all state
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.reset()
		# Create fresh event bus
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.event_bus = EventBus()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.model_post_init(None)

	# EN: Define async function `on_BrowserStartEvent`.
	# JP: 非同期関数 `on_BrowserStartEvent` を定義する。
	async def on_BrowserStartEvent(self, event: BrowserStartEvent) -> dict[str, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle browser start request.

		Returns:
		    Dict with 'cdp_url' key containing the CDP URL
		"""

		# await self.reset()

		# Initialize and attach all watchdogs FIRST so LocalBrowserWatchdog can handle BrowserLaunchEvent
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.attach_all_watchdogs()

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# If no CDP URL, launch local browser
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.cdp_url:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.is_local:
					# Launch local browser using event-driven approach
					# EN: Assign value to launch_event.
					# JP: launch_event に値を代入する。
					launch_event = self.event_bus.dispatch(BrowserLaunchEvent())
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await launch_event

					# Get the CDP URL from LocalBrowserWatchdog handler result
					# EN: Assign annotated value to launch_result.
					# JP: launch_result に型付きの値を代入する。
					launch_result: BrowserLaunchResult = cast(
						BrowserLaunchResult, await launch_event.event_result(raise_if_none=True, raise_if_any=True)
					)
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.browser_profile.cdp_url = launch_result.cdp_url
				else:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError('Got BrowserSession(is_local=False) but no cdp_url was provided to connect to!')

			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.cdp_url and '://' in self.cdp_url

			# Only connect if not already connected
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._cdp_client_root is None:
				# Setup browser via CDP (for both local and remote cases)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.connect(cdp_url=self.cdp_url)
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert self.cdp_client is not None

				# Notify that browser is connected (single place)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.event_bus.dispatch(BrowserConnectedEvent(cdp_url=self.cdp_url))
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('Already connected to CDP, skipping reconnection')

			# Return the CDP URL for other components
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return {'cdp_url': self.cdp_url}

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='BrowserStartEventError',
					message=f'Failed to start browser: {type(e).__name__} {e}',
					details={'cdp_url': self.cdp_url, 'is_local': self.is_local},
				)
			)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_NavigateToUrlEvent`.
	# JP: 非同期関数 `on_NavigateToUrlEvent` を定義する。
	async def on_NavigateToUrlEvent(self, event: NavigateToUrlEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle navigation requests - core browser functionality."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[on_NavigateToUrlEvent] Received NavigateToUrlEvent: url={event.url}, new_tab={event.new_tab}')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.agent_focus:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('Cannot navigate - browser not connected')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to target_id.
		# JP: target_id に値を代入する。
		target_id = None

		# If new_tab=True but we're already in a new tab, set new_tab=False
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.new_tab:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to current_url.
				# JP: current_url に値を代入する。
				current_url = await self.get_current_page_url()

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if is_new_tab_page(current_url):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'[on_NavigateToUrlEvent] Already in new tab ({current_url}), setting new_tab=False')
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					event.new_tab = False
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[on_NavigateToUrlEvent] Could not check current URL: {e}')

		# check if the url is already open in a tab somewhere that we're not currently on, if so, short-circuit and just switch to it
		# EN: Assign value to targets.
		# JP: targets に値を代入する。
		targets = await self._cdp_get_all_pages()
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for target in targets:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target.get('url') == event.url and target['targetId'] != self.agent_focus.target_id and not event.new_tab:
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = target['targetId']
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				event.new_tab = False
				# await self.event_bus.dispatch(SwitchTabEvent(target_id=target_id))

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Find or create target for navigation

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[on_NavigateToUrlEvent] Processing new_tab={event.new_tab}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if event.new_tab:
				# Look for existing default start page tab that's not the current one
				# EN: Assign value to targets.
				# JP: targets に値を代入する。
				targets = await self._cdp_get_all_pages()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[on_NavigateToUrlEvent] Found {len(targets)} existing tabs')
				# EN: Assign value to current_target_id.
				# JP: current_target_id に値を代入する。
				current_target_id = self.agent_focus.target_id if self.agent_focus else None
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[on_NavigateToUrlEvent] Current target_id: {current_target_id}')

				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for idx, target in enumerate(targets):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f'[on_NavigateToUrlEvent] Tab {idx}: url={target.get("url")}, targetId={target["targetId"]}'
					)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if is_new_tab_page(target.get('url')) and target['targetId'] != current_target_id:
						# EN: Assign value to target_id.
						# JP: target_id に値を代入する。
						target_id = target['targetId']
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'Reusing existing default start page tab #{target_id[-4:]}')
						# EN: Exit the current loop.
						# JP: 現在のループを終了する。
						break

				# Create new tab if no reusable one found
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not target_id:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('[on_NavigateToUrlEvent] No reusable start page tab found, creating new tab...')
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to target_id.
						# JP: target_id に値を代入する。
						target_id = await self._cdp_create_new_page(DEFAULT_NEW_TAB_URL)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'[on_NavigateToUrlEvent] Created new page with target_id: {target_id}')
						# EN: Assign value to targets.
						# JP: targets に値を代入する。
						targets = await self._cdp_get_all_pages()

						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'Created new tab #{target_id[-4:]}')
						# Dispatch TabCreatedEvent for new tab
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self.event_bus.dispatch(TabCreatedEvent(target_id=target_id, url=DEFAULT_NEW_TAB_URL))
					except Exception as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.error(f'[on_NavigateToUrlEvent] Failed to create new tab: {type(e).__name__}: {e}')
						# Fall back to using current tab
						# EN: Assign value to target_id.
						# JP: target_id に値を代入する。
						target_id = self.agent_focus.target_id
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.warning(f'[on_NavigateToUrlEvent] Falling back to current tab #{target_id[-4:]}')
			else:
				# Use current tab
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = target_id or self.agent_focus.target_id

			# Only switch tab if we're not already on the target tab
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.agent_focus is None or self.agent_focus.target_id != target_id:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'[on_NavigateToUrlEvent] Switching to target tab {target_id[-4:]} (current: {self.agent_focus.target_id[-4:] if self.agent_focus else "none"})'
				)
				# Activate target (bring to foreground)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.event_bus.dispatch(SwitchTabEvent(target_id=target_id))
				# which does this for us:
				# self.agent_focus = await self.get_or_create_cdp_session(target_id)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[on_NavigateToUrlEvent] Already on target tab {target_id[-4:]}, skipping SwitchTabEvent')

			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.agent_focus is not None and self.agent_focus.target_id == target_id, (
				'Agent focus not updated to new target_id after SwitchTabEvent should have switched to it'
			)

			# Dispatch navigation started
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.event_bus.dispatch(NavigationStartedEvent(target_id=target_id, url=event.url))

			# Navigate to URL
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.agent_focus.cdp_client.send.Page.navigate(
				params={
					'url': event.url,
					'transitionType': 'address_bar',
					# 'referrer': 'https://www.google.com',
				},
				session_id=self.agent_focus.session_id,
			)

			# # Wait a bit to ensure page starts loading
			# await asyncio.sleep(0.5)

			# Close any extension options pages that might have opened
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._close_extension_options_pages()

			# Dispatch navigation complete
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Dispatching NavigationCompleteEvent for {event.url} (tab #{target_id[-4:]})')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.event_bus.dispatch(
				NavigationCompleteEvent(
					target_id=target_id,
					url=event.url,
					status=None,  # CDP doesn't provide status directly
				)
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.event_bus.dispatch(
				AgentFocusChangedEvent(target_id=target_id, url=event.url)
			)  # do not await! AgentFocusChangedEvent calls SwitchTabEvent and it will deadlock, dispatch to enqueue and return

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if is_default_new_tab_url(event.url):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._close_data_url_tabs(exclude_target_id=target_id)

			# Note: These should be handled by dedicated watchdogs:
			# - Security checks (security_watchdog)
			# - Page health checks (crash_watchdog)
			# - Dialog handling (dialog_watchdog)
			# - Download handling (downloads_watchdog)
			# - DOM rebuilding (dom_watchdog)

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'Navigation failed: {type(e).__name__}: {e}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target_id:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.event_bus.dispatch(
					NavigationCompleteEvent(
						target_id=target_id,
						url=event.url,
						error_message=f'{type(e).__name__}: {e}',
					)
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.event_bus.dispatch(AgentFocusChangedEvent(target_id=target_id, url=event.url))
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_SwitchTabEvent`.
	# JP: 非同期関数 `on_SwitchTabEvent` を定義する。
	async def on_SwitchTabEvent(self, event: SwitchTabEvent) -> TargetID:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle tab switching - core browser functionality."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.agent_focus:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError('Cannot switch tabs - browser not connected')

		# EN: Assign value to all_pages.
		# JP: all_pages に値を代入する。
		all_pages = await self._cdp_get_all_pages()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.target_id is None:
			# most recently opened page
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if all_pages:
				# update the target id to be the id of the most recently opened page, then proceed to switch to it
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				event.target_id = all_pages[-1]['targetId']
			else:
				# no pages open at all, create a new one (handles switching to it automatically)
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert self._cdp_client_root is not None, 'CDP client root not initialized - browser may not be connected yet'
				# EN: Assign value to new_target.
				# JP: new_target に値を代入する。
				new_target = await self._cdp_client_root.send.Target.createTarget(params={'url': DEFAULT_NEW_TAB_URL})
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = new_target['targetId']
				# do not await! these may circularly trigger SwitchTabEvent and could deadlock, dispatch to enqueue and return
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.event_bus.dispatch(TabCreatedEvent(url=DEFAULT_NEW_TAB_URL, target_id=target_id))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.event_bus.dispatch(AgentFocusChangedEvent(target_id=target_id, url=DEFAULT_NEW_TAB_URL))
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return target_id

		# switch to the target
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.agent_focus = await self.get_or_create_cdp_session(target_id=event.target_id, focus=True)

		# dispatch focus changed event
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.event_bus.dispatch(
			AgentFocusChangedEvent(
				target_id=self.agent_focus.target_id,
				url=self.agent_focus.url,
			)
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.agent_focus.target_id

	# EN: Define async function `on_CloseTabEvent`.
	# JP: 非同期関数 `on_CloseTabEvent` を定義する。
	async def on_CloseTabEvent(self, event: CloseTabEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle tab closure - update focus if needed."""

		# Use root client to close target to ensure we can close it even if we're not focused on it
		# and to avoid using a session that we're about to close
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._cdp_client_root:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._cdp_client_root.send.Target.closeTarget(params={'targetId': event.target_id})

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.event_bus.dispatch(TabClosedEvent(target_id=event.target_id))

	# EN: Define async function `on_TabCreatedEvent`.
	# JP: 非同期関数 `on_TabCreatedEvent` を定義する。
	async def on_TabCreatedEvent(self, event: TabCreatedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle tab creation - apply viewport settings to new tab."""
		# Apply viewport settings if configured
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_profile.viewport and not self.browser_profile.no_viewport:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to viewport_width.
				# JP: viewport_width に値を代入する。
				viewport_width = self.browser_profile.viewport.width
				# EN: Assign value to viewport_height.
				# JP: viewport_height に値を代入する。
				viewport_height = self.browser_profile.viewport.height
				# EN: Assign value to device_scale_factor.
				# JP: device_scale_factor に値を代入する。
				device_scale_factor = self.browser_profile.device_scale_factor or 1.0

				# Use the helper method with the new tab's target_id
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._cdp_set_viewport(viewport_width, viewport_height, device_scale_factor, target_id=event.target_id)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Applied viewport {viewport_width}x{viewport_height} to tab {event.target_id[-8:]}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'Failed to set viewport for new tab {event.target_id[-8:]}: {e}')

	# EN: Define async function `on_TabClosedEvent`.
	# JP: 非同期関数 `on_TabClosedEvent` を定義する。
	async def on_TabClosedEvent(self, event: TabClosedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle tab closure - update focus if needed."""

		# Cleanup the session if it exists to prevent WebSocket leaks
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.target_id in self._cdp_session_pool:
			# EN: Assign value to session.
			# JP: session に値を代入する。
			session = self._cdp_session_pool.pop(event.target_id)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(session, 'disconnect'):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.disconnect()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Disconnected CDP session for closed tab {event.target_id}')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.agent_focus:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Get current tab index
		# EN: Assign value to current_target_id.
		# JP: current_target_id に値を代入する。
		current_target_id = self.agent_focus.target_id

		# If the closed tab was the current one, find a new target
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if current_target_id == event.target_id:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.event_bus.dispatch(SwitchTabEvent(target_id=None))

	# EN: Define async function `on_AgentFocusChangedEvent`.
	# JP: 非同期関数 `on_AgentFocusChangedEvent` を定義する。
	async def on_AgentFocusChangedEvent(self, event: AgentFocusChangedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle agent focus change - update focus and clear cache."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🔄 AgentFocusChangedEvent received: target_id=...{event.target_id[-4:]} url={event.url}')

		# Clear cached DOM state since focus changed
		# self.logger.debug('🔄 Clearing DOM cache...')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._dom_watchdog:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._dom_watchdog.clear_cache()
			# self.logger.debug('🔄 Cleared DOM cache after focus change')

		# Clear cached browser state
		# self.logger.debug('🔄 Clearing cached browser state...')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cached_browser_state_summary = None
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._cached_selector_map.clear()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('🔄 Cached browser state cleared')
		# EN: Assign value to all_targets.
		# JP: all_targets に値を代入する。
		all_targets = await self._cdp_get_all_pages(include_chrome=True)

		# Update agent focus if a specific target_id is provided
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.target_id:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.agent_focus = await self.get_or_create_cdp_session(target_id=event.target_id, focus=True)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'🔄 Updated agent focus to tab target_id=...{event.target_id[-4:]}')
		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError('AgentFocusChangedEvent received with no target_id for newly focused tab')

		# Test that the browser is responsive by evaluating a simple expression
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.agent_focus:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔄 Testing tab responsiveness...')
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to test_result.
				# JP: test_result に値を代入する。
				test_result = await asyncio.wait_for(
					self.agent_focus.cdp_client.send.Runtime.evaluate(
						params={'expression': '1 + 1', 'returnByValue': True}, session_id=self.agent_focus.session_id
					),
					timeout=2.0,
				)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if test_result.get('result', {}).get('value') == 2:
					# self.logger.debug('🔄 ✅ Browser is responsive after focus change')
					# EN: Keep a placeholder statement.
					# JP: プレースホルダー文を維持する。
					pass
				else:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise Exception('❌ Failed to execute test JS expression with Page.evaluate')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(
					f'🔄 ❌ Target {self.agent_focus.target_id} seems closed/crashed, switching to fallback page {all_targets[0]}: {type(e).__name__}: {e}'
				)
				# EN: Assign value to all_pages.
				# JP: all_pages に値を代入する。
				all_pages = await self._cdp_get_all_pages()
				# EN: Assign value to last_target_id.
				# JP: last_target_id に値を代入する。
				last_target_id = all_pages[-1]['targetId'] if all_pages else None
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.agent_focus = await self.get_or_create_cdp_session(target_id=last_target_id, focus=True)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise

		# self.logger.debug('🔄 AgentFocusChangedEvent handler completed successfully')

	# EN: Define async function `on_FileDownloadedEvent`.
	# JP: 非同期関数 `on_FileDownloadedEvent` を定義する。
	async def on_FileDownloadedEvent(self, event: FileDownloadedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Track downloaded files during this session."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'FileDownloadedEvent received: {event.file_name} at {event.path}')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.path and event.path not in self._downloaded_files:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._downloaded_files.append(event.path)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'📁 Tracked download: {event.file_name} ({len(self._downloaded_files)} total downloads in session)')
		else:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not event.path:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'FileDownloadedEvent has no path: {event}')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'File already tracked: {event.path}')

	# EN: Define async function `on_BrowserStopEvent`.
	# JP: 非同期関数 `on_BrowserStopEvent` を定義する。
	async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle browser stop request."""

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Check if we should keep the browser alive
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_profile.keep_alive and not event.force:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.event_bus.dispatch(BrowserStoppedEvent(reason='Kept alive due to keep_alive=True'))
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Clear CDP session cache before stopping
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.reset()

			# Reset state
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.is_local:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.browser_profile.cdp_url = None

			# Notify stop and wait for all handlers to complete
			# LocalBrowserWatchdog listens for BrowserStopEvent and dispatches BrowserKillEvent
			# EN: Assign value to stop_event.
			# JP: stop_event に値を代入する。
			stop_event = self.event_bus.dispatch(BrowserStoppedEvent(reason='Stopped by request'))
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await stop_event

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='BrowserStopEventError',
					message=f'Failed to stop browser: {type(e).__name__} {e}',
					details={'cdp_url': self.cdp_url, 'is_local': self.is_local},
				)
			)

	# EN: Define function `cdp_client`.
	# JP: 関数 `cdp_client` を定義する。
	@property
	def cdp_client(self) -> CDPClient:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the cached root CDP cdp_session.cdp_client. The client is created and started in self.connect()."""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self._cdp_client_root is not None, 'CDP client not initialized - browser may not be connected yet'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._cdp_client_root

	# EN: Define async function `get_or_create_cdp_session`.
	# JP: 非同期関数 `get_or_create_cdp_session` を定義する。
	async def get_or_create_cdp_session(
		self, target_id: TargetID | None = None, focus: bool = True, new_socket: bool | None = None
	) -> CDPSession:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get or create a CDP session for a target.

		Args:
		        target_id: Target ID to get session for. If None, uses current agent focus.
		        focus: If True, switches agent focus to this target. If False, just returns session without changing focus.
		        new_socket: If True, create a dedicated WebSocket connection. If None (default), creates new socket for new targets only.

		Returns:
		        CDPSession for the specified target.
		"""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.cdp_url is not None, 'CDP URL not set - browser may not be configured or launched yet'
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self._cdp_client_root is not None, 'Root CDP client not initialized - browser may not be connected yet'
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.agent_focus is not None, 'CDP session not initialized - browser may not be connected yet'

		# If no target_id specified, use the current target_id
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_id is None:
			# EN: Assign value to target_id.
			# JP: target_id に値を代入する。
			target_id = self.agent_focus.target_id

		# Check if we already have a session for this target in the pool
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_id in self._cdp_session_pool:
			# EN: Assign value to session.
			# JP: session に値を代入する。
			session = self._cdp_session_pool[target_id]
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if focus and self.agent_focus.target_id != target_id:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'[get_or_create_cdp_session] Switching agent focus from {self.agent_focus.target_id} to {target_id}'
				)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.agent_focus = session
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if focus:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.cdp_client.send.Target.activateTarget(params={'targetId': session.target_id})
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.cdp_client.send.Runtime.runIfWaitingForDebugger(session_id=session.session_id)
			# else:
			# self.logger.debug(f'[get_or_create_cdp_session] Reusing existing session for {target_id} (focus={focus})')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return session

		# If it's the current focus target, return that session
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.agent_focus.target_id == target_id:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._cdp_session_pool[target_id] = self.agent_focus
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.agent_focus

		# Create new session for this target
		# Default now configurable: shared sockets by default to avoid hub limits; can opt-in to dedicated via flag/env.
		# EN: Assign value to should_use_new_socket.
		# JP: should_use_new_socket に値を代入する。
		should_use_new_socket = _CDP_DEDICATED_SOCKET_DEFAULT if new_socket is None else new_socket
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(
			f'[get_or_create_cdp_session] Creating new CDP session for target {target_id} (new_socket={should_use_new_socket})'
		)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to session.
			# JP: session に値を代入する。
			session = await CDPSession.for_target(
				self._cdp_client_root,
				target_id,
				new_socket=should_use_new_socket,
				cdp_url=self.cdp_url if should_use_new_socket else None,
			)
		except Exception as e:
			# If dedicated socket creation fails because the DevTools hub is throttling connections, retry with shared.
			# EN: Assign value to is_ws_limit.
			# JP: is_ws_limit に値を代入する。
			is_ws_limit = (
				isinstance(e, InvalidStatus) and getattr(e, 'status_code', None) in (400, 429)
			) or 'Too many websocket connections' in str(e)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if should_use_new_socket and _CDP_NEW_SOCKET_FALLBACK and is_ws_limit:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(
					'[get_or_create_cdp_session] Dedicated CDP socket rejected (%s). Retrying with shared socket to avoid exhaustion.',
					e,
				)
				# EN: Assign value to session.
				# JP: session に値を代入する。
				session = await CDPSession.for_target(self._cdp_client_root, target_id, new_socket=False)
			else:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cdp_session_pool[target_id] = session
		# log length of _cdp_session_pool
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[get_or_create_cdp_session] new _cdp_session_pool length: {len(self._cdp_session_pool)}')

		# Only change agent focus if requested
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if focus:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'[get_or_create_cdp_session] Switching agent focus from {self.agent_focus.target_id} to {target_id}'
			)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.agent_focus = session
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await session.cdp_client.send.Target.activateTarget(params={'targetId': session.target_id})
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await session.cdp_client.send.Runtime.runIfWaitingForDebugger(session_id=session.session_id)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'[get_or_create_cdp_session] Created session for {target_id} without changing focus (still on {self.agent_focus.target_id})'
			)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return session

	# EN: Define function `current_target_id`.
	# JP: 関数 `current_target_id` を定義する。
	@property
	def current_target_id(self) -> str | None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.agent_focus.target_id if self.agent_focus else None

	# EN: Define function `current_session_id`.
	# JP: 関数 `current_session_id` を定義する。
	@property
	def current_session_id(self) -> str | None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.agent_focus.session_id if self.agent_focus else None

	# ========== Helper Methods ==========
	# EN: Define async function `get_browser_state_summary`.
	# JP: 非同期関数 `get_browser_state_summary` を定義する。
	@observe_debug(ignore_input=True, ignore_output=True, name='get_browser_state_summary')
	async def get_browser_state_summary(
		self,
		cache_clickable_elements_hashes: bool = True,
		include_screenshot: bool = True,
		cached: bool = False,
		include_recent_events: bool = False,
	) -> BrowserStateSummary:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if cached and self._cached_browser_state_summary is not None and self._cached_browser_state_summary.dom_state:
			# Don't use cached state if it has 0 interactive elements
			# EN: Assign value to selector_map.
			# JP: selector_map に値を代入する。
			selector_map = self._cached_browser_state_summary.dom_state.selector_map

			# Don't use cached state if we need a screenshot but the cached state doesn't have one
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if include_screenshot and not self._cached_browser_state_summary.screenshot:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('⚠️ Cached browser state has no screenshot, fetching fresh state with screenshot')
				# Fall through to fetch fresh state with screenshot
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif selector_map and len(selector_map) > 0:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🔄 Using pre-cached browser state summary for open tab')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return self._cached_browser_state_summary
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('⚠️ Cached browser state has 0 interactive elements, fetching fresh state')
				# Fall through to fetch fresh state

		# EN: Assign annotated value to last_error.
		# JP: last_error に型付きの値を代入する。
		last_error: Exception | None = None
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for attempt in range(2):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await ensure_browser_state_handler_registered(self)
			# Dispatch the event and wait for result
			# EN: Assign annotated value to event.
			# JP: event に型付きの値を代入する。
			event: BrowserStateRequestEvent = cast(
				BrowserStateRequestEvent,
				self.event_bus.dispatch(
					BrowserStateRequestEvent(
						include_dom=True,
						include_screenshot=include_screenshot,
						cache_clickable_elements_hashes=cache_clickable_elements_hashes,
						include_recent_events=include_recent_events,
					)
				),
			)

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# The handler returns the BrowserStateSummary directly
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await event.event_result(raise_if_none=True, raise_if_any=True)
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert result is not None and result.dom_state is not None
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return result
			except ValueError as exc:
				# EN: Assign value to handlers.
				# JP: handlers に値を代入する。
				handlers = self.event_bus.handlers.get(BrowserStateRequestEvent.__name__, [])
				# EN: Assign value to handler_count.
				# JP: handler_count に値を代入する。
				handler_count = len(handlers)
				# EN: Assign value to message.
				# JP: message に値を代入する。
				message = str(exc)
				# EN: Assign value to should_force_reattach.
				# JP: should_force_reattach に値を代入する。
				should_force_reattach = 'Expected at least one handler' in message and attempt == 0

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if should_force_reattach:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(
						'BrowserStateRequestEvent handler ValueError detected '
						'(handler_count=%s): %s; re-attaching watchdogs and retrying once.',
						handler_count,
						message,
					)

					# Force reattachment in case the internal flag is stale
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if hasattr(self, '_watchdogs_attached'):
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						self._watchdogs_attached = False  # type: ignore[attr-defined]

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.attach_all_watchdogs()
					# EN: Assign value to last_error.
					# JP: last_error に値を代入する。
					last_error = exc
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if last_error:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise last_error

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise RuntimeError('Failed to obtain browser state summary after retrying without handlers')

	# EN: Define async function `attach_all_watchdogs`.
	# JP: 非同期関数 `attach_all_watchdogs` を定義する。
	async def attach_all_watchdogs(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize and attach all watchdogs with explicit handler registration."""
		# Prevent duplicate watchdog attachment
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, '_watchdogs_attached') and self._watchdogs_attached:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('Watchdogs already attached, skipping duplicate attachment')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.aboutblank_watchdog import AboutBlankWatchdog

		# from browser_use.browser.crash_watchdog import CrashWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.default_action_watchdog import DefaultActionWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.dom_watchdog import DOMWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.downloads_watchdog import DownloadsWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.local_browser_watchdog import LocalBrowserWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.permissions_watchdog import PermissionsWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.popups_watchdog import PopupsWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.recording_watchdog import RecordingWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.screenshot_watchdog import ScreenshotWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.security_watchdog import SecurityWatchdog
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.watchdogs.storage_state_watchdog import StorageStateWatchdog

		# Initialize CrashWatchdog
		# CrashWatchdog.model_rebuild()
		# self._crash_watchdog = CrashWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(BrowserConnectedEvent, self._crash_watchdog.on_BrowserConnectedEvent)
		# self.event_bus.on(BrowserStoppedEvent, self._crash_watchdog.on_BrowserStoppedEvent)
		# self._crash_watchdog.attach_to_session()

		# Initialize DownloadsWatchdog
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		DownloadsWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._downloads_watchdog = DownloadsWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(BrowserLaunchEvent, self._downloads_watchdog.on_BrowserLaunchEvent)
		# self.event_bus.on(TabCreatedEvent, self._downloads_watchdog.on_TabCreatedEvent)
		# self.event_bus.on(TabClosedEvent, self._downloads_watchdog.on_TabClosedEvent)
		# self.event_bus.on(BrowserStoppedEvent, self._downloads_watchdog.on_BrowserStoppedEvent)
		# self.event_bus.on(NavigationCompleteEvent, self._downloads_watchdog.on_NavigationCompleteEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._downloads_watchdog.attach_to_session()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_profile.auto_download_pdfs:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('📄 PDF auto-download enabled for this session')

		# Initialize StorageStateWatchdog conditionally
		# Enable when user provides either storage_state or user_data_dir (indicating they want persistence)
		# EN: Assign value to should_enable_storage_state.
		# JP: should_enable_storage_state に値を代入する。
		should_enable_storage_state = (
			self.browser_profile.storage_state is not None or self.browser_profile.user_data_dir is not None
		)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if should_enable_storage_state:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			StorageStateWatchdog.model_rebuild()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._storage_state_watchdog = StorageStateWatchdog(
				event_bus=self.event_bus,
				browser_session=self,
				# More conservative defaults when auto-enabled
				auto_save_interval=60.0,  # 1 minute instead of 30 seconds
				save_on_change=False,  # Only save on shutdown by default
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._storage_state_watchdog.attach_to_session()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'🍪 StorageStateWatchdog enabled (storage_state: {bool(self.browser_profile.storage_state)}, user_data_dir: {bool(self.browser_profile.user_data_dir)})'
			)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🍪 StorageStateWatchdog disabled (no storage_state or user_data_dir configured)')

		# Initialize LocalBrowserWatchdog
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		LocalBrowserWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._local_browser_watchdog = LocalBrowserWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(BrowserLaunchEvent, self._local_browser_watchdog.on_BrowserLaunchEvent)
		# self.event_bus.on(BrowserKillEvent, self._local_browser_watchdog.on_BrowserKillEvent)
		# self.event_bus.on(BrowserStopEvent, self._local_browser_watchdog.on_BrowserStopEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._local_browser_watchdog.attach_to_session()

		# Initialize SecurityWatchdog (hooks NavigationWatchdog and implements allowed_domains restriction)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		SecurityWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._security_watchdog = SecurityWatchdog(event_bus=self.event_bus, browser_session=self)
		# Core navigation is now handled in BrowserSession directly
		# SecurityWatchdog only handles security policy enforcement
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._security_watchdog.attach_to_session()

		# Initialize AboutBlankWatchdog (handles about:blank pages and DVD loading animation on first load)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		AboutBlankWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._aboutblank_watchdog = AboutBlankWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(BrowserStopEvent, self._aboutblank_watchdog.on_BrowserStopEvent)
		# self.event_bus.on(BrowserStoppedEvent, self._aboutblank_watchdog.on_BrowserStoppedEvent)
		# self.event_bus.on(TabCreatedEvent, self._aboutblank_watchdog.on_TabCreatedEvent)
		# self.event_bus.on(TabClosedEvent, self._aboutblank_watchdog.on_TabClosedEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._aboutblank_watchdog.attach_to_session()

		# Initialize PopupsWatchdog (handles accepting and dismissing JS dialogs, alerts, confirm, onbeforeunload, etc.)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		PopupsWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._popups_watchdog = PopupsWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(TabCreatedEvent, self._popups_watchdog.on_TabCreatedEvent)
		# self.event_bus.on(DialogCloseEvent, self._popups_watchdog.on_DialogCloseEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._popups_watchdog.attach_to_session()

		# Initialize PermissionsWatchdog (handles granting and revoking browser permissions like clipboard, microphone, camera, etc.)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		PermissionsWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._permissions_watchdog = PermissionsWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(BrowserConnectedEvent, self._permissions_watchdog.on_BrowserConnectedEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._permissions_watchdog.attach_to_session()

		# Initialize DefaultActionWatchdog (handles all default actions like click, type, scroll, go back, go forward, refresh, wait, send keys, upload file, scroll to text, etc.)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		DefaultActionWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._default_action_watchdog = DefaultActionWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(ClickElementEvent, self._default_action_watchdog.on_ClickElementEvent)
		# self.event_bus.on(TypeTextEvent, self._default_action_watchdog.on_TypeTextEvent)
		# self.event_bus.on(ScrollEvent, self._default_action_watchdog.on_ScrollEvent)
		# self.event_bus.on(GoBackEvent, self._default_action_watchdog.on_GoBackEvent)
		# self.event_bus.on(GoForwardEvent, self._default_action_watchdog.on_GoForwardEvent)
		# self.event_bus.on(RefreshEvent, self._default_action_watchdog.on_RefreshEvent)
		# self.event_bus.on(WaitEvent, self._default_action_watchdog.on_WaitEvent)
		# self.event_bus.on(SendKeysEvent, self._default_action_watchdog.on_SendKeysEvent)
		# self.event_bus.on(UploadFileEvent, self._default_action_watchdog.on_UploadFileEvent)
		# self.event_bus.on(ScrollToTextEvent, self._default_action_watchdog.on_ScrollToTextEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._default_action_watchdog.attach_to_session()

		# Initialize ScreenshotWatchdog (handles taking screenshots of the browser)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		ScreenshotWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._screenshot_watchdog = ScreenshotWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(BrowserStartEvent, self._screenshot_watchdog.on_BrowserStartEvent)
		# self.event_bus.on(BrowserStoppedEvent, self._screenshot_watchdog.on_BrowserStoppedEvent)
		# self.event_bus.on(ScreenshotEvent, self._screenshot_watchdog.on_ScreenshotEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._screenshot_watchdog.attach_to_session()

		# Initialize DOMWatchdog (handles building the DOM tree and detecting interactive elements, depends on ScreenshotWatchdog)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		DOMWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._dom_watchdog = DOMWatchdog(event_bus=self.event_bus, browser_session=self)
		# self.event_bus.on(TabCreatedEvent, self._dom_watchdog.on_TabCreatedEvent)
		# self.event_bus.on(BrowserStateRequestEvent, self._dom_watchdog.on_BrowserStateRequestEvent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._dom_watchdog.attach_to_session()

		# Initialize RecordingWatchdog (handles video recording)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		RecordingWatchdog.model_rebuild()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._recording_watchdog = RecordingWatchdog(event_bus=self.event_bus, browser_session=self)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._recording_watchdog.attach_to_session()

		# Mark watchdogs as attached to prevent duplicate attachment
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._watchdogs_attached = True

	# EN: Define async function `connect`.
	# JP: 非同期関数 `connect` を定義する。
	async def connect(self, cdp_url: str | None = None) -> Self:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Connect to a remote chromium-based browser via CDP using cdp-use.

		This MUST succeed or the browser is unusable. Fails hard on any error.
		"""

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.browser_profile.cdp_url = cdp_url or self.cdp_url
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.cdp_url:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError('Cannot setup CDP connection without CDP URL')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.cdp_url.startswith('ws'):
			# If it's an HTTP URL, fetch the WebSocket URL from /json/version endpoint
			# EN: Assign value to url.
			# JP: url に値を代入する。
			url = self.cdp_url.rstrip('/')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not url.endswith('/json/version'):
				# EN: Assign value to url.
				# JP: url に値を代入する。
				url = url + '/json/version'

			# Run a tiny HTTP client to query for the WebSocket URL from the /json/version endpoint
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with httpx.AsyncClient() as client:
				# EN: Assign value to headers.
				# JP: headers に値を代入する。
				headers = self.browser_profile.headers or {}
				# EN: Assign value to version_info.
				# JP: version_info に値を代入する。
				version_info = await client.get(url, headers=headers)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.browser_profile.cdp_url = version_info.json()['webSocketDebuggerUrl']

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.cdp_url is not None

		# EN: Assign value to browser_location.
		# JP: browser_location に値を代入する。
		browser_location = 'local browser' if self.is_local else 'remote browser'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🌎 Connecting to existing chromium-based browser via CDP: {self.cdp_url} -> ({browser_location})')

		# EN: Assign value to attempt.
		# JP: attempt に値を代入する。
		attempt = 0
		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while True:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			attempt += 1
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Import cdp-use client

				# Convert HTTP URL to WebSocket URL if needed

				# Create and store the CDP client for direct CDP communication
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._cdp_client_root = CDPClient(self.cdp_url)
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert self._cdp_client_root is not None
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._cdp_client_root.start()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._cdp_client_root.send.Target.setAutoAttach(
					params={'autoAttach': True, 'waitForDebuggerOnStart': False, 'flatten': True}
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('CDP client connected successfully')

				# Get browser targets to find available contexts/pages
				# EN: Assign value to targets.
				# JP: targets に値を代入する。
				targets = await self._cdp_client_root.send.Target.getTargets()

				# Find main browser pages (avoiding iframes, workers, extensions, etc.)
				# EN: Assign annotated value to page_targets.
				# JP: page_targets に型付きの値を代入する。
				page_targets: list[TargetInfo] = [
					t
					for t in targets['targetInfos']
					if self._is_valid_target(
						t, include_http=True, include_about=True, include_pages=True, include_iframes=False, include_workers=False
					)
				]

				# Check for chrome://newtab pages and immediately redirect them
				# to the default start page to avoid JS issues from CDP on chrome://* urls
				# Collect all targets that need redirection
				# EN: Assign value to redirected_targets.
				# JP: redirected_targets に値を代入する。
				redirected_targets = []
				# EN: Assign value to redirect_sessions.
				# JP: redirect_sessions に値を代入する。
				redirect_sessions = {}  # Store sessions created for redirection to potentially reuse
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for target in page_targets:
					# EN: Assign value to target_url.
					# JP: target_url に値を代入する。
					target_url = target.get('url', '')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if is_new_tab_page(target_url) and not is_default_new_tab_url(target_url):
						# Redirect chrome://newtab to the default start page to avoid JS issues preventing driving chrome://newtab
						# EN: Assign value to target_id.
						# JP: target_id に値を代入する。
						target_id = target['targetId']
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'🔄 Redirecting {target_url} to {DEFAULT_NEW_TAB_URL} for target {target_id}')
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# Create a CDP session for redirection (minimal domains to avoid duplicate event handlers)
							# Only enable Page domain for navigation, avoid duplicate event handlers
							# EN: Assign value to redirect_session.
							# JP: redirect_session に値を代入する。
							redirect_session = await CDPSession.for_target(self._cdp_client_root, target_id, domains=['Page'])
							# Navigate to about:blank
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await redirect_session.cdp_client.send.Page.navigate(
								params={'url': DEFAULT_NEW_TAB_URL}, session_id=redirect_session.session_id
							)
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							redirected_targets.append(target_id)
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							redirect_sessions[target_id] = redirect_session  # Store for potential reuse
							# Update the target's URL in our list for later use
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							target['url'] = DEFAULT_NEW_TAB_URL
							# Small delay to ensure navigation completes
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await asyncio.sleep(0.05)
						except Exception as e:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.warning(f'Failed to redirect {target_url} to {DEFAULT_NEW_TAB_URL}: {e}')

				# Log summary of redirections
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if redirected_targets:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Redirected {len(redirected_targets)} chrome://newtab pages to {DEFAULT_NEW_TAB_URL}')

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not page_targets:
					# No pages found, create a new one
					# EN: Assign value to new_target.
					# JP: new_target に値を代入する。
					new_target = await self._cdp_client_root.send.Target.createTarget(params={'url': DEFAULT_NEW_TAB_URL})
					# EN: Assign value to target_id.
					# JP: target_id に値を代入する。
					target_id = new_target['targetId']
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'📄 Created new blank page with target ID: {target_id}')
				else:
					# Use the first available page
					# EN: Assign value to target_id.
					# JP: target_id に値を代入する。
					target_id = [page for page in page_targets if page.get('type') == 'page'][0]['targetId']
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'📄 Using existing page with target ID: {target_id}')

				# Store the current page target ID and add to pool
				# Reuse redirect session if available, otherwise create new one
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if target_id in redirect_sessions:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Reusing redirect session for target {target_id}')
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.agent_focus = redirect_sessions[target_id]
				else:
					# For the initial connection, we'll use the shared root WebSocket
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.agent_focus = await CDPSession.for_target(self._cdp_client_root, target_id, new_socket=False)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.agent_focus:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._cdp_session_pool[target_id] = self.agent_focus

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._apply_initial_window_state(target_id)

				# (Re)start storage monitoring now that CDP is connected.
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if getattr(self, '_storage_state_watchdog', None) is not None:
					# EN: Execute logic with managed resources.
					# JP: リソース管理付きで処理を実行する。
					with suppress(Exception):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self._storage_state_watchdog._start_monitoring()

				# Enable proxy authentication handling if configured
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._setup_proxy_auth()

				# Verify the session is working
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self.agent_focus:
						# EN: Validate a required condition.
						# JP: 必須条件を検証する。
						assert self.agent_focus.title != 'Unknown title'
					else:
						# EN: Raise an exception.
						# JP: 例外を送出する。
						raise RuntimeError('Failed to create CDP session')
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'Failed to create CDP session: {e}')
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise

				# Dispatch TabCreatedEvent for all initial tabs (so watchdogs can initialize)
				# This replaces the duplicated logic from navigation_watchdog's _initialize_agent_focus
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for idx, target in enumerate(page_targets):
					# EN: Assign value to target_url.
					# JP: target_url に値を代入する。
					target_url = target.get('url', '')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Dispatching TabCreatedEvent for initial tab {idx}: {target_url}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.event_bus.dispatch(TabCreatedEvent(url=target_url, target_id=target['targetId']))

				# Dispatch initial focus event
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if page_targets:
					# EN: Assign value to initial_url.
					# JP: initial_url に値を代入する。
					initial_url = page_targets[0].get('url', '')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.event_bus.dispatch(AgentFocusChangedEvent(target_id=page_targets[0]['targetId'], url=initial_url))
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Initial agent focus set to tab 0: {initial_url}')

				# Successful connection, break the retry loop
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return self

			except asyncio.CancelledError:
				# Allow task cancellation to propagate immediately.
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise
			except Exception as e:
				# Keep retrying instead of failing hard; allow very long-lived sessions.
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'⚠️ Failed to setup CDP connection (attempt {attempt}): {e}')
				# Clean up any partial state
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with suppress(Exception):
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self._cdp_client_root:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self._cdp_client_root.stop()
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._cdp_client_root = None
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.agent_focus = None

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if _CDP_CONNECT_MAX_RETRIES is not None and attempt >= _CDP_CONNECT_MAX_RETRIES:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error('❌ Browser cannot continue without CDP connection after %s attempts', attempt)
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise RuntimeError(f'Failed to establish CDP connection to browser: {e}') from e

				# EN: Assign value to delay.
				# JP: delay に値を代入する。
				delay = max(_CDP_CONNECT_RETRY_DELAY * min(attempt, 10), 0.1)
				# If the hub is rate-limiting (HTTP 400 / too many websockets), back off harder.
				# EN: Assign value to error_text.
				# JP: error_text に値を代入する。
				error_text = str(e).lower()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'too many websocket connections' in error_text or 'http 400' in error_text:
					# EN: Assign value to delay.
					# JP: delay に値を代入する。
					delay = max(delay, 60.0)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info('🔁 Retrying CDP connection in %.1fs...', delay)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(delay)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define function `_should_apply_initial_window_state`.
	# JP: 関数 `_should_apply_initial_window_state` を定義する。
	def _should_apply_initial_window_state(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Determine whether fullscreen requests should run for this session."""

		# EN: Assign value to preference.
		# JP: preference に値を代入する。
		preference = getattr(self.browser_profile, 'request_initial_window_state', None)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if preference is not None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return bool(preference)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return bool(self.cdp_url and not self.is_local)

	# EN: Define async function `_get_window_state_for_id`.
	# JP: 非同期関数 `_get_window_state_for_id` を定義する。
	async def _get_window_state_for_id(self, window_id: int) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return the current window state for the given window identifier."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._cdp_client_root:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to bounds.
			# JP: bounds に値を代入する。
			bounds = await self._cdp_client_root.send.Browser.getWindowBounds(
				params={'windowId': window_id},
			)
		except Exception as bounds_error:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				'Unable to verify fullscreen window state: %s: %s',
				type(bounds_error).__name__,
				bounds_error,
			)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to bounds_data.
		# JP: bounds_data に値を代入する。
		bounds_data = bounds.get('bounds') or {}
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return bounds_data.get('windowState') or bounds_data.get('window_state') or bounds_data.get('state')

	# EN: Define async function `_set_window_state_for_target`.
	# JP: 非同期関数 `_set_window_state_for_target` を定義する。
	async def _set_window_state_for_target(
		self,
		target_id: TargetID,
		desired_state: Literal['fullscreen', 'maximized'],
	) -> tuple[int | None, str | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Request a specific window state for the window hosting the given target."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._cdp_client_root:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None, None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to window_info.
			# JP: window_info に値を代入する。
			window_info = await self._cdp_client_root.send.Browser.getWindowForTarget(params={'targetId': target_id})
		except Exception as error:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				'Unable to resolve window for fullscreen request: %s: %s',
				type(error).__name__,
				error,
			)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None, None

		# EN: Assign value to window_id.
		# JP: window_id に値を代入する。
		window_id = window_info.get('windowId') or window_info.get('window_id')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if window_id is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None, None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._cdp_client_root.send.Browser.setWindowBounds(
				params={'windowId': window_id, 'bounds': {'windowState': desired_state}},
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('Requested %s window state via CDP', desired_state)
		except Exception as error:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				'Unable to request %s window state via bounds: %s: %s',
				desired_state,
				type(error).__name__,
				error,
			)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return window_id, None

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await asyncio.sleep(0.1)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return window_id, await self._get_window_state_for_id(window_id)

	# EN: Define async function `_apply_initial_window_state`.
	# JP: 非同期関数 `_apply_initial_window_state` を定義する。
	async def _apply_initial_window_state(self, target_id: TargetID | None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Request fullscreen bounds for the first window when running headful."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._should_apply_initial_window_state():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_profile.headless:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._fullscreen_requested:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not target_id or not self._cdp_client_root:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to successfully_requested.
		# JP: successfully_requested に値を代入する。
		successfully_requested = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._fullscreen_requested = True

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Give the newly created Chrome window a moment to finish rendering
			# before we try to manipulate its bounds. This ensures the fullscreen
			# (maximize) request happens roughly one second after the window
			# becomes visible, matching the desired behaviour of clicking the
			# fullscreen toolbar button after the browser appears.
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(1.0)

			# EN: Assign annotated value to window_id.
			# JP: window_id に型付きの値を代入する。
			window_id: int | None = None
			# EN: Assign annotated value to fullscreen_state.
			# JP: fullscreen_state に型付きの値を代入する。
			fullscreen_state: str | None = None

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for desired_state in ('fullscreen', 'maximized'):
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for _ in range(3):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					window_id, fullscreen_state = await self._set_window_state_for_target(target_id, desired_state)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if window_id is None:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if fullscreen_state == desired_state:
						# EN: Exit the current loop.
						# JP: 現在のループを終了する。
						break
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(0.2)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if fullscreen_state == desired_state:
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if window_id is None:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if fullscreen_state not in {'fullscreen', 'maximized'}:
				# EN: Assign value to screen.
				# JP: screen に値を代入する。
				screen = self.browser_profile.screen
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if screen is None:
					# EN: Assign value to screen.
					# JP: screen に値を代入する。
					screen = getattr(self.browser_profile, '_detected_screen', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if screen is None:
					# EN: Assign value to screen.
					# JP: screen に値を代入する。
					screen = self.browser_profile.window_size
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if screen is None:
					# EN: Assign value to screen.
					# JP: screen に値を代入する。
					screen = self.browser_profile.viewport
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if screen is None:
					# EN: Assign value to screen.
					# JP: screen に値を代入する。
					screen = ViewportSize(width=1920, height=1080)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if screen:
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self._cdp_client_root.send.Browser.setWindowBounds(
							params={
								'windowId': window_id,
								'bounds': {
									'windowState': 'normal',
									'left': 0,
									'top': 0,
									'width': screen.width,
									'height': screen.height,
								},
							},
						)
						# EN: Assign value to fullscreen_state.
						# JP: fullscreen_state に値を代入する。
						fullscreen_state = await self._get_window_state_for_id(window_id)
					except Exception as size_error:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(
							'Unable to set explicit fullscreen bounds: %s: %s', type(size_error).__name__, size_error
						)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if fullscreen_state not in {'fullscreen', 'maximized'}:
				# EN: Assign value to screen.
				# JP: screen に値を代入する。
				screen = self.browser_profile.screen
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if screen:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					screen.height = max(screen.height, 720)  # type: ignore[misc]
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					screen.width = max(screen.width, 1280)  # type: ignore[misc]
				# EN: Assign value to session.
				# JP: session に値を代入する。
				session = self.agent_focus
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if session:
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.sleep(0.25)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self._cdp_client_root.send.Browser.bringToFront(params={'windowId': window_id})
					except Exception as bring_to_front_error:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(
							'Unable to bring window to front before fullscreen key events: %s: %s',
							type(bring_to_front_error).__name__,
							bring_to_front_error,
						)
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await session.cdp_client.send.Page.bringToFront(session_id=session.session_id)
					except Exception as page_front_error:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(
							'Unable to request Page.bringToFront before fullscreen key events: %s: %s',
							type(page_front_error).__name__,
							page_front_error,
						)
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to key_payload.
						# JP: key_payload に値を代入する。
						key_payload = {'key': 'F11', 'code': 'F11', 'windowsVirtualKeyCode': 122, 'nativeVirtualKeyCode': 122}
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for event_type in ('rawKeyDown', 'keyDown'):
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await session.cdp_client.send.Input.dispatchKeyEvent(
								params={'type': event_type, **key_payload}, session_id=session.session_id
							)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await session.cdp_client.send.Input.dispatchKeyEvent(
							params={'type': 'keyUp', **key_payload}, session_id=session.session_id
						)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug('Dispatched F11 key events to request fullscreen')
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.sleep(0.3)
						# EN: Assign value to fullscreen_state.
						# JP: fullscreen_state に値を代入する。
						fullscreen_state = await self._get_window_state_for_id(window_id)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if fullscreen_state not in {'fullscreen', 'maximized'}:
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							_, fullscreen_state = await self._set_window_state_for_target(target_id, 'maximized')
					except Exception as key_error:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug('Unable to dispatch fullscreen key events: %s: %s', type(key_error).__name__, key_error)

			# EN: Assign value to successfully_requested.
			# JP: successfully_requested に値を代入する。
			successfully_requested = fullscreen_state in {'fullscreen', 'maximized'}
		finally:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not successfully_requested:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._fullscreen_requested = False

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._initial_window_state_applied = successfully_requested

	# EN: Define async function `_setup_proxy_auth`.
	# JP: 非同期関数 `_setup_proxy_auth` を定義する。
	async def _setup_proxy_auth(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Enable CDP Fetch auth handling for authenticated proxy, if credentials provided.

		Handles HTTP proxy authentication challenges (Basic/Proxy) by providing
		configured credentials from BrowserProfile.
		"""

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self._cdp_client_root

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to proxy_cfg.
			# JP: proxy_cfg に値を代入する。
			proxy_cfg = self.browser_profile.proxy
			# EN: Assign value to username.
			# JP: username に値を代入する。
			username = proxy_cfg.username if proxy_cfg else None
			# EN: Assign value to password.
			# JP: password に値を代入する。
			password = proxy_cfg.password if proxy_cfg else None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not username or not password:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('Proxy credentials not provided; skipping proxy auth setup')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Enable Fetch domain with auth handling (do not pause all requests)
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._cdp_client_root.send.Fetch.enable(params={'handleAuthRequests': True})
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('Fetch.enable(handleAuthRequests=True) enabled on root client')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Fetch.enable on root failed: {type(e).__name__}: {e}')

			# Also enable on the focused session if available to ensure events are delivered
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.agent_focus:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.agent_focus.cdp_client.send.Fetch.enable(
						params={'handleAuthRequests': True},
						session_id=self.agent_focus.session_id,
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('Fetch.enable(handleAuthRequests=True) enabled on focused session')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Fetch.enable on focused session failed: {type(e).__name__}: {e}')

			# EN: Define function `_on_auth_required`.
			# JP: 関数 `_on_auth_required` を定義する。
			def _on_auth_required(event: AuthRequiredEvent, session_id: SessionID | None = None):
				# event keys may be snake_case or camelCase depending on generator; handle both
				# EN: Assign value to request_id.
				# JP: request_id に値を代入する。
				request_id = event.get('requestId') or event.get('request_id')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not request_id:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return

				# EN: Assign value to challenge.
				# JP: challenge に値を代入する。
				challenge = event.get('authChallenge') or event.get('auth_challenge') or {}
				# EN: Assign value to source.
				# JP: source に値を代入する。
				source = (challenge.get('source') or '').lower()
				# Only respond to proxy challenges
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if source == 'proxy' and request_id:

					# EN: Define async function `_respond`.
					# JP: 非同期関数 `_respond` を定義する。
					async def _respond():
						# EN: Validate a required condition.
						# JP: 必須条件を検証する。
						assert self._cdp_client_root
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await self._cdp_client_root.send.Fetch.continueWithAuth(
								params={
									'requestId': request_id,
									'authChallengeResponse': {
										'response': 'ProvideCredentials',
										'username': username,
										'password': password,
									},
								},
								session_id=session_id,
							)
						except Exception as e:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug(f'Proxy auth respond failed: {type(e).__name__}: {e}')

					# schedule
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					asyncio.create_task(_respond())
				else:
					# Default behaviour for non-proxy challenges: let browser handle
					# EN: Define async function `_default`.
					# JP: 非同期関数 `_default` を定義する。
					async def _default():
						# EN: Validate a required condition.
						# JP: 必須条件を検証する。
						assert self._cdp_client_root
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await self._cdp_client_root.send.Fetch.continueWithAuth(
								params={'requestId': request_id, 'authChallengeResponse': {'response': 'Default'}},
								session_id=session_id,
							)
						except Exception as e:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug(f'Default auth respond failed: {type(e).__name__}: {e}')

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if request_id:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						asyncio.create_task(_default())

			# EN: Define function `_on_request_paused`.
			# JP: 関数 `_on_request_paused` を定義する。
			def _on_request_paused(event: RequestPausedEvent, session_id: SessionID | None = None):
				# Continue all paused requests to avoid stalling the network
				# EN: Assign value to request_id.
				# JP: request_id に値を代入する。
				request_id = event.get('requestId') or event.get('request_id')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not request_id:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return

				# EN: Define async function `_continue`.
				# JP: 非同期関数 `_continue` を定義する。
				async def _continue():
					# EN: Validate a required condition.
					# JP: 必須条件を検証する。
					assert self._cdp_client_root
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self._cdp_client_root.send.Fetch.continueRequest(
							params={'requestId': request_id},
							session_id=session_id,
						)
					except Exception:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				asyncio.create_task(_continue())

			# Register event handler on root client
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._cdp_client_root.register.Fetch.authRequired(_on_auth_required)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._cdp_client_root.register.Fetch.requestPaused(_on_request_paused)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.agent_focus:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.agent_focus.cdp_client.register.Fetch.authRequired(_on_auth_required)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.agent_focus.cdp_client.register.Fetch.requestPaused(_on_request_paused)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('Registered Fetch.authRequired handlers')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Failed to register authRequired handlers: {type(e).__name__}: {e}')

			# Auto-enable Fetch on every newly attached target to ensure auth callbacks fire
			# EN: Define function `_on_attached`.
			# JP: 関数 `_on_attached` を定義する。
			def _on_attached(event: AttachedToTargetEvent, session_id: SessionID | None = None):
				# EN: Assign value to sid.
				# JP: sid に値を代入する。
				sid = event.get('sessionId') or event.get('session_id') or session_id
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not sid:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return

				# EN: Define async function `_enable`.
				# JP: 非同期関数 `_enable` を定義する。
				async def _enable():
					# EN: Validate a required condition.
					# JP: 必須条件を検証する。
					assert self._cdp_client_root
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self._cdp_client_root.send.Fetch.enable(
							params={'handleAuthRequests': True},
							session_id=sid,
						)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'Fetch.enable(handleAuthRequests=True) enabled on attached session {sid}')
					except Exception as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'Fetch.enable on attached session failed: {type(e).__name__}: {e}')

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				asyncio.create_task(_enable())

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._cdp_client_root.register.Target.attachedToTarget(_on_attached)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('Registered Target.attachedToTarget handler for Fetch.enable')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Failed to register attachedToTarget handler: {type(e).__name__}: {e}')

			# Ensure Fetch is enabled for the current focused session, too
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.agent_focus:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.agent_focus.cdp_client.send.Fetch.enable(
						params={'handleAuthRequests': True, 'patterns': [{'urlPattern': '*'}]},
						session_id=self.agent_focus.session_id,
					)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Fetch.enable on focused session failed: {type(e).__name__}: {e}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Skipping proxy auth setup: {type(e).__name__}: {e}')

	# EN: Define async function `get_tabs`.
	# JP: 非同期関数 `get_tabs` を定義する。
	async def get_tabs(self) -> list[TabInfo]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get information about all open tabs using CDP Target.getTargetInfo for speed."""
		# EN: Assign value to tabs.
		# JP: tabs に値を代入する。
		tabs = []

		# Safety check - return empty list if browser not connected yet
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._cdp_client_root:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return tabs

		# Get all page targets using CDP
		# EN: Assign value to pages.
		# JP: pages に値を代入する。
		pages = await self._cdp_get_all_pages()

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, page_target in enumerate(pages):
			# EN: Assign value to target_id.
			# JP: target_id に値を代入する。
			target_id = page_target['targetId']
			# EN: Assign value to url.
			# JP: url に値を代入する。
			url = page_target['url']

			# Try to get the title directly from Target.getTargetInfo - much faster!
			# The initial getTargets() doesn't include title, but getTargetInfo does
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to target_info.
				# JP: target_info に値を代入する。
				target_info = await self.cdp_client.send.Target.getTargetInfo(params={'targetId': target_id})
				# The title is directly available in targetInfo
				# EN: Assign value to title.
				# JP: title に値を代入する。
				title = target_info.get('targetInfo', {}).get('title', '')

				# Skip JS execution for chrome:// pages and new tab pages
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if is_new_tab_page(url) or url.startswith('chrome://'):
					# Use URL as title for chrome pages, or mark new tabs as unusable
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if is_new_tab_page(url):
						# EN: Assign value to title.
						# JP: title に値を代入する。
						title = 'ignore this tab and do not use it'
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif not title:
						# For chrome:// pages without a title, use the URL itself
						# EN: Assign value to title.
						# JP: title に値を代入する。
						title = url

				# Special handling for PDF pages without titles
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if (not title or title == '') and (url.endswith('.pdf') or 'pdf' in url):
					# PDF pages might not have a title, use URL filename
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Import required modules.
						# JP: 必要なモジュールをインポートする。
						from urllib.parse import urlparse

						# EN: Assign value to filename.
						# JP: filename に値を代入する。
						filename = urlparse(url).path.split('/')[-1]
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if filename:
							# EN: Assign value to title.
							# JP: title に値を代入する。
							title = filename
					except Exception:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

			except Exception as e:
				# Fallback to basic title handling
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'⚠️ Failed to get target info for tab #{i}: {_log_pretty_url(url)} - {type(e).__name__}')

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if is_new_tab_page(url):
					# EN: Assign value to title.
					# JP: title に値を代入する。
					title = 'ignore this tab and do not use it'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif url.startswith('chrome://'):
					# EN: Assign value to title.
					# JP: title に値を代入する。
					title = url
				else:
					# EN: Assign value to title.
					# JP: title に値を代入する。
					title = ''

			# EN: Assign value to tab_info.
			# JP: tab_info に値を代入する。
			tab_info = TabInfo(
				target_id=target_id,
				url=url,
				title=title,
				parent_target_id=None,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			tabs.append(tab_info)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return tabs

	# ========== ID Lookup Methods ==========

	# EN: Define async function `get_current_target_info`.
	# JP: 非同期関数 `get_current_target_info` を定義する。
	async def get_current_target_info(self) -> TargetInfo | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get info about the current active target using CDP."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.agent_focus or not self.agent_focus.target_id:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to targets.
		# JP: targets に値を代入する。
		targets = await self.cdp_client.send.Target.getTargets()
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for target in targets.get('targetInfos', []):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target.get('targetId') == self.agent_focus.target_id:
				# Still return even if it's not a "valid" target since we're looking for a specific ID
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return target
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `get_current_page_url`.
	# JP: 非同期関数 `get_current_page_url` を定義する。
	async def get_current_page_url(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the URL of the current page using CDP."""
		# EN: Assign value to target.
		# JP: target に値を代入する。
		target = await self.get_current_target_info()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return target.get('url', '')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return DEFAULT_NEW_TAB_URL

	# EN: Define async function `get_current_page_title`.
	# JP: 非同期関数 `get_current_page_title` を定義する。
	async def get_current_page_title(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the title of the current page using CDP."""
		# EN: Assign value to target_info.
		# JP: target_info に値を代入する。
		target_info = await self.get_current_target_info()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_info:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return target_info.get('title', 'Unknown page title')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'Unknown page title'

	# EN: Define async function `navigate_to`.
	# JP: 非同期関数 `navigate_to` を定義する。
	async def navigate_to(self, url: str, new_tab: bool = False) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Navigate to a URL using the standard event system.

		Args:
		    url: URL to navigate to
		    new_tab: Whether to open in a new tab
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.events import NavigateToUrlEvent

		# EN: Assign value to event.
		# JP: event に値を代入する。
		event = self.event_bus.dispatch(NavigateToUrlEvent(url=url, new_tab=new_tab))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await event
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await event.event_result(raise_if_any=True, raise_if_none=False)

	# ========== DOM Helper Methods ==========

	# EN: Define async function `get_dom_element_by_index`.
	# JP: 非同期関数 `get_dom_element_by_index` を定義する。
	async def get_dom_element_by_index(self, index: int) -> EnhancedDOMTreeNode | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get DOM element by index.

		Get element from cached selector map.

		Args:
		    index: The element index from the serialized DOM

		Returns:
		    EnhancedDOMTreeNode or None if index not found
		"""
		#  Check cached selector map
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._cached_selector_map and index in self._cached_selector_map:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._cached_selector_map[index]

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `update_cached_selector_map`.
	# JP: 関数 `update_cached_selector_map` を定義する。
	def update_cached_selector_map(self, selector_map: dict[int, EnhancedDOMTreeNode]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update the cached selector map with new DOM state.

		This should be called by the DOM watchdog after rebuilding the DOM.

		Args:
		    selector_map: The new selector map from DOM serialization
		"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cached_selector_map = selector_map

	# Alias for backwards compatibility
	# EN: Define async function `get_element_by_index`.
	# JP: 非同期関数 `get_element_by_index` を定義する。
	async def get_element_by_index(self, index: int) -> EnhancedDOMTreeNode | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Alias for get_dom_element_by_index for backwards compatibility."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await self.get_dom_element_by_index(index)

	# EN: Define async function `get_target_id_from_tab_id`.
	# JP: 非同期関数 `get_target_id_from_tab_id` を定義する。
	async def get_target_id_from_tab_id(self, tab_id: str) -> TargetID:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the full-length TargetID from the truncated 4-char tab_id."""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for full_target_id in self._cdp_session_pool.keys():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if full_target_id.endswith(tab_id):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return full_target_id

		# may not have a cached session, so we need to get all pages and find the target id
		# EN: Assign value to all_targets.
		# JP: all_targets に値を代入する。
		all_targets = await self.cdp_client.send.Target.getTargets()
		# Filter for valid page/tab targets only
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for target in all_targets.get('targetInfos', []):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target['targetId'].endswith(tab_id):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return target['targetId']

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f'No TargetID found ending in tab_id=...{tab_id}')

	# EN: Define async function `get_target_id_from_url`.
	# JP: 非同期関数 `get_target_id_from_url` を定義する。
	async def get_target_id_from_url(self, url: str) -> TargetID:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the TargetID from a URL."""
		# EN: Assign value to all_targets.
		# JP: all_targets に値を代入する。
		all_targets = await self.cdp_client.send.Target.getTargets()
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for target in all_targets.get('targetInfos', []):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target['url'] == url and target['type'] == 'page':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return target['targetId']

		# still not found, try substring match as fallback
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for target in all_targets.get('targetInfos', []):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if url in target['url'] and target['type'] == 'page':
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return target['targetId']

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f'No TargetID found for url={url}')

	# EN: Define async function `get_most_recently_opened_target_id`.
	# JP: 非同期関数 `get_most_recently_opened_target_id` を定義する。
	async def get_most_recently_opened_target_id(self) -> TargetID:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the most recently opened target ID."""
		# EN: Assign value to all_targets.
		# JP: all_targets に値を代入する。
		all_targets = await self.cdp_client.send.Target.getTargets()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (await self._cdp_get_all_pages())[-1]['targetId']

	# EN: Define function `is_file_input`.
	# JP: 関数 `is_file_input` を定義する。
	def is_file_input(self, element: Any) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if element is a file input.

		Args:
		    element: The DOM element to check

		Returns:
		    True if element is a file input, False otherwise
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._dom_watchdog:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._dom_watchdog.is_file_input(element)
		# Fallback if watchdog not available
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (
			hasattr(element, 'node_name')
			and element.node_name.upper() == 'INPUT'
			and hasattr(element, 'attributes')
			and element.attributes.get('type', '').lower() == 'file'
		)

	# EN: Define async function `get_selector_map`.
	# JP: 非同期関数 `get_selector_map` を定義する。
	async def get_selector_map(self) -> dict[int, EnhancedDOMTreeNode]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the current selector map from cached state or DOM watchdog.

		Returns:
		    Dictionary mapping element indices to EnhancedDOMTreeNode objects
		"""
		# First try cached selector map
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._cached_selector_map:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._cached_selector_map

		# Try to get from DOM watchdog
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._dom_watchdog and hasattr(self._dom_watchdog, 'selector_map'):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._dom_watchdog.selector_map or {}

		# Return empty dict if nothing available
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {}

	# EN: Define async function `remove_highlights`.
	# JP: 非同期関数 `remove_highlights` を定義する。
	async def remove_highlights(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Remove highlights from the page using CDP."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_profile.highlight_elements:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get cached session
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.get_or_create_cdp_session()

			# Remove highlights via JavaScript - be thorough
			# EN: Assign value to script.
			# JP: script に値を代入する。
			script = """
            (function() {
                // Remove all browser-use highlight elements
                const highlights = document.querySelectorAll('[data-browser-use-highlight]');
                console.log('Removing', highlights.length, 'browser-use highlight elements');
                highlights.forEach(el => el.remove());

                // Also remove by ID in case selector missed anything
                const highlightContainer = document.getElementById('browser-use-debug-highlights');
                if (highlightContainer) {
                    console.log('Removing highlight container by ID');
                    highlightContainer.remove();
                }

                // Final cleanup - remove any orphaned tooltips
                const orphanedTooltips = document.querySelectorAll('[data-browser-use-highlight="tooltip"]');
                orphanedTooltips.forEach(el => el.remove());

                return { removed: highlights.length };
            })();
            """
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await cdp_session.cdp_client.send.Runtime.evaluate(
				params={'expression': script, 'returnByValue': True}, session_id=cdp_session.session_id
			)

			# Log the result for debugging
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if result and 'result' in result and 'value' in result['result']:
				# EN: Assign value to removed_count.
				# JP: removed_count に値を代入する。
				removed_count = result['result']['value'].get('removed', 0)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Successfully removed {removed_count} highlight elements')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('Highlight removal completed')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'Failed to remove highlights: {e}')

	# EN: Define async function `_close_extension_options_pages`.
	# JP: 非同期関数 `_close_extension_options_pages` を定義する。
	async def _close_extension_options_pages(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close any extension options/welcome pages that have opened."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get all open pages
			# EN: Assign value to targets.
			# JP: targets に値を代入する。
			targets = await self._cdp_get_all_pages()

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for target in targets:
				# EN: Assign value to target_url.
				# JP: target_url に値を代入する。
				target_url = target.get('url', '')
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = target.get('targetId', '')

				# Check if this is an extension options/welcome page
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'chrome-extension://' in target_url and (
					'options.html' in target_url or 'welcome.html' in target_url or 'onboarding.html' in target_url
				):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.info(f'[BrowserSession] 🚫 Closing extension options page: {target_url}')
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self._cdp_close_page(target_id)
					except Exception as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'[BrowserSession] Could not close extension page {target_id}: {e}')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[BrowserSession] Error closing extension options pages: {e}')

	# EN: Define async function `_close_data_url_tabs`.
	# JP: 非同期関数 `_close_data_url_tabs` を定義する。
	async def _close_data_url_tabs(self, exclude_target_id: TargetID | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close any remaining tabs that are still showing data URLs like ``data:,``."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to targets.
			# JP: targets に値を代入する。
			targets = await self._cdp_get_all_pages()
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for target in targets:
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = target.get('targetId')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not target_id or target_id == exclude_target_id:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# EN: Assign value to target_url.
				# JP: target_url に値を代入する。
				target_url = (target.get('url') or '').strip().lower()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not target_url.startswith('data:'):
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'[BrowserSession] Closing data URL tab {target_id[-4:]} ({target.get("url")})')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._cdp_close_page(target_id)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.event_bus.dispatch(TabClosedEvent(target_id=target_id))
				except Exception as close_error:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'[BrowserSession] Could not close data URL tab {target_id[-4:]}: {close_error}')
		except Exception as fetch_error:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[BrowserSession] Error while closing data URL tabs: {fetch_error}')

	# EN: Define function `downloaded_files`.
	# JP: 関数 `downloaded_files` を定義する。
	@property
	def downloaded_files(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get list of files downloaded during this browser session.

		Returns:
		    list[str]: List of absolute file paths to downloaded files in this session
		"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._downloaded_files.copy()

	# ========== CDP-based replacements for browser_context operations ==========

	# EN: Define async function `_cdp_get_all_pages`.
	# JP: 非同期関数 `_cdp_get_all_pages` を定義する。
	async def _cdp_get_all_pages(
		self,
		include_http: bool = True,
		include_about: bool = True,
		include_pages: bool = True,
		include_iframes: bool = False,
		include_workers: bool = False,
		include_chrome: bool = False,
		include_chrome_extensions: bool = False,
		include_chrome_error: bool = False,
	) -> list[TargetInfo]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get all browser pages/tabs using CDP Target.getTargets."""
		# Safety check - return empty list if browser not connected yet
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._cdp_client_root:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []
		# EN: Assign value to targets.
		# JP: targets に値を代入する。
		targets = await self.cdp_client.send.Target.getTargets()
		# Filter for valid page/tab targets only
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [
			t
			for t in targets.get('targetInfos', [])
			if self._is_valid_target(
				t,
				include_http=include_http,
				include_about=include_about,
				include_pages=include_pages,
				include_iframes=include_iframes,
				include_workers=include_workers,
				include_chrome=include_chrome,
				include_chrome_extensions=include_chrome_extensions,
				include_chrome_error=include_chrome_error,
			)
		]

	# EN: Define async function `_cdp_create_new_page`.
	# JP: 非同期関数 `_cdp_create_new_page` を定義する。
	async def _cdp_create_new_page(
		self, url: str = DEFAULT_NEW_TAB_URL, background: bool = False, new_window: bool = False
	) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create a new page/tab using CDP Target.createTarget. Returns target ID."""
		# Use the root CDP client to create tabs at the browser level
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._cdp_client_root:
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await self._cdp_client_root.send.Target.createTarget(
				params={'url': url, 'newWindow': new_window, 'background': background}
			)
		else:
			# Fallback to using cdp_client if root is not available
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await self.cdp_client.send.Target.createTarget(
				params={'url': url, 'newWindow': new_window, 'background': background}
			)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result['targetId']

	# EN: Define async function `_cdp_close_page`.
	# JP: 非同期関数 `_cdp_close_page` を定義する。
	async def _cdp_close_page(self, target_id: TargetID) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close a page/tab using CDP Target.closeTarget."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.cdp_client.send.Target.closeTarget(params={'targetId': target_id})

	# EN: Define async function `_cdp_get_cookies`.
	# JP: 非同期関数 `_cdp_get_cookies` を定義する。
	async def _cdp_get_cookies(self) -> list[Cookie]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get cookies using CDP Network.getCookies."""
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session(target_id=None, new_socket=False)
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = await asyncio.wait_for(
			cdp_session.cdp_client.send.Storage.getCookies(session_id=cdp_session.session_id), timeout=8.0
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result.get('cookies', [])

	# EN: Define async function `_cdp_set_cookies`.
	# JP: 非同期関数 `_cdp_set_cookies` を定義する。
	async def _cdp_set_cookies(self, cookies: list[Cookie]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set cookies using CDP Storage.setCookies."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.agent_focus or not cookies:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session(target_id=None, new_socket=False)
		# Storage.setCookies expects params dict with 'cookies' key
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await cdp_session.cdp_client.send.Storage.setCookies(
			params={'cookies': cookies},  # type: ignore[arg-type]
			session_id=cdp_session.session_id,
		)

	# EN: Define async function `_cdp_clear_cookies`.
	# JP: 非同期関数 `_cdp_clear_cookies` を定義する。
	async def _cdp_clear_cookies(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear all cookies using CDP Network.clearBrowserCookies."""
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await cdp_session.cdp_client.send.Storage.clearCookies(session_id=cdp_session.session_id)

	# EN: Define async function `_cdp_set_extra_headers`.
	# JP: 非同期関数 `_cdp_set_extra_headers` を定義する。
	async def _cdp_set_extra_headers(self, headers: dict[str, str]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set extra HTTP headers using CDP Network.setExtraHTTPHeaders."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.agent_focus:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session()
		# await cdp_session.cdp_client.send.Network.setExtraHTTPHeaders(params={'headers': headers}, session_id=cdp_session.session_id)
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise NotImplementedError('Not implemented yet')

	# EN: Define async function `_cdp_grant_permissions`.
	# JP: 非同期関数 `_cdp_grant_permissions` を定義する。
	async def _cdp_grant_permissions(self, permissions: list[str], origin: str | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Grant permissions using CDP Browser.grantPermissions."""
		# EN: Assign value to params.
		# JP: params に値を代入する。
		params = {'permissions': permissions}
		# if origin:
		#     params['origin'] = origin
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session()
		# await cdp_session.cdp_client.send.Browser.grantPermissions(params=params, session_id=cdp_session.session_id)
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise NotImplementedError('Not implemented yet')

	# EN: Define async function `_cdp_set_geolocation`.
	# JP: 非同期関数 `_cdp_set_geolocation` を定義する。
	async def _cdp_set_geolocation(self, latitude: float, longitude: float, accuracy: float = 100) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set geolocation using CDP Emulation.setGeolocationOverride."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.cdp_client.send.Emulation.setGeolocationOverride(
			params={'latitude': latitude, 'longitude': longitude, 'accuracy': accuracy}
		)

	# EN: Define async function `_cdp_clear_geolocation`.
	# JP: 非同期関数 `_cdp_clear_geolocation` を定義する。
	async def _cdp_clear_geolocation(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear geolocation override using CDP."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.cdp_client.send.Emulation.clearGeolocationOverride()

	# EN: Define async function `_cdp_add_init_script`.
	# JP: 非同期関数 `_cdp_add_init_script` を定義する。
	async def _cdp_add_init_script(self, script: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Add script to evaluate on new document using CDP Page.addScriptToEvaluateOnNewDocument."""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self._cdp_client_root is not None
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session()

		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = await cdp_session.cdp_client.send.Page.addScriptToEvaluateOnNewDocument(
			params={'source': script, 'runImmediately': True}, session_id=cdp_session.session_id
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result['identifier']

	# EN: Define async function `_cdp_remove_init_script`.
	# JP: 非同期関数 `_cdp_remove_init_script` を定義する。
	async def _cdp_remove_init_script(self, identifier: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Remove script added with addScriptToEvaluateOnNewDocument."""
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session(target_id=None)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await cdp_session.cdp_client.send.Page.removeScriptToEvaluateOnNewDocument(
			params={'identifier': identifier}, session_id=cdp_session.session_id
		)

	# EN: Define async function `_cdp_set_viewport`.
	# JP: 非同期関数 `_cdp_set_viewport` を定義する。
	async def _cdp_set_viewport(
		self, width: int, height: int, device_scale_factor: float = 1.0, mobile: bool = False, target_id: str | None = None
	) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set viewport using CDP Emulation.setDeviceMetricsOverride.

		Args:
		    width: Viewport width
		    height: Viewport height
		    device_scale_factor: Device scale factor (default 1.0)
		    mobile: Whether to emulate mobile device (default False)
		    target_id: Optional target ID to set viewport for. If not provided, uses agent_focus.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_id:
			# Set viewport for specific target
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.get_or_create_cdp_session(target_id, focus=False, new_socket=False)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.agent_focus:
			# Use current focus
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = self.agent_focus
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('Cannot set viewport: no target_id provided and agent_focus not initialized')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await cdp_session.cdp_client.send.Emulation.setDeviceMetricsOverride(
			params={'width': width, 'height': height, 'deviceScaleFactor': device_scale_factor, 'mobile': mobile},
			session_id=cdp_session.session_id,
		)

	# EN: Define async function `_cdp_get_origins`.
	# JP: 非同期関数 `_cdp_get_origins` を定義する。
	async def _cdp_get_origins(self) -> list[dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get origins with localStorage and sessionStorage using CDP."""
		# EN: Assign value to origins.
		# JP: origins に値を代入する。
		origins = []
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session(target_id=None, new_socket=False)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Enable DOMStorage domain to track storage
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.DOMStorage.enable(session_id=cdp_session.session_id)

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Get all frames to find unique origins
				# EN: Assign value to frames_result.
				# JP: frames_result に値を代入する。
				frames_result = await cdp_session.cdp_client.send.Page.getFrameTree(session_id=cdp_session.session_id)

				# Extract unique origins from frames
				# EN: Assign value to unique_origins.
				# JP: unique_origins に値を代入する。
				unique_origins = set()

				# EN: Define function `_extract_origins`.
				# JP: 関数 `_extract_origins` を定義する。
				def _extract_origins(frame_tree):
					# EN: Describe this block with a docstring.
					# JP: このブロックの説明をドキュメント文字列で記述する。
					"""Recursively extract origins from frame tree."""
					# EN: Assign value to frame.
					# JP: frame に値を代入する。
					frame = frame_tree.get('frame', {})
					# EN: Assign value to origin.
					# JP: origin に値を代入する。
					origin = frame.get('securityOrigin')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if origin and origin != 'null':
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						unique_origins.add(origin)

					# Process child frames
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for child in frame_tree.get('childFrames', []):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						_extract_origins(child)

				# EN: Define async function `_get_storage_items`.
				# JP: 非同期関数 `_get_storage_items` を定義する。
				async def _get_storage_items(origin: str, is_local_storage: bool) -> list[dict[str, str]] | None:
					# EN: Describe this block with a docstring.
					# JP: このブロックの説明をドキュメント文字列で記述する。
					"""Helper to get storage items for an origin."""
					# EN: Assign value to storage_type.
					# JP: storage_type に値を代入する。
					storage_type = 'localStorage' if is_local_storage else 'sessionStorage'
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to result.
						# JP: result に値を代入する。
						result = await cdp_session.cdp_client.send.DOMStorage.getDOMStorageItems(
							params={'storageId': {'securityOrigin': origin, 'isLocalStorage': is_local_storage}},
							session_id=cdp_session.session_id,
						)

						# EN: Assign value to items.
						# JP: items に値を代入する。
						items = []
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for item in result.get('entries', []):
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if len(item) == 2:  # Each item is [key, value]
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								items.append({'name': item[0], 'value': item[1]})

						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return items if items else None
					except Exception as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'Failed to get {storage_type} for {origin}: {e}')
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return None

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_extract_origins(frames_result.get('frameTree', {}))

				# For each unique origin, get localStorage and sessionStorage
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for origin in unique_origins:
					# EN: Assign value to origin_data.
					# JP: origin_data に値を代入する。
					origin_data = {'origin': origin}

					# Get localStorage
					# EN: Assign value to local_storage.
					# JP: local_storage に値を代入する。
					local_storage = await _get_storage_items(origin, is_local_storage=True)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if local_storage:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						origin_data['localStorage'] = local_storage

					# Get sessionStorage
					# EN: Assign value to session_storage.
					# JP: session_storage に値を代入する。
					session_storage = await _get_storage_items(origin, is_local_storage=False)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if session_storage:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						origin_data['sessionStorage'] = session_storage

					# Only add origin if it has storage data
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'localStorage' in origin_data or 'sessionStorage' in origin_data:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						origins.append(origin_data)

			finally:
				# Always disable DOMStorage tracking when done
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.DOMStorage.disable(session_id=cdp_session.session_id)

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'Failed to get origins: {e}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return origins

	# EN: Define async function `_cdp_get_storage_state`.
	# JP: 非同期関数 `_cdp_get_storage_state` を定義する。
	async def _cdp_get_storage_state(self) -> dict:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get storage state (cookies, localStorage, sessionStorage) using CDP."""
		# Use the _cdp_get_cookies helper which handles session attachment
		# EN: Assign value to cookies.
		# JP: cookies に値を代入する。
		cookies = await self._cdp_get_cookies()

		# Get origins with localStorage/sessionStorage
		# EN: Assign value to origins.
		# JP: origins に値を代入する。
		origins = await self._cdp_get_origins()

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'cookies': cookies,
			'origins': origins,
		}

	# EN: Define async function `_cdp_navigate`.
	# JP: 非同期関数 `_cdp_navigate` を定義する。
	async def _cdp_navigate(self, url: str, target_id: TargetID | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Navigate to URL using CDP Page.navigate."""
		# Use provided target_id or fall back to current_target_id

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self._cdp_client_root is not None, 'CDP client not initialized - browser may not be connected yet'
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.agent_focus is not None, 'CDP session not initialized - browser may not be connected yet'

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.agent_focus = await self.get_or_create_cdp_session(target_id or self.agent_focus.target_id, focus=True)

		# Use helper to navigate on the target
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.agent_focus.cdp_client.send.Page.navigate(params={'url': url}, session_id=self.agent_focus.session_id)

	# EN: Define function `_is_valid_target`.
	# JP: 関数 `_is_valid_target` を定義する。
	@staticmethod
	def _is_valid_target(
		target_info: TargetInfo,
		include_http: bool = True,
		include_chrome: bool = False,
		include_chrome_extensions: bool = False,
		include_chrome_error: bool = False,
		include_about: bool = True,
		include_iframes: bool = True,
		include_pages: bool = True,
		include_workers: bool = False,
	) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if a target should be processed.

		Args:
		    target_info: Target info dict from CDP

		Returns:
		    True if target should be processed, False if it should be skipped
		"""
		# EN: Assign value to target_type.
		# JP: target_type に値を代入する。
		target_type = target_info.get('type', '')
		# CDP TargetInfo can include a subtype for out-of-process iframes (OOPIF).
		# These report type="page" but subtype="iframe", which previously caused
		# them to be treated as top-level pages. That resulted in the agent focus
		# switching to iframe targets, breaking commands that require a top-level
		# page (screenshots, navigation, etc.). Keep track of the subtype so that
		# we can treat OOPIFs like iframes unless explicitly requested.
		# EN: Assign value to target_subtype.
		# JP: target_subtype に値を代入する。
		target_subtype = target_info.get('subtype') or target_info.get('subType') or ''
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = target_info.get('url', '')

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		url_allowed, type_allowed = False, False

		# Always allow new tab pages (chrome://new-tab-page/, chrome://newtab/, about:blank)
		# so they can be redirected to about:blank in connect()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_new_tab_page(url):
			# EN: Assign value to url_allowed.
			# JP: url_allowed に値を代入する。
			url_allowed = True

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if url.startswith('chrome-error://') and include_chrome_error:
			# EN: Assign value to url_allowed.
			# JP: url_allowed に値を代入する。
			url_allowed = True

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if url.startswith('chrome://') and include_chrome:
			# EN: Assign value to url_allowed.
			# JP: url_allowed に値を代入する。
			url_allowed = True

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if url.startswith('chrome-extension://') and include_chrome_extensions:
			# EN: Assign value to url_allowed.
			# JP: url_allowed に値を代入する。
			url_allowed = True

		# dont allow about:srcdoc! there are also other rare about: pages that we want to avoid
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if url == 'about:blank' and include_about:
			# EN: Assign value to url_allowed.
			# JP: url_allowed に値を代入する。
			url_allowed = True

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if (url.startswith('http://') or url.startswith('https://')) and include_http:
			# EN: Assign value to url_allowed.
			# JP: url_allowed に値を代入する。
			url_allowed = True

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_type in ('service_worker', 'shared_worker', 'worker') and include_workers:
			# EN: Assign value to type_allowed.
			# JP: type_allowed に値を代入する。
			type_allowed = True

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_type in ('page', 'tab'):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target_subtype == 'iframe':
				# Out-of-process iframes (OOPIFs) expose themselves as
				# type="page" but subtype="iframe". Only allow these
				# when iframe targets are requested, otherwise they are
				# treated as regular iframes and excluded from the list of
				# top-level pages used for navigation/tab focus.
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if include_iframes:
					# EN: Assign value to type_allowed.
					# JP: type_allowed に値を代入する。
					type_allowed = True
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif include_pages:
				# EN: Assign value to type_allowed.
				# JP: type_allowed に値を代入する。
				type_allowed = True

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_type in ('iframe', 'webview') and include_iframes:
			# EN: Assign value to type_allowed.
			# JP: type_allowed に値を代入する。
			type_allowed = True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return url_allowed and type_allowed

	# EN: Define async function `get_all_frames`.
	# JP: 非同期関数 `get_all_frames` を定義する。
	async def get_all_frames(self) -> tuple[dict[str, dict], dict[str, str]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get a complete frame hierarchy from all browser targets.

		Returns:
		    Tuple of (all_frames, target_sessions) where:
		    - all_frames: dict mapping frame_id -> frame info dict with all metadata
		    - target_sessions: dict mapping target_id -> session_id for active sessions
		"""
		# EN: Assign value to all_frames.
		# JP: all_frames に値を代入する。
		all_frames = {}  # frame_id -> FrameInfo dict
		# EN: Assign value to target_sessions.
		# JP: target_sessions に値を代入する。
		target_sessions = {}  # target_id -> session_id (keep sessions alive during collection)

		# Check if cross-origin iframe support is enabled
		# EN: Assign value to include_cross_origin.
		# JP: include_cross_origin に値を代入する。
		include_cross_origin = self.browser_profile.cross_origin_iframes

		# Get all targets - only include iframes if cross-origin support is enabled
		# EN: Assign value to targets.
		# JP: targets に値を代入する。
		targets = await self._cdp_get_all_pages(
			include_http=True,
			include_about=True,
			include_pages=True,
			include_iframes=include_cross_origin,  # Only include iframe targets if flag is set
			include_workers=False,
			include_chrome=False,
			include_chrome_extensions=False,
			include_chrome_error=include_cross_origin,  # Only include error pages if cross-origin is enabled
		)
		# EN: Assign value to all_targets.
		# JP: all_targets に値を代入する。
		all_targets = targets

		# First pass: collect frame trees from ALL targets
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for target in all_targets:
			# EN: Assign value to target_id.
			# JP: target_id に値を代入する。
			target_id = target['targetId']

			# Skip iframe targets if cross-origin support is disabled
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not include_cross_origin and target.get('type') == 'iframe':
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# When cross-origin support is disabled, only process the current target
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not include_cross_origin:
				# Only process the current focus target
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.agent_focus and target_id != self.agent_focus.target_id:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# Use the existing agent_focus session
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = self.agent_focus
			else:
				# Get cached session for this target (don't change focus - iterating frames)
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = await self.get_or_create_cdp_session(target_id, focus=False)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cdp_session:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				target_sessions[target_id] = cdp_session.session_id

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# Try to get frame tree (not all target types support this)
					# EN: Assign value to frame_tree_result.
					# JP: frame_tree_result に値を代入する。
					frame_tree_result = await cdp_session.cdp_client.send.Page.getFrameTree(session_id=cdp_session.session_id)

					# Process the frame tree recursively
					# EN: Define function `process_frame_tree`.
					# JP: 関数 `process_frame_tree` を定義する。
					def process_frame_tree(node, parent_frame_id=None):
						# EN: Describe this block with a docstring.
						# JP: このブロックの説明をドキュメント文字列で記述する。
						"""Recursively process frame tree and add to all_frames."""
						# EN: Assign value to frame.
						# JP: frame に値を代入する。
						frame = node.get('frame', {})
						# EN: Assign value to current_frame_id.
						# JP: current_frame_id に値を代入する。
						current_frame_id = frame.get('id')

						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if current_frame_id:
							# For iframe targets, check if the frame has a parentId field
							# This indicates it's an OOPIF with a parent in another target
							# EN: Assign value to actual_parent_id.
							# JP: actual_parent_id に値を代入する。
							actual_parent_id = frame.get('parentId') or parent_frame_id

							# Create frame info with all CDP response data plus our additions
							# EN: Assign value to frame_info.
							# JP: frame_info に値を代入する。
							frame_info = {
								**frame,  # Include all original frame data: id, url, parentId, etc.
								'frameTargetId': target_id,  # Target that can access this frame
								'parentFrameId': actual_parent_id,  # Use parentId from frame if available
								'childFrameIds': [],  # Will be populated below
								'isCrossOrigin': False,  # Will be determined based on context
								'isValidTarget': self._is_valid_target(
									target,
									include_http=True,
									include_about=True,
									include_pages=True,
									include_iframes=True,
									include_workers=False,
									include_chrome=False,  # chrome://newtab, chrome://settings, etc. are not valid frames we can control (for sanity reasons)
									include_chrome_extensions=False,  # chrome-extension://
									include_chrome_error=False,  # chrome-error://  (e.g. when iframes fail to load or are blocked by uBlock Origin)
								),
							}

							# Check if frame is cross-origin based on crossOriginIsolatedContextType
							# EN: Assign value to cross_origin_type.
							# JP: cross_origin_type に値を代入する。
							cross_origin_type = frame.get('crossOriginIsolatedContextType')
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if cross_origin_type and cross_origin_type != 'NotIsolated':
								# EN: Assign value to target variable.
								# JP: target variable に値を代入する。
								frame_info['isCrossOrigin'] = True

							# For iframe targets, the frame itself is likely cross-origin
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if target.get('type') == 'iframe':
								# EN: Assign value to target variable.
								# JP: target variable に値を代入する。
								frame_info['isCrossOrigin'] = True

							# Skip cross-origin frames if support is disabled
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if not include_cross_origin and frame_info.get('isCrossOrigin'):
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return  # Skip this frame and its children

							# Add child frame IDs (note: OOPIFs won't appear here)
							# EN: Assign value to child_frames.
							# JP: child_frames に値を代入する。
							child_frames = node.get('childFrames', [])
							# EN: Iterate over items in a loop.
							# JP: ループで要素を順に処理する。
							for child in child_frames:
								# EN: Assign value to child_frame.
								# JP: child_frame に値を代入する。
								child_frame = child.get('frame', {})
								# EN: Assign value to child_frame_id.
								# JP: child_frame_id に値を代入する。
								child_frame_id = child_frame.get('id')
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if child_frame_id:
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									frame_info['childFrameIds'].append(child_frame_id)

							# Store or merge frame info
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if current_frame_id in all_frames:
								# Frame already seen from another target, merge info
								# EN: Assign value to existing.
								# JP: existing に値を代入する。
								existing = all_frames[current_frame_id]
								# If this is an iframe target, it has direct access to the frame
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if target.get('type') == 'iframe':
									# EN: Assign value to target variable.
									# JP: target variable に値を代入する。
									existing['frameTargetId'] = target_id
									# EN: Assign value to target variable.
									# JP: target variable に値を代入する。
									existing['isCrossOrigin'] = True
							else:
								# EN: Assign value to target variable.
								# JP: target variable に値を代入する。
								all_frames[current_frame_id] = frame_info

							# Process child frames recursively (only if we're not skipping this frame)
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if include_cross_origin or not frame_info.get('isCrossOrigin'):
								# EN: Iterate over items in a loop.
								# JP: ループで要素を順に処理する。
								for child in child_frames:
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									process_frame_tree(child, current_frame_id)

					# Process the entire frame tree
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					process_frame_tree(frame_tree_result.get('frameTree', {}))

				except Exception as e:
					# Target doesn't support Page domain or has no frames
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Failed to get frame tree for target {target_id}: {e}')

		# Second pass: populate backend node IDs and parent target IDs
		# Only do this if cross-origin support is enabled
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if include_cross_origin:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._populate_frame_metadata(all_frames, target_sessions)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return all_frames, target_sessions

	# EN: Define async function `_populate_frame_metadata`.
	# JP: 非同期関数 `_populate_frame_metadata` を定義する。
	async def _populate_frame_metadata(self, all_frames: dict[str, dict], target_sessions: dict[str, str]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Populate additional frame metadata like backend node IDs and parent target IDs.

		Args:
		    all_frames: Frame hierarchy dict to populate
		    target_sessions: Active target sessions
		"""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for frame_id_iter, frame_info in all_frames.items():
			# EN: Assign value to parent_frame_id.
			# JP: parent_frame_id に値を代入する。
			parent_frame_id = frame_info.get('parentFrameId')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if parent_frame_id and parent_frame_id in all_frames:
				# EN: Assign value to parent_frame_info.
				# JP: parent_frame_info に値を代入する。
				parent_frame_info = all_frames[parent_frame_id]
				# EN: Assign value to parent_target_id.
				# JP: parent_target_id に値を代入する。
				parent_target_id = parent_frame_info.get('frameTargetId')

				# Store parent target ID
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				frame_info['parentTargetId'] = parent_target_id

				# Try to get backend node ID from parent context
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if parent_target_id in target_sessions:
					# EN: Validate a required condition.
					# JP: 必須条件を検証する。
					assert parent_target_id is not None
					# EN: Assign value to parent_session_id.
					# JP: parent_session_id に値を代入する。
					parent_session_id = target_sessions[parent_target_id]
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# Enable DOM domain
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self.cdp_client.send.DOM.enable(session_id=parent_session_id)

						# Get frame owner info to find backend node ID
						# EN: Assign value to frame_owner.
						# JP: frame_owner に値を代入する。
						frame_owner = await self.cdp_client.send.DOM.getFrameOwner(
							params={'frameId': frame_id_iter}, session_id=parent_session_id
						)

						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if frame_owner:
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							frame_info['backendNodeId'] = frame_owner.get('backendNodeId')
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							frame_info['nodeId'] = frame_owner.get('nodeId')

					except Exception:
						# Frame owner not available (likely cross-origin)
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

	# EN: Define async function `find_frame_target`.
	# JP: 非同期関数 `find_frame_target` を定義する。
	async def find_frame_target(self, frame_id: str, all_frames: dict[str, dict] | None = None) -> dict | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Find the frame info for a specific frame ID.

		Args:
		    frame_id: The frame ID to search for
		    all_frames: Optional pre-built frame hierarchy. If None, will call get_all_frames()

		Returns:
		    Frame info dict if found, None otherwise
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if all_frames is None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			all_frames, _ = await self.get_all_frames()

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return all_frames.get(frame_id)

	# EN: Define async function `cdp_client_for_target`.
	# JP: 非同期関数 `cdp_client_for_target` を定義する。
	async def cdp_client_for_target(self, target_id: TargetID) -> CDPSession:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await self.get_or_create_cdp_session(target_id, focus=False)

	# EN: Define async function `cdp_client_for_frame`.
	# JP: 非同期関数 `cdp_client_for_frame` を定義する。
	async def cdp_client_for_frame(self, frame_id: str) -> CDPSession:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get a CDP client attached to the target containing the specified frame.

		Builds a unified frame hierarchy from all targets to find the correct target
		for any frame, including OOPIFs (Out-of-Process iframes).

		Args:
		    frame_id: The frame ID to search for

		Returns:
		    Tuple of (cdp_cdp_session, target_id) for the target containing the frame

		Raises:
		    ValueError: If the frame is not found in any target
		"""
		# If cross-origin iframes are disabled, just use the main session
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_profile.cross_origin_iframes:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return await self.get_or_create_cdp_session()

		# Get complete frame hierarchy
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		all_frames, target_sessions = await self.get_all_frames()

		# Find the requested frame
		# EN: Assign value to frame_info.
		# JP: frame_info に値を代入する。
		frame_info = await self.find_frame_target(frame_id, all_frames)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if frame_info:
			# EN: Assign value to target_id.
			# JP: target_id に値を代入する。
			target_id = frame_info.get('frameTargetId')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target_id in target_sessions:
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert target_id is not None
				# Use existing session
				# EN: Assign value to session_id.
				# JP: session_id に値を代入する。
				session_id = target_sessions[target_id]
				# Return the client with session attached (don't change focus)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await self.get_or_create_cdp_session(target_id, focus=False)

		# Frame not found
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f"Frame with ID '{frame_id}' not found in any target")

	# EN: Define async function `cdp_client_for_node`.
	# JP: 非同期関数 `cdp_client_for_node` を定義する。
	async def cdp_client_for_node(self, node: EnhancedDOMTreeNode) -> CDPSession:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get CDP client for a specific DOM node based on its frame."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.frame_id:
			# # If cross-origin iframes are disabled, always use the main session
			# if not self.browser_profile.cross_origin_iframes:
			#     assert self.agent_focus is not None, 'No active CDP session'
			#     return self.agent_focus
			# Otherwise, try to get the frame-specific session
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = await self.cdp_client_for_frame(node.frame_id)
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await cdp_session.cdp_client.send.DOM.resolveNode(
					params={'backendNodeId': node.backend_node_id},
					session_id=cdp_session.session_id,
				)
				# EN: Assign value to object_id.
				# JP: object_id に値を代入する。
				object_id = result.get('object', {}).get('objectId')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not object_id:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError(
						f'Could not find #{node.element_index} backendNodeId={node.backend_node_id} in target_id={cdp_session.target_id}'
					)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return cdp_session
			except (ValueError, Exception) as e:
				# Fall back to main session if frame not found
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Failed to get CDP client for frame {node.frame_id}: {e}, using main session')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.target_id:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = await self.get_or_create_cdp_session(target_id=node.target_id, focus=False)
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await cdp_session.cdp_client.send.DOM.resolveNode(
					params={'backendNodeId': node.backend_node_id},
					session_id=cdp_session.session_id,
				)
				# EN: Assign value to object_id.
				# JP: object_id に値を代入する。
				object_id = result.get('object', {}).get('objectId')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not object_id:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError(
						f'Could not find #{node.element_index} backendNodeId={node.backend_node_id} in target_id={cdp_session.target_id}'
					)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Failed to get CDP client for target {node.target_id}: {e}, using main session')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await self.get_or_create_cdp_session()

	# EN: Define async function `take_screenshot`.
	# JP: 非同期関数 `take_screenshot` を定義する。
	async def take_screenshot(
		self,
		path: str | None = None,
		full_page: bool = False,
		format: str = 'png',
		quality: int | None = None,
		clip: dict | None = None,
	) -> bytes:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Take a screenshot using CDP.

		Args:
		    path: Optional file path to save screenshot
		    full_page: Capture entire scrollable page beyond viewport
		    format: Image format ('png', 'jpeg', 'webp')
		    quality: Quality 0-100 for JPEG format
		    clip: Region to capture {'x': int, 'y': int, 'width': int, 'height': int}

		Returns:
		    Screenshot data as bytes
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import base64

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from cdp_use.cdp.page import CaptureScreenshotParameters

		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session()

		# Build parameters dict explicitly to satisfy TypedDict expectations
		# EN: Assign annotated value to params.
		# JP: params に型付きの値を代入する。
		params: CaptureScreenshotParameters = {
			'format': format,
			'captureBeyondViewport': full_page,
		}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if quality is not None and format == 'jpeg':
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			params['quality'] = quality

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if clip:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			params['clip'] = {
				'x': clip['x'],
				'y': clip['y'],
				'width': clip['width'],
				'height': clip['height'],
				'scale': 1,
			}

		# EN: Assign value to params.
		# JP: params に値を代入する。
		params = CaptureScreenshotParameters(**params)

		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = await cdp_session.cdp_client.send.Page.captureScreenshot(params=params, session_id=cdp_session.session_id)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not result or 'data' not in result:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise Exception('Screenshot failed - no data returned')

		# EN: Assign value to screenshot_data.
		# JP: screenshot_data に値を代入する。
		screenshot_data = base64.b64decode(result['data'])

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if path:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			Path(path).write_bytes(screenshot_data)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return screenshot_data

	# EN: Define async function `screenshot_element`.
	# JP: 非同期関数 `screenshot_element` を定義する。
	async def screenshot_element(
		self,
		selector: str,
		path: str | None = None,
		format: str = 'png',
		quality: int | None = None,
	) -> bytes:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Take a screenshot of a specific element.

		Args:
		    selector: CSS selector for the element
		    path: Optional file path to save screenshot
		    format: Image format ('png', 'jpeg', 'webp')
		    quality: Quality 0-100 for JPEG format

		Returns:
		    Screenshot data as bytes
		"""

		# EN: Assign value to bounds.
		# JP: bounds に値を代入する。
		bounds = await self._get_element_bounds(selector)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not bounds:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f"Element '{selector}' not found or has no bounds")

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await self.take_screenshot(
			path=path,
			format=format,
			quality=quality,
			clip=bounds,
		)

	# EN: Define async function `_get_element_bounds`.
	# JP: 非同期関数 `_get_element_bounds` を定義する。
	async def _get_element_bounds(self, selector: str) -> dict | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get element bounding box using CDP."""

		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.get_or_create_cdp_session()

		# Get document
		# EN: Assign value to doc.
		# JP: doc に値を代入する。
		doc = await cdp_session.cdp_client.send.DOM.getDocument(params={'depth': 1}, session_id=cdp_session.session_id)

		# Query selector
		# EN: Assign value to node_result.
		# JP: node_result に値を代入する。
		node_result = await cdp_session.cdp_client.send.DOM.querySelector(
			params={'nodeId': doc['root']['nodeId'], 'selector': selector}, session_id=cdp_session.session_id
		)

		# EN: Assign value to node_id.
		# JP: node_id に値を代入する。
		node_id = node_result.get('nodeId')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not node_id:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Get bounding box
		# EN: Assign value to box_result.
		# JP: box_result に値を代入する。
		box_result = await cdp_session.cdp_client.send.DOM.getBoxModel(
			params={'nodeId': node_id}, session_id=cdp_session.session_id
		)

		# EN: Assign value to box_model.
		# JP: box_model に値を代入する。
		box_model = box_result.get('model')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not box_model:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = box_model['content']
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'x': min(content[0], content[2], content[4], content[6]),
			'y': min(content[1], content[3], content[5], content[7]),
			'width': max(content[0], content[2], content[4], content[6]) - min(content[0], content[2], content[4], content[6]),
			'height': max(content[1], content[3], content[5], content[7]) - min(content[1], content[3], content[5], content[7]),
		}

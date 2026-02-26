# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Event definitions for browser communication."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import inspect
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, Literal

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus.models import T_EventResultType
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.target import TargetID
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, Field, field_validator

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserStateSummary
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import EnhancedDOMTreeNode


# EN: Define function `_get_timeout`.
# JP: 関数 `_get_timeout` を定義する。
def _get_timeout(env_var: str, default: float | None) -> float | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Safely parse environment variable timeout values with robust error handling.

	Args:
		env_var: Environment variable name (e.g. 'TIMEOUT_NavigateToUrlEvent')
		default: Default timeout value as float or None (e.g. 15.0, or None to disable)

	Returns:
		Parsed float value or the default if parsing fails

	Raises:
		ValueError: Only if both env_var and default are invalid (should not happen with valid defaults)
	"""
	# Try environment variable first
	# EN: Assign value to env_value.
	# JP: env_value に値を代入する。
	env_value = os.getenv(env_var)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if env_value:
		# EN: Assign value to lower.
		# JP: lower に値を代入する。
		lower = env_value.strip().lower()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if lower in {'none', 'no', 'off', 'false', '0', 'unlimited'}:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to parsed.
			# JP: parsed に値を代入する。
			parsed = float(env_value)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if parsed < 0:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print(f'Warning: {env_var}={env_value} is negative, using default {default}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return default
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return parsed
		except (ValueError, TypeError):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'Warning: {env_var}={env_value} is not a valid number, using default {default}')

	# Fall back to default
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return default


# ============================================================================
# Agent/Tools -> BrowserSession Events (High-level browser actions)
# ============================================================================


# EN: Define class `ElementSelectedEvent`.
# JP: クラス `ElementSelectedEvent` を定義する。
class ElementSelectedEvent(BaseEvent[T_EventResultType]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""An element was selected."""

	# EN: Assign annotated value to node.
	# JP: node に型付きの値を代入する。
	node: EnhancedDOMTreeNode

	# EN: Define function `serialize_node`.
	# JP: 関数 `serialize_node` を定義する。
	@field_validator('node', mode='before')
	@classmethod
	def serialize_node(cls, data: EnhancedDOMTreeNode | None) -> EnhancedDOMTreeNode | None:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if data is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return EnhancedDOMTreeNode(
			element_index=data.element_index,
			node_id=data.node_id,
			backend_node_id=data.backend_node_id,
			session_id=data.session_id,
			frame_id=data.frame_id,
			target_id=data.target_id,
			node_type=data.node_type,
			node_name=data.node_name,
			node_value=data.node_value,
			attributes=data.attributes,
			is_scrollable=data.is_scrollable,
			is_visible=data.is_visible,
			absolute_position=data.absolute_position,
			# override the circular reference fields in EnhancedDOMTreeNode as they cant be serialized and aren't needed by event handlers
			# only used internally by the DOM service during DOM tree building process, not intended public API use
			content_document=None,
			shadow_root_type=None,
			shadow_roots=[],
			parent_node=None,
			children_nodes=[],
			ax_node=None,
			snapshot_node=None,
		)


# TODO: add page handle to events
# class PageHandle(share a base with browser.session.CDPSession?):
# 	url: str
# 	target_id: TargetID
#   @classmethod
#   def from_target_id(cls, target_id: TargetID) -> Self:
#     return cls(target_id=target_id)
#   @classmethod
#   def from_target_id(cls, target_id: TargetID) -> Self:
#     return cls(target_id=target_id)
#   @classmethod
#   def from_url(cls, url: str) -> Self:
#   @property
#   def root_frame_id(self) -> str:
#     return self.target_id
#   @property
#   def session_id(self) -> str:
#     return browser_session.get_or_create_cdp_session(self.target_id).session_id

# class PageSelectedEvent(BaseEvent[T_EventResultType]):
# 	"""An event like SwitchToTabEvent(page=PageHandle) or CloseTabEvent(page=PageHandle)"""
# 	page: PageHandle


# EN: Define class `NavigateToUrlEvent`.
# JP: クラス `NavigateToUrlEvent` を定義する。
class NavigateToUrlEvent(BaseEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Navigate to a specific URL."""

	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Assign annotated value to wait_until.
	# JP: wait_until に型付きの値を代入する。
	wait_until: Literal['load', 'domcontentloaded', 'networkidle', 'commit'] = 'load'
	# EN: Assign annotated value to timeout_ms.
	# JP: timeout_ms に型付きの値を代入する。
	timeout_ms: int | None = None
	# EN: Assign annotated value to new_tab.
	# JP: new_tab に型付きの値を代入する。
	new_tab: bool = Field(
		default=False, description='Set True to leave the current tab alone and open a new tab in the foreground for the new URL'
	)
	# existing_tab: PageHandle | None = None  # TODO

	# time limits enforced by bubus, not exposed to LLM:
	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_NavigateToUrlEvent', 15.0)  # seconds


# EN: Define class `ClickElementEvent`.
# JP: クラス `ClickElementEvent` を定義する。
class ClickElementEvent(ElementSelectedEvent[dict[str, Any] | None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Click an element."""

	# EN: Assign annotated value to node.
	# JP: node に型付きの値を代入する。
	node: 'EnhancedDOMTreeNode'
	# EN: Assign annotated value to button.
	# JP: button に型付きの値を代入する。
	button: Literal['left', 'right', 'middle'] = 'left'
	# EN: Assign annotated value to while_holding_ctrl.
	# JP: while_holding_ctrl に型付きの値を代入する。
	while_holding_ctrl: bool = Field(
		default=False,
		description='Set True to open any link clicked in a new tab in the background, can use switch_tab(tab_id=None) after to focus it',
	)
	# click_count: int = 1           # TODO
	# expect_download: bool = False  # moved to downloads_watchdog.py

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_ClickElementEvent', 15.0)  # seconds


# EN: Define class `TypeTextEvent`.
# JP: クラス `TypeTextEvent` を定義する。
class TypeTextEvent(ElementSelectedEvent[dict | None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Type text into an element."""

	# EN: Assign annotated value to node.
	# JP: node に型付きの値を代入する。
	node: 'EnhancedDOMTreeNode'
	# EN: Assign annotated value to text.
	# JP: text に型付きの値を代入する。
	text: str
	# EN: Assign annotated value to clear_existing.
	# JP: clear_existing に型付きの値を代入する。
	clear_existing: bool = True
	# EN: Assign annotated value to is_sensitive.
	# JP: is_sensitive に型付きの値を代入する。
	is_sensitive: bool = False  # Flag to indicate if text contains sensitive data
	# EN: Assign annotated value to sensitive_key_name.
	# JP: sensitive_key_name に型付きの値を代入する。
	sensitive_key_name: str | None = None  # Name of the sensitive key being typed (e.g., 'username', 'password')

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_TypeTextEvent', 15.0)  # seconds


# EN: Define class `ScrollEvent`.
# JP: クラス `ScrollEvent` を定義する。
class ScrollEvent(ElementSelectedEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Scroll the page or element."""

	# EN: Assign annotated value to direction.
	# JP: direction に型付きの値を代入する。
	direction: Literal['up', 'down', 'left', 'right']
	# EN: Assign annotated value to amount.
	# JP: amount に型付きの値を代入する。
	amount: int  # pixels
	# EN: Assign annotated value to node.
	# JP: node に型付きの値を代入する。
	node: 'EnhancedDOMTreeNode | None' = None  # None means scroll page

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_ScrollEvent', 8.0)  # seconds


# EN: Define class `SwitchTabEvent`.
# JP: クラス `SwitchTabEvent` を定義する。
class SwitchTabEvent(BaseEvent[TargetID]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Switch to a different tab."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID | None = Field(default=None, description='None means switch to the most recently opened tab')

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_SwitchTabEvent', 10.0)  # seconds


# EN: Define class `CloseTabEvent`.
# JP: クラス `CloseTabEvent` を定義する。
class CloseTabEvent(BaseEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Close a tab."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_CloseTabEvent', 10.0)  # seconds


# EN: Define class `ScreenshotEvent`.
# JP: クラス `ScreenshotEvent` を定義する。
class ScreenshotEvent(BaseEvent[str]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Request to take a screenshot."""

	# EN: Assign annotated value to full_page.
	# JP: full_page に型付きの値を代入する。
	full_page: bool = False
	# EN: Assign annotated value to clip.
	# JP: clip に型付きの値を代入する。
	clip: dict[str, float] | None = None  # {x, y, width, height}

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_ScreenshotEvent', 8.0)  # seconds


# EN: Define class `BrowserStateRequestEvent`.
# JP: クラス `BrowserStateRequestEvent` を定義する。
class BrowserStateRequestEvent(BaseEvent[BrowserStateSummary]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Request current browser state."""

	# EN: Assign annotated value to include_dom.
	# JP: include_dom に型付きの値を代入する。
	include_dom: bool = True
	# EN: Assign annotated value to include_screenshot.
	# JP: include_screenshot に型付きの値を代入する。
	include_screenshot: bool = True
	# EN: Assign annotated value to cache_clickable_elements_hashes.
	# JP: cache_clickable_elements_hashes に型付きの値を代入する。
	cache_clickable_elements_hashes: bool = True
	# EN: Assign annotated value to include_recent_events.
	# JP: include_recent_events に型付きの値を代入する。
	include_recent_events: bool = False

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_BrowserStateRequestEvent', 30.0)  # seconds


# class WaitForConditionEvent(BaseEvent):
# 	"""Wait for a condition."""

# 	condition: Literal['navigation', 'selector', 'timeout', 'load_state']
# 	timeout: float = 30000
# 	selector: str | None = None
# 	state: Literal['attached', 'detached', 'visible', 'hidden'] | None = None


# EN: Define class `GoBackEvent`.
# JP: クラス `GoBackEvent` を定義する。
class GoBackEvent(BaseEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Navigate back in browser history."""

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_GoBackEvent', 15.0)  # seconds


# EN: Define class `GoForwardEvent`.
# JP: クラス `GoForwardEvent` を定義する。
class GoForwardEvent(BaseEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Navigate forward in browser history."""

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_GoForwardEvent', 15.0)  # seconds


# EN: Define class `RefreshEvent`.
# JP: クラス `RefreshEvent` を定義する。
class RefreshEvent(BaseEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Refresh/reload the current page."""

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_RefreshEvent', 15.0)  # seconds


# EN: Define class `WaitEvent`.
# JP: クラス `WaitEvent` を定義する。
class WaitEvent(BaseEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Wait for a specified number of seconds."""

	# EN: Assign annotated value to seconds.
	# JP: seconds に型付きの値を代入する。
	seconds: float = 3.0
	# EN: Assign annotated value to max_seconds.
	# JP: max_seconds に型付きの値を代入する。
	max_seconds: float = 10.0  # Safety cap

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_WaitEvent', 60.0)  # seconds


# EN: Define class `SendKeysEvent`.
# JP: クラス `SendKeysEvent` を定義する。
class SendKeysEvent(BaseEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Send keyboard keys/shortcuts."""

	# EN: Assign annotated value to keys.
	# JP: keys に型付きの値を代入する。
	keys: str  # e.g., "ctrl+a", "cmd+c", "Enter"

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_SendKeysEvent', 15.0)  # seconds


# EN: Define class `UploadFileEvent`.
# JP: クラス `UploadFileEvent` を定義する。
class UploadFileEvent(ElementSelectedEvent[None]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Upload a file to an element."""

	# EN: Assign annotated value to node.
	# JP: node に型付きの値を代入する。
	node: 'EnhancedDOMTreeNode'
	# EN: Assign annotated value to file_path.
	# JP: file_path に型付きの値を代入する。
	file_path: str

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_UploadFileEvent', 30.0)  # seconds


# EN: Define class `GetDropdownOptionsEvent`.
# JP: クラス `GetDropdownOptionsEvent` を定義する。
class GetDropdownOptionsEvent(ElementSelectedEvent[dict[str, str]]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get all options from any dropdown (native <select>, ARIA menus, or custom dropdowns).

	Returns a dict containing dropdown type, options list, and element metadata."""

	# EN: Assign annotated value to node.
	# JP: node に型付きの値を代入する。
	node: 'EnhancedDOMTreeNode'

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout(
		'TIMEOUT_GetDropdownOptionsEvent',
		15.0,
	)  # some dropdowns lazy-load the list of options on first interaction, so we need to wait for them to load (e.g. table filter lists can have thousands of options)


# EN: Define class `SelectDropdownOptionEvent`.
# JP: クラス `SelectDropdownOptionEvent` を定義する。
class SelectDropdownOptionEvent(ElementSelectedEvent[dict[str, str]]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Select a dropdown option by exact text from any dropdown type.

	Returns a dict containing success status and selection details."""

	# EN: Assign annotated value to node.
	# JP: node に型付きの値を代入する。
	node: 'EnhancedDOMTreeNode'
	# EN: Assign annotated value to text.
	# JP: text に型付きの値を代入する。
	text: str  # The option text to select

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_SelectDropdownOptionEvent', 8.0)  # seconds


# EN: Define class `ScrollToTextEvent`.
# JP: クラス `ScrollToTextEvent` を定義する。
class ScrollToTextEvent(BaseEvent[bool]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Scroll to specific text on the page. Returns True on success, False if not found."""

	# EN: Assign annotated value to text.
	# JP: text に型付きの値を代入する。
	text: str
	# EN: Assign annotated value to direction.
	# JP: direction に型付きの値を代入する。
	direction: Literal['up', 'down'] = 'down'

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_ScrollToTextEvent', 15.0)  # seconds


# ============================================================================


# EN: Define class `BrowserStartEvent`.
# JP: クラス `BrowserStartEvent` を定義する。
class BrowserStartEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Start/connect to browser."""

	# EN: Assign annotated value to cdp_url.
	# JP: cdp_url に型付きの値を代入する。
	cdp_url: str | None = None
	# EN: Assign annotated value to launch_options.
	# JP: launch_options に型付きの値を代入する。
	launch_options: dict[str, Any] = Field(default_factory=dict)

	# Disable timeout by default so long-running reconnects don't fail.
	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_BrowserStartEvent', None)  # seconds


# EN: Define class `BrowserStopEvent`.
# JP: クラス `BrowserStopEvent` を定義する。
class BrowserStopEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Stop/disconnect from browser."""

	# EN: Assign annotated value to force.
	# JP: force に型付きの値を代入する。
	force: bool = False

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_BrowserStopEvent', 45.0)  # seconds


# EN: Define class `BrowserLaunchResult`.
# JP: クラス `BrowserLaunchResult` を定義する。
class BrowserLaunchResult(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Result of launching a browser."""

	# TODO: add browser executable_path, pid, version, latency, user_data_dir, X11 $DISPLAY, host IP address, etc.
	# EN: Assign annotated value to cdp_url.
	# JP: cdp_url に型付きの値を代入する。
	cdp_url: str


# EN: Define class `BrowserLaunchEvent`.
# JP: クラス `BrowserLaunchEvent` を定義する。
class BrowserLaunchEvent(BaseEvent[BrowserLaunchResult]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Launch a local browser process."""

	# TODO: add executable_path, proxy settings, preferences, extra launch args, etc.

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_BrowserLaunchEvent', 30.0)  # seconds


# EN: Define class `BrowserKillEvent`.
# JP: クラス `BrowserKillEvent` を定義する。
class BrowserKillEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Kill local browser subprocess."""

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_BrowserKillEvent', 30.0)  # seconds


# TODO: replace all Runtime.evaluate() calls with this event
# class ExecuteJavaScriptEvent(BaseEvent):
# 	"""Execute JavaScript in page context."""

# 	target_id: TargetID
# 	expression: str
# 	await_promise: bool = True

# 	event_timeout: float | None = 60.0  # seconds

# TODO: add this and use the old BrowserProfile.viewport options to set it
# class SetViewportEvent(BaseEvent):
# 	"""Set the viewport size."""

# 	width: int
# 	height: int
# 	device_scale_factor: float = 1.0

# 	event_timeout: float | None = 15.0  # seconds


# Moved to storage state
# class SetCookiesEvent(BaseEvent):
# 	"""Set browser cookies."""

# 	cookies: list[dict[str, Any]]

# 	event_timeout: float | None = (
# 		30.0  # only long to support the edge case of restoring a big localStorage / on many origins (has to O(n) visit each origin to restore)
# 	)


# class GetCookiesEvent(BaseEvent):
# 	"""Get browser cookies."""

# 	urls: list[str] | None = None

# 	event_timeout: float | None = 30.0  # seconds


# ============================================================================
# DOM-related Events
# ============================================================================


# EN: Define class `BrowserConnectedEvent`.
# JP: クラス `BrowserConnectedEvent` を定義する。
class BrowserConnectedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Browser has started/connected."""

	# EN: Assign annotated value to cdp_url.
	# JP: cdp_url に型付きの値を代入する。
	cdp_url: str

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_BrowserConnectedEvent', 30.0)  # seconds


# EN: Define class `BrowserStoppedEvent`.
# JP: クラス `BrowserStoppedEvent` を定義する。
class BrowserStoppedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Browser has stopped/disconnected."""

	# EN: Assign annotated value to reason.
	# JP: reason に型付きの値を代入する。
	reason: str | None = None

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_BrowserStoppedEvent', 30.0)  # seconds


# EN: Define class `TabCreatedEvent`.
# JP: クラス `TabCreatedEvent` を定義する。
class TabCreatedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""A new tab was created."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_TabCreatedEvent', 30.0)  # seconds


# EN: Define class `TabClosedEvent`.
# JP: クラス `TabClosedEvent` を定義する。
class TabClosedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""A tab was closed."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID

	# TODO:
	# new_focus_target_id: int | None = None
	# new_focus_url: str | None = None

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_TabClosedEvent', 10.0)  # seconds


# TODO: emit this when DOM changes significantly, inner frame navigates, form submits, history.pushState(), etc.
# class TabUpdatedEvent(BaseEvent):
# 	"""Tab information updated (URL changed, etc.)."""

# 	target_id: TargetID
# 	url: str


# EN: Define class `AgentFocusChangedEvent`.
# JP: クラス `AgentFocusChangedEvent` を定義する。
class AgentFocusChangedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Agent focus changed to a different tab."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_AgentFocusChangedEvent', 10.0)  # seconds


# EN: Define class `TargetCrashedEvent`.
# JP: クラス `TargetCrashedEvent` を定義する。
class TargetCrashedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""A target has crashed."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID
	# EN: Assign annotated value to error.
	# JP: error に型付きの値を代入する。
	error: str

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_TargetCrashedEvent', 10.0)  # seconds


# EN: Define class `NavigationStartedEvent`.
# JP: クラス `NavigationStartedEvent` を定義する。
class NavigationStartedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Navigation started."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_NavigationStartedEvent', 30.0)  # seconds


# EN: Define class `NavigationCompleteEvent`.
# JP: クラス `NavigationCompleteEvent` を定義する。
class NavigationCompleteEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Navigation completed."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Assign annotated value to status.
	# JP: status に型付きの値を代入する。
	status: int | None = None
	# EN: Assign annotated value to error_message.
	# JP: error_message に型付きの値を代入する。
	error_message: str | None = None  # Error/timeout message if navigation had issues
	# EN: Assign annotated value to loading_status.
	# JP: loading_status に型付きの値を代入する。
	loading_status: str | None = None  # Detailed loading status (e.g., network timeout info)

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_NavigationCompleteEvent', 30.0)  # seconds


# ============================================================================
# Error Events
# ============================================================================


# EN: Define class `BrowserErrorEvent`.
# JP: クラス `BrowserErrorEvent` を定義する。
class BrowserErrorEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""An error occurred in the browser layer."""

	# EN: Assign annotated value to error_type.
	# JP: error_type に型付きの値を代入する。
	error_type: str
	# EN: Assign annotated value to message.
	# JP: message に型付きの値を代入する。
	message: str
	# EN: Assign annotated value to details.
	# JP: details に型付きの値を代入する。
	details: dict[str, Any] = Field(default_factory=dict)

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_BrowserErrorEvent', 30.0)  # seconds


# ============================================================================
# Storage State Events
# ============================================================================


# EN: Define class `SaveStorageStateEvent`.
# JP: クラス `SaveStorageStateEvent` を定義する。
class SaveStorageStateEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Request to save browser storage state."""

	# EN: Assign annotated value to path.
	# JP: path に型付きの値を代入する。
	path: str | None = None  # Optional path, uses profile default if not provided

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_SaveStorageStateEvent', 45.0)  # seconds


# EN: Define class `StorageStateSavedEvent`.
# JP: クラス `StorageStateSavedEvent` を定義する。
class StorageStateSavedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Notification that storage state was saved."""

	# EN: Assign annotated value to path.
	# JP: path に型付きの値を代入する。
	path: str
	# EN: Assign annotated value to cookies_count.
	# JP: cookies_count に型付きの値を代入する。
	cookies_count: int
	# EN: Assign annotated value to origins_count.
	# JP: origins_count に型付きの値を代入する。
	origins_count: int

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_StorageStateSavedEvent', 30.0)  # seconds


# EN: Define class `LoadStorageStateEvent`.
# JP: クラス `LoadStorageStateEvent` を定義する。
class LoadStorageStateEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Request to load browser storage state."""

	# EN: Assign annotated value to path.
	# JP: path に型付きの値を代入する。
	path: str | None = None  # Optional path, uses profile default if not provided

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_LoadStorageStateEvent', 45.0)  # seconds


# TODO: refactor this to:
# - on_BrowserConnectedEvent() -> dispatch(LoadStorageStateEvent()) -> _copy_storage_state_from_json_to_browser(json_file, new_cdp_session) + return storage_state from handler
# - on_BrowserStopEvent() -> dispatch(SaveStorageStateEvent()) -> _copy_storage_state_from_browser_to_json(new_cdp_session, json_file)
# and get rid of StorageStateSavedEvent and StorageStateLoadedEvent, have the original events + provide handler return values for any results
# EN: Define class `StorageStateLoadedEvent`.
# JP: クラス `StorageStateLoadedEvent` を定義する。
class StorageStateLoadedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Notification that storage state was loaded."""

	# EN: Assign annotated value to path.
	# JP: path に型付きの値を代入する。
	path: str
	# EN: Assign annotated value to cookies_count.
	# JP: cookies_count に型付きの値を代入する。
	cookies_count: int
	# EN: Assign annotated value to origins_count.
	# JP: origins_count に型付きの値を代入する。
	origins_count: int

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_StorageStateLoadedEvent', 30.0)  # seconds


# ============================================================================
# File Download Events
# ============================================================================


# EN: Define class `FileDownloadedEvent`.
# JP: クラス `FileDownloadedEvent` を定義する。
class FileDownloadedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""A file has been downloaded."""

	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Assign annotated value to path.
	# JP: path に型付きの値を代入する。
	path: str
	# EN: Assign annotated value to file_name.
	# JP: file_name に型付きの値を代入する。
	file_name: str
	# EN: Assign annotated value to file_size.
	# JP: file_size に型付きの値を代入する。
	file_size: int
	# EN: Assign annotated value to file_type.
	# JP: file_type に型付きの値を代入する。
	file_type: str | None = None  # e.g., 'pdf', 'zip', 'docx', etc.
	# EN: Assign annotated value to mime_type.
	# JP: mime_type に型付きの値を代入する。
	mime_type: str | None = None  # e.g., 'application/pdf'
	# EN: Assign annotated value to from_cache.
	# JP: from_cache に型付きの値を代入する。
	from_cache: bool = False
	# EN: Assign annotated value to auto_download.
	# JP: auto_download に型付きの値を代入する。
	auto_download: bool = False  # Whether this was an automatic download (e.g., PDF auto-download)

	# EN: Assign annotated value to event_timeout.
	# JP: event_timeout に型付きの値を代入する。
	event_timeout: float | None = _get_timeout('TIMEOUT_FileDownloadedEvent', 30.0)  # seconds


# EN: Define class `AboutBlankDVDScreensaverShownEvent`.
# JP: クラス `AboutBlankDVDScreensaverShownEvent` を定義する。
class AboutBlankDVDScreensaverShownEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""AboutBlankWatchdog has shown DVD screensaver animation on an about:blank tab."""

	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID
	# EN: Assign annotated value to error.
	# JP: error に型付きの値を代入する。
	error: str | None = None


# EN: Define class `DialogOpenedEvent`.
# JP: クラス `DialogOpenedEvent` を定義する。
class DialogOpenedEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Event dispatched when a JavaScript dialog is opened and handled."""

	# EN: Assign annotated value to dialog_type.
	# JP: dialog_type に型付きの値を代入する。
	dialog_type: str  # 'alert', 'confirm', 'prompt', or 'beforeunload'
	# EN: Assign annotated value to message.
	# JP: message に型付きの値を代入する。
	message: str
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Assign annotated value to frame_id.
	# JP: frame_id に型付きの値を代入する。
	frame_id: str | None = None  # Can be None when frameId is not provided by CDP
	# target_id: TargetID   # TODO: add this to avoid needing target_id_from_frame() later


# Note: Model rebuilding for forward references is handled in the importing modules
# Events with 'EnhancedDOMTreeNode' forward references (ClickElementEvent, TypeTextEvent,
# ScrollEvent, UploadFileEvent) need model_rebuild() called after imports are complete


# EN: Define function `_check_event_names_dont_overlap`.
# JP: 関数 `_check_event_names_dont_overlap` を定義する。
def _check_event_names_dont_overlap():
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	check that event names defined in this file are valid and non-overlapping
	(naiively n^2 so it's pretty slow but ok for now, optimize when >20 events)
	"""
	# EN: Assign value to event_names.
	# JP: event_names に値を代入する。
	event_names = {
		name.split('[')[0]
		for name in globals().keys()
		if not name.startswith('_')
		and inspect.isclass(globals()[name])
		and issubclass(globals()[name], BaseEvent)
		and name != 'BaseEvent'
	}
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for name_a in event_names:
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert name_a.endswith('Event'), f'Event with name {name_a} does not end with "Event"'
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for name_b in event_names:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if name_a != name_b:  # Skip self-comparison
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert name_a not in name_b, (
					f'Event with name {name_a} is a substring of {name_b}, all events must be completely unique to avoid find-and-replace accidents'
				)


# overlapping event names are a nightmare to trace and rename later, dont do it!
# e.g. prevent ClickEvent and FailedClickEvent are terrible names because one is a substring of the other,
# must be ClickEvent and ClickFailedEvent to preserve the usefulnes of codebase grep/sed/awk as refactoring tools.
# at import time, we do a quick check that all event names defined above are valid and non-overlapping.
# this is hand written in blood by a human! not LLM slop. feel free to optimize but do not remove it without a good reason.
# EN: Evaluate an expression.
# JP: 式を評価する。
_check_event_names_dont_overlap()

from dataclasses import dataclass, field
from typing import Any

from bubus import BaseEvent
from cdp_use.cdp.target import TargetID
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer

from browser_use.dom.views import DOMInteractedElement, SerializedDOMState

# Known placeholder image data for about:blank pages - a 4x4 white PNG
PLACEHOLDER_4PX_SCREENSHOT = (
	'iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAFElEQVR4nGP8//8/AwwwMSAB3BwAlm4DBfIlvvkAAAAASUVORK5CYII='
)


# Pydantic
# EN: Define class `TabInfo`.
# JP: クラス `TabInfo` を定義する。
class TabInfo(BaseModel):
	"""Represents information about a browser tab"""

	model_config = ConfigDict(
		extra='forbid',
		validate_by_name=True,
		validate_by_alias=True,
		populate_by_name=True,
	)

	# Original fields
	url: str
	title: str
	target_id: TargetID = Field(serialization_alias='tab_id', validation_alias=AliasChoices('tab_id', 'target_id'))
	parent_target_id: TargetID | None = Field(
		default=None, serialization_alias='parent_tab_id', validation_alias=AliasChoices('parent_tab_id', 'parent_target_id')
	)  # parent page that contains this popup or cross-origin iframe

	# EN: Define function `serialize_target_id`.
	# JP: 関数 `serialize_target_id` を定義する。
	@field_serializer('target_id')
	def serialize_target_id(self, target_id: TargetID, _info: Any) -> str:
		return target_id[-4:]

	# EN: Define function `serialize_parent_target_id`.
	# JP: 関数 `serialize_parent_target_id` を定義する。
	@field_serializer('parent_target_id')
	def serialize_parent_target_id(self, parent_target_id: TargetID | None, _info: Any) -> str | None:
		return parent_target_id[-4:] if parent_target_id else None


# EN: Define class `PageInfo`.
# JP: クラス `PageInfo` を定義する。
class PageInfo(BaseModel):
	"""Comprehensive page size and scroll information"""

	# Current viewport dimensions
	viewport_width: int
	viewport_height: int

	# Total page dimensions
	page_width: int
	page_height: int

	# Current scroll position
	scroll_x: int
	scroll_y: int

	# Calculated scroll information
	pixels_above: int
	pixels_below: int
	pixels_left: int
	pixels_right: int

	# Page statistics are now computed dynamically instead of stored


# EN: Define class `BrowserStateSummary`.
# JP: クラス `BrowserStateSummary` を定義する。
@dataclass
class BrowserStateSummary:
	"""The summary of the browser's current state designed for an LLM to process"""

	# provided by SerializedDOMState:
	dom_state: SerializedDOMState

	url: str
	title: str
	tabs: list[TabInfo]
	screenshot: str | None = field(default=None, repr=False)
	page_info: PageInfo | None = None  # Enhanced page information

	# Keep legacy fields for backward compatibility
	pixels_above: int = 0
	pixels_below: int = 0
	browser_errors: list[str] = field(default_factory=list)
	is_pdf_viewer: bool = False  # Whether the current page is a PDF viewer
	recent_events: str | None = None  # Text summary of recent browser events


# EN: Define class `BrowserStateHistory`.
# JP: クラス `BrowserStateHistory` を定義する。
@dataclass
class BrowserStateHistory:
	"""The summary of the browser's state at a past point in time to usse in LLM message history"""

	url: str
	title: str
	tabs: list[TabInfo]
	interacted_element: list[DOMInteractedElement | None] | list[None]
	screenshot_path: str | None = None

	# EN: Define function `get_screenshot`.
	# JP: 関数 `get_screenshot` を定義する。
	def get_screenshot(self) -> str | None:
		"""Load screenshot from disk and return as base64 string"""
		if not self.screenshot_path:
			return None

		import base64
		from pathlib import Path

		path_obj = Path(self.screenshot_path)
		if not path_obj.exists():
			return None

		try:
			with open(path_obj, 'rb') as f:
				screenshot_data = f.read()
			return base64.b64encode(screenshot_data).decode('utf-8')
		except Exception:
			return None

	# EN: Define function `to_dict`.
	# JP: 関数 `to_dict` を定義する。
	def to_dict(self) -> dict[str, Any]:
		data = {}
		data['tabs'] = [tab.model_dump() for tab in self.tabs]
		data['screenshot_path'] = self.screenshot_path
		data['interacted_element'] = [el.to_dict() if el else None for el in self.interacted_element]
		data['url'] = self.url
		data['title'] = self.title
		return data


# EN: Define class `BrowserError`.
# JP: クラス `BrowserError` を定義する。
class BrowserError(Exception):
	"""Browser error with structured memory for LLM context management.

	This exception class provides separate memory contexts for browser actions:
	- short_term_memory: Immediate context shown once to the LLM for the next action
	- long_term_memory: Persistent error information stored across steps
	"""

	message: str
	short_term_memory: str | None = None
	long_term_memory: str | None = None
	details: dict[str, Any] | None = None
	while_handling_event: BaseEvent[Any] | None = None

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		message: str,
		short_term_memory: str | None = None,
		long_term_memory: str | None = None,
		details: dict[str, Any] | None = None,
		event: BaseEvent[Any] | None = None,
	):
		"""Initialize a BrowserError with structured memory contexts.

		Args:
			message: Technical error message for logging and debugging
			short_term_memory: Context shown once to LLM (e.g., available actions, options)
			long_term_memory: Persistent error info stored in agent memory
			details: Additional metadata for debugging
			event: The browser event that triggered this error
		"""
		self.message = message
		self.short_term_memory = short_term_memory
		self.long_term_memory = long_term_memory
		self.details = details
		self.while_handling_event = event
		super().__init__(message)

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		if self.details:
			return f'{self.message} ({self.details}) during: {self.while_handling_event}'
		elif self.while_handling_event:
			return f'{self.message} (while handling: {self.while_handling_event})'
		else:
			return self.message


# EN: Define class `URLNotAllowedError`.
# JP: クラス `URLNotAllowedError` を定義する。
class URLNotAllowedError(BrowserError):
	"""Error raised when a URL is not allowed"""

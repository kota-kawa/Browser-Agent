# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass, field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.target import TargetID
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_serializer

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import DOMInteractedElement, SerializedDOMState

# Known placeholder image data for about:blank pages - a 4x4 white PNG
# EN: Assign value to PLACEHOLDER_4PX_SCREENSHOT.
# JP: PLACEHOLDER_4PX_SCREENSHOT に値を代入する。
PLACEHOLDER_4PX_SCREENSHOT = (
	'iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAFElEQVR4nGP8//8/AwwwMSAB3BwAlm4DBfIlvvkAAAAASUVORK5CYII='
)


# Pydantic
# EN: Define class `TabInfo`.
# JP: クラス `TabInfo` を定義する。
class TabInfo(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Represents information about a browser tab"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(
		extra='forbid',
		validate_by_name=True,
		validate_by_alias=True,
		populate_by_name=True,
	)

	# Original fields
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Assign annotated value to title.
	# JP: title に型付きの値を代入する。
	title: str
	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID = Field(serialization_alias='tab_id', validation_alias=AliasChoices('tab_id', 'target_id'))
	# EN: Assign annotated value to parent_target_id.
	# JP: parent_target_id に型付きの値を代入する。
	parent_target_id: TargetID | None = Field(
		default=None, serialization_alias='parent_tab_id', validation_alias=AliasChoices('parent_tab_id', 'parent_target_id')
	)  # parent page that contains this popup or cross-origin iframe

	# EN: Define function `serialize_target_id`.
	# JP: 関数 `serialize_target_id` を定義する。
	@field_serializer('target_id')
	def serialize_target_id(self, target_id: TargetID, _info: Any) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return target_id[-4:]

	# EN: Define function `serialize_parent_target_id`.
	# JP: 関数 `serialize_parent_target_id` を定義する。
	@field_serializer('parent_target_id')
	def serialize_parent_target_id(self, parent_target_id: TargetID | None, _info: Any) -> str | None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return parent_target_id[-4:] if parent_target_id else None


# EN: Define class `PageInfo`.
# JP: クラス `PageInfo` を定義する。
class PageInfo(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Comprehensive page size and scroll information"""

	# Current viewport dimensions
	# EN: Assign annotated value to viewport_width.
	# JP: viewport_width に型付きの値を代入する。
	viewport_width: int
	# EN: Assign annotated value to viewport_height.
	# JP: viewport_height に型付きの値を代入する。
	viewport_height: int

	# Total page dimensions
	# EN: Assign annotated value to page_width.
	# JP: page_width に型付きの値を代入する。
	page_width: int
	# EN: Assign annotated value to page_height.
	# JP: page_height に型付きの値を代入する。
	page_height: int

	# Current scroll position
	# EN: Assign annotated value to scroll_x.
	# JP: scroll_x に型付きの値を代入する。
	scroll_x: int
	# EN: Assign annotated value to scroll_y.
	# JP: scroll_y に型付きの値を代入する。
	scroll_y: int

	# Calculated scroll information
	# EN: Assign annotated value to pixels_above.
	# JP: pixels_above に型付きの値を代入する。
	pixels_above: int
	# EN: Assign annotated value to pixels_below.
	# JP: pixels_below に型付きの値を代入する。
	pixels_below: int
	# EN: Assign annotated value to pixels_left.
	# JP: pixels_left に型付きの値を代入する。
	pixels_left: int
	# EN: Assign annotated value to pixels_right.
	# JP: pixels_right に型付きの値を代入する。
	pixels_right: int

	# Page statistics are now computed dynamically instead of stored


# EN: Define class `BrowserStateSummary`.
# JP: クラス `BrowserStateSummary` を定義する。
@dataclass
class BrowserStateSummary:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The summary of the browser's current state designed for an LLM to process"""

	# provided by SerializedDOMState:
	# EN: Assign annotated value to dom_state.
	# JP: dom_state に型付きの値を代入する。
	dom_state: SerializedDOMState

	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Assign annotated value to title.
	# JP: title に型付きの値を代入する。
	title: str
	# EN: Assign annotated value to tabs.
	# JP: tabs に型付きの値を代入する。
	tabs: list[TabInfo]
	# EN: Assign annotated value to screenshot.
	# JP: screenshot に型付きの値を代入する。
	screenshot: str | None = field(default=None, repr=False)
	# EN: Assign annotated value to page_info.
	# JP: page_info に型付きの値を代入する。
	page_info: PageInfo | None = None  # Enhanced page information

	# Keep legacy fields for backward compatibility
	# EN: Assign annotated value to pixels_above.
	# JP: pixels_above に型付きの値を代入する。
	pixels_above: int = 0
	# EN: Assign annotated value to pixels_below.
	# JP: pixels_below に型付きの値を代入する。
	pixels_below: int = 0
	# EN: Assign annotated value to browser_errors.
	# JP: browser_errors に型付きの値を代入する。
	browser_errors: list[str] = field(default_factory=list)
	# EN: Assign annotated value to is_pdf_viewer.
	# JP: is_pdf_viewer に型付きの値を代入する。
	is_pdf_viewer: bool = False  # Whether the current page is a PDF viewer
	# EN: Assign annotated value to recent_events.
	# JP: recent_events に型付きの値を代入する。
	recent_events: str | None = None  # Text summary of recent browser events


# EN: Define class `BrowserStateHistory`.
# JP: クラス `BrowserStateHistory` を定義する。
@dataclass
class BrowserStateHistory:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""The summary of the browser's state at a past point in time to usse in LLM message history"""

	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Assign annotated value to title.
	# JP: title に型付きの値を代入する。
	title: str
	# EN: Assign annotated value to tabs.
	# JP: tabs に型付きの値を代入する。
	tabs: list[TabInfo]
	# EN: Assign annotated value to interacted_element.
	# JP: interacted_element に型付きの値を代入する。
	interacted_element: list[DOMInteractedElement | None] | list[None]
	# EN: Assign annotated value to screenshot_path.
	# JP: screenshot_path に型付きの値を代入する。
	screenshot_path: str | None = None

	# EN: Define function `get_screenshot`.
	# JP: 関数 `get_screenshot` を定義する。
	def get_screenshot(self) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load screenshot from disk and return as base64 string"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.screenshot_path:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import base64
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from pathlib import Path

		# EN: Assign value to path_obj.
		# JP: path_obj に値を代入する。
		path_obj = Path(self.screenshot_path)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not path_obj.exists():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with open(path_obj, 'rb') as f:
				# EN: Assign value to screenshot_data.
				# JP: screenshot_data に値を代入する。
				screenshot_data = f.read()
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return base64.b64encode(screenshot_data).decode('utf-8')
		except Exception:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

	# EN: Define function `to_dict`.
	# JP: 関数 `to_dict` を定義する。
	def to_dict(self) -> dict[str, Any]:
		# EN: Assign value to data.
		# JP: data に値を代入する。
		data = {}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		data['tabs'] = [tab.model_dump() for tab in self.tabs]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		data['screenshot_path'] = self.screenshot_path
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		data['interacted_element'] = [el.to_dict() if el else None for el in self.interacted_element]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		data['url'] = self.url
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		data['title'] = self.title
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return data


# EN: Define class `BrowserError`.
# JP: クラス `BrowserError` を定義する。
class BrowserError(Exception):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Browser error with structured memory for LLM context management.

	This exception class provides separate memory contexts for browser actions:
	- short_term_memory: Immediate context shown once to the LLM for the next action
	- long_term_memory: Persistent error information stored across steps
	"""

	# EN: Assign annotated value to message.
	# JP: message に型付きの値を代入する。
	message: str
	# EN: Assign annotated value to short_term_memory.
	# JP: short_term_memory に型付きの値を代入する。
	short_term_memory: str | None = None
	# EN: Assign annotated value to long_term_memory.
	# JP: long_term_memory に型付きの値を代入する。
	long_term_memory: str | None = None
	# EN: Assign annotated value to details.
	# JP: details に型付きの値を代入する。
	details: dict[str, Any] | None = None
	# EN: Assign annotated value to while_handling_event.
	# JP: while_handling_event に型付きの値を代入する。
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
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize a BrowserError with structured memory contexts.

		Args:
			message: Technical error message for logging and debugging
			short_term_memory: Context shown once to LLM (e.g., available actions, options)
			long_term_memory: Persistent error info stored in agent memory
			details: Additional metadata for debugging
			event: The browser event that triggered this error
		"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.message = message
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.short_term_memory = short_term_memory
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.long_term_memory = long_term_memory
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.details = details
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.while_handling_event = event
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__(message)

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.details:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'{self.message} ({self.details}) during: {self.while_handling_event}'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.while_handling_event:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'{self.message} (while handling: {self.while_handling_event})'
		else:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.message


# EN: Define class `URLNotAllowedError`.
# JP: クラス `URLNotAllowedError` を定義する。
class URLNotAllowedError(BrowserError):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Error raised when a URL is not allowed"""

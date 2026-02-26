# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""DOM watchdog for browser DOM tree management using CDP."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	BrowserErrorEvent,
	BrowserStateRequestEvent,
	ScreenshotEvent,
	TabCreatedEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.service import DomService
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import (
	EnhancedDOMTreeNode,
	SerializedDOMState,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe_debug
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import time_execution_async

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser.views import BrowserStateSummary, PageInfo


# EN: Define class `DOMWatchdog`.
# JP: クラス `DOMWatchdog` を定義する。
class DOMWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Handles DOM tree building, serialization, and element access via CDP.

	This watchdog acts as a bridge between the event-driven browser session
	and the DomService implementation, maintaining cached state and providing
	helper methods for other watchdogs.
	"""

	# EN: Assign value to LISTENS_TO.
	# JP: LISTENS_TO に値を代入する。
	LISTENS_TO = [TabCreatedEvent, BrowserStateRequestEvent]
	# EN: Assign value to EMITS.
	# JP: EMITS に値を代入する。
	EMITS = [BrowserErrorEvent]

	# Public properties for other watchdogs
	# EN: Assign annotated value to selector_map.
	# JP: selector_map に型付きの値を代入する。
	selector_map: dict[int, EnhancedDOMTreeNode] | None = None
	# EN: Assign annotated value to current_dom_state.
	# JP: current_dom_state に型付きの値を代入する。
	current_dom_state: SerializedDOMState | None = None
	# EN: Assign annotated value to enhanced_dom_tree.
	# JP: enhanced_dom_tree に型付きの値を代入する。
	enhanced_dom_tree: EnhancedDOMTreeNode | None = None

	# Internal DOM service
	# EN: Assign annotated value to _dom_service.
	# JP: _dom_service に型付きの値を代入する。
	_dom_service: DomService | None = None

	# EN: Define async function `on_TabCreatedEvent`.
	# JP: 非同期関数 `on_TabCreatedEvent` を定義する。
	async def on_TabCreatedEvent(self, event: TabCreatedEvent) -> None:
		# self.logger.debug('Setting up init scripts in browser')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `_get_recent_events_str`.
	# JP: 関数 `_get_recent_events_str` を定義する。
	def _get_recent_events_str(self, limit: int = 10) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the most recent events from the event bus as JSON.

		Args:
			limit: Maximum number of recent events to include

		Returns:
			JSON string of recent events or None if not available
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import json

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get all events from history, sorted by creation time (most recent first)
			# EN: Assign value to all_events.
			# JP: all_events に値を代入する。
			all_events = sorted(
				self.browser_session.event_bus.event_history.values(), key=lambda e: e.event_created_at.timestamp(), reverse=True
			)

			# Take the most recent events and create JSON-serializable data
			# EN: Assign value to recent_events_data.
			# JP: recent_events_data に値を代入する。
			recent_events_data = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for event in all_events[:limit]:
				# EN: Assign value to event_data.
				# JP: event_data に値を代入する。
				event_data = {
					'event_type': event.event_type,
					'timestamp': event.event_created_at.isoformat(),
				}
				# Add specific fields for certain event types
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(event, 'url'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					event_data['url'] = getattr(event, 'url')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(event, 'error_message'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					event_data['error_message'] = getattr(event, 'error_message')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(event, 'target_id'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					event_data['target_id'] = getattr(event, 'target_id')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				recent_events_data.append(event_data)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return json.dumps(recent_events_data)  # Return empty array if no events
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Failed to get recent events: {e}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return json.dumps([])  # Return empty JSON array on error

	# EN: Define async function `on_BrowserStateRequestEvent`.
	# JP: 非同期関数 `on_BrowserStateRequestEvent` を定義する。
	async def on_BrowserStateRequestEvent(self, event: BrowserStateRequestEvent) -> 'BrowserStateSummary':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle browser state request by coordinating DOM building and screenshot capture.

		This is the main entry point for getting the complete browser state.

		Args:
			event: The browser state request event with options

		Returns:
			Complete BrowserStateSummary with DOM, screenshot, and target info
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.views import BrowserStateSummary, PageInfo

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: STARTING browser state request')
		# EN: Assign value to page_url.
		# JP: page_url に値を代入する。
		page_url = await self.browser_session.get_current_page_url()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Got page URL: {page_url}')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session.agent_focus:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'Current page URL: {page_url}, target_id: {self.browser_session.agent_focus.target_id}, session_id: {self.browser_session.agent_focus.session_id}'
			)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Current page URL: {page_url}, no cdp_session attached')

		# check if we should skip DOM tree build for pointless pages
		# EN: Assign value to not_a_meaningful_website.
		# JP: not_a_meaningful_website に値を代入する。
		not_a_meaningful_website = page_url.lower().split(':', 1)[0] not in ('http', 'https')

		# Wait for page stability using browser profile settings (main branch pattern)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not not_a_meaningful_website:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: ⏳ Waiting for page stability...')
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._wait_for_stable_network()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: ✅ Page stability complete')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(
					f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Network waiting failed: {e}, continuing anyway...'
				)

		# Get tabs info once at the beginning for all paths
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: Getting tabs info...')
		# EN: Assign value to tabs_info.
		# JP: tabs_info に値を代入する。
		tabs_info = await self.browser_session.get_tabs()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Got {len(tabs_info)} tabs')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Tabs info: {tabs_info}')

		# Get viewport / scroll position info, remember changing scroll position should invalidate selector_map cache because it only includes visible elements
		# cdp_session = await self.browser_session.get_or_create_cdp_session(focus=True)
		# scroll_info = await cdp_session.cdp_client.send.Runtime.evaluate(
		# 	params={'expression': 'JSON.stringify({y: document.body.scrollTop, x: document.body.scrollLeft, width: document.documentElement.clientWidth, height: document.documentElement.clientHeight})'},
		# 	session_id=cdp_session.session_id,
		# )
		# self.logger.debug(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Got scroll info: {scroll_info["result"]}')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Fast path for empty pages
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not_a_meaningful_website:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'⚡ Skipping BuildDOMTree for empty target: {page_url}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'📸 Not taking screenshot for empty page: {page_url} (non-http/https URL)')

				# Create minimal DOM state
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = SerializedDOMState(_root=None, selector_map={})

				# Skip screenshot for empty pages
				# EN: Assign value to screenshot_b64.
				# JP: screenshot_b64 に値を代入する。
				screenshot_b64 = None

				# Try to get page info from CDP, fall back to defaults if unavailable
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to page_info.
					# JP: page_info に値を代入する。
					page_info = await self._get_page_info()
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Failed to get page info from CDP for empty page: {e}, using fallback')
					# Use default viewport dimensions
					# EN: Assign value to viewport.
					# JP: viewport に値を代入する。
					viewport = self.browser_session.browser_profile.viewport or {'width': 1280, 'height': 720}
					# EN: Assign value to page_info.
					# JP: page_info に値を代入する。
					page_info = PageInfo(
						viewport_width=viewport['width'],
						viewport_height=viewport['height'],
						page_width=viewport['width'],
						page_height=viewport['height'],
						scroll_x=0,
						scroll_y=0,
						pixels_above=0,
						pixels_below=0,
						pixels_left=0,
						pixels_right=0,
					)

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return BrowserStateSummary(
					dom_state=content,
					url=page_url,
					title='Empty Tab',
					tabs=tabs_info,
					screenshot=screenshot_b64,
					page_info=page_info,
					pixels_above=0,
					pixels_below=0,
					browser_errors=[],
					is_pdf_viewer=False,
					recent_events=self._get_recent_events_str() if event.include_recent_events else None,
				)

			# Execute DOM building and screenshot capture in parallel
			# EN: Assign value to dom_task.
			# JP: dom_task に値を代入する。
			dom_task = None
			# EN: Assign value to screenshot_task.
			# JP: screenshot_task に値を代入する。
			screenshot_task = None

			# Start DOM building task if requested
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if event.include_dom:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: 🌳 Starting DOM tree build task...')

				# EN: Assign value to previous_state.
				# JP: previous_state に値を代入する。
				previous_state = (
					self.browser_session._cached_browser_state_summary.dom_state
					if self.browser_session._cached_browser_state_summary
					else None
				)

				# EN: Assign value to dom_task.
				# JP: dom_task に値を代入する。
				dom_task = asyncio.create_task(self._build_dom_tree_without_highlights(previous_state))

			# Start clean screenshot task if requested (without JS highlights)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if event.include_screenshot:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: 📸 Starting clean screenshot task...')
				# EN: Assign value to screenshot_task.
				# JP: screenshot_task に値を代入する。
				screenshot_task = asyncio.create_task(self._capture_clean_screenshot())

			# Wait for both tasks to complete
			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = None
			# EN: Assign value to screenshot_b64.
			# JP: screenshot_b64 に値を代入する。
			screenshot_b64 = None

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if dom_task:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to content.
					# JP: content に値を代入する。
					content = await dom_task
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: ✅ DOM tree build completed')
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: DOM build failed: {e}, using minimal state')
					# EN: Assign value to content.
					# JP: content に値を代入する。
					content = SerializedDOMState(_root=None, selector_map={})
			else:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = SerializedDOMState(_root=None, selector_map={})

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if screenshot_task:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to screenshot_b64.
					# JP: screenshot_b64 に値を代入する。
					screenshot_b64 = await screenshot_task
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: ✅ Clean screenshot captured')
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Clean screenshot failed: {e}')
					# EN: Assign value to screenshot_b64.
					# JP: screenshot_b64 に値を代入する。
					screenshot_b64 = None

			# Apply Python-based highlighting if both DOM and screenshot are available
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if screenshot_b64 and content and content.selector_map and self.browser_session.browser_profile.highlight_elements:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: 🎨 Applying Python-based highlighting...')
					# EN: Import required modules.
					# JP: 必要なモジュールをインポートする。
					from browser_use.browser.python_highlights import create_highlighted_screenshot_async

					# Get CDP session for viewport info
					# EN: Assign value to cdp_session.
					# JP: cdp_session に値を代入する。
					cdp_session = await self.browser_session.get_or_create_cdp_session()
					# EN: Assign value to start.
					# JP: start に値を代入する。
					start = time.time()
					# EN: Assign value to screenshot_b64.
					# JP: screenshot_b64 に値を代入する。
					screenshot_b64 = await create_highlighted_screenshot_async(
						screenshot_b64,
						content.selector_map,
						cdp_session,
						self.browser_session.browser_profile.filter_highlight_ids,
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: ✅ Applied highlights to {len(content.selector_map)} elements in {time.time() - start:.2f}s'
					)
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Python highlighting failed: {e}')

			# Ensure we have valid content
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not content:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = SerializedDOMState(_root=None, selector_map={})

			# Tabs info already fetched at the beginning

			# Get target title safely
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: Getting page title...')
				# EN: Assign value to title.
				# JP: title に値を代入する。
				title = await asyncio.wait_for(self.browser_session.get_current_page_title(), timeout=1.0)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Got title: {title}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Failed to get title: {e}')
				# EN: Assign value to title.
				# JP: title に値を代入する。
				title = 'Page'

			# Get comprehensive page info from CDP with timeout
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: Getting page info from CDP...')
				# EN: Assign value to page_info.
				# JP: page_info に値を代入する。
				page_info = await asyncio.wait_for(self._get_page_info(), timeout=1.0)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Got page info from CDP: {page_info}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: Failed to get page info from CDP: {e}, using fallback'
				)
				# Fallback to default viewport dimensions
				# EN: Assign value to viewport.
				# JP: viewport に値を代入する。
				viewport = self.browser_session.browser_profile.viewport or {'width': 1280, 'height': 720}
				# EN: Assign value to page_info.
				# JP: page_info に値を代入する。
				page_info = PageInfo(
					viewport_width=viewport['width'],
					viewport_height=viewport['height'],
					page_width=viewport['width'],
					page_height=viewport['height'],
					scroll_x=0,
					scroll_y=0,
					pixels_above=0,
					pixels_below=0,
					pixels_left=0,
					pixels_right=0,
				)

			# Check for PDF viewer
			# EN: Assign value to is_pdf_viewer.
			# JP: is_pdf_viewer に値を代入する。
			is_pdf_viewer = page_url.endswith('.pdf') or '/pdf/' in page_url

			# Build and cache the browser state summary
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if screenshot_b64:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'🔍 DOMWatchdog.on_BrowserStateRequestEvent: 📸 Creating BrowserStateSummary with screenshot, length: {len(screenshot_b64)}'
				)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					'🔍 DOMWatchdog.on_BrowserStateRequestEvent: 📸 Creating BrowserStateSummary WITHOUT screenshot'
				)

			# EN: Assign value to browser_state.
			# JP: browser_state に値を代入する。
			browser_state = BrowserStateSummary(
				dom_state=content,
				url=page_url,
				title=title,
				tabs=tabs_info,
				screenshot=screenshot_b64,
				page_info=page_info,
				pixels_above=0,
				pixels_below=0,
				browser_errors=[],
				is_pdf_viewer=is_pdf_viewer,
				recent_events=self._get_recent_events_str() if event.include_recent_events else None,
			)

			# Cache the state
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.browser_session._cached_browser_state_summary = browser_state

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔍 DOMWatchdog.on_BrowserStateRequestEvent: ✅ COMPLETED - Returning browser state')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return browser_state

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'Failed to get browser state: {e}')

			# Return minimal recovery state
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return BrowserStateSummary(
				dom_state=SerializedDOMState(_root=None, selector_map={}),
				url=page_url if 'page_url' in locals() else '',
				title='Error',
				tabs=[],
				screenshot=None,
				page_info=PageInfo(
					viewport_width=1280,
					viewport_height=720,
					page_width=1280,
					page_height=720,
					scroll_x=0,
					scroll_y=0,
					pixels_above=0,
					pixels_below=0,
					pixels_left=0,
					pixels_right=0,
				),
				pixels_above=0,
				pixels_below=0,
				browser_errors=[str(e)],
				is_pdf_viewer=False,
				recent_events=None,
			)

	# EN: Define async function `_build_dom_tree_without_highlights`.
	# JP: 非同期関数 `_build_dom_tree_without_highlights` を定義する。
	@time_execution_async('build_dom_tree_without_highlights')
	@observe_debug(ignore_input=True, ignore_output=True, name='build_dom_tree_without_highlights')
	async def _build_dom_tree_without_highlights(self, previous_state: SerializedDOMState | None = None) -> SerializedDOMState:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Build DOM tree without injecting JavaScript highlights (for parallel execution)."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔍 DOMWatchdog._build_dom_tree_without_highlights: STARTING DOM tree build')

			# Create or reuse DOM service
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._dom_service is None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._dom_service = DomService(
					browser_session=self.browser_session,
					logger=self.logger,
					cross_origin_iframes=self.browser_session.browser_profile.cross_origin_iframes,
					paint_order_filtering=self.browser_session.browser_profile.paint_order_filtering,
					max_iframes=self.browser_session.browser_profile.max_iframes,
					max_iframe_depth=self.browser_session.browser_profile.max_iframe_depth,
				)

			# Get serialized DOM tree using the service
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔍 DOMWatchdog._build_dom_tree_without_highlights: Calling DomService.get_serialized_dom_tree...')
			# EN: Assign value to start.
			# JP: start に値を代入する。
			start = time.time()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.current_dom_state, self.enhanced_dom_tree, timing_info = await self._dom_service.get_serialized_dom_tree(
				previous_cached_state=previous_state,
			)
			# EN: Assign value to end.
			# JP: end に値を代入する。
			end = time.time()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				'🔍 DOMWatchdog._build_dom_tree_without_highlights: ✅ DomService.get_serialized_dom_tree completed'
			)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Time taken to get DOM tree: {end - start} seconds')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Timing breakdown: {timing_info}')

			# Update selector map for other watchdogs
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔍 DOMWatchdog._build_dom_tree_without_highlights: Updating selector maps...')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.selector_map = self.current_dom_state.selector_map
			# Update BrowserSession's cached selector map
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.browser_session.update_cached_selector_map(self.selector_map)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'🔍 DOMWatchdog._build_dom_tree_without_highlights: ✅ Selector maps updated, {len(self.selector_map)} elements'
			)

			# Skip JavaScript highlighting injection - Python highlighting will be applied later
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔍 DOMWatchdog._build_dom_tree_without_highlights: ✅ COMPLETED DOM tree build (no JS highlights)')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.current_dom_state

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'Failed to build DOM tree without highlights: {e}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='DOMBuildFailed',
					message=str(e),
				)
			)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `_capture_clean_screenshot`.
	# JP: 非同期関数 `_capture_clean_screenshot` を定義する。
	@time_execution_async('capture_clean_screenshot')
	@observe_debug(ignore_input=True, ignore_output=True, name='capture_clean_screenshot')
	async def _capture_clean_screenshot(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Capture a clean screenshot without JavaScript highlights."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔍 DOMWatchdog._capture_clean_screenshot: Capturing clean screenshot...')

			# Ensure we have a focused CDP session
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.browser_session.agent_focus is not None, 'No current target ID'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.browser_session.get_or_create_cdp_session(target_id=self.browser_session.agent_focus.target_id, focus=True)

			# Check if handler is registered
			# EN: Assign value to handlers.
			# JP: handlers に値を代入する。
			handlers = self.event_bus.handlers.get('ScreenshotEvent', [])
			# EN: Assign value to handler_names.
			# JP: handler_names に値を代入する。
			handler_names = [getattr(h, '__name__', str(h)) for h in handlers]
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📸 ScreenshotEvent handlers registered: {len(handlers)} - {handler_names}')

			# EN: Assign value to screenshot_event.
			# JP: screenshot_event に値を代入する。
			screenshot_event = self.event_bus.dispatch(ScreenshotEvent(full_page=False))
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('📸 Dispatched ScreenshotEvent, waiting for event to complete...')

			# Wait for the event itself to complete (this waits for all handlers)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await screenshot_event

			# Get the single handler result
			# EN: Assign value to screenshot_b64.
			# JP: screenshot_b64 に値を代入する。
			screenshot_b64 = await screenshot_event.event_result(raise_if_any=True, raise_if_none=True)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if screenshot_b64 is None:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError('Screenshot handler returned None')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🔍 DOMWatchdog._capture_clean_screenshot: ✅ Clean screenshot captured successfully')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str(screenshot_b64)

		except TimeoutError:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('📸 Clean screenshot timed out after 6 seconds - no handler registered or slow page?')
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'📸 Clean screenshot failed: {type(e).__name__}: {e}')
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `_wait_for_stable_network`.
	# JP: 非同期関数 `_wait_for_stable_network` を定義する。
	async def _wait_for_stable_network(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Wait for page stability - simplified for CDP-only branch."""
		# EN: Assign value to start_time.
		# JP: start_time に値を代入する。
		start_time = time.time()

		# Apply minimum wait time first (let page settle)
		# EN: Assign value to min_wait.
		# JP: min_wait に値を代入する。
		min_wait = self.browser_session.browser_profile.minimum_wait_page_load_time
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if min_wait > 0:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'⏳ Minimum wait: {min_wait}s')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(min_wait)

		# Apply network idle wait time (for dynamic content like iframes)
		# EN: Assign value to network_idle_wait.
		# JP: network_idle_wait に値を代入する。
		network_idle_wait = self.browser_session.browser_profile.wait_for_network_idle_page_load_time
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if network_idle_wait > 0:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'⏳ Network idle wait: {network_idle_wait}s')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(network_idle_wait)

		# EN: Assign value to elapsed.
		# JP: elapsed に値を代入する。
		elapsed = time.time() - start_time
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'✅ Page stability wait completed in {elapsed:.2f}s')

	# EN: Define async function `_get_page_info`.
	# JP: 非同期関数 `_get_page_info` を定義する。
	async def _get_page_info(self) -> 'PageInfo':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get comprehensive page information using a single CDP call.

		TODO: should we make this an event as well?

		Returns:
			PageInfo with all viewport, page dimensions, and scroll information
		"""

		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.browser.views import PageInfo

		# Get CDP session for the current target
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session.agent_focus:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError('No active CDP session - browser may not be connected yet')

		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.browser_session.get_or_create_cdp_session(
			target_id=self.browser_session.agent_focus.target_id, focus=True
		)

		# Get layout metrics which includes all the information we need
		# EN: Assign value to metrics.
		# JP: metrics に値を代入する。
		metrics = await asyncio.wait_for(
			cdp_session.cdp_client.send.Page.getLayoutMetrics(session_id=cdp_session.session_id), timeout=10.0
		)

		# Extract different viewport types
		# EN: Assign value to layout_viewport.
		# JP: layout_viewport に値を代入する。
		layout_viewport = metrics.get('layoutViewport', {})
		# EN: Assign value to visual_viewport.
		# JP: visual_viewport に値を代入する。
		visual_viewport = metrics.get('visualViewport', {})
		# EN: Assign value to css_visual_viewport.
		# JP: css_visual_viewport に値を代入する。
		css_visual_viewport = metrics.get('cssVisualViewport', {})
		# EN: Assign value to css_layout_viewport.
		# JP: css_layout_viewport に値を代入する。
		css_layout_viewport = metrics.get('cssLayoutViewport', {})
		# EN: Assign value to content_size.
		# JP: content_size に値を代入する。
		content_size = metrics.get('contentSize', {})

		# Calculate device pixel ratio to convert between device pixels and CSS pixels
		# This matches the approach in dom/service.py _get_viewport_ratio method
		# EN: Assign value to css_width.
		# JP: css_width に値を代入する。
		css_width = css_visual_viewport.get('clientWidth', css_layout_viewport.get('clientWidth', 1280.0))
		# EN: Assign value to device_width.
		# JP: device_width に値を代入する。
		device_width = visual_viewport.get('clientWidth', css_width)
		# EN: Assign value to device_pixel_ratio.
		# JP: device_pixel_ratio に値を代入する。
		device_pixel_ratio = device_width / css_width if css_width > 0 else 1.0

		# For viewport dimensions, use CSS pixels (what JavaScript sees)
		# Prioritize CSS layout viewport, then fall back to layout viewport
		# EN: Assign value to viewport_width.
		# JP: viewport_width に値を代入する。
		viewport_width = int(css_layout_viewport.get('clientWidth') or layout_viewport.get('clientWidth', 1280))
		# EN: Assign value to viewport_height.
		# JP: viewport_height に値を代入する。
		viewport_height = int(css_layout_viewport.get('clientHeight') or layout_viewport.get('clientHeight', 720))

		# For total page dimensions, content size is typically in device pixels, so convert to CSS pixels
		# by dividing by device pixel ratio
		# EN: Assign value to raw_page_width.
		# JP: raw_page_width に値を代入する。
		raw_page_width = content_size.get('width', viewport_width * device_pixel_ratio)
		# EN: Assign value to raw_page_height.
		# JP: raw_page_height に値を代入する。
		raw_page_height = content_size.get('height', viewport_height * device_pixel_ratio)
		# EN: Assign value to page_width.
		# JP: page_width に値を代入する。
		page_width = int(raw_page_width / device_pixel_ratio)
		# EN: Assign value to page_height.
		# JP: page_height に値を代入する。
		page_height = int(raw_page_height / device_pixel_ratio)

		# For scroll position, use CSS visual viewport if available, otherwise CSS layout viewport
		# These should already be in CSS pixels
		# EN: Assign value to scroll_x.
		# JP: scroll_x に値を代入する。
		scroll_x = int(css_visual_viewport.get('pageX') or css_layout_viewport.get('pageX', 0))
		# EN: Assign value to scroll_y.
		# JP: scroll_y に値を代入する。
		scroll_y = int(css_visual_viewport.get('pageY') or css_layout_viewport.get('pageY', 0))

		# Calculate scroll information - pixels that are above/below/left/right of current viewport
		# EN: Assign value to pixels_above.
		# JP: pixels_above に値を代入する。
		pixels_above = scroll_y
		# EN: Assign value to pixels_below.
		# JP: pixels_below に値を代入する。
		pixels_below = max(0, page_height - viewport_height - scroll_y)
		# EN: Assign value to pixels_left.
		# JP: pixels_left に値を代入する。
		pixels_left = scroll_x
		# EN: Assign value to pixels_right.
		# JP: pixels_right に値を代入する。
		pixels_right = max(0, page_width - viewport_width - scroll_x)

		# EN: Assign value to page_info.
		# JP: page_info に値を代入する。
		page_info = PageInfo(
			viewport_width=viewport_width,
			viewport_height=viewport_height,
			page_width=page_width,
			page_height=page_height,
			scroll_x=scroll_x,
			scroll_y=scroll_y,
			pixels_above=pixels_above,
			pixels_below=pixels_below,
			pixels_left=pixels_left,
			pixels_right=pixels_right,
		)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return page_info

	# ========== Public Helper Methods ==========

	# EN: Define async function `get_element_by_index`.
	# JP: 非同期関数 `get_element_by_index` を定義する。
	async def get_element_by_index(self, index: int) -> EnhancedDOMTreeNode | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get DOM element by index from cached selector map.

		Builds DOM if not cached.

		Returns:
			EnhancedDOMTreeNode or None if index not found
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.selector_map:
			# Build DOM if not cached
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._build_dom_tree_without_highlights()

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.selector_map.get(index) if self.selector_map else None

	# EN: Define function `clear_cache`.
	# JP: 関数 `clear_cache` を定義する。
	def clear_cache(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear cached DOM state to force rebuild on next access."""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.selector_map = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.current_dom_state = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.enhanced_dom_tree = None
		# Keep the DOM service instance to reuse its CDP client connection

	# EN: Define function `is_file_input`.
	# JP: 関数 `is_file_input` を定義する。
	def is_file_input(self, element: EnhancedDOMTreeNode) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if element is a file input."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return element.node_name.upper() == 'INPUT' and element.attributes.get('type', '').lower() == 'file'

	# EN: Define function `is_element_visible_according_to_all_parents`.
	# JP: 関数 `is_element_visible_according_to_all_parents` を定義する。
	@staticmethod
	def is_element_visible_according_to_all_parents(node: EnhancedDOMTreeNode, html_frames: list[EnhancedDOMTreeNode]) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the element is visible according to all its parent HTML frames.

		Delegates to the DomService static method.
		"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return DomService.is_element_visible_according_to_all_parents(node, html_frames)

	# EN: Define async function `__aexit__`.
	# JP: 非同期関数 `__aexit__` を定義する。
	async def __aexit__(self, exc_type, exc_value, traceback):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clean up DOM service on exit."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._dom_service:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._dom_service.__aexit__(exc_type, exc_value, traceback)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._dom_service = None

	# EN: Define function `__del__`.
	# JP: 関数 `__del__` を定義する。
	def __del__(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clean up DOM service on deletion."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__del__()
		# DOM service will clean up its own CDP client
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._dom_service = None

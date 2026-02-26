# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import enum
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
from typing import Any, Generic, TypeVar

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from lmnr import Laminar  # type: ignore
except ImportError:
	# EN: Assign value to Laminar.
	# JP: Laminar に値を代入する。
	Laminar = None  # type: ignore
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.scratchpad import Scratchpad
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import ActionModel, ActionResult
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser import BrowserSession
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	ClickElementEvent,
	CloseTabEvent,
	GetDropdownOptionsEvent,
	GoBackEvent,
	NavigateToUrlEvent,
	ScrollEvent,
	ScrollToTextEvent,
	SendKeysEvent,
	SwitchTabEvent,
	TypeTextEvent,
	UploadFileEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.service import EnhancedDOMTreeNode
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystem
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import SystemMessage, UserMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe_debug
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.registry.service import Registry
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.views import (
	ClickElementAction,
	CloseTabAction,
	DoneAction,
	GetDropdownOptionsAction,
	GoToUrlAction,
	InputTextAction,
	NoParamsAction,
	ScratchpadAddAction,
	ScratchpadClearAction,
	ScratchpadGetAction,
	ScratchpadRemoveAction,
	ScratchpadUpdateAction,
	ScrollAction,
	SearchGoogleAction,
	SelectDropdownOptionAction,
	SendKeysAction,
	StructuredOutputAction,
	SwitchTabAction,
	UploadFileAction,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import _log_pretty_url, time_execution_sync

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)

# Import EnhancedDOMTreeNode and rebuild event models that have forward references to it
# This must be done after all imports are complete
# EN: Evaluate an expression.
# JP: 式を評価する。
ClickElementEvent.model_rebuild()
# EN: Evaluate an expression.
# JP: 式を評価する。
TypeTextEvent.model_rebuild()
# EN: Evaluate an expression.
# JP: 式を評価する。
ScrollEvent.model_rebuild()
# EN: Evaluate an expression.
# JP: 式を評価する。
UploadFileEvent.model_rebuild()

# EN: Assign value to Context.
# JP: Context に値を代入する。
Context = TypeVar('Context')

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define function `_detect_sensitive_key_name`.
# JP: 関数 `_detect_sensitive_key_name` を定義する。
def _detect_sensitive_key_name(text: str, sensitive_data: dict[str, str | dict[str, str]] | None) -> str | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Detect which sensitive key name corresponds to the given text value."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not sensitive_data or not text:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# Collect all sensitive values and their keys
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for domain_or_key, content in sensitive_data.items():
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(content, dict):
			# New format: {domain: {key: value}}
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for key, value in content.items():
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if value and value == text:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif content:  # Old format: {key: value}
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if content == text:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return domain_or_key

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define function `handle_browser_error`.
# JP: 関数 `handle_browser_error` を定義する。
def handle_browser_error(e: BrowserError) -> ActionResult:
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if e.long_term_memory is not None:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if e.short_term_memory is not None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=e.short_term_memory, error=e.long_term_memory, include_extracted_content_only_once=True
			)
		else:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(error=e.long_term_memory)
	# Fallback to original error handling if long_term_memory is None
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.warning(
		'⚠️ A BrowserError was raised without long_term_memory - always set long_term_memory when raising BrowserError to propagate right messages to LLM.'
	)
	# EN: Raise an exception.
	# JP: 例外を送出する。
	raise e


# EN: Define class `Tools`.
# JP: クラス `Tools` を定義する。
class Tools(Generic[Context]):
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		exclude_actions: list[str] = [],
		output_model: type[T] | None = None,
		display_files_in_done_text: bool = True,
	):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.registry = Registry[Context](exclude_actions)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.display_files_in_done_text = display_files_in_done_text

		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Register all default browser actions"""

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._register_scratchpad_actions()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._register_done_action(output_model)

		# Basic Navigation Actions
		# EN: Define async function `search_google`.
		# JP: 非同期関数 `search_google` を定義する。
		@self.registry.action(
			'Search the query in Google, the query should be a search query like humans search in Google, concrete and not vague or super long.',
			param_model=SearchGoogleAction,
		)
		async def search_google(params: SearchGoogleAction, browser_session: BrowserSession):
			# EN: Assign value to search_url.
			# JP: search_url に値を代入する。
			search_url = f'https://www.google.com/search?q={params.query}&udm=14'

			# Check if there's already a tab open on Google or agent's about:blank
			# EN: Assign value to use_new_tab.
			# JP: use_new_tab に値を代入する。
			use_new_tab = True
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to tabs.
				# JP: tabs に値を代入する。
				tabs = await browser_session.get_tabs()
				# Get last 4 chars of browser session ID to identify agent's tabs
				# EN: Assign value to browser_session_label.
				# JP: browser_session_label に値を代入する。
				browser_session_label = str(browser_session.id)[-4:]
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Checking {len(tabs)} tabs for reusable tab (browser_session_label: {browser_session_label})')

				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for i, tab in enumerate(tabs):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug(f'Tab {i}: url="{tab.url}", title="{tab.title}"')
					# Check if tab is on Google domain
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if tab.url and tab.url.strip('/').lower() in ('https://www.google.com', 'https://google.com'):
						# Found existing Google tab, navigate in it
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.debug(f'Found existing Google tab at index {i}: {tab.url}, reusing it')

						# Switch to this tab first if it's not the current one
						# EN: Import required modules.
						# JP: 必要なモジュールをインポートする。
						from browser_use.browser.events import SwitchTabEvent

						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if browser_session.agent_focus and tab.target_id != browser_session.agent_focus.target_id:
							# EN: Handle exceptions around this block.
							# JP: このブロックで例外処理を行う。
							try:
								# EN: Assign value to switch_event.
								# JP: switch_event に値を代入する。
								switch_event = browser_session.event_bus.dispatch(SwitchTabEvent(target_id=tab.target_id))
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								await switch_event
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								await switch_event.event_result(raise_if_none=False)
							except Exception as e:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								logger.warning(f'Failed to switch to existing Google tab: {e}, will use new tab')
								# EN: Continue to the next loop iteration.
								# JP: ループの次の反復に進む。
								continue

						# EN: Assign value to use_new_tab.
						# JP: use_new_tab に値を代入する。
						use_new_tab = False
						# EN: Exit the current loop.
						# JP: 現在のループを終了する。
						break
					# Check if it's an agent-owned about:blank page (has "Starting agent XXXX..." title)
					# IMPORTANT: about:blank is also used briefly for new tabs the agent is trying to open, dont take over those!
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif tab.url == 'about:blank' and tab.title:
						# Check if this is our agent's about:blank page with DVD animation
						# The title should be "Starting agent XXXX..." where XXXX is the browser_session_label
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if browser_session_label in tab.title:
							# This is our agent's about:blank page
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							logger.debug(f'Found agent-owned about:blank tab at index {i} with title: "{tab.title}", reusing it')

							# Switch to this tab first
							# EN: Import required modules.
							# JP: 必要なモジュールをインポートする。
							from browser_use.browser.events import SwitchTabEvent

							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if browser_session.agent_focus and tab.target_id != browser_session.agent_focus.target_id:
								# EN: Handle exceptions around this block.
								# JP: このブロックで例外処理を行う。
								try:
									# EN: Assign value to switch_event.
									# JP: switch_event に値を代入する。
									switch_event = browser_session.event_bus.dispatch(SwitchTabEvent(target_id=tab.target_id))
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									await switch_event
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									await switch_event.event_result()
								except Exception as e:
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									logger.warning(f'Failed to switch to agent-owned tab: {e}, will use new tab')
									# EN: Continue to the next loop iteration.
									# JP: ループの次の反復に進む。
									continue

							# EN: Assign value to use_new_tab.
							# JP: use_new_tab に値を代入する。
							use_new_tab = False
							# EN: Exit the current loop.
							# JP: 現在のループを終了する。
							break
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Could not check for existing tabs: {e}, using new tab')

			# Dispatch navigation event
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(
					NavigateToUrlEvent(
						url=search_url,
						new_tab=use_new_tab,
					)
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event.event_result(raise_if_any=True, raise_if_none=False)
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = f"Searched Google for '{params.query}'"
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'🔍  {memory}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=memory, long_term_memory=memory)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to search Google: {e}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=f'Failed to search Google for "{params.query}": {str(e)}')

		# EN: Define async function `go_to_url`.
		# JP: 非同期関数 `go_to_url` を定義する。
		@self.registry.action(
			'Navigate to URL, set new_tab=True to open in new tab, False to navigate in current tab', param_model=GoToUrlAction
		)
		async def go_to_url(params: GoToUrlAction, browser_session: BrowserSession):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Dispatch navigation event
				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=params.url, new_tab=params.new_tab))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event.event_result(raise_if_any=True, raise_if_none=False)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if params.new_tab:
					# EN: Assign value to memory.
					# JP: memory に値を代入する。
					memory = f'Opened new tab with URL {params.url}'
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f'🔗  Opened new tab with url {params.url}'
				else:
					# EN: Assign value to memory.
					# JP: memory に値を代入する。
					memory = f'Navigated to {params.url}'
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f'🔗 {memory}'

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=msg, long_term_memory=memory)
			except Exception as e:
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = str(e)
				# Always log the actual error first for debugging
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				browser_session.logger.error(f'❌ Navigation failed: {error_msg}')

				# Check if it's specifically a RuntimeError about CDP client
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(e, RuntimeError) and 'CDP client not initialized' in error_msg:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					browser_session.logger.error('❌ Browser connection failed - CDP client not properly initialized')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=f'Browser connection error: {error_msg}')
				# Check for network-related errors
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif any(
					err in error_msg
					for err in [
						'ERR_NAME_NOT_RESOLVED',
						'ERR_INTERNET_DISCONNECTED',
						'ERR_CONNECTION_REFUSED',
						'ERR_TIMED_OUT',
						'net::',
					]
				):
					# EN: Assign value to site_unavailable_msg.
					# JP: site_unavailable_msg に値を代入する。
					site_unavailable_msg = f'Navigation failed - site unavailable: {params.url}'
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					browser_session.logger.warning(f'⚠️ {site_unavailable_msg} - {error_msg}')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=site_unavailable_msg)
				else:
					# Return error in ActionResult instead of re-raising
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=f'Navigation failed: {str(e)}')

		# EN: Define async function `go_back`.
		# JP: 非同期関数 `go_back` を定義する。
		@self.registry.action('Go back', param_model=NoParamsAction)
		async def go_back(_: NoParamsAction, browser_session: BrowserSession):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(GoBackEvent())
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = 'Navigated back'
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'🔙  {memory}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=memory)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to dispatch GoBackEvent: {type(e).__name__}: {e}')
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = f'Failed to go back: {str(e)}'
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=error_msg)

		# EN: Define async function `wait`.
		# JP: 非同期関数 `wait` を定義する。
		@self.registry.action(
			'Wait for x seconds (default 3) (max 30 seconds). This can be used to wait until the page is fully loaded.'
		)
		async def wait(seconds: int = 3):
			# Cap wait time at maximum 30 seconds
			# Reduce the wait time by 3 seconds to account for the llm call which takes at least 3 seconds
			# So if the model decides to wait for 5 seconds, the llm call took at least 3 seconds, so we only need to wait for 2 seconds
			# Note by Mert: the above doesnt make sense because we do the LLM call right after this or this could be followed by another action after which we would like to wait
			# so I revert this.
			# EN: Assign value to actual_seconds.
			# JP: actual_seconds に値を代入する。
			actual_seconds = min(max(seconds - 3, 0), 30)
			# EN: Assign value to memory.
			# JP: memory に値を代入する。
			memory = f'Waited for {seconds} seconds'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'🕒 waited for {actual_seconds} seconds + 3 seconds for LLM call')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(actual_seconds)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(extracted_content=memory, long_term_memory=memory)

		# Element Interaction Actions

		# EN: Define async function `click_element_by_index`.
		# JP: 非同期関数 `click_element_by_index` を定義する。
		@self.registry.action(
			'Click element by index. Only indices from your browser_state are allowed. Never use an index that is not inside your current browser_state. Set while_holding_ctrl=True to open any resulting navigation in a new tab.',
			param_model=ClickElementAction,
		)
		async def click_element_by_index(params: ClickElementAction, browser_session: BrowserSession):
			# Dispatch click event with node
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert params.index != 0, (
					'Cannot click on element with index 0. If there are no interactive elements use scroll(), wait(), refresh(), etc. to troubleshoot'
				)

				# Look up the node from the selector map
				# EN: Assign value to node.
				# JP: node に値を代入する。
				node = await browser_session.get_element_by_index(params.index)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node is None:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError(f'Element index {params.index} not found in browser state')

				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(
					ClickElementEvent(node=node, while_holding_ctrl=params.while_holding_ctrl or False)
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# Wait for handler to complete and get any exception or metadata
				# EN: Assign value to click_metadata.
				# JP: click_metadata に値を代入する。
				click_metadata = await event.event_result(raise_if_any=True, raise_if_none=False)
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = 'Clicked element'

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if params.while_holding_ctrl:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					memory += ' and opened in new tab'

				# Check if a new tab was opened (from watchdog metadata)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(click_metadata, dict) and click_metadata.get('new_tab_opened'):
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					memory += ' - which opened a new tab'

				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'🖱️ {memory}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)

				# Include click coordinates in metadata if available
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					long_term_memory=memory,
					metadata=click_metadata if isinstance(click_metadata, dict) else None,
				)
			except BrowserError as e:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'Cannot click on <select> elements.' in str(e):
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return await get_dropdown_options(
							params=GetDropdownOptionsAction(index=params.index), browser_session=browser_session
						)
					except Exception as dropdown_error:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.error(
							f'Failed to get dropdown options as shortcut during click_element_by_index on dropdown: {type(dropdown_error).__name__}: {dropdown_error}'
						)

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return handle_browser_error(e)
			except Exception as e:
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = f'Failed to click element {params.index}: {str(e)}'
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=error_msg)

		# EN: Define async function `input_text`.
		# JP: 非同期関数 `input_text` を定義する。
		@self.registry.action(
			'Input text into an input interactive element. Only input text into indices that are inside your current browser_state. Never input text into indices that are not inside your current browser_state.',
			param_model=InputTextAction,
		)
		async def input_text(
			params: InputTextAction,
			browser_session: BrowserSession,
			has_sensitive_data: bool = False,
			sensitive_data: dict[str, str | dict[str, str]] | None = None,
		):
			# Look up the node from the selector map
			# EN: Assign value to node.
			# JP: node に値を代入する。
			node = await browser_session.get_element_by_index(params.index)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node is None:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f'Element index {params.index} not found in browser state')

			# Dispatch type text event with node
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Detect which sensitive key is being used
				# EN: Assign value to sensitive_key_name.
				# JP: sensitive_key_name に値を代入する。
				sensitive_key_name = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if has_sensitive_data and sensitive_data:
					# EN: Assign value to sensitive_key_name.
					# JP: sensitive_key_name に値を代入する。
					sensitive_key_name = _detect_sensitive_key_name(params.text, sensitive_data)

				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(
					TypeTextEvent(
						node=node,
						text=params.text,
						clear_existing=params.clear_existing,
						is_sensitive=has_sensitive_data,
						sensitive_key_name=sensitive_key_name,
					)
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Assign value to input_metadata.
				# JP: input_metadata に値を代入する。
				input_metadata = await event.event_result(raise_if_any=True, raise_if_none=False)

				# Create message with sensitive data handling
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if has_sensitive_data:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if sensitive_key_name:
						# EN: Assign value to msg.
						# JP: msg に値を代入する。
						msg = f'Input {sensitive_key_name} into element {params.index}.'
						# EN: Assign value to log_msg.
						# JP: log_msg に値を代入する。
						log_msg = f'Input <{sensitive_key_name}> into element {params.index}.'
					else:
						# EN: Assign value to msg.
						# JP: msg に値を代入する。
						msg = f'Input sensitive data into element {params.index}.'
						# EN: Assign value to log_msg.
						# JP: log_msg に値を代入する。
						log_msg = f'Input <sensitive> into element {params.index}.'
				else:
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f"Input '{params.text}' into element {params.index}."
					# EN: Assign value to log_msg.
					# JP: log_msg に値を代入する。
					log_msg = msg

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(log_msg)

				# Include input coordinates in metadata if available
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					extracted_content=msg,
					long_term_memory=msg,
					metadata=input_metadata if isinstance(input_metadata, dict) else None,
				)
			except BrowserError as e:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return handle_browser_error(e)
			except Exception as e:
				# Log the full error for debugging
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to dispatch TypeTextEvent: {type(e).__name__}: {e}')
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = f'Failed to input text into element {params.index}: {e}'
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=error_msg)

		# EN: Define async function `upload_file_to_element`.
		# JP: 非同期関数 `upload_file_to_element` を定義する。
		@self.registry.action('Upload file to interactive element with file path', param_model=UploadFileAction)
		async def upload_file_to_element(
			params: UploadFileAction, browser_session: BrowserSession, available_file_paths: list[str], file_system: FileSystem
		):
			# Check if file is in available_file_paths (user-provided or downloaded files)
			# For remote browsers (is_local=False), we allow absolute remote paths even if not tracked locally
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if params.path not in available_file_paths:
				# Also check if it's a recently downloaded file that might not be in available_file_paths yet
				# EN: Assign value to downloaded_files.
				# JP: downloaded_files に値を代入する。
				downloaded_files = browser_session.downloaded_files
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if params.path not in downloaded_files:
					# Finally, check if it's a file in the FileSystem service
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if file_system and file_system.get_dir():
						# Check if the file is actually managed by the FileSystem service
						# The path should be just the filename for FileSystem files
						# EN: Assign value to file_obj.
						# JP: file_obj に値を代入する。
						file_obj = file_system.get_file(params.path)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if file_obj:
							# File is managed by FileSystem, construct the full path
							# EN: Assign value to file_system_path.
							# JP: file_system_path に値を代入する。
							file_system_path = str(file_system.get_dir() / params.path)
							# EN: Assign value to params.
							# JP: params に値を代入する。
							params = UploadFileAction(index=params.index, path=file_system_path)
						else:
							# If browser is remote, allow passing a remote-accessible absolute path
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if not browser_session.is_local:
								# EN: Keep a placeholder statement.
								# JP: プレースホルダー文を維持する。
								pass
							else:
								# EN: Assign value to msg.
								# JP: msg に値を代入する。
								msg = f'File path {params.path} is not available. Upload files must be in available_file_paths, downloaded_files, or a file managed by file_system.'
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								logger.error(f'❌ {msg}')
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return ActionResult(error=msg)
					else:
						# If browser is remote, allow passing a remote-accessible absolute path
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if not browser_session.is_local:
							# EN: Keep a placeholder statement.
							# JP: プレースホルダー文を維持する。
							pass
						else:
							# EN: Assign value to msg.
							# JP: msg に値を代入する。
							msg = f'File path {params.path} is not available. Upload files must be in available_file_paths, downloaded_files, or a file managed by file_system.'
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise BrowserError(message=msg, long_term_memory=msg)

			# For local browsers, ensure the file exists on the local filesystem
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if browser_session.is_local:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not os.path.exists(params.path):
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f'File {params.path} does not exist'
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=msg)

			# Get the selector map to find the node
			# EN: Assign value to selector_map.
			# JP: selector_map に値を代入する。
			selector_map = await browser_session.get_selector_map()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if params.index not in selector_map:
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Element with index {params.index} does not exist.'
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=msg)

			# EN: Assign value to node.
			# JP: node に値を代入する。
			node = selector_map[params.index]

			# Helper function to find file input near the selected element
			# EN: Define function `find_file_input_near_element`.
			# JP: 関数 `find_file_input_near_element` を定義する。
			def find_file_input_near_element(
				node: EnhancedDOMTreeNode, max_height: int = 3, max_descendant_depth: int = 3
			) -> EnhancedDOMTreeNode | None:
				# EN: Describe this block with a docstring.
				# JP: このブロックの説明をドキュメント文字列で記述する。
				"""Find the closest file input to the selected element."""

				# EN: Define function `find_file_input_in_descendants`.
				# JP: 関数 `find_file_input_in_descendants` を定義する。
				def find_file_input_in_descendants(n: EnhancedDOMTreeNode, depth: int) -> EnhancedDOMTreeNode | None:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if depth < 0:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return None
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if browser_session.is_file_input(n):
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return n
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for child in n.children_nodes or []:
						# EN: Assign value to result.
						# JP: result に値を代入する。
						result = find_file_input_in_descendants(child, depth - 1)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if result:
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return result
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None

				# EN: Assign value to current.
				# JP: current に値を代入する。
				current = node
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for _ in range(max_height + 1):
					# Check the current node itself
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if browser_session.is_file_input(current):
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return current
					# Check all descendants of the current node
					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = find_file_input_in_descendants(current, max_descendant_depth)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if result:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return result
					# Check all siblings and their descendants
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if current.parent_node:
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for sibling in current.parent_node.children_nodes or []:
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if sibling is current:
								# EN: Continue to the next loop iteration.
								# JP: ループの次の反復に進む。
								continue
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if browser_session.is_file_input(sibling):
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return sibling
							# EN: Assign value to result.
							# JP: result に値を代入する。
							result = find_file_input_in_descendants(sibling, max_descendant_depth)
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if result:
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return result
					# EN: Assign value to current.
					# JP: current に値を代入する。
					current = current.parent_node
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if not current:
						# EN: Exit the current loop.
						# JP: 現在のループを終了する。
						break
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

			# Try to find a file input element near the selected element
			# EN: Assign value to file_input_node.
			# JP: file_input_node に値を代入する。
			file_input_node = find_file_input_near_element(node)

			# If not found near the selected element, fallback to finding the closest file input to current scroll position
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if file_input_node is None:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(
					f'No file upload element found near index {params.index}, searching for closest file input to scroll position'
				)

				# Get current scroll position
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = await browser_session.get_or_create_cdp_session()
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to scroll_info.
					# JP: scroll_info に値を代入する。
					scroll_info = await cdp_session.cdp_client.send.Runtime.evaluate(
						params={'expression': 'window.scrollY || window.pageYOffset || 0'}, session_id=cdp_session.session_id
					)
					# EN: Assign value to current_scroll_y.
					# JP: current_scroll_y に値を代入する。
					current_scroll_y = scroll_info.get('result', {}).get('value', 0)
				except Exception:
					# EN: Assign value to current_scroll_y.
					# JP: current_scroll_y に値を代入する。
					current_scroll_y = 0

				# Find all file inputs in the selector map and pick the closest one to scroll position
				# EN: Assign value to closest_file_input.
				# JP: closest_file_input に値を代入する。
				closest_file_input = None
				# EN: Assign value to min_distance.
				# JP: min_distance に値を代入する。
				min_distance = float('inf')

				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for idx, element in selector_map.items():
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if browser_session.is_file_input(element):
						# Get element's Y position
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if element.absolute_position:
							# EN: Assign value to element_y.
							# JP: element_y に値を代入する。
							element_y = element.absolute_position.y
							# EN: Assign value to distance.
							# JP: distance に値を代入する。
							distance = abs(element_y - current_scroll_y)
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if distance < min_distance:
								# EN: Assign value to min_distance.
								# JP: min_distance に値を代入する。
								min_distance = distance
								# EN: Assign value to closest_file_input.
								# JP: closest_file_input に値を代入する。
								closest_file_input = element

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if closest_file_input:
					# EN: Assign value to file_input_node.
					# JP: file_input_node に値を代入する。
					file_input_node = closest_file_input
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info(f'Found file input closest to scroll position (distance: {min_distance}px)')
				else:
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = 'No file upload element found on the page'
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(msg)
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise BrowserError(msg)
					# TODO: figure out why this fails sometimes + add fallback hail mary, just look for any file input on page

			# Dispatch upload file event with the file input node
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(UploadFileEvent(node=file_input_node, file_path=params.path))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event.event_result(raise_if_any=True, raise_if_none=False)
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Successfully uploaded file to index {params.index}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'📁 {msg}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					extracted_content=msg,
					long_term_memory=f'Uploaded file {params.path} to element {params.index}',
				)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to upload file: {e}')
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise BrowserError(f'Failed to upload file: {e}')

		# Tab Management Actions

		# EN: Define async function `switch_tab`.
		# JP: 非同期関数 `switch_tab` を定義する。
		@self.registry.action('Switch tab', param_model=SwitchTabAction)
		async def switch_tab(params: SwitchTabAction, browser_session: BrowserSession):
			# Dispatch switch tab event
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = await browser_session.get_target_id_from_tab_id(params.tab_id)

				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(SwitchTabEvent(target_id=target_id))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Assign value to new_target_id.
				# JP: new_target_id に値を代入する。
				new_target_id = await event.event_result(raise_if_any=True, raise_if_none=False)
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert new_target_id, 'SwitchTabEvent did not return a TargetID for the new tab that was switched to'
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = f'Switched to Tab with ID {new_target_id[-4:]}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'🔄  {memory}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=memory, long_term_memory=memory)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to switch tab: {type(e).__name__}: {e}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=f'Failed to switch to tab {params.tab_id}.')

		# EN: Define async function `close_tab`.
		# JP: 非同期関数 `close_tab` を定義する。
		@self.registry.action('Close an existing tab', param_model=CloseTabAction)
		async def close_tab(params: CloseTabAction, browser_session: BrowserSession):
			# Dispatch close tab event
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = await browser_session.get_target_id_from_tab_id(params.tab_id)
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = await browser_session.get_or_create_cdp_session()
				# EN: Assign value to target_info.
				# JP: target_info に値を代入する。
				target_info = await cdp_session.cdp_client.send.Target.getTargetInfo(
					params={'targetId': target_id}, session_id=cdp_session.session_id
				)
				# EN: Assign value to tab_url.
				# JP: tab_url に値を代入する。
				tab_url = target_info['targetInfo']['url']
				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(CloseTabEvent(target_id=target_id))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event.event_result(raise_if_any=True, raise_if_none=False)
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = f'Closed tab # {params.tab_id} ({_log_pretty_url(tab_url)})'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'🗑️  {memory}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					extracted_content=memory,
					long_term_memory=memory,
				)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to close tab: {e}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=f'Failed to close tab {params.tab_id}.')

		# Content Actions

		# TODO: Refactor to use events instead of direct page access
		# This action is temporarily disabled as it needs refactoring to use events

		# EN: Define async function `extract_structured_data`.
		# JP: 非同期関数 `extract_structured_data` を定義する。
		@self.registry.action(
			"""This tool sends the markdown of the current page with the query to an LLM to extract structured, semantic data (e.g. product description, price, all information about XYZ) from the markdown of the current webpage based on a query.
Only use when:
- You are sure that you are on the right page for the query
- You know exactly the information you need to extract from the page
- You did not previously call this tool on the same page
You can not use this tool to:
- Get interactive elements like buttons, links, dropdowns, menus, etc.
- If you previously asked extract_structured_data on the same page with the same query, you should not call it again.

Set extract_links=True only if your query requires extracting links/URLs from the page.
Use start_from_char to start extraction from a specific character position (use if extraction was previously truncated and you want more content).

If this tool does not return the desired outcome, do not call it again, use scroll_to_text or scroll to find the desired information.
""",
		)
		async def extract_structured_data(
			query: str,
			extract_links: bool,
			browser_session: BrowserSession,
			page_extraction_llm: BaseChatModel,
			file_system: FileSystem,
			start_from_char: int = 0,
		):
			# Constants
			# EN: Assign value to MAX_CHAR_LIMIT.
			# JP: MAX_CHAR_LIMIT に値を代入する。
			MAX_CHAR_LIMIT = 30000

			# Extract clean markdown using the new method
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				content, content_stats = await self.extract_clean_markdown(browser_session, extract_links)
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError(f'Could not extract clean markdown: {type(e).__name__}')

			# Original content length for processing
			# EN: Assign value to final_filtered_length.
			# JP: final_filtered_length に値を代入する。
			final_filtered_length = content_stats['final_filtered_chars']

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if start_from_char > 0:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if start_from_char >= len(content):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(
						error=f'start_from_char ({start_from_char}) exceeds content length ({len(content)}). Content has {final_filtered_length} characters after filtering.'
					)
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = content[start_from_char:]
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				content_stats['started_from_char'] = start_from_char

			# Smart truncation with context preservation
			# EN: Assign value to truncated.
			# JP: truncated に値を代入する。
			truncated = False
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(content) > MAX_CHAR_LIMIT:
				# Try to truncate at a natural break point (paragraph, sentence)
				# EN: Assign value to truncate_at.
				# JP: truncate_at に値を代入する。
				truncate_at = MAX_CHAR_LIMIT

				# Look for paragraph break within last 500 chars of limit
				# EN: Assign value to paragraph_break.
				# JP: paragraph_break に値を代入する。
				paragraph_break = content.rfind('\n\n', MAX_CHAR_LIMIT - 500, MAX_CHAR_LIMIT)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if paragraph_break > 0:
					# EN: Assign value to truncate_at.
					# JP: truncate_at に値を代入する。
					truncate_at = paragraph_break
				else:
					# Look for sentence break within last 200 chars of limit
					# EN: Assign value to sentence_break.
					# JP: sentence_break に値を代入する。
					sentence_break = content.rfind('.', MAX_CHAR_LIMIT - 200, MAX_CHAR_LIMIT)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if sentence_break > 0:
						# EN: Assign value to truncate_at.
						# JP: truncate_at に値を代入する。
						truncate_at = sentence_break + 1

				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = content[:truncate_at]
				# EN: Assign value to truncated.
				# JP: truncated に値を代入する。
				truncated = True
				# EN: Assign value to next_start.
				# JP: next_start に値を代入する。
				next_start = (start_from_char or 0) + truncate_at
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				content_stats['truncated_at_char'] = truncate_at
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				content_stats['next_start_char'] = next_start

			# Add content statistics to the result
			# EN: Assign value to original_html_length.
			# JP: original_html_length に値を代入する。
			original_html_length = content_stats['original_html_chars']
			# EN: Assign value to initial_markdown_length.
			# JP: initial_markdown_length に値を代入する。
			initial_markdown_length = content_stats['initial_markdown_chars']
			# EN: Assign value to chars_filtered.
			# JP: chars_filtered に値を代入する。
			chars_filtered = content_stats['filtered_chars_removed']

			# EN: Assign value to stats_summary.
			# JP: stats_summary に値を代入する。
			stats_summary = f"""Content processed: {original_html_length:,} HTML chars → {initial_markdown_length:,} initial markdown → {final_filtered_length:,} filtered markdown"""
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if start_from_char > 0:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				stats_summary += f' (started from char {start_from_char:,})'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if truncated:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				stats_summary += f' → {len(content):,} final chars (truncated, use start_from_char={content_stats["next_start_char"]} to continue)'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif chars_filtered > 0:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				stats_summary += f' (filtered {chars_filtered:,} chars of noise)'

			# EN: Assign value to system_prompt.
			# JP: system_prompt に値を代入する。
			system_prompt = """
You are an expert at extracting data from the markdown of a webpage.

<input>
You will be given a query and the markdown of a webpage that has been filtered to remove noise and advertising content.
</input>

<instructions>
- You are tasked to extract information from the webpage that is relevant to the query.
- You should ONLY use the information available in the webpage to answer the query. Do not make up information or provide guess from your own knowledge. 
- If the information relevant to the query is not available in the page, your response should mention that.
- If the query asks for all items, products, etc., make sure to directly list all of them.
- If the content was truncated and you need more information, note that the user can use start_from_char parameter to continue from where truncation occurred.
</instructions>

<output>
- Your output should present ALL the information relevant to the query in a concise way.
- Do not answer in conversational format - directly output the relevant information or that the information is unavailable.
</output>
""".strip()

			# EN: Assign value to prompt.
			# JP: prompt に値を代入する。
			prompt = f'<query>\n{query}\n</query>\n\n<content_stats>\n{stats_summary}\n</content_stats>\n\n<webpage_content>\n{content}\n</webpage_content>'

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await asyncio.wait_for(
					page_extraction_llm.ainvoke([SystemMessage(content=system_prompt), UserMessage(content=prompt)]),
					timeout=120.0,
				)

				# EN: Assign value to current_url.
				# JP: current_url に値を代入する。
				current_url = await browser_session.get_current_page_url()
				# EN: Assign value to extracted_content.
				# JP: extracted_content に値を代入する。
				extracted_content = (
					f'<url>\n{current_url}\n</url>\n<query>\n{query}\n</query>\n<result>\n{response.completion}\n</result>'
				)

				# Simple memory handling
				# EN: Assign value to MAX_MEMORY_LENGTH.
				# JP: MAX_MEMORY_LENGTH に値を代入する。
				MAX_MEMORY_LENGTH = 1000
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if len(extracted_content) < MAX_MEMORY_LENGTH:
					# EN: Assign value to memory.
					# JP: memory に値を代入する。
					memory = extracted_content
					# EN: Assign value to include_extracted_content_only_once.
					# JP: include_extracted_content_only_once に値を代入する。
					include_extracted_content_only_once = False
				else:
					# EN: Assign value to save_result.
					# JP: save_result に値を代入する。
					save_result = await file_system.save_extracted_content(extracted_content)
					# EN: Assign value to memory.
					# JP: memory に値を代入する。
					memory = f'Extracted content from {current_url} for query: {query}\nContent saved to file system: {save_result} and displayed in <read_state>.'
					# EN: Assign value to include_extracted_content_only_once.
					# JP: include_extracted_content_only_once に値を代入する。
					include_extracted_content_only_once = True

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'📄 {memory}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					extracted_content=extracted_content,
					include_extracted_content_only_once=include_extracted_content_only_once,
					long_term_memory=memory,
				)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Error extracting content: {e}')
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError(str(e))

		# EN: Define async function `scroll`.
		# JP: 非同期関数 `scroll` を定義する。
		@self.registry.action(
			"""Scroll the page by specified number of pages (set down=True to scroll down, down=False to scroll up, num_pages=number of pages to scroll like 0.5 for half page, 10.0 for ten pages, etc.). 
			Default behavior is to scroll the entire page. This is enough for most cases.
			Optional if there are multiple scroll containers, use frame_element_index parameter with an element inside the container you want to scroll in. For that you must use indices that exist in your browser_state (works well for dropdowns and custom UI components). 
			Instead of scrolling step after step, use a high number of pages at once like 10 to get to the bottom of the page.
			If you know where you want to scroll to, use scroll_to_text instead of this tool.
			""",
			param_model=ScrollAction,
		)
		async def scroll(params: ScrollAction, browser_session: BrowserSession):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Look up the node from the selector map if index is provided
				# Special case: index 0 means scroll the whole page (root/body element)
				# EN: Assign value to node.
				# JP: node に値を代入する。
				node = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if params.frame_element_index is not None and params.frame_element_index != 0:
					# EN: Assign value to node.
					# JP: node に値を代入する。
					node = await browser_session.get_element_by_index(params.frame_element_index)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if node is None:
						# Element does not exist
						# EN: Assign value to msg.
						# JP: msg に値を代入する。
						msg = f'Element index {params.frame_element_index} not found in browser state'
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return ActionResult(error=msg)

				# Dispatch scroll event with node - the complex logic is handled in the event handler
				# Convert pages to pixels (assuming 1000px per page as standard viewport height)
				# EN: Assign value to pixels.
				# JP: pixels に値を代入する。
				pixels = int(params.num_pages * 1000)
				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(
					ScrollEvent(direction='down' if params.down else 'up', amount=pixels, node=node)
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event.event_result(raise_if_any=True, raise_if_none=False)
				# EN: Assign value to direction.
				# JP: direction に値を代入する。
				direction = 'down' if params.down else 'up'

				# If index is 0 or None, we're scrolling the page
				# EN: Assign value to target.
				# JP: target に値を代入する。
				target = (
					'the page'
					if params.frame_element_index is None or params.frame_element_index == 0
					else f'element {params.frame_element_index}'
				)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if params.num_pages == 1.0:
					# EN: Assign value to long_term_memory.
					# JP: long_term_memory に値を代入する。
					long_term_memory = f'Scrolled {direction} {target} by one page'
				else:
					# EN: Assign value to long_term_memory.
					# JP: long_term_memory に値を代入する。
					long_term_memory = f'Scrolled {direction} {target} by {params.num_pages} pages'

				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'🔍 {long_term_memory}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=msg, long_term_memory=long_term_memory)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to dispatch ScrollEvent: {type(e).__name__}: {e}')
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = 'Failed to execute scroll action.'
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=error_msg)

		# EN: Define async function `send_keys`.
		# JP: 非同期関数 `send_keys` を定義する。
		@self.registry.action(
			'Send strings of special keys to use e.g. Escape, Backspace, Insert, PageDown, Delete, Enter, or Shortcuts such as `Control+o`, `Control+Shift+T`',
			param_model=SendKeysAction,
		)
		async def send_keys(params: SendKeysAction, browser_session: BrowserSession):
			# Dispatch send keys event
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = browser_session.event_bus.dispatch(SendKeysEvent(keys=params.keys))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await event.event_result(raise_if_any=True, raise_if_none=False)
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = f'Sent keys: {params.keys}'
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'⌨️  {memory}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=memory, long_term_memory=memory)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to dispatch SendKeysEvent: {type(e).__name__}: {e}')
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = f'Failed to send keys: {str(e)}'
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=error_msg)

		# EN: Define async function `scroll_to_text`.
		# JP: 非同期関数 `scroll_to_text` を定義する。
		@self.registry.action(
			description='Scroll to a text in the current page. This helps you to be efficient. Prefer this tool over scrolling step by step.',
		)
		async def scroll_to_text(text: str, browser_session: BrowserSession):  # type: ignore
			# Dispatch scroll to text event
			# EN: Assign value to event.
			# JP: event に値を代入する。
			event = browser_session.event_bus.dispatch(ScrollToTextEvent(text=text))

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# The handler returns True on success, False if not found
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await event.event_result(raise_if_any=True, raise_if_none=False)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if result is False or (isinstance(result, dict) and not result.get('found', True)):
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f"Text '{text}' not found or not visible on page"
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info(msg)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(
						extracted_content=msg,
						long_term_memory=f"Tried scrolling to text '{text}' but it was not found",
					)

				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = f'Scrolled to text: {text}'
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'🔍  {memory}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=memory, long_term_memory=memory)
			except Exception as e:
				# Text not found
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f"Text '{text}' not found or not visible on page"
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					extracted_content=msg,
					long_term_memory=f"Tried scrolling to text '{text}' but it was not found",
				)

		# Dropdown Actions

		# EN: Define async function `get_dropdown_options`.
		# JP: 非同期関数 `get_dropdown_options` を定義する。
		@self.registry.action(
			'Get list of values for a dropdown input field. Only works on dropdown-style form elements (<select>, Semantic UI/aria-labeled select, etc.). Do not use this tool for none dropdown elements.',
			param_model=GetDropdownOptionsAction,
		)
		async def get_dropdown_options(params: GetDropdownOptionsAction, browser_session: BrowserSession):
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Get all options from a native dropdown or ARIA menu"""
			# Look up the node from the selector map
			# EN: Assign value to node.
			# JP: node に値を代入する。
			node = await browser_session.get_element_by_index(params.index)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node is None:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f'Element index {params.index} not found in browser state')

			# Dispatch GetDropdownOptionsEvent to the event handler

			# EN: Assign value to event.
			# JP: event に値を代入する。
			event = browser_session.event_bus.dispatch(GetDropdownOptionsEvent(node=node))
			# EN: Assign value to dropdown_data.
			# JP: dropdown_data に値を代入する。
			dropdown_data = await event.event_result(timeout=3.0, raise_if_none=True, raise_if_any=True)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not dropdown_data:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError('Failed to get dropdown options - no data returned')

			# Use structured memory from the handler
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=dropdown_data['short_term_memory'],
				long_term_memory=dropdown_data['long_term_memory'],
				include_extracted_content_only_once=True,
			)

		# EN: Define async function `select_dropdown_option`.
		# JP: 非同期関数 `select_dropdown_option` を定義する。
		@self.registry.action(
			'Select dropdown option by exact text from any dropdown type (native <select>, ARIA menus, or custom dropdowns). Searches target element and children to find selectable options.',
			param_model=SelectDropdownOptionAction,
		)
		async def select_dropdown_option(params: SelectDropdownOptionAction, browser_session: BrowserSession):
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Select dropdown option by the text of the option you want to select"""
			# Look up the node from the selector map
			# EN: Assign value to node.
			# JP: node に値を代入する。
			node = await browser_session.get_element_by_index(params.index)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node is None:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f'Element index {params.index} not found in browser state')

			# Dispatch SelectDropdownOptionEvent to the event handler
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from browser_use.browser.events import SelectDropdownOptionEvent

			# EN: Assign value to event.
			# JP: event に値を代入する。
			event = browser_session.event_bus.dispatch(SelectDropdownOptionEvent(node=node, text=params.text))
			# EN: Assign value to selection_data.
			# JP: selection_data に値を代入する。
			selection_data = await event.event_result()

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not selection_data:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError('Failed to select dropdown option - no data returned')

			# Check if the selection was successful
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if selection_data.get('success') == 'true':
				# Extract the message from the returned data
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = selection_data.get('message', f'Selected option: {params.text}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					extracted_content=msg,
					include_in_memory=True,
					long_term_memory=f"Selected dropdown option '{params.text}' at index {params.index}",
				)
			else:
				# Handle structured error response
				# TODO: raise BrowserError instead of returning ActionResult
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'short_term_memory' in selection_data and 'long_term_memory' in selection_data:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(
						extracted_content=selection_data['short_term_memory'],
						long_term_memory=selection_data['long_term_memory'],
						include_extracted_content_only_once=True,
					)
				else:
					# Fallback to regular error
					# EN: Assign value to error_msg.
					# JP: error_msg に値を代入する。
					error_msg = selection_data.get('error', f'Failed to select option: {params.text}')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=error_msg)

		# File System Actions
		# EN: Define async function `write_file`.
		# JP: 非同期関数 `write_file` を定義する。
		@self.registry.action(
			'Write or append content to file_name in file system. Allowed extensions are .md, .txt, .json, .csv, .pdf. For .pdf files, write the content in markdown format and it will automatically be converted to a properly formatted PDF document.'
		)
		async def write_file(
			file_name: str,
			content: str,
			file_system: FileSystem,
			append: bool = False,
			trailing_newline: bool = True,
			leading_newline: bool = False,
		):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if trailing_newline:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				content += '\n'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if leading_newline:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = '\n' + content
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if append:
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await file_system.append_file(file_name, content)
			else:
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await file_system.write_file(file_name, content)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'💾 {result}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(extracted_content=result, long_term_memory=result)

		# EN: Define async function `replace_file_str`.
		# JP: 非同期関数 `replace_file_str` を定義する。
		@self.registry.action(
			'Replace old_str with new_str in file_name. old_str must exactly match the string to replace in original text. Recommended tool to mark completed items in todo.md or change specific contents in a file.'
		)
		async def replace_file_str(file_name: str, old_str: str, new_str: str, file_system: FileSystem):
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await file_system.replace_file_str(file_name, old_str, new_str)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'💾 {result}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(extracted_content=result, long_term_memory=result)

		# EN: Define async function `read_file`.
		# JP: 非同期関数 `read_file` を定義する。
		@self.registry.action('Read file_name from file system')
		async def read_file(file_name: str, available_file_paths: list[str], file_system: FileSystem):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if available_file_paths and file_name in available_file_paths:
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await file_system.read_file(file_name, external_file=True)
			else:
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await file_system.read_file(file_name)

			# EN: Assign value to MAX_MEMORY_SIZE.
			# JP: MAX_MEMORY_SIZE に値を代入する。
			MAX_MEMORY_SIZE = 1000
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(result) > MAX_MEMORY_SIZE:
				# EN: Assign value to lines.
				# JP: lines に値を代入する。
				lines = result.splitlines()
				# EN: Assign value to display.
				# JP: display に値を代入する。
				display = ''
				# EN: Assign value to lines_count.
				# JP: lines_count に値を代入する。
				lines_count = 0
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for line in lines:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if len(display) + len(line) < MAX_MEMORY_SIZE:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						display += line + '\n'
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						lines_count += 1
					else:
						# EN: Exit the current loop.
						# JP: 現在のループを終了する。
						break
				# EN: Assign value to remaining_lines.
				# JP: remaining_lines に値を代入する。
				remaining_lines = len(lines) - lines_count
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = f'{display}{remaining_lines} more lines...' if remaining_lines > 0 else display
			else:
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = result
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'💾 {memory}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=result,
				long_term_memory=memory,
				include_extracted_content_only_once=True,
			)

		# EN: Define async function `execute_js`.
		# JP: 非同期関数 `execute_js` を定義する。
		@self.registry.action(
			"""This JavaScript code gets executed with Runtime.evaluate and 'returnByValue': True, 'awaitPromise': True
EXAMPLES:
Using when other tools fail, filling a form all at once, hovering, dragging, extracting only links, extracting content from the page, Clicking on coordinates, zooming, use this if the user provides custom selecotrs which you can otherwise not interact with ....
You can also use it to explore the website.
- Write code to solve problems you could not solve with other tools.
- Don't write comments in here, no human reads that.
- Write only valid js code. 
- use this to e.g. extract + filter links, convert the page to json into the format you need etc...
- wrap your code in (function(){ ... })() or (async function(){ ... })() for async code
- wrap your code in a try catch block
- limit the output otherwise your context will explode
- think if you deal with special elements like iframes / shadow roots etc
- Adopt your strategy for React Native Web, React, Angular, Vue, MUI pages etc.
- e.g. with  synthetic events, keyboard simulation, shadow DOM, etc.

## Return values:
- Async functions (with await, promises, timeouts) are automatically handled
- Returns strings, numbers, booleans, and serialized objects/arrays
- Use JSON.stringify() for complex objects: JSON.stringify(Array.from(document.querySelectorAll('a')).map(el => el.textContent.trim()))

""",
		)
		async def execute_js(code: str, browser_session: BrowserSession):
			# Execute JavaScript with proper error handling and promise support

			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await browser_session.get_or_create_cdp_session()

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Always use awaitPromise=True - it's ignored for non-promises
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await cdp_session.cdp_client.send.Runtime.evaluate(
					params={'expression': code, 'returnByValue': True, 'awaitPromise': True},
					session_id=cdp_session.session_id,
				)

				# Check for JavaScript execution errors
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if result.get('exceptionDetails'):
					# EN: Assign value to exception.
					# JP: exception に値を代入する。
					exception = result['exceptionDetails']
					# EN: Assign value to error_msg.
					# JP: error_msg に値を代入する。
					error_msg = f'JavaScript execution error: {exception.get("text", "Unknown error")}'
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'lineNumber' in exception:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						error_msg += f' at line {exception["lineNumber"]}'
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f'Code: {code}\n\nError: {error_msg}'
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info(msg)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=msg)

				# Get the result data
				# EN: Assign value to result_data.
				# JP: result_data に値を代入する。
				result_data = result.get('result', {})

				# Check for wasThrown flag (backup error detection)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if result_data.get('wasThrown'):
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = f'Code: {code}\n\nError: JavaScript execution failed (wasThrown=true)'
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info(msg)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=msg)

				# Get the actual value
				# EN: Assign value to value.
				# JP: value に値を代入する。
				value = result_data.get('value')

				# Handle different value types
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if value is None:
					# Could be legitimate null/undefined result
					# EN: Assign value to result_text.
					# JP: result_text に値を代入する。
					result_text = str(value) if 'value' in result_data else 'undefined'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(value, (dict, list)):
					# Complex objects - should be serialized by returnByValue
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to result_text.
						# JP: result_text に値を代入する。
						result_text = json.dumps(value, ensure_ascii=False)
					except (TypeError, ValueError):
						# Fallback for non-serializable objects
						# EN: Assign value to result_text.
						# JP: result_text に値を代入する。
						result_text = str(value)
				else:
					# Primitive values (string, number, boolean)
					# EN: Assign value to result_text.
					# JP: result_text に値を代入する。
					result_text = str(value)

				# Keep full result text (no truncation) so UI/external consumers can inspect everything
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Code: {code}\n\nResult: {result_text}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=f'Code: {code}\n\nResult: {result_text}')

			except Exception as e:
				# CDP communication or other system errors
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = f'Code: {code}\n\nError: {error_msg} Failed to execute JavaScript: {type(e).__name__}: {e}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(error_msg)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=error_msg)

	# Custom done action for structured output
	# EN: Define async function `extract_clean_markdown`.
	# JP: 非同期関数 `extract_clean_markdown` を定義する。
	async def extract_clean_markdown(
		self, browser_session: BrowserSession, extract_links: bool = False
	) -> tuple[str, dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract clean markdown from the current page.

		Args:
			browser_session: Browser session to extract content from
			extract_links: Whether to preserve links in markdown

		Returns:
			tuple: (clean_markdown_content, content_statistics)
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import re

		# Get HTML content from current page
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await browser_session.get_or_create_cdp_session()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to body_id.
			# JP: body_id に値を代入する。
			body_id = await cdp_session.cdp_client.send.DOM.getDocument(session_id=cdp_session.session_id)
			# EN: Assign value to page_html_result.
			# JP: page_html_result に値を代入する。
			page_html_result = await cdp_session.cdp_client.send.DOM.getOuterHTML(
				params={'backendNodeId': body_id['root']['backendNodeId']}, session_id=cdp_session.session_id
			)
			# EN: Assign value to page_html.
			# JP: page_html に値を代入する。
			page_html = page_html_result['outerHTML']
			# EN: Assign value to current_url.
			# JP: current_url に値を代入する。
			current_url = await browser_session.get_current_page_url()
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError(f"Couldn't extract page content: {e}")

		# EN: Assign value to original_html_length.
		# JP: original_html_length に値を代入する。
		original_html_length = len(page_html)

		# Use html2text for clean markdown conversion
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import html2text

		# EN: Assign value to h.
		# JP: h に値を代入する。
		h = html2text.HTML2Text()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		h.ignore_links = not extract_links
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		h.ignore_images = True
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		h.ignore_emphasis = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		h.body_width = 0  # Don't wrap lines
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		h.unicode_snob = True
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		h.skip_internal_links = True
		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = h.handle(page_html)

		# EN: Assign value to initial_markdown_length.
		# JP: initial_markdown_length に値を代入する。
		initial_markdown_length = len(content)

		# Minimal cleanup - html2text already does most of the work
		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = re.sub(r'%[0-9A-Fa-f]{2}', '', content)  # Remove any remaining URL encoding

		# Apply light preprocessing to clean up excessive whitespace
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		content, chars_filtered = self._preprocess_markdown_content(content)

		# EN: Assign value to final_filtered_length.
		# JP: final_filtered_length に値を代入する。
		final_filtered_length = len(content)

		# Content statistics
		# EN: Assign value to stats.
		# JP: stats に値を代入する。
		stats = {
			'url': current_url,
			'original_html_chars': original_html_length,
			'initial_markdown_chars': initial_markdown_length,
			'filtered_chars_removed': chars_filtered,
			'final_filtered_chars': final_filtered_length,
		}

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return content, stats

	# EN: Define function `_preprocess_markdown_content`.
	# JP: 関数 `_preprocess_markdown_content` を定義する。
	def _preprocess_markdown_content(self, content: str, max_newlines: int = 3) -> tuple[str, int]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Light preprocessing of html2text output - minimal cleanup since html2text is already clean.

		Args:
			content: Markdown content from html2text to lightly filter
			max_newlines: Maximum consecutive newlines to allow

		Returns:
			tuple: (filtered_content, chars_filtered)
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import re

		# EN: Assign value to original_length.
		# JP: original_length に値を代入する。
		original_length = len(content)

		# Compress consecutive newlines (4+ newlines become max_newlines)
		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = re.sub(r'\n{4,}', '\n' * max_newlines, content)

		# Remove lines that are only whitespace or very short (likely artifacts)
		# EN: Assign value to lines.
		# JP: lines に値を代入する。
		lines = content.split('\n')
		# EN: Assign value to filtered_lines.
		# JP: filtered_lines に値を代入する。
		filtered_lines = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for line in lines:
			# EN: Assign value to stripped.
			# JP: stripped に値を代入する。
			stripped = line.strip()
			# Keep lines with substantial content (html2text output is already clean)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(stripped) > 2:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				filtered_lines.append(line)

		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = '\n'.join(filtered_lines)
		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = content.strip()

		# EN: Assign value to chars_filtered.
		# JP: chars_filtered に値を代入する。
		chars_filtered = original_length - len(content)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return content, chars_filtered

	# EN: Define function `_register_scratchpad_actions`.
	# JP: 関数 `_register_scratchpad_actions` を定義する。
	def _register_scratchpad_actions(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Register Scratchpad (外部メモ) actions for structured data collection."""

		# EN: Define async function `scratchpad_add`.
		# JP: 非同期関数 `scratchpad_add` を定義する。
		@self.registry.action(
			"""【Scratchpad】構造化データをメモ帳に追加。収集した情報を一時保存し、タスク終了時にまとめて報告できます。
例: 店舗情報（店名、座敷有無、評価）、比較データ、検索結果など。
- key: エントリの識別子（例: "店舗A"）
- data: 構造化データ（例: {"座敷": "あり", "評価": 4.5, "価格帯": "3000-5000円"}）
- source_url: 情報取得元のURL（省略可）
- notes: 追加メモ（省略可）""",
			param_model=ScratchpadAddAction,
		)
		async def scratchpad_add(params: ScratchpadAddAction, scratchpad: Scratchpad):
			# EN: Assign value to entry.
			# JP: entry に値を代入する。
			entry = scratchpad.add_entry(
				key=params.key,
				data=params.data,
				source_url=params.source_url,
				notes=params.notes,
			)
			# EN: Assign value to memory.
			# JP: memory に値を代入する。
			memory = f'Scratchpadに追加: {params.key} (データ{len(params.data)}件)'
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = f'📝 {memory}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(msg)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=f'Scratchpadに追加しました:\n{entry.to_summary()}',
				long_term_memory=memory,
			)

		# EN: Define async function `scratchpad_update`.
		# JP: 非同期関数 `scratchpad_update` を定義する。
		@self.registry.action(
			"""【Scratchpad】既存のエントリを更新。
- key: 更新するエントリのキー
- data: 更新するデータ（mergeがTrueなら既存データとマージ）
- notes: 更新するメモ
- merge: True=既存データとマージ、False=完全に置換""",
			param_model=ScratchpadUpdateAction,
		)
		async def scratchpad_update(params: ScratchpadUpdateAction, scratchpad: Scratchpad):
			# EN: Assign value to entry.
			# JP: entry に値を代入する。
			entry = scratchpad.update_entry(
				key=params.key,
				data=params.data,
				notes=params.notes,
				merge=params.merge,
			)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry is None:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=f'Scratchpadにキー "{params.key}" が見つかりません')

			# EN: Assign value to memory.
			# JP: memory に値を代入する。
			memory = f'Scratchpadを更新: {params.key}'
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = f'📝 {memory}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(msg)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=f'Scratchpadを更新しました:\n{entry.to_summary()}',
				long_term_memory=memory,
			)

		# EN: Define async function `scratchpad_remove`.
		# JP: 非同期関数 `scratchpad_remove` を定義する。
		@self.registry.action(
			'【Scratchpad】エントリを削除。key: 削除するエントリのキー',
			param_model=ScratchpadRemoveAction,
		)
		async def scratchpad_remove(params: ScratchpadRemoveAction, scratchpad: Scratchpad):
			# EN: Assign value to success.
			# JP: success に値を代入する。
			success = scratchpad.remove_entry(params.key)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not success:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(error=f'Scratchpadにキー "{params.key}" が見つかりません')

			# EN: Assign value to memory.
			# JP: memory に値を代入する。
			memory = f'Scratchpadから削除: {params.key}'
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = f'📝 {memory}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(msg)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=f'Scratchpadから "{params.key}" を削除しました',
				long_term_memory=memory,
			)

		# EN: Define async function `scratchpad_get`.
		# JP: 非同期関数 `scratchpad_get` を定義する。
		@self.registry.action(
			"""【Scratchpad】保存された情報を取得。
- key: 取得するエントリのキー（省略時は全エントリのサマリーを表示）
タスク終了前にScratchpadの内容を確認し、doneアクションで報告する際に活用できます。""",
			param_model=ScratchpadGetAction,
		)
		async def scratchpad_get(params: ScratchpadGetAction, scratchpad: Scratchpad):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if params.key:
				# EN: Assign value to entry.
				# JP: entry に値を代入する。
				entry = scratchpad.get_entry(params.key)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if entry is None:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=f'Scratchpadにキー "{params.key}" が見つかりません')
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = entry.to_summary()
			else:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = scratchpad.to_summary()

			# EN: Assign value to memory.
			# JP: memory に値を代入する。
			memory = f'Scratchpadを取得: {params.key or "全件"}（{scratchpad.count()}件）'
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = f'📝 {memory}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(msg)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=content,
				long_term_memory=memory,
				include_extracted_content_only_once=True,
			)

		# EN: Define async function `scratchpad_clear`.
		# JP: 非同期関数 `scratchpad_clear` を定義する。
		@self.registry.action(
			'【Scratchpad】すべてのエントリをクリア。収集データを全削除します。',
			param_model=ScratchpadClearAction,
		)
		async def scratchpad_clear(_: ScratchpadClearAction, scratchpad: Scratchpad):
			# EN: Assign value to count.
			# JP: count に値を代入する。
			count = scratchpad.count()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			scratchpad.clear()
			# EN: Assign value to memory.
			# JP: memory に値を代入する。
			memory = f'Scratchpadをクリア: {count}件を削除'
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = f'📝 {memory}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(msg)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=f'Scratchpadをクリアしました（{count}件削除）',
				long_term_memory=memory,
			)

	# EN: Define function `_register_done_action`.
	# JP: 関数 `_register_done_action` を定義する。
	def _register_done_action(self, output_model: type[T] | None, display_files_in_done_text: bool = True):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if output_model is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.display_files_in_done_text = display_files_in_done_text

			# EN: Define async function `done`.
			# JP: 非同期関数 `done` を定義する。
			@self.registry.action(
				'Complete task - with return text and if the task is finished (success=True) or not yet completely finished (success=False), because last step is reached',
				param_model=StructuredOutputAction[output_model],
			)
			async def done(params: StructuredOutputAction):
				# Exclude success from the output JSON since it's an internal parameter
				# EN: Assign value to output_dict.
				# JP: output_dict に値を代入する。
				output_dict = params.data.model_dump()

				# Enums are not serializable, convert to string
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for key, value in output_dict.items():
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if isinstance(value, enum.Enum):
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						output_dict[key] = value.value

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					is_done=True,
					success=params.success,
					extracted_content=json.dumps(output_dict, ensure_ascii=False),
					long_term_memory=f'Task completed. Success Status: {params.success}',
				)

		else:

			# EN: Define async function `done`.
			# JP: 非同期関数 `done` を定義する。
			@self.registry.action(
				'Complete task - provide a summary of results for the user. Set success=True if task completed successfully, false otherwise. Text should be your response to the user summarizing results. Include files you would like to display to the user in files_to_display.',
				param_model=DoneAction,
			)
			async def done(params: DoneAction, file_system: FileSystem):
				# EN: Assign value to user_message.
				# JP: user_message に値を代入する。
				user_message = params.text

				# EN: Assign value to len_text.
				# JP: len_text に値を代入する。
				len_text = len(params.text)
				# EN: Assign value to len_max_memory.
				# JP: len_max_memory に値を代入する。
				len_max_memory = 100
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = f'Task completed: {params.success} - {params.text[:len_max_memory]}'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if len_text > len_max_memory:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					memory += f' - {len_text - len_max_memory} more characters'

				# EN: Assign value to attachments.
				# JP: attachments に値を代入する。
				attachments = []
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if params.files_to_display:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self.display_files_in_done_text:
						# EN: Assign value to file_msg.
						# JP: file_msg に値を代入する。
						file_msg = ''
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for file_name in params.files_to_display:
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if file_name == 'todo.md':
								# EN: Continue to the next loop iteration.
								# JP: ループの次の反復に進む。
								continue
							# EN: Assign value to file_content.
							# JP: file_content に値を代入する。
							file_content = file_system.display_file(file_name)
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if file_content:
								# EN: Update variable with augmented assignment.
								# JP: 複合代入で変数を更新する。
								file_msg += f'\n\n{file_name}:\n{file_content}'
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								attachments.append(file_name)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if file_msg:
							# EN: Update variable with augmented assignment.
							# JP: 複合代入で変数を更新する。
							user_message += '\n\nAttachments:'
							# EN: Update variable with augmented assignment.
							# JP: 複合代入で変数を更新する。
							user_message += file_msg
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							logger.warning('Agent wanted to display files but none were found')
					else:
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for file_name in params.files_to_display:
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if file_name == 'todo.md':
								# EN: Continue to the next loop iteration.
								# JP: ループの次の反復に進む。
								continue
							# EN: Assign value to file_content.
							# JP: file_content に値を代入する。
							file_content = file_system.display_file(file_name)
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if file_content:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								attachments.append(file_name)

				# EN: Assign value to attachments.
				# JP: attachments に値を代入する。
				attachments = [str(file_system.get_dir() / file_name) for file_name in attachments]

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					is_done=True,
					success=params.success,
					extracted_content=user_message,
					long_term_memory=memory,
					attachments=attachments,
				)

	# EN: Define function `use_structured_output_action`.
	# JP: 関数 `use_structured_output_action` を定義する。
	def use_structured_output_action(self, output_model: type[T]):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._register_done_action(output_model)

	# Register ---------------------------------------------------------------

	# EN: Define function `action`.
	# JP: 関数 `action` を定義する。
	def action(self, description: str, **kwargs):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Decorator for registering custom actions

		@param description: Describe the LLM what the function does (better description == better function calling)
		"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.registry.action(description, **kwargs)

	# Act --------------------------------------------------------------------
	# EN: Define async function `act`.
	# JP: 非同期関数 `act` を定義する。
	@observe_debug(ignore_input=True, ignore_output=True, name='act')
	@time_execution_sync('--act')
	async def act(
		self,
		action: ActionModel,
		browser_session: BrowserSession,
		#
		page_extraction_llm: BaseChatModel | None = None,
		sensitive_data: dict[str, str | dict[str, str]] | None = None,
		available_file_paths: list[str] | None = None,
		file_system: FileSystem | None = None,
		scratchpad: Scratchpad | None = None,
	) -> ActionResult:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute an action"""

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for action_name, params in action.model_dump(exclude_unset=True).items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if params is not None:
				# Use Laminar span if available, otherwise use no-op context manager
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if Laminar is not None:
					# EN: Assign value to span_context.
					# JP: span_context に値を代入する。
					span_context = Laminar.start_as_current_span(
						name=action_name,
						input={
							'action': action_name,
							'params': params,
						},
						span_type='TOOL',
					)
				else:
					# No-op context manager when lmnr is not available
					# EN: Import required modules.
					# JP: 必要なモジュールをインポートする。
					from contextlib import nullcontext

					# EN: Assign value to span_context.
					# JP: span_context に値を代入する。
					span_context = nullcontext()

				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with span_context:
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to result.
						# JP: result に値を代入する。
						result = await self.registry.execute_action(
							action_name=action_name,
							params=params,
							browser_session=browser_session,
							page_extraction_llm=page_extraction_llm,
							file_system=file_system,
							sensitive_data=sensitive_data,
							available_file_paths=available_file_paths,
							scratchpad=scratchpad,
						)
					except BrowserError as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.error(f'❌ Action {action_name} failed with BrowserError: {str(e)}')
						# EN: Assign value to result.
						# JP: result に値を代入する。
						result = handle_browser_error(e)
					except TimeoutError as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.error(f'❌ Action {action_name} failed with TimeoutError: {str(e)}')
						# EN: Assign value to result.
						# JP: result に値を代入する。
						result = ActionResult(error=f'{action_name} was not executed due to timeout.')
					except Exception as e:
						# Log the original exception with traceback for observability
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.error(f"Action '{action_name}' failed with error: {str(e)}")
						# EN: Assign value to result.
						# JP: result に値を代入する。
						result = ActionResult(error=str(e))

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if Laminar is not None:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						Laminar.set_span_output(result)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(result, str):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(extracted_content=result)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif isinstance(result, ActionResult):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return result
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif result is None:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult()
				else:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError(f'Invalid action result type: {type(result)} of {result}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ActionResult()


# Alias for backwards compatibility
# EN: Assign value to Controller.
# JP: Controller に値を代入する。
Controller = Tools

# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Default browser action handlers using CDP."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import platform

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	ClickElementEvent,
	GetDropdownOptionsEvent,
	GoBackEvent,
	GoForwardEvent,
	RefreshEvent,
	ScrollEvent,
	ScrollToTextEvent,
	SelectDropdownOptionEvent,
	SendKeysEvent,
	TypeTextEvent,
	UploadFileEvent,
	WaitEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserError, URLNotAllowedError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.service import EnhancedDOMTreeNode

# Import EnhancedDOMTreeNode and rebuild event models that have forward references to it
# This must be done after all imports are complete
# EN: Evaluate an expression.
# JP: 式を評価する。
ClickElementEvent.model_rebuild()
# EN: Evaluate an expression.
# JP: 式を評価する。
GetDropdownOptionsEvent.model_rebuild()
# EN: Evaluate an expression.
# JP: 式を評価する。
SelectDropdownOptionEvent.model_rebuild()
# EN: Evaluate an expression.
# JP: 式を評価する。
TypeTextEvent.model_rebuild()
# EN: Evaluate an expression.
# JP: 式を評価する。
ScrollEvent.model_rebuild()
# EN: Evaluate an expression.
# JP: 式を評価する。
UploadFileEvent.model_rebuild()


# EN: Define class `DefaultActionWatchdog`.
# JP: クラス `DefaultActionWatchdog` を定義する。
class DefaultActionWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Handles default browser actions like click, type, and scroll using CDP."""

	# EN: Define async function `on_ClickElementEvent`.
	# JP: 非同期関数 `on_ClickElementEvent` を定義する。
	async def on_ClickElementEvent(self, event: ClickElementEvent) -> dict | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle click request with CDP."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Check if session is alive before attempting any operations
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.browser_session.agent_focus or not self.browser_session.agent_focus.target_id:
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = 'Cannot execute click: browser session is corrupted (target_id=None). Session may have crashed.'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(f'⚠️ {error_msg}')
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise BrowserError(error_msg)

			# Use the provided node
			# EN: Assign value to element_node.
			# JP: element_node に値を代入する。
			element_node = event.node
			# EN: Assign value to index_for_logging.
			# JP: index_for_logging に値を代入する。
			index_for_logging = element_node.element_index or 'unknown'
			# EN: Assign value to starting_target_id.
			# JP: starting_target_id に値を代入する。
			starting_target_id = self.browser_session.agent_focus.target_id

			# Track initial number of tabs to detect new tab opening
			# EN: Assign value to initial_target_ids.
			# JP: initial_target_ids に値を代入する。
			initial_target_ids = await self.browser_session._cdp_get_all_pages()

			# Check if element is a file input (should not be clicked)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session.is_file_input(element_node):
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Index {index_for_logging} - has an element which opens file upload dialog. To upload files please use a specific function to upload files'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(msg)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise BrowserError(
					message=msg,
					long_term_memory=msg,
				)

			# Perform the actual click using internal implementation
			# EN: Assign value to click_metadata.
			# JP: click_metadata に値を代入する。
			click_metadata = None
			# EN: Assign value to click_metadata.
			# JP: click_metadata に値を代入する。
			click_metadata = await self._click_element_node_impl(element_node, while_holding_ctrl=event.while_holding_ctrl)
			# EN: Assign value to download_path.
			# JP: download_path に値を代入する。
			download_path = None  # moved to downloads_watchdog.py

			# Build success message
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if download_path:
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Downloaded file to {download_path}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'💾 {msg}')
			else:
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Clicked button {element_node.node_name}: {element_node.get_all_children_text(max_depth=2)}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'🖱️ {msg}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Element xpath: {element_node.xpath}')

			# Wait a bit for potential new tab to be created
			# This is necessary because tab creation is async and might not be immediate
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(0.1)

			# Note: We don't clear cached state here - let multi_act handle DOM change detection
			# by explicitly rebuilding and comparing when needed
			# Successfully clicked, always reset session back to parent page session context
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.browser_session.agent_focus = await self.browser_session.get_or_create_cdp_session(
				target_id=starting_target_id, focus=True
			)

			# Check if a new tab was opened
			# EN: Assign value to after_target_ids.
			# JP: after_target_ids に値を代入する。
			after_target_ids = await self.browser_session._cdp_get_all_pages()
			# EN: Assign value to new_target_ids.
			# JP: new_target_ids に値を代入する。
			new_target_ids = {t['targetId'] for t in after_target_ids} - {t['targetId'] for t in initial_target_ids}
			# EN: Assign value to new_tab_opened.
			# JP: new_tab_opened に値を代入する。
			new_tab_opened = len(new_target_ids) > 0

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if new_target_ids:
				# EN: Assign value to new_tab_msg.
				# JP: new_tab_msg に値を代入する。
				new_tab_msg = 'New tab opened - switching to it'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				msg += f' - {new_tab_msg}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'🔗 {new_tab_msg}')

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not event.while_holding_ctrl:
					# if while_holding_ctrl=False it means agent was not expecting a new tab to be opened
					# so we need to switch to the new tab to make the agent aware of the surprise new tab that was opened.
					# when while_holding_ctrl=True we dont actually want to switch to it,
					# we should match human expectations of ctrl+click which opens in the background,
					# so in multi_act it usually already sends [click_element_by_index(123, while_holding_ctrl=True), switch_tab(tab_id=None)] anyway
					# EN: Import required modules.
					# JP: 必要なモジュールをインポートする。
					from browser_use.browser.events import SwitchTabEvent

					# EN: Assign value to new_target_id.
					# JP: new_target_id に値を代入する。
					new_target_id = new_target_ids.pop()
					# EN: Assign value to switch_event.
					# JP: switch_event に値を代入する。
					switch_event = await self.event_bus.dispatch(SwitchTabEvent(target_id=new_target_id))
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await switch_event

			# Return click metadata including new tab information
			# EN: Assign value to result_metadata.
			# JP: result_metadata に値を代入する。
			result_metadata = click_metadata if isinstance(click_metadata, dict) else {}
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			result_metadata['new_tab_opened'] = new_tab_opened

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return result_metadata
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_TypeTextEvent`.
	# JP: 非同期関数 `on_TypeTextEvent` を定義する。
	async def on_TypeTextEvent(self, event: TypeTextEvent) -> dict | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle text input request with CDP."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Use the provided node
			# EN: Assign value to element_node.
			# JP: element_node に値を代入する。
			element_node = event.node
			# EN: Assign value to index_for_logging.
			# JP: index_for_logging に値を代入する。
			index_for_logging = element_node.element_index or 'unknown'

			# Check if this is index 0 or a falsy index - type to the page (whatever has focus)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not element_node.element_index or element_node.element_index == 0:
				# Type to the page without focusing any specific element
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._type_to_page(event.text)
				# Log with sensitive data protection
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if event.is_sensitive:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if event.sensitive_key_name:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.info(f'⌨️ Typed <{event.sensitive_key_name}> to the page (current focus)')
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.info('⌨️ Typed <sensitive> to the page (current focus)')
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.info(f'⌨️ Typed "{event.text}" to the page (current focus)')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None  # No coordinates available for page typing
			else:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# Try to type to the specific element
					# EN: Assign value to input_metadata.
					# JP: input_metadata に値を代入する。
					input_metadata = await self._input_text_element_node_impl(
						element_node,
						event.text,
						clear_existing=event.clear_existing or (not event.text),
						is_sensitive=event.is_sensitive,
					)
					# Log with sensitive data protection
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if event.is_sensitive:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if event.sensitive_key_name:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.info(f'⌨️ Typed <{event.sensitive_key_name}> into element with index {index_for_logging}')
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.info(f'⌨️ Typed <sensitive> into element with index {index_for_logging}')
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.info(f'⌨️ Typed "{event.text}" into element with index {index_for_logging}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Element xpath: {element_node.xpath}')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return input_metadata  # Return coordinates if available
				except Exception as e:
					# Element not found or error - fall back to typing to the page
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'Failed to type to element {index_for_logging}: {e}. Falling back to page typing.')
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.wait_for(self._click_element_node_impl(element_node, while_holding_ctrl=False), timeout=3.0)
					except Exception as e:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._type_to_page(event.text)
					# Log with sensitive data protection
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if event.is_sensitive:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if event.sensitive_key_name:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.info(f'⌨️ Typed <{event.sensitive_key_name}> to the page as fallback')
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.info('⌨️ Typed <sensitive> to the page as fallback')
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.info(f'⌨️ Typed "{event.text}" to the page as fallback')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None  # No coordinates available for fallback typing

			# Note: We don't clear cached state here - let multi_act handle DOM change detection
			# by explicitly rebuilding and comparing when needed
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_ScrollEvent`.
	# JP: 非同期関数 `on_ScrollEvent` を定義する。
	async def on_ScrollEvent(self, event: ScrollEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle scroll request with CDP."""
		# Check if we have a current target for scrolling
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session.agent_focus:
			# EN: Assign value to error_msg.
			# JP: error_msg に値を代入する。
			error_msg = 'No active target for scrolling'
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise BrowserError(error_msg)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Convert direction and amount to pixels
			# Positive pixels = scroll down, negative = scroll up
			# EN: Assign value to pixels.
			# JP: pixels に値を代入する。
			pixels = event.amount if event.direction == 'down' else -event.amount

			# CRITICAL: CDP calls time out without this, even if the target is already active
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.browser_session.agent_focus.cdp_client.send.Target.activateTarget(
				params={'targetId': self.browser_session.agent_focus.target_id}
			)

			# Element-specific scrolling if node is provided
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if event.node is not None:
				# EN: Assign value to element_node.
				# JP: element_node に値を代入する。
				element_node = event.node
				# EN: Assign value to index_for_logging.
				# JP: index_for_logging に値を代入する。
				index_for_logging = element_node.backend_node_id or 'unknown'

				# Check if the element is an iframe
				# EN: Assign value to is_iframe.
				# JP: is_iframe に値を代入する。
				is_iframe = element_node.tag_name and element_node.tag_name.upper() == 'IFRAME'

				# Try to scroll the element's container
				# EN: Assign value to success.
				# JP: success に値を代入する。
				success = await self._scroll_element_container(element_node, pixels)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if success:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f'📜 Scrolled element {index_for_logging} container {event.direction} by {event.amount} pixels'
					)

					# CRITICAL: For iframe scrolling, we need to force a full DOM refresh
					# because the iframe's content has changed position
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if is_iframe:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug('🔄 Forcing DOM refresh after iframe scroll')
						# Note: We don't clear cached state here - let multi_act handle DOM change detection
						# by explicitly rebuilding and comparing when needed

						# Wait a bit for the scroll to settle and DOM to update
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.sleep(0.2)

					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None

			# Perform target-level scroll
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._scroll_with_cdp_gesture(pixels)

			# CRITICAL: CDP calls time out without this, even if the target is already active
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.browser_session.agent_focus.cdp_client.send.Target.activateTarget(
				params={'targetId': self.browser_session.agent_focus.target_id}
			)

			# Note: We don't clear cached state here - let multi_act handle DOM change detection
			# by explicitly rebuilding and comparing when needed

			# Log success
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📜 Scrolled {event.direction} by {event.amount} pixels')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# ========== Implementation Methods ==========

	# EN: Define async function `_click_element_node_impl`.
	# JP: 非同期関数 `_click_element_node_impl` を定義する。
	async def _click_element_node_impl(self, element_node, while_holding_ctrl: bool = False) -> dict | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Click an element using pure CDP with multiple fallback methods for getting element geometry.

		Args:
			element_node: The DOM element to click
			new_tab: If True, open any resulting navigation in a new tab
		"""

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Check if element is a file input or select dropdown - these should not be clicked
			# EN: Assign value to tag_name.
			# JP: tag_name に値を代入する。
			tag_name = element_node.tag_name.lower() if element_node.tag_name else ''
			# EN: Assign value to element_type.
			# JP: element_type に値を代入する。
			element_type = element_node.attributes.get('type', '').lower() if element_node.attributes else ''

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if tag_name == 'select':
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Cannot click on <select> elements. Use get_dropdown_options(index={element_node.element_index}) action instead.'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(msg)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise BrowserError(
					message=msg,
					long_term_memory=msg,
				)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if tag_name == 'input' and element_type == 'file':
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Cannot click on file input element (index={element_node.element_index}). File uploads must be handled using upload_file_to_element action.'
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise BrowserError(
					message=msg,
					long_term_memory=msg,
				)

			# Get CDP client
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.cdp_client_for_node(element_node)

			# Get the correct session ID for the element's frame
			# EN: Assign value to session_id.
			# JP: session_id に値を代入する。
			session_id = cdp_session.session_id

			# Get element bounds
			# EN: Assign value to backend_node_id.
			# JP: backend_node_id に値を代入する。
			backend_node_id = element_node.backend_node_id

			# Get viewport dimensions for visibility checks
			# EN: Assign value to layout_metrics.
			# JP: layout_metrics に値を代入する。
			layout_metrics = await cdp_session.cdp_client.send.Page.getLayoutMetrics(session_id=session_id)
			# EN: Assign value to viewport_width.
			# JP: viewport_width に値を代入する。
			viewport_width = layout_metrics['layoutViewport']['clientWidth']
			# EN: Assign value to viewport_height.
			# JP: viewport_height に値を代入する。
			viewport_height = layout_metrics['layoutViewport']['clientHeight']

			# Try multiple methods to get element geometry
			# EN: Assign value to quads.
			# JP: quads に値を代入する。
			quads = []

			# Method 1: Try DOM.getContentQuads first (best for inline elements and complex layouts)
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to content_quads_result.
				# JP: content_quads_result に値を代入する。
				content_quads_result = await cdp_session.cdp_client.send.DOM.getContentQuads(
					params={'backendNodeId': backend_node_id}, session_id=session_id
				)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'quads' in content_quads_result and content_quads_result['quads']:
					# EN: Assign value to quads.
					# JP: quads に値を代入する。
					quads = content_quads_result['quads']
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Got {len(quads)} quads from DOM.getContentQuads')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'DOM.getContentQuads failed: {e}')

			# Method 2: Fall back to DOM.getBoxModel
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not quads:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to box_model.
					# JP: box_model に値を代入する。
					box_model = await cdp_session.cdp_client.send.DOM.getBoxModel(
						params={'backendNodeId': backend_node_id}, session_id=session_id
					)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'model' in box_model and 'content' in box_model['model']:
						# EN: Assign value to content_quad.
						# JP: content_quad に値を代入する。
						content_quad = box_model['model']['content']
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if len(content_quad) >= 8:
							# Convert box model format to quad format
							# EN: Assign value to quads.
							# JP: quads に値を代入する。
							quads = [
								[
									content_quad[0],
									content_quad[1],  # x1, y1
									content_quad[2],
									content_quad[3],  # x2, y2
									content_quad[4],
									content_quad[5],  # x3, y3
									content_quad[6],
									content_quad[7],  # x4, y4
								]
							]
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug('Got quad from DOM.getBoxModel')
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'DOM.getBoxModel failed: {e}')

			# Method 3: Fall back to JavaScript getBoundingClientRect
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not quads:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = await cdp_session.cdp_client.send.DOM.resolveNode(
						params={'backendNodeId': backend_node_id},
						session_id=session_id,
					)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'object' in result and 'objectId' in result['object']:
						# EN: Assign value to object_id.
						# JP: object_id に値を代入する。
						object_id = result['object']['objectId']

						# Get bounding rect via JavaScript
						# EN: Assign value to bounds_result.
						# JP: bounds_result に値を代入する。
						bounds_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
							params={
								'functionDeclaration': """
									function() {
										const rect = this.getBoundingClientRect();
										return {
											x: rect.left,
											y: rect.top,
											width: rect.width,
											height: rect.height
										};
									}
								""",
								'objectId': object_id,
								'returnByValue': True,
							},
							session_id=session_id,
						)

						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if 'result' in bounds_result and 'value' in bounds_result['result']:
							# EN: Assign value to rect.
							# JP: rect に値を代入する。
							rect = bounds_result['result']['value']
							# Convert rect to quad format
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							x, y, w, h = rect['x'], rect['y'], rect['width'], rect['height']
							# EN: Assign value to quads.
							# JP: quads に値を代入する。
							quads = [
								[
									x,
									y,  # top-left
									x + w,
									y,  # top-right
									x + w,
									y + h,  # bottom-right
									x,
									y + h,  # bottom-left
								]
							]
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug('Got quad from getBoundingClientRect')
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'JavaScript getBoundingClientRect failed: {e}')

			# If we still don't have quads, fall back to JS click
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not quads:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning('⚠️ Could not get element geometry from any method, falling back to JavaScript click')
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = await cdp_session.cdp_client.send.DOM.resolveNode(
						params={'backendNodeId': backend_node_id},
						session_id=session_id,
					)
					# EN: Validate a required condition.
					# JP: 必須条件を検証する。
					assert 'object' in result and 'objectId' in result['object'], (
						'Failed to find DOM element based on backendNodeId, maybe page content changed?'
					)
					# EN: Assign value to object_id.
					# JP: object_id に値を代入する。
					object_id = result['object']['objectId']

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': 'function() { this.click(); }',
							'objectId': object_id,
						},
						session_id=session_id,
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(0.05)
					# Navigation is handled by BrowserSession via events
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None
				except Exception as js_e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'CDP JavaScript click also failed: {js_e}')
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise Exception(f'Failed to click element: {js_e}')

			# Find the largest visible quad within the viewport
			# EN: Assign value to best_quad.
			# JP: best_quad に値を代入する。
			best_quad = None
			# EN: Assign value to best_area.
			# JP: best_area に値を代入する。
			best_area = 0

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for quad in quads:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if len(quad) < 8:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# Calculate quad bounds
				# EN: Assign value to xs.
				# JP: xs に値を代入する。
				xs = [quad[i] for i in range(0, 8, 2)]
				# EN: Assign value to ys.
				# JP: ys に値を代入する。
				ys = [quad[i] for i in range(1, 8, 2)]
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				min_x, max_x = min(xs), max(xs)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				min_y, max_y = min(ys), max(ys)

				# Check if quad intersects with viewport
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if max_x < 0 or max_y < 0 or min_x > viewport_width or min_y > viewport_height:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue  # Quad is completely outside viewport

				# Calculate visible area (intersection with viewport)
				# EN: Assign value to visible_min_x.
				# JP: visible_min_x に値を代入する。
				visible_min_x = max(0, min_x)
				# EN: Assign value to visible_max_x.
				# JP: visible_max_x に値を代入する。
				visible_max_x = min(viewport_width, max_x)
				# EN: Assign value to visible_min_y.
				# JP: visible_min_y に値を代入する。
				visible_min_y = max(0, min_y)
				# EN: Assign value to visible_max_y.
				# JP: visible_max_y に値を代入する。
				visible_max_y = min(viewport_height, max_y)

				# EN: Assign value to visible_width.
				# JP: visible_width に値を代入する。
				visible_width = visible_max_x - visible_min_x
				# EN: Assign value to visible_height.
				# JP: visible_height に値を代入する。
				visible_height = visible_max_y - visible_min_y
				# EN: Assign value to visible_area.
				# JP: visible_area に値を代入する。
				visible_area = visible_width * visible_height

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if visible_area > best_area:
					# EN: Assign value to best_area.
					# JP: best_area に値を代入する。
					best_area = visible_area
					# EN: Assign value to best_quad.
					# JP: best_quad に値を代入する。
					best_quad = quad

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not best_quad:
				# No visible quad found, use the first quad anyway
				# EN: Assign value to best_quad.
				# JP: best_quad に値を代入する。
				best_quad = quads[0]
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning('No visible quad found, using first quad')

			# Calculate center point of the best quad
			# EN: Assign value to center_x.
			# JP: center_x に値を代入する。
			center_x = sum(best_quad[i] for i in range(0, 8, 2)) / 4
			# EN: Assign value to center_y.
			# JP: center_y に値を代入する。
			center_y = sum(best_quad[i] for i in range(1, 8, 2)) / 4

			# Ensure click point is within viewport bounds
			# EN: Assign value to center_x.
			# JP: center_x に値を代入する。
			center_x = max(0, min(viewport_width - 1, center_x))
			# EN: Assign value to center_y.
			# JP: center_y に値を代入する。
			center_y = max(0, min(viewport_height - 1, center_y))

			# Scroll element into view
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.DOM.scrollIntoViewIfNeeded(
					params={'backendNodeId': backend_node_id}, session_id=session_id
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.05)  # Wait for scroll to complete
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Failed to scroll element into view: {e}')

			# Perform the click using CDP
			# TODO: do occlusion detection first, if element is not on the top, fire JS-based
			# click event instead using xpath of x,y coordinate clicking, because we wont be able to click *through* occluding elements using x,y clicks
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'👆 Dragging mouse over element before clicking x: {center_x}px y: {center_y}px ...')
				# Move mouse to element
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mouseMoved',
						'x': center_x,
						'y': center_y,
					},
					session_id=session_id,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.05)

				# Calculate modifier bitmask for CDP
				# CDP Modifier bits: Alt=1, Control=2, Meta/Command=4, Shift=8
				# EN: Assign value to modifiers.
				# JP: modifiers に値を代入する。
				modifiers = 0
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if while_holding_ctrl:
					# Use platform-appropriate modifier for "open in new tab"
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if platform.system() == 'Darwin':
						# EN: Assign value to modifiers.
						# JP: modifiers に値を代入する。
						modifiers = 4  # Meta/Cmd key
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug('⌘ Using Cmd modifier for new tab click...')
					else:
						# EN: Assign value to modifiers.
						# JP: modifiers に値を代入する。
						modifiers = 2  # Control key
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug('⌃ Using Ctrl modifier for new tab click...')

				# Mouse down
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'👆🏾 Clicking x: {center_x}px y: {center_y}px with modifiers: {modifiers} ...')
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.wait_for(
						cdp_session.cdp_client.send.Input.dispatchMouseEvent(
							params={
								'type': 'mousePressed',
								'x': center_x,
								'y': center_y,
								'button': 'left',
								'clickCount': 1,
								'modifiers': modifiers,
							},
							session_id=session_id,
						),
						timeout=1.0,  # 1 second timeout for mousePressed
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(0.08)
				except TimeoutError:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('⏱️ Mouse down timed out (likely due to dialog), continuing...')
					# Don't sleep if we timed out

				# Mouse up
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.wait_for(
						cdp_session.cdp_client.send.Input.dispatchMouseEvent(
							params={
								'type': 'mouseReleased',
								'x': center_x,
								'y': center_y,
								'button': 'left',
								'clickCount': 1,
								'modifiers': modifiers,
							},
							session_id=session_id,
						),
						timeout=3.0,  # 1 second timeout for mouseReleased
					)
				except TimeoutError:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('⏱️ Mouse up timed out (possibly due to lag or dialog popup), continuing...')

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🖱️ Clicked successfully using x,y coordinates')
				# Return coordinates as dict for metadata
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return {'click_x': center_x, 'click_y': center_y}

			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'CDP click failed: {type(e).__name__}: {e}')
				# Fall back to JavaScript click via CDP
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = await cdp_session.cdp_client.send.DOM.resolveNode(
						params={'backendNodeId': backend_node_id},
						session_id=session_id,
					)
					# EN: Validate a required condition.
					# JP: 必須条件を検証する。
					assert 'object' in result and 'objectId' in result['object'], (
						'Failed to find DOM element based on backendNodeId, maybe page content changed?'
					)
					# EN: Assign value to object_id.
					# JP: object_id に値を代入する。
					object_id = result['object']['objectId']

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': 'function() { this.click(); }',
							'objectId': object_id,
						},
						session_id=session_id,
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(0.1)
					# Navigation is handled by BrowserSession via events
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None
				except Exception as js_e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'CDP JavaScript click also failed: {js_e}')
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise Exception(f'Failed to click element: {e}')
			finally:
				# always re-focus back to original top-level page session context in case click opened a new tab/popup/window/dialog/etc.
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = await self.browser_session.get_or_create_cdp_session(focus=True)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Target.activateTarget(params={'targetId': cdp_session.target_id})
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Runtime.runIfWaitingForDebugger(session_id=cdp_session.session_id)

		except URLNotAllowedError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise e
		except BrowserError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise e
		except Exception as e:
			# Extract key element info for error message
			# EN: Assign value to element_info.
			# JP: element_info に値を代入する。
			element_info = f'<{element_node.tag_name or "unknown"}'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if element_node.element_index:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				element_info += f' index={element_node.element_index}'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			element_info += '>'
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise BrowserError(
				message=f'Failed to click element: {e}',
				long_term_memory=f'Failed to click element {element_info}. The element may not be interactable or visible.',
			)

	# EN: Define async function `_type_to_page`.
	# JP: 非同期関数 `_type_to_page` を定義する。
	async def _type_to_page(self, text: str):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Type text to the page (whatever element currently has focus).
		This is used when index is 0 or when an element can't be found.
		"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get CDP client and session
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=None, focus=True)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Target.activateTarget(params={'targetId': cdp_session.target_id})

			# Type the text character by character to the focused element
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for char in text:
				# Handle newline characters as Enter key
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if char == '\n':
					# Send proper Enter key sequence
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': 'Enter',
							'code': 'Enter',
							'windowsVirtualKeyCode': 13,
						},
						session_id=cdp_session.session_id,
					)
					# Send char event with carriage return
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': '\r',
						},
						session_id=cdp_session.session_id,
					)
					# Send keyup
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': 'Enter',
							'code': 'Enter',
							'windowsVirtualKeyCode': 13,
						},
						session_id=cdp_session.session_id,
					)
				else:
					# Handle regular characters
					# Send keydown
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': char,
						},
						session_id=cdp_session.session_id,
					)
					# Send char for actual text input
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': char,
						},
						session_id=cdp_session.session_id,
					)
					# Send keyup
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': char,
						},
						session_id=cdp_session.session_id,
					)
				# Add 18ms delay between keystrokes
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.018)

		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise Exception(f'Failed to type to page: {str(e)}')

	# EN: Define function `_get_char_modifiers_and_vk`.
	# JP: 関数 `_get_char_modifiers_and_vk` を定義する。
	def _get_char_modifiers_and_vk(self, char: str) -> tuple[int, int, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get modifiers, virtual key code, and base key for a character.

		Returns:
			(modifiers, windowsVirtualKeyCode, base_key)
		"""
		# Characters that require Shift modifier
		# EN: Assign value to shift_chars.
		# JP: shift_chars に値を代入する。
		shift_chars = {
			'!': ('1', 49),
			'@': ('2', 50),
			'#': ('3', 51),
			'$': ('4', 52),
			'%': ('5', 53),
			'^': ('6', 54),
			'&': ('7', 55),
			'*': ('8', 56),
			'(': ('9', 57),
			')': ('0', 48),
			'_': ('-', 189),
			'+': ('=', 187),
			'{': ('[', 219),
			'}': (']', 221),
			'|': ('\\', 220),
			':': (';', 186),
			'"': ("'", 222),
			'<': (',', 188),
			'>': ('.', 190),
			'?': ('/', 191),
			'~': ('`', 192),
		}

		# Check if character requires Shift
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if char in shift_chars:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			base_key, vk_code = shift_chars[char]
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return (8, vk_code, base_key)  # Shift=8

		# Uppercase letters require Shift
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if char.isupper():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return (8, ord(char), char.lower())  # Shift=8

		# Lowercase letters
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if char.islower():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return (0, ord(char.upper()), char)

		# Numbers
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if char.isdigit():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return (0, ord(char), char)

		# Special characters without Shift
		# EN: Assign value to no_shift_chars.
		# JP: no_shift_chars に値を代入する。
		no_shift_chars = {
			' ': 32,
			'-': 189,
			'=': 187,
			'[': 219,
			']': 221,
			'\\': 220,
			';': 186,
			"'": 222,
			',': 188,
			'.': 190,
			'/': 191,
			'`': 192,
		}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if char in no_shift_chars:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return (0, no_shift_chars[char], char)

		# Fallback
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (0, ord(char.upper()) if char.isalpha() else ord(char), char)

	# EN: Define function `_get_key_code_for_char`.
	# JP: 関数 `_get_key_code_for_char` を定義する。
	def _get_key_code_for_char(self, char: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the proper key code for a character (like Playwright does)."""
		# Key code mapping for common characters (using proper base keys + modifiers)
		# EN: Assign value to key_codes.
		# JP: key_codes に値を代入する。
		key_codes = {
			' ': 'Space',
			'.': 'Period',
			',': 'Comma',
			'-': 'Minus',
			'_': 'Minus',  # Underscore uses Minus with Shift
			'@': 'Digit2',  # @ uses Digit2 with Shift
			'!': 'Digit1',  # ! uses Digit1 with Shift (not 'Exclamation')
			'?': 'Slash',  # ? uses Slash with Shift
			':': 'Semicolon',  # : uses Semicolon with Shift
			';': 'Semicolon',
			'(': 'Digit9',  # ( uses Digit9 with Shift
			')': 'Digit0',  # ) uses Digit0 with Shift
			'[': 'BracketLeft',
			']': 'BracketRight',
			'{': 'BracketLeft',  # { uses BracketLeft with Shift
			'}': 'BracketRight',  # } uses BracketRight with Shift
			'/': 'Slash',
			'\\': 'Backslash',
			'=': 'Equal',
			'+': 'Equal',  # + uses Equal with Shift
			'*': 'Digit8',  # * uses Digit8 with Shift
			'&': 'Digit7',  # & uses Digit7 with Shift
			'%': 'Digit5',  # % uses Digit5 with Shift
			'$': 'Digit4',  # $ uses Digit4 with Shift
			'#': 'Digit3',  # # uses Digit3 with Shift
			'^': 'Digit6',  # ^ uses Digit6 with Shift
			'~': 'Backquote',  # ~ uses Backquote with Shift
			'`': 'Backquote',
			"'": 'Quote',
			'"': 'Quote',  # " uses Quote with Shift
		}

		# Numbers
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if char.isdigit():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Digit{char}'

		# Letters
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if char.isalpha():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Key{char.upper()}'

		# Special characters
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if char in key_codes:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return key_codes[char]

		# Fallback for unknown characters
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Key{char.upper()}'

	# EN: Define async function `_clear_text_field`.
	# JP: 非同期関数 `_clear_text_field` を定義する。
	async def _clear_text_field(self, object_id: str, cdp_session) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear text field using multiple strategies, starting with the most reliable."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Strategy 1: Direct JavaScript value setting (most reliable for modern web apps)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🧹 Clearing text field using JavaScript value setting')

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Runtime.callFunctionOn(
				params={
					'functionDeclaration': """
						function() { 
							this.value = ""; 
							this.dispatchEvent(new Event("input", { bubbles: true })); 
							this.dispatchEvent(new Event("change", { bubbles: true })); 
							return this.value;
						}
					""",
					'objectId': object_id,
					'returnByValue': True,
				},
				session_id=cdp_session.session_id,
			)

			# Verify clearing worked by checking the value
			# EN: Assign value to verify_result.
			# JP: verify_result に値を代入する。
			verify_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
				params={
					'functionDeclaration': 'function() { return this.value; }',
					'objectId': object_id,
					'returnByValue': True,
				},
				session_id=cdp_session.session_id,
			)

			# EN: Assign value to current_value.
			# JP: current_value に値を代入する。
			current_value = verify_result.get('result', {}).get('value', '')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not current_value:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('✅ Text field cleared successfully using JavaScript')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'⚠️ JavaScript clear partially failed, field still contains: "{current_value}"')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'JavaScript clear failed: {e}')

		# Strategy 2: Triple-click + Delete (fallback for stubborn fields)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('🧹 Fallback: Clearing using triple-click + Delete')

			# Get element center coordinates for triple-click
			# EN: Assign value to bounds_result.
			# JP: bounds_result に値を代入する。
			bounds_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
				params={
					'functionDeclaration': 'function() { return this.getBoundingClientRect(); }',
					'objectId': object_id,
					'returnByValue': True,
				},
				session_id=cdp_session.session_id,
			)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if bounds_result.get('result', {}).get('value'):
				# EN: Assign value to bounds.
				# JP: bounds に値を代入する。
				bounds = bounds_result['result']['value']
				# EN: Assign value to center_x.
				# JP: center_x に値を代入する。
				center_x = bounds['x'] + bounds['width'] / 2
				# EN: Assign value to center_y.
				# JP: center_y に値を代入する。
				center_y = bounds['y'] + bounds['height'] / 2

				# Triple-click to select all text
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mousePressed',
						'x': center_x,
						'y': center_y,
						'button': 'left',
						'clickCount': 3,
					},
					session_id=cdp_session.session_id,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mouseReleased',
						'x': center_x,
						'y': center_y,
						'button': 'left',
						'clickCount': 3,
					},
					session_id=cdp_session.session_id,
				)

				# Delete selected text
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
					params={
						'type': 'keyDown',
						'key': 'Delete',
						'code': 'Delete',
					},
					session_id=cdp_session.session_id,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
					params={
						'type': 'keyUp',
						'key': 'Delete',
						'code': 'Delete',
					},
					session_id=cdp_session.session_id,
				)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('✅ Text field cleared using triple-click + Delete')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Triple-click clear failed: {e}')

		# Strategy 3: Keyboard shortcuts (last resort)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import platform

			# EN: Assign value to is_macos.
			# JP: is_macos に値を代入する。
			is_macos = platform.system() == 'Darwin'
			# EN: Assign value to select_all_modifier.
			# JP: select_all_modifier に値を代入する。
			select_all_modifier = 4 if is_macos else 2  # Meta=4 (Cmd), Ctrl=2
			# EN: Assign value to modifier_name.
			# JP: modifier_name に値を代入する。
			modifier_name = 'Cmd' if is_macos else 'Ctrl'

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'🧹 Last resort: Clearing using {modifier_name}+A + Backspace')

			# Select all text (Ctrl/Cmd+A)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
				params={
					'type': 'keyDown',
					'key': 'a',
					'code': 'KeyA',
					'modifiers': select_all_modifier,
				},
				session_id=cdp_session.session_id,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
				params={
					'type': 'keyUp',
					'key': 'a',
					'code': 'KeyA',
					'modifiers': select_all_modifier,
				},
				session_id=cdp_session.session_id,
			)

			# Delete selected text (Backspace)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
				params={
					'type': 'keyDown',
					'key': 'Backspace',
					'code': 'Backspace',
				},
				session_id=cdp_session.session_id,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
				params={
					'type': 'keyUp',
					'key': 'Backspace',
					'code': 'Backspace',
				},
				session_id=cdp_session.session_id,
			)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('✅ Text field cleared using keyboard shortcuts')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'All clearing strategies failed: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# EN: Define async function `_focus_element_simple`.
	# JP: 非同期関数 `_focus_element_simple` を定義する。
	async def _focus_element_simple(
		self, backend_node_id: int, object_id: str, cdp_session, input_coordinates: dict | None = None
	) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Simple focus strategy: CDP first, then click if failed."""

		# Strategy 1: Try CDP DOM.focus first
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await cdp_session.cdp_client.send.DOM.focus(
				params={'backendNodeId': backend_node_id},
				session_id=cdp_session.session_id,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Element focused using CDP DOM.focus (result: {result})')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'❌ CDP DOM.focus threw exception: {type(e).__name__}: {e}')

		# Strategy 2: Try click to focus if CDP failed
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if input_coordinates and 'input_x' in input_coordinates and 'input_y' in input_coordinates:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to click_x.
				# JP: click_x に値を代入する。
				click_x = input_coordinates['input_x']
				# EN: Assign value to click_y.
				# JP: click_y に値を代入する。
				click_y = input_coordinates['input_y']

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'🎯 Attempting click-to-focus at ({click_x:.1f}, {click_y:.1f})')

				# Click to focus
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mousePressed',
						'x': click_x,
						'y': click_y,
						'button': 'left',
						'clickCount': 1,
					},
					session_id=cdp_session.session_id,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mouseReleased',
						'x': click_x,
						'y': click_y,
						'button': 'left',
						'clickCount': 1,
					},
					session_id=cdp_session.session_id,
				)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('✅ Element focused using click method')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Click focus failed: {e}')

		# Both strategies failed
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.warning('⚠️ All focus strategies failed')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define async function `_input_text_element_node_impl`.
	# JP: 非同期関数 `_input_text_element_node_impl` を定義する。
	async def _input_text_element_node_impl(
		self, element_node: EnhancedDOMTreeNode, text: str, clear_existing: bool = True, is_sensitive: bool = False
	) -> dict | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Input text into an element using pure CDP with improved focus fallbacks.
		"""

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get CDP client
			# EN: Assign value to cdp_client.
			# JP: cdp_client に値を代入する。
			cdp_client = self.browser_session.cdp_client

			# Get the correct session ID for the element's iframe
			# session_id = await self._get_session_id_for_element(element_node)

			# cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=element_node.target_id, focus=True)
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.cdp_client_for_node(element_node)

			# Get element info
			# EN: Assign value to backend_node_id.
			# JP: backend_node_id に値を代入する。
			backend_node_id = element_node.backend_node_id

			# Track coordinates for metadata
			# EN: Assign value to input_coordinates.
			# JP: input_coordinates に値を代入する。
			input_coordinates = None

			# Scroll element into view
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.DOM.scrollIntoViewIfNeeded(
					params={'backendNodeId': backend_node_id}, session_id=cdp_session.session_id
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.01)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(
					f'⚠️ Failed to focus the page {cdp_session} and scroll element {element_node} into view before typing in text: {type(e).__name__}: {e}'
				)

			# Get object ID for the element
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await cdp_client.send.DOM.resolveNode(
				params={'backendNodeId': backend_node_id},
				session_id=cdp_session.session_id,
			)
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert 'object' in result and 'objectId' in result['object'], (
				'Failed to find DOM element based on backendNodeId, maybe page content changed?'
			)
			# EN: Assign value to object_id.
			# JP: object_id に値を代入する。
			object_id = result['object']['objectId']

			# Use element_node absolute_position coordinates (correct coordinates including iframe offsets)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if element_node.absolute_position:
				# EN: Assign value to center_x.
				# JP: center_x に値を代入する。
				center_x = element_node.absolute_position.x + element_node.absolute_position.width / 2
				# EN: Assign value to center_y.
				# JP: center_y に値を代入する。
				center_y = element_node.absolute_position.y + element_node.absolute_position.height / 2
				# EN: Assign value to input_coordinates.
				# JP: input_coordinates に値を代入する。
				input_coordinates = {'input_x': center_x, 'input_y': center_y}
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Using absolute_position coordinates: x={center_x:.1f}, y={center_y:.1f}')
			else:
				# EN: Assign value to input_coordinates.
				# JP: input_coordinates に値を代入する。
				input_coordinates = None
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning('⚠️ No absolute_position available for element')

			# Ensure we have a valid object_id before proceeding
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not object_id:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError('Could not get object_id for element')

			# Step 1: Focus the element using simple strategy
			# EN: Assign value to focused_successfully.
			# JP: focused_successfully に値を代入する。
			focused_successfully = await self._focus_element_simple(
				backend_node_id=backend_node_id, object_id=object_id, cdp_session=cdp_session, input_coordinates=input_coordinates
			)

			# Step 2: Clear existing text if requested
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if clear_existing and focused_successfully:
				# EN: Assign value to cleared_successfully.
				# JP: cleared_successfully に値を代入する。
				cleared_successfully = await self._clear_text_field(object_id=object_id, cdp_session=cdp_session)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not cleared_successfully:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning('⚠️ Text field clearing failed, typing may append to existing text')

			# Step 3: Type the text character by character using proper human-like key events
			# This emulates exactly how a human would type, which modern websites expect
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if is_sensitive:
				# Note: sensitive_key_name is not passed to this low-level method,
				# but we could extend the signature if needed for more granular logging
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('🎯 Typing <sensitive> character by character')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'🎯 Typing text character by character: "{text}"')

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, char in enumerate(text):
				# Handle newline characters as Enter key
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if char == '\n':
					# Send proper Enter key sequence
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': 'Enter',
							'code': 'Enter',
							'windowsVirtualKeyCode': 13,
						},
						session_id=cdp_session.session_id,
					)

					# Small delay to emulate human typing speed
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(0.001)

					# Send char event with carriage return
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': '\r',
							'key': 'Enter',
						},
						session_id=cdp_session.session_id,
					)

					# Send keyUp event
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': 'Enter',
							'code': 'Enter',
							'windowsVirtualKeyCode': 13,
						},
						session_id=cdp_session.session_id,
					)
				else:
					# Handle regular characters
					# Get proper modifiers, VK code, and base key for the character
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					modifiers, vk_code, base_key = self._get_char_modifiers_and_vk(char)
					# EN: Assign value to key_code.
					# JP: key_code に値を代入する。
					key_code = self._get_key_code_for_char(base_key)

					# self.logger.debug(f'🎯 Typing character {i + 1}/{len(text)}: "{char}" (base_key: {base_key}, code: {key_code}, modifiers: {modifiers}, vk: {vk_code})')

					# Step 1: Send keyDown event (NO text parameter)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': base_key,
							'code': key_code,
							'modifiers': modifiers,
							'windowsVirtualKeyCode': vk_code,
						},
						session_id=cdp_session.session_id,
					)

					# Small delay to emulate human typing speed
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(0.001)

					# Step 2: Send char event (WITH text parameter) - this is crucial for text input
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': char,
							'key': char,
						},
						session_id=cdp_session.session_id,
					)

					# Step 3: Send keyUp event (NO text parameter)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': base_key,
							'code': key_code,
							'modifiers': modifiers,
							'windowsVirtualKeyCode': vk_code,
						},
						session_id=cdp_session.session_id,
					)

				# Small delay between characters to look human (realistic typing speed)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.001)

			# Return coordinates metadata if available
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return input_coordinates

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'Failed to input text via CDP: {type(e).__name__}: {e}')
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise BrowserError(f'Failed to input text into element: {repr(element_node)}')

	# EN: Define async function `_scroll_with_cdp_gesture`.
	# JP: 非同期関数 `_scroll_with_cdp_gesture` を定義する。
	async def _scroll_with_cdp_gesture(self, pixels: int) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Scroll using CDP Input.dispatchMouseEvent to simulate mouse wheel.

		Args:
			pixels: Number of pixels to scroll (positive = down, negative = up)

		Returns:
			True if successful, False if failed
		"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get CDP client and session
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.browser_session.agent_focus is not None, 'CDP session not initialized - browser may not be connected yet'
			# EN: Assign value to cdp_client.
			# JP: cdp_client に値を代入する。
			cdp_client = self.browser_session.agent_focus.cdp_client
			# EN: Assign value to session_id.
			# JP: session_id に値を代入する。
			session_id = self.browser_session.agent_focus.session_id

			# Get viewport dimensions
			# EN: Assign value to layout_metrics.
			# JP: layout_metrics に値を代入する。
			layout_metrics = await cdp_client.send.Page.getLayoutMetrics(session_id=session_id)
			# EN: Assign value to viewport_width.
			# JP: viewport_width に値を代入する。
			viewport_width = layout_metrics['layoutViewport']['clientWidth']
			# EN: Assign value to viewport_height.
			# JP: viewport_height に値を代入する。
			viewport_height = layout_metrics['layoutViewport']['clientHeight']

			# Calculate center of viewport
			# EN: Assign value to center_x.
			# JP: center_x に値を代入する。
			center_x = viewport_width / 2
			# EN: Assign value to center_y.
			# JP: center_y に値を代入する。
			center_y = viewport_height / 2

			# For mouse wheel, positive deltaY scrolls down, negative scrolls up
			# EN: Assign value to delta_y.
			# JP: delta_y に値を代入する。
			delta_y = pixels

			# Dispatch mouse wheel event
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_client.send.Input.dispatchMouseEvent(
				params={
					'type': 'mouseWheel',
					'x': center_x,
					'y': center_y,
					'deltaX': 0,
					'deltaY': delta_y,
				},
				session_id=session_id,
			)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📄 Scrolled via CDP mouse wheel: {pixels}px')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'❌ Scrolling via CDP failed: {type(e).__name__}: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# EN: Define async function `_scroll_element_container`.
	# JP: 非同期関数 `_scroll_element_container` を定義する。
	async def _scroll_element_container(self, element_node, pixels: int) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Try to scroll an element's container using CDP."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.cdp_client_for_node(element_node)

			# Check if this is an iframe - if so, scroll its content directly
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if element_node.tag_name and element_node.tag_name.upper() == 'IFRAME':
				# For iframes, we need to scroll the content document, not the iframe element itself
				# Use JavaScript to directly scroll the iframe's content
				# EN: Assign value to backend_node_id.
				# JP: backend_node_id に値を代入する。
				backend_node_id = element_node.backend_node_id

				# Resolve the node to get an object ID
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await cdp_session.cdp_client.send.DOM.resolveNode(
					params={'backendNodeId': backend_node_id},
					session_id=cdp_session.session_id,
				)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'object' in result and 'objectId' in result['object']:
					# EN: Assign value to object_id.
					# JP: object_id に値を代入する。
					object_id = result['object']['objectId']

					# Scroll the iframe's content directly
					# EN: Assign value to scroll_result.
					# JP: scroll_result に値を代入する。
					scroll_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': f"""
								function() {{
									try {{
										const doc = this.contentDocument || this.contentWindow.document;
										if (doc) {{
											const scrollElement = doc.documentElement || doc.body;
											if (scrollElement) {{
												const oldScrollTop = scrollElement.scrollTop;
												scrollElement.scrollTop += {pixels};
												const newScrollTop = scrollElement.scrollTop;
												return {{
													success: true,
													oldScrollTop: oldScrollTop,
													newScrollTop: newScrollTop,
													scrolled: newScrollTop - oldScrollTop
												}};
											}}
										}}
										return {{success: false, error: 'Could not access iframe content'}};
									}} catch (e) {{
										return {{success: false, error: e.toString()}};
									}}
								}}
							""",
							'objectId': object_id,
							'returnByValue': True,
						},
						session_id=cdp_session.session_id,
					)

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if scroll_result and 'result' in scroll_result and 'value' in scroll_result['result']:
						# EN: Assign value to result_value.
						# JP: result_value に値を代入する。
						result_value = scroll_result['result']['value']
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if result_value.get('success'):
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug(f'Successfully scrolled iframe content by {result_value.get("scrolled", 0)}px')
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return True
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug(f'Failed to scroll iframe: {result_value.get("error", "Unknown error")}')

			# For non-iframe elements, use the standard mouse wheel approach
			# Get element bounds to know where to scroll
			# EN: Assign value to backend_node_id.
			# JP: backend_node_id に値を代入する。
			backend_node_id = element_node.backend_node_id
			# EN: Assign value to box_model.
			# JP: box_model に値を代入する。
			box_model = await cdp_session.cdp_client.send.DOM.getBoxModel(
				params={'backendNodeId': backend_node_id}, session_id=cdp_session.session_id
			)
			# EN: Assign value to content_quad.
			# JP: content_quad に値を代入する。
			content_quad = box_model['model']['content']

			# Calculate center point
			# EN: Assign value to center_x.
			# JP: center_x に値を代入する。
			center_x = (content_quad[0] + content_quad[2] + content_quad[4] + content_quad[6]) / 4
			# EN: Assign value to center_y.
			# JP: center_y に値を代入する。
			center_y = (content_quad[1] + content_quad[3] + content_quad[5] + content_quad[7]) / 4

			# Dispatch mouse wheel event at element location
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
				params={
					'type': 'mouseWheel',
					'x': center_x,
					'y': center_y,
					'deltaX': 0,
					'deltaY': pixels,
				},
				session_id=cdp_session.session_id,
			)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Failed to scroll element container via CDP: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# EN: Define async function `_get_session_id_for_element`.
	# JP: 非同期関数 `_get_session_id_for_element` を定義する。
	async def _get_session_id_for_element(self, element_node: EnhancedDOMTreeNode) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the appropriate CDP session ID for an element based on its frame."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if element_node.frame_id:
			# Element is in an iframe, need to get session for that frame
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Get all targets
				# EN: Assign value to targets.
				# JP: targets に値を代入する。
				targets = await self.browser_session.cdp_client.send.Target.getTargets()

				# Find the target for this frame
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for target in targets['targetInfos']:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if target['type'] == 'iframe' and element_node.frame_id in str(target.get('targetId', '')):
						# Create temporary session for iframe target without switching focus
						# EN: Assign value to target_id.
						# JP: target_id に値を代入する。
						target_id = target['targetId']
						# EN: Assign value to temp_session.
						# JP: temp_session に値を代入する。
						temp_session = await self.browser_session.get_or_create_cdp_session(target_id, focus=False)
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return temp_session.session_id

				# If frame not found in targets, use main target session
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Frame {element_node.frame_id} not found in targets, using main session')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Error getting frame session: {e}, using main session')

		# Use main target session
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session.agent_focus is not None, 'CDP session not initialized - browser may not be connected yet'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.browser_session.agent_focus.session_id

	# EN: Define async function `on_GoBackEvent`.
	# JP: 非同期関数 `on_GoBackEvent` を定義する。
	async def on_GoBackEvent(self, event: GoBackEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle navigate back request with CDP."""
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.browser_session.get_or_create_cdp_session()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get CDP client and session

			# Get navigation history
			# EN: Assign value to history.
			# JP: history に値を代入する。
			history = await cdp_session.cdp_client.send.Page.getNavigationHistory(session_id=cdp_session.session_id)
			# EN: Assign value to current_index.
			# JP: current_index に値を代入する。
			current_index = history['currentIndex']
			# EN: Assign value to entries.
			# JP: entries に値を代入する。
			entries = history['entries']

			# Check if we can go back
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_index <= 0:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning('⚠️ Cannot go back - no previous entry in history')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Navigate to the previous entry
			# EN: Assign value to previous_entry_id.
			# JP: previous_entry_id に値を代入する。
			previous_entry_id = entries[current_index - 1]['id']
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Page.navigateToHistoryEntry(
				params={'entryId': previous_entry_id}, session_id=cdp_session.session_id
			)

			# Wait for navigation
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(0.5)
			# Navigation is handled by BrowserSession via events

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'🔙 Navigated back to {entries[current_index - 1]["url"]}')
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_GoForwardEvent`.
	# JP: 非同期関数 `on_GoForwardEvent` を定義する。
	async def on_GoForwardEvent(self, event: GoForwardEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle navigate forward request with CDP."""
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.browser_session.get_or_create_cdp_session()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get navigation history
			# EN: Assign value to history.
			# JP: history に値を代入する。
			history = await cdp_session.cdp_client.send.Page.getNavigationHistory(session_id=cdp_session.session_id)
			# EN: Assign value to current_index.
			# JP: current_index に値を代入する。
			current_index = history['currentIndex']
			# EN: Assign value to entries.
			# JP: entries に値を代入する。
			entries = history['entries']

			# Check if we can go forward
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_index >= len(entries) - 1:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning('⚠️ Cannot go forward - no next entry in history')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Navigate to the next entry
			# EN: Assign value to next_entry_id.
			# JP: next_entry_id に値を代入する。
			next_entry_id = entries[current_index + 1]['id']
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Page.navigateToHistoryEntry(
				params={'entryId': next_entry_id}, session_id=cdp_session.session_id
			)

			# Wait for navigation
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(0.5)
			# Navigation is handled by BrowserSession via events

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'🔜 Navigated forward to {entries[current_index + 1]["url"]}')
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_RefreshEvent`.
	# JP: 非同期関数 `on_RefreshEvent` を定義する。
	async def on_RefreshEvent(self, event: RefreshEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle target refresh request with CDP."""
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.browser_session.get_or_create_cdp_session()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Reload the target
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Page.reload(session_id=cdp_session.session_id)

			# Wait for reload
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(1.0)

			# Note: We don't clear cached state here - let the next state fetch rebuild as needed

			# Navigation is handled by BrowserSession via events

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info('🔄 Target refreshed')
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_WaitEvent`.
	# JP: 非同期関数 `on_WaitEvent` を定義する。
	async def on_WaitEvent(self, event: WaitEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle wait request."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Cap wait time at maximum
			# EN: Assign value to actual_seconds.
			# JP: actual_seconds に値を代入する。
			actual_seconds = min(max(event.seconds, 0), event.max_seconds)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if actual_seconds != event.seconds:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'🕒 Waiting for {actual_seconds} seconds (capped from {event.seconds}s)')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'🕒 Waiting for {actual_seconds} seconds')

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(actual_seconds)
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_SendKeysEvent`.
	# JP: 非同期関数 `on_SendKeysEvent` を定義する。
	async def on_SendKeysEvent(self, event: SendKeysEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle send keys request with CDP."""
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.browser_session.get_or_create_cdp_session(focus=True)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Parse key combination
			# EN: Assign value to keys.
			# JP: keys に値を代入する。
			keys = event.keys.lower()

			# Handle special key combinations
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if '+' in keys:
				# Handle modifier keys
				# EN: Assign value to parts.
				# JP: parts に値を代入する。
				parts = keys.split('+')
				# EN: Assign value to key.
				# JP: key に値を代入する。
				key = parts[-1]

				# Calculate modifier bits inline
				# CDP Modifier bits: Alt=1, Control=2, Meta/Command=4, Shift=8
				# EN: Assign value to modifiers.
				# JP: modifiers に値を代入する。
				modifiers = 0
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for part in parts[:-1]:
					# EN: Assign value to part_lower.
					# JP: part_lower に値を代入する。
					part_lower = part.lower()
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if part_lower in ['alt', 'option']:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						modifiers |= 1  # Alt
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif part_lower in ['ctrl', 'control']:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						modifiers |= 2  # Control
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif part_lower in ['meta', 'cmd', 'command']:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						modifiers |= 4  # Meta/Command
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif part_lower in ['shift']:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						modifiers |= 8  # Shift

				# Send key with modifiers
				# Use rawKeyDown for non-text keys (like shortcuts)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
					params={
						'type': 'rawKeyDown',
						'key': key.capitalize() if len(key) == 1 else key,
						'modifiers': modifiers,
					},
					session_id=cdp_session.session_id,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
					params={
						'type': 'keyUp',
						'key': key.capitalize() if len(key) == 1 else key,
						'modifiers': modifiers,
					},
					session_id=cdp_session.session_id,
				)
			else:
				# Single key
				# EN: Assign value to key_map.
				# JP: key_map に値を代入する。
				key_map = {
					'enter': 'Enter',
					'return': 'Enter',
					'tab': 'Tab',
					'delete': 'Delete',
					'backspace': 'Backspace',
					'escape': 'Escape',
					'esc': 'Escape',
					'space': ' ',
					'up': 'ArrowUp',
					'down': 'ArrowDown',
					'left': 'ArrowLeft',
					'right': 'ArrowRight',
					'pageup': 'PageUp',
					'pagedown': 'PageDown',
					'home': 'Home',
					'end': 'End',
				}

				# EN: Assign value to key.
				# JP: key に値を代入する。
				key = key_map.get(keys, keys)

				# Keys that need 3-step sequence (produce characters)
				# EN: Assign value to keys_needing_char_event.
				# JP: keys_needing_char_event に値を代入する。
				keys_needing_char_event = ['enter', 'return', 'space']

				# Virtual key codes for proper key identification
				# EN: Assign value to virtual_key_codes.
				# JP: virtual_key_codes に値を代入する。
				virtual_key_codes = {
					'enter': 13,
					'return': 13,
					'tab': 9,
					'escape': 27,
					'esc': 27,
					'space': 32,
					'backspace': 8,
					'delete': 46,
					'up': 38,
					'down': 40,
					'left': 37,
					'right': 39,
					'home': 36,
					'end': 35,
					'pageup': 33,
					'pagedown': 34,
				}

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if keys in keys_needing_char_event:
					# 3-step sequence for keys that produce characters
					# EN: Assign value to vk_code.
					# JP: vk_code に値を代入する。
					vk_code = virtual_key_codes.get(keys, 0)
					# EN: Assign value to char_text.
					# JP: char_text に値を代入する。
					char_text = '\r' if keys in ['enter', 'return'] else ' ' if keys == 'space' else ''

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'rawKeyDown',
							'windowsVirtualKeyCode': vk_code,
							'code': key_map.get(keys, keys),
							'key': key_map.get(keys, keys),
						},
						session_id=cdp_session.session_id,
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={'type': 'char', 'text': char_text, 'unmodifiedText': char_text},
						session_id=cdp_session.session_id,
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'windowsVirtualKeyCode': vk_code,
							'code': key_map.get(keys, keys),
							'key': key_map.get(keys, keys),
						},
						session_id=cdp_session.session_id,
					)
				else:
					# 2-step sequence for other keys
					# EN: Assign value to key_type.
					# JP: key_type に値を代入する。
					key_type = 'rawKeyDown' if keys in key_map else 'keyDown'
					# EN: Assign value to vk_code.
					# JP: vk_code に値を代入する。
					vk_code = virtual_key_codes.get(keys)

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if vk_code:
						# Special keys with virtual key codes
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={
								'type': key_type,
								'key': key,
								'windowsVirtualKeyCode': vk_code,
								'code': key_map.get(keys, keys),
							},
							session_id=cdp_session.session_id,
						)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={
								'type': 'keyUp',
								'key': key,
								'windowsVirtualKeyCode': vk_code,
								'code': key_map.get(keys, keys),
							},
							session_id=cdp_session.session_id,
						)
					else:
						# Regular characters without virtual key codes
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={'type': key_type, 'key': key},
							session_id=cdp_session.session_id,
						)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={'type': 'keyUp', 'key': key},
							session_id=cdp_session.session_id,
						)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'⌨️ Sent keys: {event.keys}')

			# Note: We don't clear cached state on Enter; multi_act will detect DOM changes
			# and rebuild explicitly. We still wait briefly for potential navigation.
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'enter' in event.keys.lower() or 'return' in event.keys.lower():
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.1)
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_UploadFileEvent`.
	# JP: 非同期関数 `on_UploadFileEvent` を定義する。
	async def on_UploadFileEvent(self, event: UploadFileEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle file upload request with CDP."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Use the provided node
			# EN: Assign value to element_node.
			# JP: element_node に値を代入する。
			element_node = event.node
			# EN: Assign value to index_for_logging.
			# JP: index_for_logging に値を代入する。
			index_for_logging = element_node.element_index or 'unknown'

			# Check if it's a file input
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.browser_session.is_file_input(element_node):
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Upload failed - element {index_for_logging} is not a file input.'
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise BrowserError(message=msg, long_term_memory=msg)

			# Get CDP client and session
			# EN: Assign value to cdp_client.
			# JP: cdp_client に値を代入する。
			cdp_client = self.browser_session.cdp_client
			# EN: Assign value to session_id.
			# JP: session_id に値を代入する。
			session_id = await self._get_session_id_for_element(element_node)

			# Set file(s) to upload
			# EN: Assign value to backend_node_id.
			# JP: backend_node_id に値を代入する。
			backend_node_id = element_node.backend_node_id
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_client.send.DOM.setFileInputFiles(
				params={
					'files': [event.file_path],
					'backendNodeId': backend_node_id,
				},
				session_id=session_id,
			)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'📎 Uploaded file {event.file_path} to element {index_for_logging}')
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_ScrollToTextEvent`.
	# JP: 非同期関数 `on_ScrollToTextEvent` を定義する。
	async def on_ScrollToTextEvent(self, event: ScrollToTextEvent) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle scroll to text request with CDP.

		Returns True when the text is located and scrolled into view, or False if it
		could not be found. We avoid raising to keep the agent flow resilient."""

		# TODO: handle looking for text inside cross-origin iframes as well

		# Get CDP client and session
		# EN: Assign value to cdp_client.
		# JP: cdp_client に値を代入する。
		cdp_client = self.browser_session.cdp_client
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session.agent_focus is None:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise BrowserError('CDP session not initialized - browser may not be connected yet')
		# EN: Assign value to session_id.
		# JP: session_id に値を代入する。
		session_id = self.browser_session.agent_focus.session_id

		# Enable DOM
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await cdp_client.send.DOM.enable(session_id=session_id)

		# Get document
		# EN: Assign value to doc.
		# JP: doc に値を代入する。
		doc = await cdp_client.send.DOM.getDocument(params={'depth': -1}, session_id=session_id)
		# EN: Assign value to root_node_id.
		# JP: root_node_id に値を代入する。
		root_node_id = doc['root']['nodeId']

		# Search for text using XPath
		# EN: Assign value to search_queries.
		# JP: search_queries に値を代入する。
		search_queries = [
			f'//*[contains(text(), "{event.text}")]',
			f'//*[contains(., "{event.text}")]',
			f'//*[@*[contains(., "{event.text}")]]',
		]

		# EN: Assign value to found.
		# JP: found に値を代入する。
		found = False
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for query in search_queries:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Perform search
				# EN: Assign value to search_result.
				# JP: search_result に値を代入する。
				search_result = await cdp_client.send.DOM.performSearch(params={'query': query}, session_id=session_id)
				# EN: Assign value to search_id.
				# JP: search_id に値を代入する。
				search_id = search_result['searchId']
				# EN: Assign value to result_count.
				# JP: result_count に値を代入する。
				result_count = search_result['resultCount']

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if result_count > 0:
					# Get the first match
					# EN: Assign value to node_ids.
					# JP: node_ids に値を代入する。
					node_ids = await cdp_client.send.DOM.getSearchResults(
						params={'searchId': search_id, 'fromIndex': 0, 'toIndex': 1},
						session_id=session_id,
					)

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if node_ids['nodeIds']:
						# EN: Assign value to node_id.
						# JP: node_id に値を代入する。
						node_id = node_ids['nodeIds'][0]

						# Scroll the element into view
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await cdp_client.send.DOM.scrollIntoViewIfNeeded(params={'nodeId': node_id}, session_id=session_id)

						# EN: Assign value to found.
						# JP: found に値を代入する。
						found = True
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'📜 Scrolled to text: "{event.text}"')
						# EN: Exit the current loop.
						# JP: 現在のループを終了する。
						break

				# Clean up search
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_client.send.DOM.discardSearchResults(params={'searchId': search_id}, session_id=session_id)
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Search query failed: {query}, error: {e}')
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

		# Short-circuit if the DOM search succeeded
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if found:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Fallback: Try JavaScript search
		# EN: Assign value to js_result.
		# JP: js_result に値を代入する。
		js_result = await cdp_client.send.Runtime.evaluate(
			params={
				'expression': f'''
					(() => {{
						const walker = document.createTreeWalker(
							document.body,
							NodeFilter.SHOW_TEXT,
							null,
							false
						);
						let node;
						while (node = walker.nextNode()) {{
							if (node.textContent.includes("{event.text}")) {{
								node.parentElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
								return true;
							}}
						}}
						return false;
					}})()
				'''
			},
			session_id=session_id,
		)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if js_result.get('result', {}).get('value'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'📜 Scrolled to text: "{event.text}" (via JS)')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.warning(f'⚠️ Text not found: "{event.text}"')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define async function `on_GetDropdownOptionsEvent`.
	# JP: 非同期関数 `on_GetDropdownOptionsEvent` を定義する。
	async def on_GetDropdownOptionsEvent(self, event: GetDropdownOptionsEvent) -> dict[str, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle get dropdown options request with CDP."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Use the provided node
			# EN: Assign value to element_node.
			# JP: element_node に値を代入する。
			element_node = event.node
			# EN: Assign value to index_for_logging.
			# JP: index_for_logging に値を代入する。
			index_for_logging = element_node.element_index or 'unknown'

			# Get CDP session for this node
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.cdp_client_for_node(element_node)

			# Convert node to object ID for CDP operations
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to object_result.
				# JP: object_result に値を代入する。
				object_result = await cdp_session.cdp_client.send.DOM.resolveNode(
					params={'backendNodeId': element_node.backend_node_id}, session_id=cdp_session.session_id
				)
				# EN: Assign value to remote_object.
				# JP: remote_object に値を代入する。
				remote_object = object_result.get('object', {})
				# EN: Assign value to object_id.
				# JP: object_id に値を代入する。
				object_id = remote_object.get('objectId')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not object_id:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError('Could not get object ID from resolved node')
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f'Failed to resolve node to object: {e}') from e

			# Use JavaScript to extract dropdown options
			# EN: Assign value to options_script.
			# JP: options_script に値を代入する。
			options_script = """
			function() {
				const startElement = this;
				
				// Function to check if an element is a dropdown and extract options
				function checkDropdownElement(element) {
					// Check if it's a native select element
					if (element.tagName.toLowerCase() === 'select') {
						return {
							type: 'select',
							options: Array.from(element.options).map((opt, idx) => ({
								text: opt.text.trim(),
								value: opt.value,
								index: idx,
								selected: opt.selected
							})),
							id: element.id || '',
							name: element.name || '',
							source: 'target'
						};
					}
					
					// Check if it's an ARIA dropdown/menu
					const role = element.getAttribute('role');
					if (role === 'menu' || role === 'listbox' || role === 'combobox') {
						// Find all menu items/options
						const menuItems = element.querySelectorAll('[role="menuitem"], [role="option"]');
						const options = [];
						
						menuItems.forEach((item, idx) => {
							const text = item.textContent ? item.textContent.trim() : '';
							if (text) {
								options.push({
									text: text,
									value: item.getAttribute('data-value') || text,
									index: idx,
									selected: item.getAttribute('aria-selected') === 'true' || item.classList.contains('selected')
								});
							}
						});
						
						return {
							type: 'aria',
							options: options,
							id: element.id || '',
							name: element.getAttribute('aria-label') || '',
							source: 'target'
						};
					}
					
					// Check if it's a Semantic UI dropdown or similar
					if (element.classList.contains('dropdown') || element.classList.contains('ui')) {
						const menuItems = element.querySelectorAll('.item, .option, [data-value]');
						const options = [];
						
						menuItems.forEach((item, idx) => {
							const text = item.textContent ? item.textContent.trim() : '';
							if (text) {
								options.push({
									text: text,
									value: item.getAttribute('data-value') || text,
									index: idx,
									selected: item.classList.contains('selected') || item.classList.contains('active')
								});
							}
						});
						
						if (options.length > 0) {
							return {
								type: 'custom',
								options: options,
								id: element.id || '',
								name: element.getAttribute('aria-label') || '',
								source: 'target'
							};
						}
					}
					
					return null;
				}
				
				// Function to recursively search children up to specified depth
				function searchChildrenForDropdowns(element, maxDepth, currentDepth = 0) {
					if (currentDepth >= maxDepth) return null;
					
					// Check all direct children
					for (let child of element.children) {
						// Check if this child is a dropdown
						const result = checkDropdownElement(child);
						if (result) {
							result.source = `child-depth-${currentDepth + 1}`;
							return result;
						}
						
						// Recursively check this child's children
						const childResult = searchChildrenForDropdowns(child, maxDepth, currentDepth + 1);
						if (childResult) {
							return childResult;
						}
					}
					
					return null;
				}
				
				// First check the target element itself
				let dropdownResult = checkDropdownElement(startElement);
				if (dropdownResult) {
					return dropdownResult;
				}
				
				// If target element is not a dropdown, search children up to depth 4
				dropdownResult = searchChildrenForDropdowns(startElement, 4);
				if (dropdownResult) {
					return dropdownResult;
				}
				
				return {
					error: `Element and its children (depth 4) are not recognizable dropdown types (tag: ${startElement.tagName}, role: ${startElement.getAttribute('role')}, classes: ${startElement.className})`
				};
			}
			"""

			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
				params={
					'functionDeclaration': options_script,
					'objectId': object_id,
					'returnByValue': True,
				},
				session_id=cdp_session.session_id,
			)

			# EN: Assign value to dropdown_data.
			# JP: dropdown_data に値を代入する。
			dropdown_data = result.get('result', {}).get('value', {})

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if dropdown_data.get('error'):
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise BrowserError(message=dropdown_data['error'], long_term_memory=dropdown_data['error'])

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not dropdown_data.get('options'):
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'No options found in dropdown at index {index_for_logging}'
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise BrowserError(message=msg, long_term_memory=msg)

			# Format options for display
			# EN: Assign value to formatted_options.
			# JP: formatted_options に値を代入する。
			formatted_options = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for opt in dropdown_data['options']:
				# Use JSON encoding to ensure exact string matching
				# EN: Assign value to encoded_text.
				# JP: encoded_text に値を代入する。
				encoded_text = json.dumps(opt['text'])
				# EN: Assign value to status.
				# JP: status に値を代入する。
				status = ' (selected)' if opt.get('selected') else ''
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				formatted_options.append(f'{opt["index"]}: text={encoded_text}, value={json.dumps(opt["value"])}{status}')

			# EN: Assign value to dropdown_type.
			# JP: dropdown_type に値を代入する。
			dropdown_type = dropdown_data.get('type', 'select')
			# EN: Assign value to element_info.
			# JP: element_info に値を代入する。
			element_info = f'Index: {index_for_logging}, Type: {dropdown_type}, ID: {dropdown_data.get("id", "none")}, Name: {dropdown_data.get("name", "none")}'
			# EN: Assign value to source_info.
			# JP: source_info に値を代入する。
			source_info = dropdown_data.get('source', 'unknown')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if source_info == 'target':
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Found {dropdown_type} dropdown ({element_info}):\n' + '\n'.join(formatted_options)
			else:
				# EN: Assign value to msg.
				# JP: msg に値を代入する。
				msg = f'Found {dropdown_type} dropdown in {source_info} ({element_info}):\n' + '\n'.join(formatted_options)
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			msg += f'\n\nUse the exact text or value string (without quotes) in select_dropdown_option(index={index_for_logging}, text=...)'

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if source_info == 'target':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'📋 Found {len(dropdown_data["options"])} dropdown options for index {index_for_logging}')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(
					f'📋 Found {len(dropdown_data["options"])} dropdown options for index {index_for_logging} in {source_info}'
				)

			# Create structured memory for the response
			# EN: Assign value to short_term_memory.
			# JP: short_term_memory に値を代入する。
			short_term_memory = msg
			# EN: Assign value to long_term_memory.
			# JP: long_term_memory に値を代入する。
			long_term_memory = f'Got dropdown options for index {index_for_logging}'

			# Return the dropdown data as a dict with structured memory
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return {
				'type': dropdown_type,
				'options': json.dumps(dropdown_data['options']),  # Convert list to JSON string for dict[str, str] type
				'element_info': element_info,
				'source': source_info,
				'formatted_options': '\n'.join(formatted_options),
				'message': msg,
				'short_term_memory': short_term_memory,
				'long_term_memory': long_term_memory,
				'element_index': str(index_for_logging),
			}

		except BrowserError:
			# Re-raise BrowserError as-is to preserve structured memory
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise
		except TimeoutError:
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = f'Failed to get dropdown options for index {index_for_logging} due to timeout.'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(msg)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise BrowserError(message=msg, long_term_memory=msg)
		except Exception as e:
			# EN: Assign value to msg.
			# JP: msg に値を代入する。
			msg = 'Failed to get dropdown options'
			# EN: Assign value to error_msg.
			# JP: error_msg に値を代入する。
			error_msg = f'{msg}: {str(e)}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(error_msg)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise BrowserError(
				message=error_msg, long_term_memory=f'Failed to get dropdown options for index {index_for_logging}.'
			)

	# EN: Define async function `on_SelectDropdownOptionEvent`.
	# JP: 非同期関数 `on_SelectDropdownOptionEvent` を定義する。
	async def on_SelectDropdownOptionEvent(self, event: SelectDropdownOptionEvent) -> dict[str, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle select dropdown option request with CDP."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Use the provided node
			# EN: Assign value to element_node.
			# JP: element_node に値を代入する。
			element_node = event.node
			# EN: Assign value to index_for_logging.
			# JP: index_for_logging に値を代入する。
			index_for_logging = element_node.element_index or 'unknown'
			# EN: Assign value to target_text.
			# JP: target_text に値を代入する。
			target_text = event.text

			# Get CDP session for this node
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.cdp_client_for_node(element_node)

			# Convert node to object ID for CDP operations
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to object_result.
				# JP: object_result に値を代入する。
				object_result = await cdp_session.cdp_client.send.DOM.resolveNode(
					params={'backendNodeId': element_node.backend_node_id}, session_id=cdp_session.session_id
				)
				# EN: Assign value to remote_object.
				# JP: remote_object に値を代入する。
				remote_object = object_result.get('object', {})
				# EN: Assign value to object_id.
				# JP: object_id に値を代入する。
				object_id = remote_object.get('objectId')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not object_id:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError('Could not get object ID from resolved node')
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f'Failed to resolve node to object: {e}') from e

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Use JavaScript to select the option
				# EN: Assign value to selection_script.
				# JP: selection_script に値を代入する。
				selection_script = """
				function(targetText) {
					const startElement = this;
					
					// Function to attempt selection on a dropdown element
					function attemptSelection(element) {
						// Handle native select elements
						if (element.tagName.toLowerCase() === 'select') {
							const options = Array.from(element.options);
							const targetTextLower = targetText.toLowerCase();
							
							for (const option of options) {
								const optionTextLower = option.text.trim().toLowerCase();
								const optionValueLower = option.value.toLowerCase();
								
								// Match against both text and value (case-insensitive)
								if (optionTextLower === targetTextLower || optionValueLower === targetTextLower) {
									element.value = option.value;
									option.selected = true;
									
									// Trigger change events
									const changeEvent = new Event('change', { bubbles: true });
									element.dispatchEvent(changeEvent);
									
									return {
										success: true,
										message: `Selected option: ${option.text.trim()} (value: ${option.value})`,
										value: option.value
									};
								}
							}
							
							// Return available options as separate field
							const availableOptions = options.map(opt => ({
								text: opt.text.trim(),
								value: opt.value
							}));
							
							return {
								success: false,
								error: `Option with text or value '${targetText}' not found in select element`,
								availableOptions: availableOptions
							};
						}
						
						// Handle ARIA dropdowns/menus
						const role = element.getAttribute('role');
						if (role === 'menu' || role === 'listbox' || role === 'combobox') {
							const menuItems = element.querySelectorAll('[role="menuitem"], [role="option"]');
							const targetTextLower = targetText.toLowerCase();
							
							for (const item of menuItems) {
								if (item.textContent) {
									const itemTextLower = item.textContent.trim().toLowerCase();
									const itemValueLower = (item.getAttribute('data-value') || '').toLowerCase();
									
									// Match against both text and data-value (case-insensitive)
									if (itemTextLower === targetTextLower || itemValueLower === targetTextLower) {
										// Clear previous selections
										menuItems.forEach(mi => {
											mi.setAttribute('aria-selected', 'false');
											mi.classList.remove('selected');
										});
										
										// Select this item
										item.setAttribute('aria-selected', 'true');
										item.classList.add('selected');
										
										// Trigger click and change events
										item.click();
										const clickEvent = new MouseEvent('click', { view: window, bubbles: true, cancelable: true });
										item.dispatchEvent(clickEvent);
										
										return {
											success: true,
											message: `Selected ARIA menu item: ${item.textContent.trim()}`
										};
									}
								}
							}
							
							// Return available options as separate field
							const availableOptions = Array.from(menuItems).map(item => ({
								text: item.textContent ? item.textContent.trim() : '',
								value: item.getAttribute('data-value') || ''
							})).filter(opt => opt.text || opt.value);
							
							return {
								success: false,
								error: `Menu item with text or value '${targetText}' not found`,
								availableOptions: availableOptions
							};
						}
						
						// Handle Semantic UI or custom dropdowns
						if (element.classList.contains('dropdown') || element.classList.contains('ui')) {
							const menuItems = element.querySelectorAll('.item, .option, [data-value]');
							const targetTextLower = targetText.toLowerCase();
							
							for (const item of menuItems) {
								if (item.textContent) {
									const itemTextLower = item.textContent.trim().toLowerCase();
									const itemValueLower = (item.getAttribute('data-value') || '').toLowerCase();
									
									// Match against both text and data-value (case-insensitive)
									if (itemTextLower === targetTextLower || itemValueLower === targetTextLower) {
										// Clear previous selections
										menuItems.forEach(mi => {
											mi.classList.remove('selected', 'active');
										});
										
										// Select this item
										item.classList.add('selected', 'active');
										
										// Update dropdown text if there's a text element
										const textElement = element.querySelector('.text');
										if (textElement) {
											textElement.textContent = item.textContent.trim();
										}
										
										// Trigger click and change events
										item.click();
										const clickEvent = new MouseEvent('click', { view: window, bubbles: true, cancelable: true });
										item.dispatchEvent(clickEvent);
										
										// Also dispatch on the main dropdown element
										const dropdownChangeEvent = new Event('change', { bubbles: true });
										element.dispatchEvent(dropdownChangeEvent);
										
										return {
											success: true,
											message: `Selected custom dropdown item: ${item.textContent.trim()}`
										};
									}
								}
							}
							
							// Return available options as separate field
							const availableOptions = Array.from(menuItems).map(item => ({
								text: item.textContent ? item.textContent.trim() : '',
								value: item.getAttribute('data-value') || ''
							})).filter(opt => opt.text || opt.value);
							
							return {
								success: false,
								error: `Custom dropdown item with text or value '${targetText}' not found`,
								availableOptions: availableOptions
							};
						}
						
						return null; // Not a dropdown element
					}
					
					// Function to recursively search children for dropdowns
					function searchChildrenForSelection(element, maxDepth, currentDepth = 0) {
						if (currentDepth >= maxDepth) return null;
						
						// Check all direct children
						for (let child of element.children) {
							// Try selection on this child
							const result = attemptSelection(child);
							if (result && result.success) {
								return result;
							}
							
							// Recursively check this child's children
							const childResult = searchChildrenForSelection(child, maxDepth, currentDepth + 1);
							if (childResult && childResult.success) {
								return childResult;
							}
						}
						
						return null;
					}
					
					// First try the target element itself
					let selectionResult = attemptSelection(startElement);
					if (selectionResult) {
						// If attemptSelection returned a result (success or failure), use it
						// Don't search children if we found a dropdown element but selection failed
						return selectionResult;
					}
					
					// Only search children if target element is not a dropdown element
					selectionResult = searchChildrenForSelection(startElement, 4);
					if (selectionResult && selectionResult.success) {
						return selectionResult;
					}
					
					return {
						success: false,
						error: `Element and its children (depth 4) do not contain a dropdown with option '${targetText}' (tag: ${startElement.tagName}, role: ${startElement.getAttribute('role')}, classes: ${startElement.className})`
					};
				}
				"""

				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
					params={
						'functionDeclaration': selection_script,
						'arguments': [{'value': target_text}],
						'objectId': object_id,
						'returnByValue': True,
					},
					session_id=cdp_session.session_id,
				)

				# EN: Assign value to selection_result.
				# JP: selection_result に値を代入する。
				selection_result = result.get('result', {}).get('value', {})

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if selection_result.get('success'):
					# EN: Assign value to msg.
					# JP: msg に値を代入する。
					msg = selection_result.get('message', f'Selected option: {target_text}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'{msg}')

					# Return the result as a dict
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return {
						'success': 'true',
						'message': msg,
						'value': selection_result.get('value', target_text),
						'element_index': str(index_for_logging),
					}
				else:
					# EN: Assign value to error_msg.
					# JP: error_msg に値を代入する。
					error_msg = selection_result.get('error', f'Failed to select option: {target_text}')
					# EN: Assign value to available_options.
					# JP: available_options に値を代入する。
					available_options = selection_result.get('availableOptions', [])
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'❌ {error_msg}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Available options from JavaScript: {available_options}')

					# If we have available options, return structured error data
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if available_options:
						# Format options for short_term_memory (simple bulleted list)
						# EN: Assign value to short_term_options.
						# JP: short_term_options に値を代入する。
						short_term_options = []
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for opt in available_options:
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if isinstance(opt, dict):
								# EN: Assign value to text.
								# JP: text に値を代入する。
								text = opt.get('text', '').strip()
								# EN: Assign value to value.
								# JP: value に値を代入する。
								value = opt.get('value', '').strip()
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if text:
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									short_term_options.append(f'- {text}')
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								elif value:
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									short_term_options.append(f'- {value}')
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							elif isinstance(opt, str):
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								short_term_options.append(f'- {opt}')

						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if short_term_options:
							# EN: Assign value to short_term_memory.
							# JP: short_term_memory に値を代入する。
							short_term_memory = f'Available dropdown options at index {index_for_logging} are:\n' + '\n'.join(
								short_term_options
							)
							# EN: Assign value to long_term_memory.
							# JP: long_term_memory に値を代入する。
							long_term_memory = f"Couldn't select the dropdown option at index {index_for_logging} as '{target_text}' is not one of the available options."

							# Return error result with structured memory instead of raising exception
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return {
								'success': 'false',
								'error': error_msg,
								'short_term_memory': short_term_memory,
								'long_term_memory': long_term_memory,
								'element_index': str(index_for_logging),
							}

					# Fallback to regular error result if no available options
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return {
						'success': 'false',
						'error': error_msg,
						'element_index': str(index_for_logging),
					}

			except Exception as e:
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = f'Failed to select dropdown option: {str(e)}'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(error_msg)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(error_msg) from e

		except Exception as e:
			# EN: Assign value to error_msg.
			# JP: error_msg に値を代入する。
			error_msg = f'Failed to select dropdown option "{target_text}" for element {index_for_logging}: {str(e)}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(error_msg)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(error_msg) from e

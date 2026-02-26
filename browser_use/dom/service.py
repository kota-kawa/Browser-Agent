# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.accessibility.commands import GetFullAXTreeReturns
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.accessibility.types import AXNode
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.dom.types import Node
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.target import TargetID

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.enhanced_snapshot import (
	REQUIRED_COMPUTED_STYLES,
	build_snapshot_lookup,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.serializer.serializer import DOMTreeSerializer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import (
	CurrentPageTargets,
	DOMRect,
	EnhancedAXNode,
	EnhancedAXProperty,
	EnhancedDOMTreeNode,
	NodeType,
	SerializedDOMState,
	TargetAllTrees,
)

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser.session import BrowserSession

# Note: iframe limits are now configurable via BrowserProfile.max_iframes and BrowserProfile.max_iframe_depth


# EN: Define class `DomService`.
# JP: クラス `DomService` を定義する。
class DomService:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Service for getting the DOM tree and other DOM-related information.

	Either browser or page must be provided.

	TODO: currently we start a new websocket connection PER STEP, we should definitely keep this persistent
	"""

	# EN: Assign annotated value to logger.
	# JP: logger に型付きの値を代入する。
	logger: logging.Logger

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		browser_session: 'BrowserSession',
		logger: logging.Logger | None = None,
		cross_origin_iframes: bool = False,
		paint_order_filtering: bool = True,
		max_iframes: int = 100,
		max_iframe_depth: int = 5,
	):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.browser_session = browser_session
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.logger = logger or browser_session.logger
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.cross_origin_iframes = cross_origin_iframes
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.paint_order_filtering = paint_order_filtering
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.max_iframes = max_iframes
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.max_iframe_depth = max_iframe_depth

	# EN: Define async function `__aenter__`.
	# JP: 非同期関数 `__aenter__` を定義する。
	async def __aenter__(self):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define async function `__aexit__`.
	# JP: 非同期関数 `__aexit__` を定義する。
	async def __aexit__(self, exc_type, exc_value, traceback):
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass  # no need to cleanup anything, browser_session auto handles cleaning up session cache

	# EN: Define async function `_get_targets_for_page`.
	# JP: 非同期関数 `_get_targets_for_page` を定義する。
	async def _get_targets_for_page(self, target_id: TargetID | None = None) -> CurrentPageTargets:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the target info for a specific page.

		Args:
			target_id: The target ID to get info for. If None, uses current_target_id.
		"""
		# EN: Assign value to targets.
		# JP: targets に値を代入する。
		targets = await self.browser_session.cdp_client.send.Target.getTargets()

		# Use provided target_id or fall back to current_target_id
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_id is None:
			# EN: Assign value to target_id.
			# JP: target_id に値を代入する。
			target_id = self.browser_session.current_target_id
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not target_id:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError('No current target ID set in browser session')

		# Find main page target by ID
		# EN: Assign value to main_target.
		# JP: main_target に値を代入する。
		main_target = next((t for t in targets['targetInfos'] if t['targetId'] == target_id), None)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not main_target:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'No target found for target ID: {target_id}')

		# Get all frames using the new method to find iframe targets for this page
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		all_frames, _ = await self.browser_session.get_all_frames()

		# Find iframe targets that are children of this target
		# EN: Assign value to iframe_targets.
		# JP: iframe_targets に値を代入する。
		iframe_targets = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for frame_info in all_frames.values():
			# Check if this frame is a cross-origin iframe with its own target
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if frame_info.get('isCrossOrigin') and frame_info.get('frameTargetId'):
				# Check if this frame belongs to our target
				# EN: Assign value to parent_target.
				# JP: parent_target に値を代入する。
				parent_target = frame_info.get('parentTargetId', frame_info.get('frameTargetId'))
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if parent_target == target_id:
					# Find the target info for this iframe
					# EN: Assign value to iframe_target.
					# JP: iframe_target に値を代入する。
					iframe_target = next(
						(t for t in targets['targetInfos'] if t['targetId'] == frame_info['frameTargetId']), None
					)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if iframe_target:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						iframe_targets.append(iframe_target)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return CurrentPageTargets(
			page_session=main_target,
			iframe_sessions=iframe_targets,
		)

	# EN: Define function `_build_enhanced_ax_node`.
	# JP: 関数 `_build_enhanced_ax_node` を定義する。
	def _build_enhanced_ax_node(self, ax_node: AXNode) -> EnhancedAXNode:
		# EN: Assign annotated value to properties.
		# JP: properties に型付きの値を代入する。
		properties: list[EnhancedAXProperty] | None = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'properties' in ax_node and ax_node['properties']:
			# EN: Assign value to properties.
			# JP: properties に値を代入する。
			properties = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for property in ax_node['properties']:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# test whether property name can go into the enum (sometimes Chrome returns some random properties)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					properties.append(
						EnhancedAXProperty(
							name=property['name'],
							value=property.get('value', {}).get('value', None),
							# related_nodes=[],  # TODO: add related nodes
						)
					)
				except ValueError:
					# EN: Keep a placeholder statement.
					# JP: プレースホルダー文を維持する。
					pass

		# EN: Assign value to enhanced_ax_node.
		# JP: enhanced_ax_node に値を代入する。
		enhanced_ax_node = EnhancedAXNode(
			ax_node_id=ax_node['nodeId'],
			ignored=ax_node['ignored'],
			role=ax_node.get('role', {}).get('value', None),
			name=ax_node.get('name', {}).get('value', None),
			description=ax_node.get('description', {}).get('value', None),
			properties=properties,
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return enhanced_ax_node

	# EN: Define async function `_get_viewport_ratio`.
	# JP: 非同期関数 `_get_viewport_ratio` を定義する。
	async def _get_viewport_ratio(self, target_id: TargetID) -> float:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get viewport dimensions, device pixel ratio, and scroll position using CDP."""

		# Remember the currently focused target so we can restore it if needed
		# EN: Assign annotated value to previous_focus_target.
		# JP: previous_focus_target に型付きの値を代入する。
		previous_focus_target: TargetID | None = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session.agent_focus:
			# EN: Assign value to previous_focus_target.
			# JP: previous_focus_target に値を代入する。
			previous_focus_target = self.browser_session.agent_focus.target_id

		# Never change the agent focus when collecting viewport data – this helper can be
		# executed for cross-origin iframes while the agent is working in another tab.
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=target_id, focus=False)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get the layout metrics which includes the visual viewport
			# EN: Assign value to metrics.
			# JP: metrics に値を代入する。
			metrics = await cdp_session.cdp_client.send.Page.getLayoutMetrics(session_id=cdp_session.session_id)

			# EN: Assign value to visual_viewport.
			# JP: visual_viewport に値を代入する。
			visual_viewport = metrics.get('visualViewport', {})

			# IMPORTANT: Use CSS viewport instead of device pixel viewport
			# This fixes the coordinate mismatch on high-DPI displays
			# EN: Assign value to css_visual_viewport.
			# JP: css_visual_viewport に値を代入する。
			css_visual_viewport = metrics.get('cssVisualViewport', {})
			# EN: Assign value to css_layout_viewport.
			# JP: css_layout_viewport に値を代入する。
			css_layout_viewport = metrics.get('cssLayoutViewport', {})

			# Use CSS pixels (what JavaScript sees) instead of device pixels
			# EN: Assign value to width.
			# JP: width に値を代入する。
			width = css_visual_viewport.get('clientWidth', css_layout_viewport.get('clientWidth', 1920.0))

			# Calculate device pixel ratio
			# EN: Assign value to device_width.
			# JP: device_width に値を代入する。
			device_width = visual_viewport.get('clientWidth', width)
			# EN: Assign value to css_width.
			# JP: css_width に値を代入する。
			css_width = css_visual_viewport.get('clientWidth', width)
			# EN: Assign value to device_pixel_ratio.
			# JP: device_pixel_ratio に値を代入する。
			device_pixel_ratio = device_width / css_width if css_width > 0 else 1.0

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return float(device_pixel_ratio)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Viewport size detection failed: {e}')
			# Fallback to default viewport size
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 1.0
		finally:
			# Restore the previous focus if it changed while collecting metrics
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				previous_focus_target
				and self.browser_session.agent_focus
				and self.browser_session.agent_focus.target_id != previous_focus_target
			):
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self.browser_session.get_or_create_cdp_session(target_id=previous_focus_target, focus=True)
				except Exception as restore_error:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'Failed to restore focus after viewport lookup: {restore_error}')

	# EN: Define function `is_element_visible_according_to_all_parents`.
	# JP: 関数 `is_element_visible_according_to_all_parents` を定義する。
	@classmethod
	def is_element_visible_according_to_all_parents(
		cls, node: EnhancedDOMTreeNode, html_frames: list[EnhancedDOMTreeNode]
	) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the element is visible according to all its parent HTML frames."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not node.snapshot_node:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Assign value to computed_styles.
		# JP: computed_styles に値を代入する。
		computed_styles = node.snapshot_node.computed_styles or {}

		# EN: Assign value to display.
		# JP: display に値を代入する。
		display = computed_styles.get('display', '').lower()
		# EN: Assign value to visibility.
		# JP: visibility に値を代入する。
		visibility = computed_styles.get('visibility', '').lower()
		# EN: Assign value to opacity.
		# JP: opacity に値を代入する。
		opacity = computed_styles.get('opacity', '1')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if display == 'none' or visibility == 'hidden':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if float(opacity) <= 0:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return False
		except (ValueError, TypeError):
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass

		# Start with the element's local bounds (in its own frame's coordinate system)
		# EN: Assign value to current_bounds.
		# JP: current_bounds に値を代入する。
		current_bounds = node.snapshot_node.bounds

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not current_bounds:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False  # If there are no bounds, the element is not visible

		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Reverse iterate through the html frames (that can be either iframe or document -> if it's a document frame compare if the current bounds interest with it (taking scroll into account) otherwise move the current bounds by the iframe offset)
		"""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for frame in reversed(html_frames):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				frame.node_type == NodeType.ELEMENT_NODE
				and (frame.node_name.upper() == 'IFRAME' or frame.node_name.upper() == 'FRAME')
				and frame.snapshot_node
				and frame.snapshot_node.bounds
			):
				# EN: Assign value to iframe_bounds.
				# JP: iframe_bounds に値を代入する。
				iframe_bounds = frame.snapshot_node.bounds

				# negate the values added in `_construct_enhanced_node`
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				current_bounds.x += iframe_bounds.x
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				current_bounds.y += iframe_bounds.y

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				frame.node_type == NodeType.ELEMENT_NODE
				and frame.node_name == 'HTML'
				and frame.snapshot_node
				and frame.snapshot_node.scrollRects
				and frame.snapshot_node.clientRects
			):
				# For iframe content, we need to check visibility within the iframe's viewport
				# The scrollRects represent the current scroll position
				# The clientRects represent the viewport size
				# Elements are visible if they fall within the viewport after accounting for scroll

				# The viewport of the frame (what's actually visible)
				# EN: Assign value to viewport_left.
				# JP: viewport_left に値を代入する。
				viewport_left = 0  # Viewport always starts at 0 in frame coordinates
				# EN: Assign value to viewport_top.
				# JP: viewport_top に値を代入する。
				viewport_top = 0
				# EN: Assign value to viewport_right.
				# JP: viewport_right に値を代入する。
				viewport_right = frame.snapshot_node.clientRects.width
				# EN: Assign value to viewport_bottom.
				# JP: viewport_bottom に値を代入する。
				viewport_bottom = frame.snapshot_node.clientRects.height

				# Adjust element bounds by the scroll offset to get position relative to viewport
				# When scrolled down, scrollRects.y is positive, so we subtract it from element's y
				# EN: Assign value to adjusted_x.
				# JP: adjusted_x に値を代入する。
				adjusted_x = current_bounds.x - frame.snapshot_node.scrollRects.x
				# EN: Assign value to adjusted_y.
				# JP: adjusted_y に値を代入する。
				adjusted_y = current_bounds.y - frame.snapshot_node.scrollRects.y

				# EN: Assign value to frame_intersects.
				# JP: frame_intersects に値を代入する。
				frame_intersects = (
					adjusted_x < viewport_right
					and adjusted_x + current_bounds.width > viewport_left
					and adjusted_y < viewport_bottom
					and adjusted_y + current_bounds.height > viewport_top
				)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not frame_intersects:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return False

				# Keep the original coordinate adjustment to maintain consistency
				# This adjustment is needed for proper coordinate transformation
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				current_bounds.x -= frame.snapshot_node.scrollRects.x
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				current_bounds.y -= frame.snapshot_node.scrollRects.y

		# If we reach here, element is visible in main viewport and all containing iframes
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Define async function `_get_ax_tree_for_all_frames`.
	# JP: 非同期関数 `_get_ax_tree_for_all_frames` を定義する。
	async def _get_ax_tree_for_all_frames(self, target_id: TargetID) -> GetFullAXTreeReturns:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Recursively collect all frames and merge their accessibility trees into a single array."""

		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=target_id, focus=False)
		# EN: Assign value to frame_tree.
		# JP: frame_tree に値を代入する。
		frame_tree = await cdp_session.cdp_client.send.Page.getFrameTree(session_id=cdp_session.session_id)

		# EN: Define function `collect_all_frame_ids`.
		# JP: 関数 `collect_all_frame_ids` を定義する。
		def collect_all_frame_ids(frame_tree_node) -> list[str]:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Recursively collect all frame IDs from the frame tree."""
			# EN: Assign value to frame_ids.
			# JP: frame_ids に値を代入する。
			frame_ids = [frame_tree_node['frame']['id']]

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'childFrames' in frame_tree_node and frame_tree_node['childFrames']:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for child_frame in frame_tree_node['childFrames']:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					frame_ids.extend(collect_all_frame_ids(child_frame))

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return frame_ids

		# Collect all frame IDs recursively
		# EN: Assign value to all_frame_ids.
		# JP: all_frame_ids に値を代入する。
		all_frame_ids = collect_all_frame_ids(frame_tree['frameTree'])

		# Get accessibility tree for each frame
		# EN: Assign value to ax_tree_requests.
		# JP: ax_tree_requests に値を代入する。
		ax_tree_requests = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for frame_id in all_frame_ids:
			# EN: Assign value to ax_tree_request.
			# JP: ax_tree_request に値を代入する。
			ax_tree_request = cdp_session.cdp_client.send.Accessibility.getFullAXTree(
				params={'frameId': frame_id}, session_id=cdp_session.session_id
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			ax_tree_requests.append(ax_tree_request)

		# Wait for all requests to complete
		# EN: Assign value to ax_trees.
		# JP: ax_trees に値を代入する。
		ax_trees = await asyncio.gather(*ax_tree_requests)

		# Merge all AX nodes into a single array
		# EN: Assign annotated value to merged_nodes.
		# JP: merged_nodes に型付きの値を代入する。
		merged_nodes: list[AXNode] = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for ax_tree in ax_trees:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			merged_nodes.extend(ax_tree['nodes'])

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {'nodes': merged_nodes}

	# EN: Define async function `_get_all_trees`.
	# JP: 非同期関数 `_get_all_trees` を定義する。
	async def _get_all_trees(self, target_id: TargetID) -> TargetAllTrees:
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=target_id, focus=False)

		# Wait for the page to be ready first
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to ready_state.
			# JP: ready_state に値を代入する。
			ready_state = await cdp_session.cdp_client.send.Runtime.evaluate(
				params={'expression': 'document.readyState'}, session_id=cdp_session.session_id
			)
		except Exception as e:
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass  # Page might not be ready yet
		# DEBUG: Log before capturing snapshot
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🔍 DEBUG: Capturing DOM snapshot for target {target_id}')

		# Get actual scroll positions for all iframes before capturing snapshot
		# EN: Assign value to iframe_scroll_positions.
		# JP: iframe_scroll_positions に値を代入する。
		iframe_scroll_positions = {}
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to scroll_result.
			# JP: scroll_result に値を代入する。
			scroll_result = await cdp_session.cdp_client.send.Runtime.evaluate(
				params={
					'expression': """
					(() => {
						const scrollData = {};
						const iframes = document.querySelectorAll('iframe');
						iframes.forEach((iframe, index) => {
							try {
								const doc = iframe.contentDocument || iframe.contentWindow.document;
								if (doc) {
									scrollData[index] = {
										scrollTop: doc.documentElement.scrollTop || doc.body.scrollTop || 0,
										scrollLeft: doc.documentElement.scrollLeft || doc.body.scrollLeft || 0
									};
								}
							} catch (e) {
								// Cross-origin iframe, can't access
							}
						});
						return scrollData;
					})()
					""",
					'returnByValue': True,
				},
				session_id=cdp_session.session_id,
			)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if scroll_result and 'result' in scroll_result and 'value' in scroll_result['result']:
				# EN: Assign value to iframe_scroll_positions.
				# JP: iframe_scroll_positions に値を代入する。
				iframe_scroll_positions = scroll_result['result']['value']
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for idx, scroll_data in iframe_scroll_positions.items():
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f'🔍 DEBUG: Iframe {idx} actual scroll position - scrollTop={scroll_data.get("scrollTop", 0)}, scrollLeft={scroll_data.get("scrollLeft", 0)}'
					)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Failed to get iframe scroll positions: {e}')

		# Define CDP request factories to avoid duplication
		# EN: Define function `create_snapshot_request`.
		# JP: 関数 `create_snapshot_request` を定義する。
		def create_snapshot_request():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return cdp_session.cdp_client.send.DOMSnapshot.captureSnapshot(
				params={
					'computedStyles': REQUIRED_COMPUTED_STYLES,
					'includePaintOrder': True,
					'includeDOMRects': True,
					'includeBlendedBackgroundColors': False,
					'includeTextColorOpacities': False,
				},
				session_id=cdp_session.session_id,
			)

		# EN: Define function `create_dom_tree_request`.
		# JP: 関数 `create_dom_tree_request` を定義する。
		def create_dom_tree_request():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return cdp_session.cdp_client.send.DOM.getDocument(
				params={'depth': -1, 'pierce': True}, session_id=cdp_session.session_id
			)

		# EN: Assign value to start.
		# JP: start に値を代入する。
		start = time.time()

		# Create initial tasks
		# EN: Assign value to tasks.
		# JP: tasks に値を代入する。
		tasks = {
			'snapshot': asyncio.create_task(create_snapshot_request()),
			'dom_tree': asyncio.create_task(create_dom_tree_request()),
			'ax_tree': asyncio.create_task(self._get_ax_tree_for_all_frames(target_id)),
			'device_pixel_ratio': asyncio.create_task(self._get_viewport_ratio(target_id)),
		}

		# Wait for all tasks with timeout
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		done, pending = await asyncio.wait(tasks.values(), timeout=10.0)

		# Retry any failed or timed out tasks
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if pending:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for task in pending:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				task.cancel()

			# Retry mapping for pending tasks
			# EN: Assign value to retry_map.
			# JP: retry_map に値を代入する。
			retry_map = {
				tasks['snapshot']: lambda: asyncio.create_task(create_snapshot_request()),
				tasks['dom_tree']: lambda: asyncio.create_task(create_dom_tree_request()),
				tasks['ax_tree']: lambda: asyncio.create_task(self._get_ax_tree_for_all_frames(target_id)),
				tasks['device_pixel_ratio']: lambda: asyncio.create_task(self._get_viewport_ratio(target_id)),
			}

			# Create new tasks only for the ones that didn't complete
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for key, task in tasks.items():
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if task in pending and task in retry_map:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					tasks[key] = retry_map[task]()

			# Wait again with shorter timeout
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			done2, pending2 = await asyncio.wait([t for t in tasks.values() if not t.done()], timeout=2.0)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if pending2:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for task in pending2:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					task.cancel()

		# Extract results, tracking which ones failed
		# EN: Assign value to results.
		# JP: results に値を代入する。
		results = {}
		# EN: Assign value to failed.
		# JP: failed に値を代入する。
		failed = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for key, task in tasks.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if task.done() and not task.cancelled():
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					results[key] = task.result()
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'CDP request {key} failed with exception: {e}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					failed.append(key)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'CDP request {key} timed out')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				failed.append(key)

		# If any required tasks failed, raise an exception
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if failed:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise TimeoutError(f'CDP requests failed or timed out: {", ".join(failed)}')

		# EN: Assign value to snapshot.
		# JP: snapshot に値を代入する。
		snapshot = results['snapshot']
		# EN: Assign value to dom_tree.
		# JP: dom_tree に値を代入する。
		dom_tree = results['dom_tree']
		# EN: Assign value to ax_tree.
		# JP: ax_tree に値を代入する。
		ax_tree = results['ax_tree']
		# EN: Assign value to device_pixel_ratio.
		# JP: device_pixel_ratio に値を代入する。
		device_pixel_ratio = results['device_pixel_ratio']
		# EN: Assign value to end.
		# JP: end に値を代入する。
		end = time.time()
		# EN: Assign value to cdp_timing.
		# JP: cdp_timing に値を代入する。
		cdp_timing = {'cdp_calls_total': end - start}

		# DEBUG: Log snapshot info and limit documents to prevent explosion
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if snapshot and 'documents' in snapshot:
			# EN: Assign value to original_doc_count.
			# JP: original_doc_count に値を代入する。
			original_doc_count = len(snapshot['documents'])
			# Limit to max_iframes documents to prevent iframe explosion
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if original_doc_count > self.max_iframes:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(
					f'⚠️ Limiting processing of {original_doc_count} iframes on page to only first {self.max_iframes} to prevent crashes!'
				)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				snapshot['documents'] = snapshot['documents'][: self.max_iframes]

			# EN: Assign value to total_nodes.
			# JP: total_nodes に値を代入する。
			total_nodes = sum(len(doc.get('nodes', [])) for doc in snapshot['documents'])
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'🔍 DEBUG: Snapshot contains {len(snapshot["documents"])} frames with {total_nodes} total nodes')
			# Log iframe-specific info
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for doc_idx, doc in enumerate(snapshot['documents']):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if doc_idx > 0:  # Not the main document
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f'🔍 DEBUG: Iframe #{doc_idx} {doc.get("frameId", "no-frame-id")} {doc.get("url", "no-url")} has {len(doc.get("nodes", []))} nodes'
					)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return TargetAllTrees(
			snapshot=snapshot,
			dom_tree=dom_tree,
			ax_tree=ax_tree,
			device_pixel_ratio=device_pixel_ratio,
			cdp_timing=cdp_timing,
		)

	# EN: Define async function `get_dom_tree`.
	# JP: 非同期関数 `get_dom_tree` を定義する。
	async def get_dom_tree(
		self,
		target_id: TargetID,
		initial_html_frames: list[EnhancedDOMTreeNode] | None = None,
		initial_total_frame_offset: DOMRect | None = None,
		iframe_depth: int = 0,
	) -> EnhancedDOMTreeNode:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the DOM tree for a specific target.

		Args:
			target_id: Target ID of the page to get the DOM tree for.
			initial_html_frames: List of HTML frame nodes encountered so far
			initial_total_frame_offset: Accumulated coordinate offset
			iframe_depth: Current depth of iframe nesting to prevent infinite recursion
		"""

		# EN: Assign value to trees.
		# JP: trees に値を代入する。
		trees = await self._get_all_trees(target_id)

		# EN: Assign value to dom_tree.
		# JP: dom_tree に値を代入する。
		dom_tree = trees.dom_tree
		# EN: Assign value to ax_tree.
		# JP: ax_tree に値を代入する。
		ax_tree = trees.ax_tree
		# EN: Assign value to snapshot.
		# JP: snapshot に値を代入する。
		snapshot = trees.snapshot
		# EN: Assign value to device_pixel_ratio.
		# JP: device_pixel_ratio に値を代入する。
		device_pixel_ratio = trees.device_pixel_ratio

		# EN: Assign annotated value to ax_tree_lookup.
		# JP: ax_tree_lookup に型付きの値を代入する。
		ax_tree_lookup: dict[int, AXNode] = {
			ax_node['backendDOMNodeId']: ax_node for ax_node in ax_tree['nodes'] if 'backendDOMNodeId' in ax_node
		}

		# EN: Assign annotated value to enhanced_dom_tree_node_lookup.
		# JP: enhanced_dom_tree_node_lookup に型付きの値を代入する。
		enhanced_dom_tree_node_lookup: dict[int, EnhancedDOMTreeNode] = {}
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		""" NodeId (NOT backend node id) -> enhanced dom tree node"""  # way to get the parent/content node

		# Parse snapshot data with everything calculated upfront
		# EN: Assign value to snapshot_lookup.
		# JP: snapshot_lookup に値を代入する。
		snapshot_lookup = build_snapshot_lookup(snapshot, device_pixel_ratio)

		# EN: Define async function `_construct_enhanced_node`.
		# JP: 非同期関数 `_construct_enhanced_node` を定義する。
		async def _construct_enhanced_node(
			node: Node, html_frames: list[EnhancedDOMTreeNode] | None, total_frame_offset: DOMRect | None
		) -> EnhancedDOMTreeNode:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""
			Recursively construct enhanced DOM tree nodes.

			Args:
				node: The DOM node to construct
				html_frames: List of HTML frame nodes encountered so far
				accumulated_iframe_offset: Accumulated coordinate translation from parent iframes (includes scroll corrections)
			"""

			# Initialize lists if not provided
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if html_frames is None:
				# EN: Assign value to html_frames.
				# JP: html_frames に値を代入する。
				html_frames = []

			# to get rid of the pointer references
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if total_frame_offset is None:
				# EN: Assign value to total_frame_offset.
				# JP: total_frame_offset に値を代入する。
				total_frame_offset = DOMRect(x=0.0, y=0.0, width=0.0, height=0.0)
			else:
				# EN: Assign value to total_frame_offset.
				# JP: total_frame_offset に値を代入する。
				total_frame_offset = DOMRect(
					total_frame_offset.x, total_frame_offset.y, total_frame_offset.width, total_frame_offset.height
				)

			# memoize the mf (I don't know if some nodes are duplicated)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node['nodeId'] in enhanced_dom_tree_node_lookup:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return enhanced_dom_tree_node_lookup[node['nodeId']]

			# EN: Assign value to ax_node.
			# JP: ax_node に値を代入する。
			ax_node = ax_tree_lookup.get(node['backendNodeId'])
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if ax_node:
				# EN: Assign value to enhanced_ax_node.
				# JP: enhanced_ax_node に値を代入する。
				enhanced_ax_node = self._build_enhanced_ax_node(ax_node)
			else:
				# EN: Assign value to enhanced_ax_node.
				# JP: enhanced_ax_node に値を代入する。
				enhanced_ax_node = None

			# To make attributes more readable
			# EN: Assign annotated value to attributes.
			# JP: attributes に型付きの値を代入する。
			attributes: dict[str, str] | None = None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'attributes' in node and node['attributes']:
				# EN: Assign value to attributes.
				# JP: attributes に値を代入する。
				attributes = {}
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for i in range(0, len(node['attributes']), 2):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					attributes[node['attributes'][i]] = node['attributes'][i + 1]

			# EN: Assign value to shadow_root_type.
			# JP: shadow_root_type に値を代入する。
			shadow_root_type = None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'shadowRootType' in node and node['shadowRootType']:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to shadow_root_type.
					# JP: shadow_root_type に値を代入する。
					shadow_root_type = node['shadowRootType']
				except ValueError:
					# EN: Keep a placeholder statement.
					# JP: プレースホルダー文を維持する。
					pass

			# Get snapshot data and calculate absolute position
			# EN: Assign value to snapshot_data.
			# JP: snapshot_data に値を代入する。
			snapshot_data = snapshot_lookup.get(node['backendNodeId'], None)
			# EN: Assign value to absolute_position.
			# JP: absolute_position に値を代入する。
			absolute_position = None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if snapshot_data and snapshot_data.bounds:
				# EN: Assign value to absolute_position.
				# JP: absolute_position に値を代入する。
				absolute_position = DOMRect(
					x=snapshot_data.bounds.x + total_frame_offset.x,
					y=snapshot_data.bounds.y + total_frame_offset.y,
					width=snapshot_data.bounds.width,
					height=snapshot_data.bounds.height,
				)

			# EN: Assign value to dom_tree_node.
			# JP: dom_tree_node に値を代入する。
			dom_tree_node = EnhancedDOMTreeNode(
				node_id=node['nodeId'],
				backend_node_id=node['backendNodeId'],
				node_type=NodeType(node['nodeType']),
				node_name=node['nodeName'],
				node_value=node['nodeValue'],
				attributes=attributes or {},
				is_scrollable=node.get('isScrollable', None),
				frame_id=node.get('frameId', None),
				session_id=self.browser_session.agent_focus.session_id if self.browser_session.agent_focus else None,
				target_id=target_id,
				content_document=None,
				shadow_root_type=shadow_root_type,
				shadow_roots=None,
				parent_node=None,
				children_nodes=None,
				ax_node=enhanced_ax_node,
				snapshot_node=snapshot_data,
				is_visible=None,
				absolute_position=absolute_position,
				element_index=None,
			)

			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			enhanced_dom_tree_node_lookup[node['nodeId']] = dom_tree_node

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'parentId' in node and node['parentId']:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				dom_tree_node.parent_node = enhanced_dom_tree_node_lookup[
					node['parentId']
				]  # parents should always be in the lookup

			# Check if this is an HTML frame node and add it to the list
			# EN: Assign value to updated_html_frames.
			# JP: updated_html_frames に値を代入する。
			updated_html_frames = html_frames.copy()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node['nodeType'] == NodeType.ELEMENT_NODE.value and node['nodeName'] == 'HTML' and node.get('frameId') is not None:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				updated_html_frames.append(dom_tree_node)

				# and adjust the total frame offset by scroll
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if snapshot_data and snapshot_data.scrollRects:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					total_frame_offset.x -= snapshot_data.scrollRects.x
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					total_frame_offset.y -= snapshot_data.scrollRects.y
					# DEBUG: Log iframe scroll information
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f'🔍 DEBUG: HTML frame scroll - scrollY={snapshot_data.scrollRects.y}, scrollX={snapshot_data.scrollRects.x}, frameId={node.get("frameId")}, nodeId={node["nodeId"]}'
					)

			# Calculate new iframe offset for content documents, accounting for iframe scroll
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				(node['nodeName'].upper() == 'IFRAME' or node['nodeName'].upper() == 'FRAME')
				and snapshot_data
				and snapshot_data.bounds
			):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if snapshot_data.bounds:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					updated_html_frames.append(dom_tree_node)

					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					total_frame_offset.x += snapshot_data.bounds.x
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					total_frame_offset.y += snapshot_data.bounds.y

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'contentDocument' in node and node['contentDocument']:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				dom_tree_node.content_document = await _construct_enhanced_node(
					node['contentDocument'], updated_html_frames, total_frame_offset
				)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				dom_tree_node.content_document.parent_node = dom_tree_node
				# forcefully set the parent node to the content document node (helps traverse the tree)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'shadowRoots' in node and node['shadowRoots']:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				dom_tree_node.shadow_roots = []
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for shadow_root in node['shadowRoots']:
					# EN: Assign value to shadow_root_node.
					# JP: shadow_root_node に値を代入する。
					shadow_root_node = await _construct_enhanced_node(shadow_root, updated_html_frames, total_frame_offset)
					# forcefully set the parent node to the shadow root node (helps traverse the tree)
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					shadow_root_node.parent_node = dom_tree_node
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					dom_tree_node.shadow_roots.append(shadow_root_node)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'children' in node and node['children']:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				dom_tree_node.children_nodes = []
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for child in node['children']:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					dom_tree_node.children_nodes.append(
						await _construct_enhanced_node(child, updated_html_frames, total_frame_offset)
					)

			# Set visibility using the collected HTML frames
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			dom_tree_node.is_visible = self.is_element_visible_according_to_all_parents(dom_tree_node, updated_html_frames)

			# DEBUG: Log visibility info for form elements in iframes
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if dom_tree_node.tag_name and dom_tree_node.tag_name.upper() in ['INPUT', 'SELECT', 'TEXTAREA', 'LABEL']:
				# EN: Assign value to attrs.
				# JP: attrs に値を代入する。
				attrs = dom_tree_node.attributes or {}
				# EN: Assign value to elem_id.
				# JP: elem_id に値を代入する。
				elem_id = attrs.get('id', '')
				# EN: Assign value to elem_name.
				# JP: elem_name に値を代入する。
				elem_name = attrs.get('name', '')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if (
					'city' in elem_id.lower()
					or 'city' in elem_name.lower()
					or 'state' in elem_id.lower()
					or 'state' in elem_name.lower()
					or 'zip' in elem_id.lower()
					or 'zip' in elem_name.lower()
				):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f"🔍 DEBUG: Form element {dom_tree_node.tag_name} id='{elem_id}' name='{elem_name}' - visible={dom_tree_node.is_visible}, bounds={dom_tree_node.snapshot_node.bounds if dom_tree_node.snapshot_node else 'NO_SNAPSHOT'}"
					)

			# handle cross origin iframe (just recursively call the main function with the proper target if it exists in iframes)
			# only do this if the iframe is visible (otherwise it's not worth it)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				# TODO: hacky way to disable cross origin iframes for now
				self.cross_origin_iframes and node['nodeName'].upper() == 'IFRAME' and node.get('contentDocument', None) is None
			):  # None meaning there is no content
				# Check iframe depth to prevent infinite recursion
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if iframe_depth >= self.max_iframe_depth:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f'Skipping iframe at depth {iframe_depth} to prevent infinite recursion (max depth: {self.max_iframe_depth})'
					)
				else:
					# Check if iframe is visible and large enough (>= 200px in both dimensions)
					# EN: Assign value to should_process_iframe.
					# JP: should_process_iframe に値を代入する。
					should_process_iframe = False

					# First check if the iframe element itself is visible
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if dom_tree_node.is_visible:
						# Check iframe dimensions
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if dom_tree_node.snapshot_node and dom_tree_node.snapshot_node.bounds:
							# EN: Assign value to bounds.
							# JP: bounds に値を代入する。
							bounds = dom_tree_node.snapshot_node.bounds
							# EN: Assign value to width.
							# JP: width に値を代入する。
							width = bounds.width
							# EN: Assign value to height.
							# JP: height に値を代入する。
							height = bounds.height

							# Only process if iframe is at least 200px in both dimensions
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if width >= 200 and height >= 200:
								# EN: Assign value to should_process_iframe.
								# JP: should_process_iframe に値を代入する。
								should_process_iframe = True
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								self.logger.debug(f'Processing cross-origin iframe: visible=True, width={width}, height={height}')
							else:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								self.logger.debug(
									f'Skipping small cross-origin iframe: width={width}, height={height} (needs >= 200px)'
								)
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug('Skipping cross-origin iframe: no bounds available')
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug('Skipping invisible cross-origin iframe')

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if should_process_iframe:
						# Use get_all_frames to find the iframe's target
						# EN: Assign value to frame_id.
						# JP: frame_id に値を代入する。
						frame_id = node.get('frameId', None)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if frame_id:
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							all_frames, _ = await self.browser_session.get_all_frames()
							# EN: Assign value to frame_info.
							# JP: frame_info に値を代入する。
							frame_info = all_frames.get(frame_id)
							# EN: Assign value to iframe_document_target.
							# JP: iframe_document_target に値を代入する。
							iframe_document_target = None
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if frame_info and frame_info.get('frameTargetId'):
								# Get the target info for this iframe
								# EN: Assign value to targets.
								# JP: targets に値を代入する。
								targets = await self.browser_session.cdp_client.send.Target.getTargets()
								# EN: Assign value to iframe_document_target.
								# JP: iframe_document_target に値を代入する。
								iframe_document_target = next(
									(t for t in targets['targetInfos'] if t['targetId'] == frame_info['frameTargetId']), None
								)
						else:
							# EN: Assign value to iframe_document_target.
							# JP: iframe_document_target に値を代入する。
							iframe_document_target = None
						# if target actually exists in one of the frames, just recursively build the dom tree for it
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if iframe_document_target:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug(
								f'Getting content document for iframe {node.get("frameId", None)} at depth {iframe_depth + 1}'
							)
							# EN: Assign value to content_document.
							# JP: content_document に値を代入する。
							content_document = await self.get_dom_tree(
								target_id=iframe_document_target.get('targetId'),
								# TODO: experiment with this values -> not sure whether the whole cross origin iframe should be ALWAYS included as soon as some part of it is visible or not.
								# Current config: if the cross origin iframe is AT ALL visible, then just include everything inside of it!
								# initial_html_frames=updated_html_frames,
								initial_total_frame_offset=total_frame_offset,
								iframe_depth=iframe_depth + 1,
							)

							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							dom_tree_node.content_document = content_document
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							dom_tree_node.content_document.parent_node = dom_tree_node

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return dom_tree_node

		# EN: Assign value to enhanced_dom_tree_node.
		# JP: enhanced_dom_tree_node に値を代入する。
		enhanced_dom_tree_node = await _construct_enhanced_node(dom_tree['root'], initial_html_frames, initial_total_frame_offset)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return enhanced_dom_tree_node

	# EN: Define async function `get_serialized_dom_tree`.
	# JP: 非同期関数 `get_serialized_dom_tree` を定義する。
	async def get_serialized_dom_tree(
		self, previous_cached_state: SerializedDOMState | None = None
	) -> tuple[SerializedDOMState, EnhancedDOMTreeNode, dict[str, float]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the serialized DOM tree representation for LLM consumption.

		Returns:
			Tuple of (serialized_dom_state, enhanced_dom_tree_root, timing_info)
		"""

		# Use current target (None means use current)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session.current_target_id is not None
		# EN: Assign value to enhanced_dom_tree.
		# JP: enhanced_dom_tree に値を代入する。
		enhanced_dom_tree = await self.get_dom_tree(target_id=self.browser_session.current_target_id)

		# EN: Assign value to start.
		# JP: start に値を代入する。
		start = time.time()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		serialized_dom_state, serializer_timing = DOMTreeSerializer(
			enhanced_dom_tree, previous_cached_state, paint_order_filtering=self.paint_order_filtering
		).serialize_accessible_elements()

		# EN: Assign value to end.
		# JP: end に値を代入する。
		end = time.time()
		# EN: Assign value to serialize_total_timing.
		# JP: serialize_total_timing に値を代入する。
		serialize_total_timing = {'serialize_dom_tree_total': end - start}

		# Combine all timing info
		# EN: Assign value to all_timing.
		# JP: all_timing に値を代入する。
		all_timing = {**serializer_timing, **serialize_total_timing}

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return serialized_dom_state, enhanced_dom_tree, all_timing

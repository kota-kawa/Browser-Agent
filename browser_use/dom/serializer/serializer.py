# @file purpose: Serializes enhanced DOM trees to string format for LLM consumption


# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.serializer.clickable_elements import ClickableElementDetector
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.serializer.paint_order import PaintOrderRemover
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.utils import cap_text_length
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import (
	DOMRect,
	DOMSelectorMap,
	EnhancedDOMTreeNode,
	NodeType,
	PropagatingBounds,
	SerializedDOMState,
	SimplifiedNode,
)

# EN: Assign value to DISABLED_ELEMENTS.
# JP: DISABLED_ELEMENTS に値を代入する。
DISABLED_ELEMENTS = {'style', 'script', 'head', 'meta', 'link', 'title'}


# EN: Define class `DOMTreeSerializer`.
# JP: クラス `DOMTreeSerializer` を定義する。
class DOMTreeSerializer:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serializes enhanced DOM trees to string format."""

	# Configuration - elements that propagate bounds to their children
	# EN: Assign value to PROPAGATING_ELEMENTS.
	# JP: PROPAGATING_ELEMENTS に値を代入する。
	PROPAGATING_ELEMENTS = [
		{'tag': 'a', 'role': None},  # Any <a> tag
		{'tag': 'button', 'role': None},  # Any <button> tag
		{'tag': 'div', 'role': 'button'},  # <div role="button">
		{'tag': 'div', 'role': 'combobox'},  # <div role="combobox"> - dropdowns/selects
		{'tag': 'span', 'role': 'button'},  # <span role="button">
		{'tag': 'span', 'role': 'combobox'},  # <span role="combobox">
		{'tag': 'input', 'role': 'combobox'},  # <input role="combobox"> - autocomplete inputs
		{'tag': 'input', 'role': 'combobox'},  # <input type="text"> - text inputs with suggestions
		# {'tag': 'div', 'role': 'link'},     # <div role="link">
		# {'tag': 'span', 'role': 'link'},    # <span role="link">
	]
	# EN: Assign value to DEFAULT_CONTAINMENT_THRESHOLD.
	# JP: DEFAULT_CONTAINMENT_THRESHOLD に値を代入する。
	DEFAULT_CONTAINMENT_THRESHOLD = 0.99  # 99% containment by default

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		root_node: EnhancedDOMTreeNode,
		previous_cached_state: SerializedDOMState | None = None,
		enable_bbox_filtering: bool = True,
		containment_threshold: float | None = None,
		paint_order_filtering: bool = True,
	):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.root_node = root_node
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._interactive_counter = 1
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._selector_map: DOMSelectorMap = {}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._previous_cached_selector_map = previous_cached_state.selector_map if previous_cached_state else None
		# Add timing tracking
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.timing_info: dict[str, float] = {}
		# Cache for clickable element detection to avoid redundant calls
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._clickable_cache: dict[int, bool] = {}
		# Bounding box filtering configuration
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.enable_bbox_filtering = enable_bbox_filtering
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.containment_threshold = containment_threshold or self.DEFAULT_CONTAINMENT_THRESHOLD
		# Paint order filtering configuration
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.paint_order_filtering = paint_order_filtering

	# EN: Define function `serialize_accessible_elements`.
	# JP: 関数 `serialize_accessible_elements` を定義する。
	def serialize_accessible_elements(self) -> tuple[SerializedDOMState, dict[str, float]]:
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import time

		# EN: Assign value to start_total.
		# JP: start_total に値を代入する。
		start_total = time.time()

		# Reset state
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._interactive_counter = 1
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._selector_map = {}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._semantic_groups = []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._clickable_cache = {}  # Clear cache for new serialization

		# Step 1: Create simplified tree (includes clickable element detection)
		# EN: Assign value to start_step1.
		# JP: start_step1 に値を代入する。
		start_step1 = time.time()
		# EN: Assign value to simplified_tree.
		# JP: simplified_tree に値を代入する。
		simplified_tree = self._create_simplified_tree(self.root_node)
		# EN: Assign value to end_step1.
		# JP: end_step1 に値を代入する。
		end_step1 = time.time()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.timing_info['create_simplified_tree'] = end_step1 - start_step1

		# Step 2: Remove elements based on paint order
		# EN: Assign value to start_step3.
		# JP: start_step3 に値を代入する。
		start_step3 = time.time()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.paint_order_filtering and simplified_tree:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			PaintOrderRemover(simplified_tree).calculate_paint_order()
		# EN: Assign value to end_step3.
		# JP: end_step3 に値を代入する。
		end_step3 = time.time()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.timing_info['calculate_paint_order'] = end_step3 - start_step3

		# Step 3: Optimize tree (remove unnecessary parents)
		# EN: Assign value to start_step2.
		# JP: start_step2 に値を代入する。
		start_step2 = time.time()
		# EN: Assign value to optimized_tree.
		# JP: optimized_tree に値を代入する。
		optimized_tree = self._optimize_tree(simplified_tree)
		# EN: Assign value to end_step2.
		# JP: end_step2 に値を代入する。
		end_step2 = time.time()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.timing_info['optimize_tree'] = end_step2 - start_step2

		# Step 3: Apply bounding box filtering (NEW)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.enable_bbox_filtering and optimized_tree:
			# EN: Assign value to start_step3.
			# JP: start_step3 に値を代入する。
			start_step3 = time.time()
			# EN: Assign value to filtered_tree.
			# JP: filtered_tree に値を代入する。
			filtered_tree = self._apply_bounding_box_filtering(optimized_tree)
			# EN: Assign value to end_step3.
			# JP: end_step3 に値を代入する。
			end_step3 = time.time()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.timing_info['bbox_filtering'] = end_step3 - start_step3
		else:
			# EN: Assign value to filtered_tree.
			# JP: filtered_tree に値を代入する。
			filtered_tree = optimized_tree

		# Step 4: Assign interactive indices to clickable elements
		# EN: Assign value to start_step4.
		# JP: start_step4 に値を代入する。
		start_step4 = time.time()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._assign_interactive_indices_and_mark_new_nodes(filtered_tree)
		# EN: Assign value to end_step4.
		# JP: end_step4 に値を代入する。
		end_step4 = time.time()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.timing_info['assign_interactive_indices'] = end_step4 - start_step4

		# EN: Assign value to end_total.
		# JP: end_total に値を代入する。
		end_total = time.time()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.timing_info['serialize_accessible_elements_total'] = end_total - start_total

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return SerializedDOMState(_root=filtered_tree, selector_map=self._selector_map), self.timing_info

	# EN: Define function `_is_interactive_cached`.
	# JP: 関数 `_is_interactive_cached` を定義する。
	def _is_interactive_cached(self, node: EnhancedDOMTreeNode) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Cached version of clickable element detection to avoid redundant calls."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.node_id not in self._clickable_cache:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import time

			# EN: Assign value to start_time.
			# JP: start_time に値を代入する。
			start_time = time.time()
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = ClickableElementDetector.is_interactive(node)
			# EN: Assign value to end_time.
			# JP: end_time に値を代入する。
			end_time = time.time()

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'clickable_detection_time' not in self.timing_info:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.timing_info['clickable_detection_time'] = 0
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self.timing_info['clickable_detection_time'] += end_time - start_time

			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._clickable_cache[node.node_id] = result

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._clickable_cache[node.node_id]

	# EN: Define function `_create_simplified_tree`.
	# JP: 関数 `_create_simplified_tree` を定義する。
	def _create_simplified_tree(self, node: EnhancedDOMTreeNode, depth: int = 0) -> SimplifiedNode | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Step 1: Create a simplified tree with enhanced element detection."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.node_type == NodeType.DOCUMENT_NODE:
			# for all cldren including shadow roots
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for child in node.children_and_shadow_roots:
				# EN: Assign value to simplified_child.
				# JP: simplified_child に値を代入する。
				simplified_child = self._create_simplified_tree(child, depth + 1)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if simplified_child:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return simplified_child

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
			# ENHANCED shadow DOM processing - always include shadow content
			# EN: Assign value to simplified.
			# JP: simplified に値を代入する。
			simplified = SimplifiedNode(original_node=node, children=[])
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for child in node.children_and_shadow_roots:
				# EN: Assign value to simplified_child.
				# JP: simplified_child に値を代入する。
				simplified_child = self._create_simplified_tree(child, depth + 1)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if simplified_child:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					simplified.children.append(simplified_child)

			# Always return shadow DOM fragments, even if children seem empty
			# Shadow DOM often contains the actual interactive content in SPAs
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return simplified if simplified.children else SimplifiedNode(original_node=node, children=[])

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif node.node_type == NodeType.ELEMENT_NODE:
			# Skip non-content elements
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.node_name.lower() in DISABLED_ELEMENTS:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.node_name == 'IFRAME' or node.node_name == 'FRAME':
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node.content_document:
					# EN: Assign value to simplified.
					# JP: simplified に値を代入する。
					simplified = SimplifiedNode(original_node=node, children=[])
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for child in node.content_document.children_nodes or []:
						# EN: Assign value to simplified_child.
						# JP: simplified_child に値を代入する。
						simplified_child = self._create_simplified_tree(child, depth + 1)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if simplified_child is not None:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							simplified.children.append(simplified_child)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return simplified

			# EN: Assign value to is_visible.
			# JP: is_visible に値を代入する。
			is_visible = node.is_visible
			# EN: Assign value to is_scrollable.
			# JP: is_scrollable に値を代入する。
			is_scrollable = node.is_actually_scrollable
			# EN: Assign value to has_shadow_content.
			# JP: has_shadow_content に値を代入する。
			has_shadow_content = bool(node.children_and_shadow_roots)

			# ENHANCED SHADOW DOM DETECTION: Include shadow hosts even if not visible
			# EN: Assign value to is_shadow_host.
			# JP: is_shadow_host に値を代入する。
			is_shadow_host = any(child.node_type == NodeType.DOCUMENT_FRAGMENT_NODE for child in node.children_and_shadow_roots)

			# Include if interactive (regardless of visibility), scrollable, has children, or is shadow host
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if is_visible or is_scrollable or has_shadow_content or is_shadow_host:
				# EN: Assign value to simplified.
				# JP: simplified に値を代入する。
				simplified = SimplifiedNode(original_node=node, children=[], is_shadow_host=is_shadow_host)

				# Process ALL children including shadow roots with enhanced logging
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for child in node.children_and_shadow_roots:
					# EN: Assign value to simplified_child.
					# JP: simplified_child に値を代入する。
					simplified_child = self._create_simplified_tree(child, depth + 1)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if simplified_child:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						simplified.children.append(simplified_child)

				# SHADOW DOM SPECIAL CASE: Always include shadow hosts even if not visible
				# Many SPA frameworks (React, Vue) render content in shadow DOM
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if is_shadow_host and simplified.children:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return simplified

				# Return if meaningful or has meaningful children
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if is_visible or is_scrollable or simplified.children:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return simplified

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif node.node_type == NodeType.TEXT_NODE:
			# Include meaningful text nodes
			# EN: Assign value to is_visible.
			# JP: is_visible に値を代入する。
			is_visible = node.snapshot_node and node.is_visible
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if is_visible and node.node_value and node.node_value.strip() and len(node.node_value.strip()) > 1:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return SimplifiedNode(original_node=node, children=[])

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `_optimize_tree`.
	# JP: 関数 `_optimize_tree` を定義する。
	def _optimize_tree(self, node: SimplifiedNode | None) -> SimplifiedNode | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Step 2: Optimize tree structure."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not node:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Process children
		# EN: Assign value to optimized_children.
		# JP: optimized_children に値を代入する。
		optimized_children = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for child in node.children:
			# EN: Assign value to optimized_child.
			# JP: optimized_child に値を代入する。
			optimized_child = self._optimize_tree(child)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if optimized_child:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				optimized_children.append(optimized_child)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		node.children = optimized_children

		# Keep meaningful nodes
		# EN: Assign value to is_interactive_opt.
		# JP: is_interactive_opt に値を代入する。
		is_interactive_opt = self._is_interactive_cached(node.original_node)
		# EN: Assign value to is_visible.
		# JP: is_visible に値を代入する。
		is_visible = node.original_node.snapshot_node and node.original_node.is_visible

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if (
			is_visible  # Keep all visible nodes
			or node.original_node.is_actually_scrollable
			or node.original_node.node_type == NodeType.TEXT_NODE
			or node.children
		):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return node

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `_collect_interactive_elements`.
	# JP: 関数 `_collect_interactive_elements` を定義する。
	def _collect_interactive_elements(self, node: SimplifiedNode, elements: list[SimplifiedNode]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Recursively collect interactive elements that are also visible."""
		# EN: Assign value to is_interactive.
		# JP: is_interactive に値を代入する。
		is_interactive = self._is_interactive_cached(node.original_node)
		# EN: Assign value to is_visible.
		# JP: is_visible に値を代入する。
		is_visible = node.original_node.snapshot_node and node.original_node.is_visible

		# Only collect elements that are both interactive AND visible
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_interactive and is_visible:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			elements.append(node)

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for child in node.children:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._collect_interactive_elements(child, elements)

	# EN: Define function `_assign_interactive_indices_and_mark_new_nodes`.
	# JP: 関数 `_assign_interactive_indices_and_mark_new_nodes` を定義する。
	def _assign_interactive_indices_and_mark_new_nodes(self, node: SimplifiedNode | None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Assign interactive indices to clickable elements that are also visible."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not node:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Skip assigning index to excluded nodes, or ignored by paint order
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not node.excluded_by_parent and not node.ignored_by_paint_order:
			# Assign index to clickable elements that are also visible
			# EN: Assign value to is_interactive_assign.
			# JP: is_interactive_assign に値を代入する。
			is_interactive_assign = self._is_interactive_cached(node.original_node)
			# EN: Assign value to is_visible.
			# JP: is_visible に値を代入する。
			is_visible = node.original_node.snapshot_node and node.original_node.is_visible

			# Only add to selector map if element is both interactive AND visible
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if is_interactive_assign and is_visible:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				node.interactive_index = self._interactive_counter
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				node.original_node.element_index = self._interactive_counter
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._selector_map[self._interactive_counter] = node.original_node
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				self._interactive_counter += 1

				# Check if node is new
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._previous_cached_selector_map:
					# EN: Assign value to previous_backend_node_ids.
					# JP: previous_backend_node_ids に値を代入する。
					previous_backend_node_ids = {node.backend_node_id for node in self._previous_cached_selector_map.values()}
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if node.original_node.backend_node_id not in previous_backend_node_ids:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						node.is_new = True

		# Process children
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for child in node.children:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._assign_interactive_indices_and_mark_new_nodes(child)

	# EN: Define function `_apply_bounding_box_filtering`.
	# JP: 関数 `_apply_bounding_box_filtering` を定義する。
	def _apply_bounding_box_filtering(self, node: SimplifiedNode | None) -> SimplifiedNode | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Filter children contained within propagating parent bounds."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not node:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Start with no active bounds
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._filter_tree_recursive(node, active_bounds=None, depth=0)

		# Log statistics
		# EN: Assign value to excluded_count.
		# JP: excluded_count に値を代入する。
		excluded_count = self._count_excluded_nodes(node)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if excluded_count > 0:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import logging

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logging.debug(f'BBox filtering excluded {excluded_count} nodes')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return node

	# EN: Define function `_filter_tree_recursive`.
	# JP: 関数 `_filter_tree_recursive` を定義する。
	def _filter_tree_recursive(self, node: SimplifiedNode, active_bounds: PropagatingBounds | None = None, depth: int = 0):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Recursively filter tree with bounding box propagation.
		Bounds propagate to ALL descendants until overridden.
		"""

		# Check if this node should be excluded by active bounds
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if active_bounds and self._should_exclude_child(node, active_bounds):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			node.excluded_by_parent = True
			# Important: Still check if this node starts NEW propagation

		# Check if this node starts new propagation (even if excluded!)
		# EN: Assign value to new_bounds.
		# JP: new_bounds に値を代入する。
		new_bounds = None
		# EN: Assign value to tag.
		# JP: tag に値を代入する。
		tag = node.original_node.tag_name.lower()
		# EN: Assign value to role.
		# JP: role に値を代入する。
		role = node.original_node.attributes.get('role') if node.original_node.attributes else None
		# EN: Assign value to attributes.
		# JP: attributes に値を代入する。
		attributes = {
			'tag': tag,
			'role': role,
		}
		# Check if this element matches any propagating element pattern
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._is_propagating_element(attributes):
			# This node propagates bounds to ALL its descendants
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.original_node.snapshot_node and node.original_node.snapshot_node.bounds:
				# EN: Assign value to new_bounds.
				# JP: new_bounds に値を代入する。
				new_bounds = PropagatingBounds(
					tag=tag,
					bounds=node.original_node.snapshot_node.bounds,
					node_id=node.original_node.node_id,
					depth=depth,
				)

		# Propagate to ALL children
		# Use new_bounds if this node starts propagation, otherwise continue with active_bounds
		# EN: Assign value to propagate_bounds.
		# JP: propagate_bounds に値を代入する。
		propagate_bounds = new_bounds if new_bounds else active_bounds

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for child in node.children:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._filter_tree_recursive(child, propagate_bounds, depth + 1)

	# EN: Define function `_should_exclude_child`.
	# JP: 関数 `_should_exclude_child` を定義する。
	def _should_exclude_child(self, node: SimplifiedNode, active_bounds: PropagatingBounds) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Determine if child should be excluded based on propagating bounds.
		"""

		# Never exclude text nodes - we always want to preserve text content
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.original_node.node_type == NodeType.TEXT_NODE:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Get child bounds
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not node.original_node.snapshot_node or not node.original_node.snapshot_node.bounds:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False  # No bounds = can't determine containment

		# EN: Assign value to child_bounds.
		# JP: child_bounds に値を代入する。
		child_bounds = node.original_node.snapshot_node.bounds

		# Check containment with configured threshold
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_contained(child_bounds, active_bounds.bounds, self.containment_threshold):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False  # Not sufficiently contained

		# EXCEPTION RULES - Keep these even if contained:

		# EN: Assign value to child_tag.
		# JP: child_tag に値を代入する。
		child_tag = node.original_node.tag_name.lower()
		# EN: Assign value to child_role.
		# JP: child_role に値を代入する。
		child_role = node.original_node.attributes.get('role') if node.original_node.attributes else None
		# EN: Assign value to child_attributes.
		# JP: child_attributes に値を代入する。
		child_attributes = {
			'tag': child_tag,
			'role': child_role,
		}

		# 1. Never exclude form elements (they need individual interaction)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if child_tag in ['input', 'select', 'textarea', 'label']:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# 2. Keep if child is also a propagating element
		# (might have stopPropagation, e.g., button in button)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._is_propagating_element(child_attributes):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# 3. Keep if has explicit onclick handler
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.original_node.attributes and 'onclick' in node.original_node.attributes:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# 4. Keep if has aria-label suggesting it's independently interactive
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.original_node.attributes:
			# EN: Assign value to aria_label.
			# JP: aria_label に値を代入する。
			aria_label = node.original_node.attributes.get('aria-label')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if aria_label and aria_label.strip():
				# Has meaningful aria-label, likely interactive
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return False

		# 5. Keep if has role suggesting interactivity
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.original_node.attributes:
			# EN: Assign value to role.
			# JP: role に値を代入する。
			role = node.original_node.attributes.get('role')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if role in ['button', 'link', 'checkbox', 'radio', 'tab', 'menuitem']:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return False

		# Default: exclude this child
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Define function `_is_contained`.
	# JP: 関数 `_is_contained` を定義する。
	def _is_contained(self, child: DOMRect, parent: DOMRect, threshold: float) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Check if child is contained within parent bounds.

		Args:
			threshold: Percentage (0.0-1.0) of child that must be within parent
		"""
		# Calculate intersection
		# EN: Assign value to x_overlap.
		# JP: x_overlap に値を代入する。
		x_overlap = max(0, min(child.x + child.width, parent.x + parent.width) - max(child.x, parent.x))
		# EN: Assign value to y_overlap.
		# JP: y_overlap に値を代入する。
		y_overlap = max(0, min(child.y + child.height, parent.y + parent.height) - max(child.y, parent.y))

		# EN: Assign value to intersection_area.
		# JP: intersection_area に値を代入する。
		intersection_area = x_overlap * y_overlap
		# EN: Assign value to child_area.
		# JP: child_area に値を代入する。
		child_area = child.width * child.height

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if child_area == 0:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False  # Zero-area element

		# EN: Assign value to containment_ratio.
		# JP: containment_ratio に値を代入する。
		containment_ratio = intersection_area / child_area
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return containment_ratio >= threshold

	# EN: Define function `_count_excluded_nodes`.
	# JP: 関数 `_count_excluded_nodes` を定義する。
	def _count_excluded_nodes(self, node: SimplifiedNode, count: int = 0) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Count how many nodes were excluded (for debugging)."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(node, 'excluded_by_parent') and node.excluded_by_parent:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			count += 1
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for child in node.children:
			# EN: Assign value to count.
			# JP: count に値を代入する。
			count = self._count_excluded_nodes(child, count)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return count

	# EN: Define function `_is_propagating_element`.
	# JP: 関数 `_is_propagating_element` を定義する。
	def _is_propagating_element(self, attributes: dict[str, str | None]) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Check if an element should propagate bounds based on attributes.
		If the element satisfies one of the patterns, it propagates bounds to all its children.
		"""
		# EN: Assign value to keys_to_check.
		# JP: keys_to_check に値を代入する。
		keys_to_check = ['tag', 'role']
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for pattern in self.PROPAGATING_ELEMENTS:
			# Check if the element satisfies the pattern
			# EN: Assign value to check.
			# JP: check に値を代入する。
			check = [pattern.get(key) is None or pattern.get(key) == attributes.get(key) for key in keys_to_check]
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if all(check):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `serialize_tree`.
	# JP: 関数 `serialize_tree` を定義する。
	@staticmethod
	def serialize_tree(node: SimplifiedNode | None, include_attributes: list[str], depth: int = 0) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serialize the optimized tree to string format."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not node:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''

		# Skip rendering excluded nodes, but process their children
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(node, 'excluded_by_parent') and node.excluded_by_parent:
			# EN: Assign value to formatted_text.
			# JP: formatted_text に値を代入する。
			formatted_text = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for child in node.children:
				# EN: Assign value to child_text.
				# JP: child_text に値を代入する。
				child_text = DOMTreeSerializer.serialize_tree(child, include_attributes, depth)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if child_text:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					formatted_text.append(child_text)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '\n'.join(formatted_text)

		# EN: Assign value to formatted_text.
		# JP: formatted_text に値を代入する。
		formatted_text = []
		# EN: Assign value to depth_str.
		# JP: depth_str に値を代入する。
		depth_str = depth * '\t'
		# EN: Assign value to next_depth.
		# JP: next_depth に値を代入する。
		next_depth = depth

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.original_node.node_type == NodeType.ELEMENT_NODE:
			# Skip displaying nodes marked as should_display=False
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not node.should_display:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for child in node.children:
					# EN: Assign value to child_text.
					# JP: child_text に値を代入する。
					child_text = DOMTreeSerializer.serialize_tree(child, include_attributes, depth)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if child_text:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						formatted_text.append(child_text)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return '\n'.join(formatted_text)

			# Add element with interactive_index if clickable, scrollable, or iframe
			# EN: Assign value to is_any_scrollable.
			# JP: is_any_scrollable に値を代入する。
			is_any_scrollable = node.original_node.is_actually_scrollable or node.original_node.is_scrollable
			# EN: Assign value to should_show_scroll.
			# JP: should_show_scroll に値を代入する。
			should_show_scroll = node.original_node.should_show_scroll_info
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				node.interactive_index is not None
				or is_any_scrollable
				or node.original_node.tag_name.upper() == 'IFRAME'
				or node.original_node.tag_name.upper() == 'FRAME'
			):
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				next_depth += 1

				# Build attributes string
				# EN: Assign value to attributes_html_str.
				# JP: attributes_html_str に値を代入する。
				attributes_html_str = DOMTreeSerializer._build_attributes_string(node.original_node, include_attributes, '')

				# Build the line with shadow host indicator
				# EN: Assign value to shadow_prefix.
				# JP: shadow_prefix に値を代入する。
				shadow_prefix = ''
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node.is_shadow_host:
					# Check if any shadow children are closed
					# EN: Assign value to has_closed_shadow.
					# JP: has_closed_shadow に値を代入する。
					has_closed_shadow = any(
						child.original_node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE
						and child.original_node.shadow_root_type
						and child.original_node.shadow_root_type.lower() == 'closed'
						for child in node.children
					)
					# EN: Assign value to shadow_prefix.
					# JP: shadow_prefix に値を代入する。
					shadow_prefix = '|SHADOW(closed)|' if has_closed_shadow else '|SHADOW(open)|'

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if should_show_scroll and node.interactive_index is None:
					# Scrollable container but not clickable
					# EN: Assign value to line.
					# JP: line に値を代入する。
					line = f'{depth_str}{shadow_prefix}|SCROLL|<{node.original_node.tag_name}'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif node.interactive_index is not None:
					# Clickable (and possibly scrollable)
					# EN: Assign value to new_prefix.
					# JP: new_prefix に値を代入する。
					new_prefix = '*' if node.is_new else ''
					# EN: Assign value to scroll_prefix.
					# JP: scroll_prefix に値を代入する。
					scroll_prefix = '|SCROLL+' if should_show_scroll else '['
					# EN: Assign value to line.
					# JP: line に値を代入する。
					line = f'{depth_str}{shadow_prefix}{new_prefix}{scroll_prefix}{node.interactive_index}]<{node.original_node.tag_name}'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif node.original_node.tag_name.upper() == 'IFRAME':
					# Iframe element (not interactive)
					# EN: Assign value to line.
					# JP: line に値を代入する。
					line = f'{depth_str}{shadow_prefix}|IFRAME|<{node.original_node.tag_name}'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif node.original_node.tag_name.upper() == 'FRAME':
					# Frame element (not interactive)
					# EN: Assign value to line.
					# JP: line に値を代入する。
					line = f'{depth_str}{shadow_prefix}|FRAME|<{node.original_node.tag_name}'
				else:
					# EN: Assign value to line.
					# JP: line に値を代入する。
					line = f'{depth_str}{shadow_prefix}<{node.original_node.tag_name}'

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if attributes_html_str:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					line += f' {attributes_html_str}'

				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				line += ' />'

				# Add scroll information only when we should show it
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if should_show_scroll:
					# EN: Assign value to scroll_info_text.
					# JP: scroll_info_text に値を代入する。
					scroll_info_text = node.original_node.get_scroll_info_text()
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if scroll_info_text:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						line += f' ({scroll_info_text})'

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				formatted_text.append(line)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif node.original_node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
			# Shadow DOM representation - show clearly to LLM
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.original_node.shadow_root_type and node.original_node.shadow_root_type.lower() == 'closed':
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				formatted_text.append(f'{depth_str}▼ Shadow Content (Closed)')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				formatted_text.append(f'{depth_str}▼ Shadow Content (Open)')

			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			next_depth += 1

			# Process shadow DOM children
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for child in node.children:
				# EN: Assign value to child_text.
				# JP: child_text に値を代入する。
				child_text = DOMTreeSerializer.serialize_tree(child, include_attributes, next_depth)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if child_text:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					formatted_text.append(child_text)

			# Close shadow DOM indicator
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.children:  # Only show close if we had content
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				formatted_text.append(f'{depth_str}▲ Shadow Content End')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif node.original_node.node_type == NodeType.TEXT_NODE:
			# Include visible text
			# EN: Assign value to is_visible.
			# JP: is_visible に値を代入する。
			is_visible = node.original_node.snapshot_node and node.original_node.is_visible
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				is_visible
				and node.original_node.node_value
				and node.original_node.node_value.strip()
				and len(node.original_node.node_value.strip()) > 1
			):
				# EN: Assign value to clean_text.
				# JP: clean_text に値を代入する。
				clean_text = node.original_node.node_value.strip()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				formatted_text.append(f'{depth_str}{clean_text}')

		# Process children (for non-shadow elements)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.original_node.node_type != NodeType.DOCUMENT_FRAGMENT_NODE:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for child in node.children:
				# EN: Assign value to child_text.
				# JP: child_text に値を代入する。
				child_text = DOMTreeSerializer.serialize_tree(child, include_attributes, next_depth)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if child_text:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					formatted_text.append(child_text)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(formatted_text)

	# EN: Define function `_build_attributes_string`.
	# JP: 関数 `_build_attributes_string` を定義する。
	@staticmethod
	def _build_attributes_string(node: EnhancedDOMTreeNode, include_attributes: list[str], text: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Build the attributes string for an element."""
		# EN: Assign value to attributes_to_include.
		# JP: attributes_to_include に値を代入する。
		attributes_to_include = {}

		# Include HTML attributes
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.attributes:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			attributes_to_include.update(
				{
					key: str(value).strip()
					for key, value in node.attributes.items()
					if key in include_attributes and str(value).strip() != ''
				}
			)

		# Include accessibility properties
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.ax_node and node.ax_node.properties:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for prop in node.ax_node.properties:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if prop.name in include_attributes and prop.value is not None:
						# Convert boolean to lowercase string, keep others as-is
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if isinstance(prop.value, bool):
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							attributes_to_include[prop.name] = str(prop.value).lower()
						else:
							# EN: Assign value to prop_value_str.
							# JP: prop_value_str に値を代入する。
							prop_value_str = str(prop.value).strip()
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if prop_value_str:
								# EN: Assign value to target variable.
								# JP: target variable に値を代入する。
								attributes_to_include[prop.name] = prop_value_str
				except (AttributeError, ValueError):
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not attributes_to_include:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''

		# Remove duplicate values
		# EN: Assign value to ordered_keys.
		# JP: ordered_keys に値を代入する。
		ordered_keys = [key for key in include_attributes if key in attributes_to_include]

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(ordered_keys) > 1:
			# EN: Assign value to keys_to_remove.
			# JP: keys_to_remove に値を代入する。
			keys_to_remove = set()
			# EN: Assign value to seen_values.
			# JP: seen_values に値を代入する。
			seen_values = {}

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for key in ordered_keys:
				# EN: Assign value to value.
				# JP: value に値を代入する。
				value = attributes_to_include[key]
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if len(value) > 5:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if value in seen_values:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						keys_to_remove.add(key)
					else:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						seen_values[value] = key

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for key in keys_to_remove:
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del attributes_to_include[key]

		# Remove attributes that duplicate accessibility data
		# EN: Assign value to role.
		# JP: role に値を代入する。
		role = node.ax_node.role if node.ax_node else None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if role and node.node_name == role:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			attributes_to_include.pop('role', None)

		# EN: Assign value to attrs_to_remove_if_text_matches.
		# JP: attrs_to_remove_if_text_matches に値を代入する。
		attrs_to_remove_if_text_matches = ['aria-label', 'placeholder', 'title']
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for attr in attrs_to_remove_if_text_matches:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if attributes_to_include.get(attr) and attributes_to_include.get(attr, '').strip().lower() == text.strip().lower():
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del attributes_to_include[attr]

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if attributes_to_include:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ' '.join(f'{key}={cap_text_length(value, 100)}' for key, value in attributes_to_include.items())

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

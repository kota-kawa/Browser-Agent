# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Enhanced snapshot processing for browser-use DOM tree extraction.

This module provides stateless functions for parsing Chrome DevTools Protocol (CDP) DOMSnapshot data
to extract visibility, clickability, cursor styles, and other layout information.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.domsnapshot.commands import CaptureSnapshotReturns
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.domsnapshot.types import (
	LayoutTreeSnapshot,
	NodeTreeSnapshot,
	RareBooleanData,
)

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import DOMRect, EnhancedSnapshotNode

# Only the ESSENTIAL computed styles for interactivity and visibility detection
# EN: Assign value to REQUIRED_COMPUTED_STYLES.
# JP: REQUIRED_COMPUTED_STYLES に値を代入する。
REQUIRED_COMPUTED_STYLES = [
	# Only styles actually accessed in the codebase (prevents Chrome crashes on heavy sites)
	'display',  # Used in service.py visibility detection
	'visibility',  # Used in service.py visibility detection
	'opacity',  # Used in service.py visibility detection
	'overflow',  # Used in views.py scrollability detection
	'overflow-x',  # Used in views.py scrollability detection
	'overflow-y',  # Used in views.py scrollability detection
	'cursor',  # Used in enhanced_snapshot.py cursor extraction
	'pointer-events',  # Used for clickability logic
	'position',  # Used for visibility logic
	'background-color',  # Used for visibility logic
]


# EN: Define function `_parse_rare_boolean_data`.
# JP: 関数 `_parse_rare_boolean_data` を定義する。
def _parse_rare_boolean_data(rare_data: RareBooleanData, index: int) -> bool | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Parse rare boolean data from snapshot - returns True if index is in the rare data."""
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return index in rare_data['index']


# EN: Define function `_parse_computed_styles`.
# JP: 関数 `_parse_computed_styles` を定義する。
def _parse_computed_styles(strings: list[str], style_indices: list[int]) -> dict[str, str]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Parse computed styles from layout tree using string indices."""
	# EN: Assign value to styles.
	# JP: styles に値を代入する。
	styles = {}
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for i, style_index in enumerate(style_indices):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if i < len(REQUIRED_COMPUTED_STYLES) and 0 <= style_index < len(strings):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			styles[REQUIRED_COMPUTED_STYLES[i]] = strings[style_index]
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return styles


# EN: Define function `build_snapshot_lookup`.
# JP: 関数 `build_snapshot_lookup` を定義する。
def build_snapshot_lookup(
	snapshot: CaptureSnapshotReturns,
	device_pixel_ratio: float = 1.0,
) -> dict[int, EnhancedSnapshotNode]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Build a lookup table of backend node ID to enhanced snapshot data with everything calculated upfront."""
	# EN: Assign annotated value to snapshot_lookup.
	# JP: snapshot_lookup に型付きの値を代入する。
	snapshot_lookup: dict[int, EnhancedSnapshotNode] = {}

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not snapshot['documents']:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return snapshot_lookup

	# EN: Assign value to strings.
	# JP: strings に値を代入する。
	strings = snapshot['strings']

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for document in snapshot['documents']:
		# EN: Assign annotated value to nodes.
		# JP: nodes に型付きの値を代入する。
		nodes: NodeTreeSnapshot = document['nodes']
		# EN: Assign annotated value to layout.
		# JP: layout に型付きの値を代入する。
		layout: LayoutTreeSnapshot = document['layout']

		# Build backend node id to snapshot index lookup
		# EN: Assign value to backend_node_to_snapshot_index.
		# JP: backend_node_to_snapshot_index に値を代入する。
		backend_node_to_snapshot_index = {}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'backendNodeId' in nodes:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, backend_node_id in enumerate(nodes['backendNodeId']):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				backend_node_to_snapshot_index[backend_node_id] = i

		# PERFORMANCE: Pre-build layout index map to eliminate O(n²) double lookups
		# Preserve original behavior: use FIRST occurrence for duplicates
		# EN: Assign value to layout_index_map.
		# JP: layout_index_map に値を代入する。
		layout_index_map = {}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if layout and 'nodeIndex' in layout:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for layout_idx, node_index in enumerate(layout['nodeIndex']):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node_index not in layout_index_map:  # Only store first occurrence
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					layout_index_map[node_index] = layout_idx

		# Build snapshot lookup for each backend node id
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for backend_node_id, snapshot_index in backend_node_to_snapshot_index.items():
			# EN: Assign value to is_clickable.
			# JP: is_clickable に値を代入する。
			is_clickable = None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'isClickable' in nodes:
				# EN: Assign value to is_clickable.
				# JP: is_clickable に値を代入する。
				is_clickable = _parse_rare_boolean_data(nodes['isClickable'], snapshot_index)

			# Find corresponding layout node
			# EN: Assign value to cursor_style.
			# JP: cursor_style に値を代入する。
			cursor_style = None
			# EN: Assign value to is_visible.
			# JP: is_visible に値を代入する。
			is_visible = None
			# EN: Assign value to bounding_box.
			# JP: bounding_box に値を代入する。
			bounding_box = None
			# EN: Assign value to computed_styles.
			# JP: computed_styles に値を代入する。
			computed_styles = {}

			# Look for layout tree node that corresponds to this snapshot node
			# EN: Assign value to paint_order.
			# JP: paint_order に値を代入する。
			paint_order = None
			# EN: Assign value to client_rects.
			# JP: client_rects に値を代入する。
			client_rects = None
			# EN: Assign value to scroll_rects.
			# JP: scroll_rects に値を代入する。
			scroll_rects = None
			# EN: Assign value to stacking_contexts.
			# JP: stacking_contexts に値を代入する。
			stacking_contexts = None
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if snapshot_index in layout_index_map:
				# EN: Assign value to layout_idx.
				# JP: layout_idx に値を代入する。
				layout_idx = layout_index_map[snapshot_index]
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if layout_idx < len(layout.get('bounds', [])):
					# Parse bounding box
					# EN: Assign value to bounds.
					# JP: bounds に値を代入する。
					bounds = layout['bounds'][layout_idx]
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if len(bounds) >= 4:
						# IMPORTANT: CDP coordinates are in device pixels, convert to CSS pixels
						# by dividing by the device pixel ratio
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						raw_x, raw_y, raw_width, raw_height = bounds[0], bounds[1], bounds[2], bounds[3]

						# Apply device pixel ratio scaling to convert device pixels to CSS pixels
						# EN: Assign value to bounding_box.
						# JP: bounding_box に値を代入する。
						bounding_box = DOMRect(
							x=raw_x / device_pixel_ratio,
							y=raw_y / device_pixel_ratio,
							width=raw_width / device_pixel_ratio,
							height=raw_height / device_pixel_ratio,
						)

					# Parse computed styles for this layout node
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if layout_idx < len(layout.get('styles', [])):
						# EN: Assign value to style_indices.
						# JP: style_indices に値を代入する。
						style_indices = layout['styles'][layout_idx]
						# EN: Assign value to computed_styles.
						# JP: computed_styles に値を代入する。
						computed_styles = _parse_computed_styles(strings, style_indices)
						# EN: Assign value to cursor_style.
						# JP: cursor_style に値を代入する。
						cursor_style = computed_styles.get('cursor')

					# Extract paint order if available
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if layout_idx < len(layout.get('paintOrders', [])):
						# EN: Assign value to paint_order.
						# JP: paint_order に値を代入する。
						paint_order = layout.get('paintOrders', [])[layout_idx]

					# Extract client rects if available
					# EN: Assign value to client_rects_data.
					# JP: client_rects_data に値を代入する。
					client_rects_data = layout.get('clientRects', [])
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if layout_idx < len(client_rects_data):
						# EN: Assign value to client_rect_data.
						# JP: client_rect_data に値を代入する。
						client_rect_data = client_rects_data[layout_idx]
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if client_rect_data and len(client_rect_data) >= 4:
							# EN: Assign value to client_rects.
							# JP: client_rects に値を代入する。
							client_rects = DOMRect(
								x=client_rect_data[0],
								y=client_rect_data[1],
								width=client_rect_data[2],
								height=client_rect_data[3],
							)

					# Extract scroll rects if available
					# EN: Assign value to scroll_rects_data.
					# JP: scroll_rects_data に値を代入する。
					scroll_rects_data = layout.get('scrollRects', [])
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if layout_idx < len(scroll_rects_data):
						# EN: Assign value to scroll_rect_data.
						# JP: scroll_rect_data に値を代入する。
						scroll_rect_data = scroll_rects_data[layout_idx]
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if scroll_rect_data and len(scroll_rect_data) >= 4:
							# EN: Assign value to scroll_rects.
							# JP: scroll_rects に値を代入する。
							scroll_rects = DOMRect(
								x=scroll_rect_data[0],
								y=scroll_rect_data[1],
								width=scroll_rect_data[2],
								height=scroll_rect_data[3],
							)

					# Extract stacking contexts if available
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if layout_idx < len(layout.get('stackingContexts', [])):
						# EN: Assign value to stacking_contexts.
						# JP: stacking_contexts に値を代入する。
						stacking_contexts = layout.get('stackingContexts', {}).get('index', [])[layout_idx]

			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			snapshot_lookup[backend_node_id] = EnhancedSnapshotNode(
				is_clickable=is_clickable,
				cursor_style=cursor_style,
				bounds=bounding_box,
				clientRects=client_rects,
				scrollRects=scroll_rects,
				computed_styles=computed_styles if computed_styles else None,
				paint_order=paint_order,
				stacking_contexts=stacking_contexts,
			)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return snapshot_lookup

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import EnhancedDOMTreeNode, NodeType


# EN: Define class `ClickableElementDetector`.
# JP: クラス `ClickableElementDetector` を定義する。
class ClickableElementDetector:
	# EN: Define function `is_interactive`.
	# JP: 関数 `is_interactive` を定義する。
	@staticmethod
	def is_interactive(node: EnhancedDOMTreeNode) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if this node is clickable/interactive using enhanced scoring."""

		# Skip non-element nodes
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.node_type != NodeType.ELEMENT_NODE:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# # if ax ignored skip
		# if node.ax_node and node.ax_node.ignored:
		# 	return False

		# remove html and body nodes
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.tag_name in {'html', 'body'}:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# IFRAME elements should be interactive if they're large enough to potentially need scrolling
		# Small iframes (< 100px width or height) are unlikely to have scrollable content
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.tag_name and node.tag_name.upper() == 'IFRAME' or node.tag_name.upper() == 'FRAME':
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.snapshot_node and node.snapshot_node.bounds:
				# EN: Assign value to width.
				# JP: width に値を代入する。
				width = node.snapshot_node.bounds.width
				# EN: Assign value to height.
				# JP: height に値を代入する。
				height = node.snapshot_node.bounds.height
				# Only include iframes larger than 100x100px
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if width > 100 and height > 100:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True

		# RELAXED SIZE CHECK: Allow all elements including size 0 (they might be interactive overlays, etc.)
		# Note: Size 0 elements can still be interactive (e.g., invisible clickable overlays)
		# Visibility is determined separately by CSS styles, not just bounding box size

		# SEARCH ELEMENT DETECTION: Check for search-related classes and attributes
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.attributes:
			# EN: Assign value to search_indicators.
			# JP: search_indicators に値を代入する。
			search_indicators = {
				'search',
				'magnify',
				'glass',
				'lookup',
				'find',
				'query',
				'search-icon',
				'search-btn',
				'search-button',
				'searchbox',
			}

			# Check class names for search indicators
			# EN: Assign value to class_list.
			# JP: class_list に値を代入する。
			class_list = node.attributes.get('class', '').lower().split()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if any(indicator in ' '.join(class_list) for indicator in search_indicators):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

			# Check id for search indicators
			# EN: Assign value to element_id.
			# JP: element_id に値を代入する。
			element_id = node.attributes.get('id', '').lower()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if any(indicator in element_id for indicator in search_indicators):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

			# Check data attributes for search functionality
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for attr_name, attr_value in node.attributes.items():
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if attr_name.startswith('data-') and any(indicator in attr_value.lower() for indicator in search_indicators):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True

		# Enhanced accessibility property checks - direct clear indicators only
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.ax_node and node.ax_node.properties:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for prop in node.ax_node.properties:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# aria disabled
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if prop.name == 'disabled' and prop.value:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return False

					# aria hidden
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if prop.name == 'hidden' and prop.value:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return False

					# Direct interactiveness indicators
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if prop.name in ['focusable', 'editable', 'settable'] and prop.value:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return True

					# Interactive state properties (presence indicates interactive widget)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if prop.name in ['checked', 'expanded', 'pressed', 'selected']:
						# These properties only exist on interactive elements
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return True

					# Form-related interactiveness
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if prop.name in ['required', 'autocomplete'] and prop.value:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return True

					# Elements with keyboard shortcuts are interactive
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if prop.name == 'keyshortcuts' and prop.value:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return True
				except (AttributeError, ValueError):
					# Skip properties we can't process
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# ENHANCED TAG CHECK: Include truly interactive elements
		# Note: 'label' removed - labels are handled by other attribute checks below - other wise labels with "for" attribute can destroy the real clickable element on apartments.com
		# EN: Assign value to interactive_tags.
		# JP: interactive_tags に値を代入する。
		interactive_tags = {
			'button',
			'input',
			'select',
			'textarea',
			'a',
			'details',
			'summary',
			'option',
			'optgroup',
		}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.tag_name in interactive_tags:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# SVG elements need special handling - only interactive if they have explicit handlers
		# svg_tags = {'svg', 'path', 'circle', 'rect', 'polygon', 'ellipse', 'line', 'polyline', 'g'}
		# if node.tag_name in svg_tags:
		# 	# Only consider SVG elements interactive if they have:
		# 	# 1. Explicit event handlers
		# 	# 2. Interactive role attributes
		# 	# 3. Cursor pointer style
		# 	if node.attributes:
		# 		# Check for event handlers
		# 		if any(attr.startswith('on') for attr in node.attributes):
		# 			return True
		# 		# Check for interactive roles
		# 		if node.attributes.get('role') in {'button', 'link', 'menuitem'}:
		# 			return True
		# 		# Check for cursor pointer (indicating clickability)
		# 		if node.attributes.get('style') and 'cursor: pointer' in node.attributes.get('style', ''):
		# 			return True
		# 	# Otherwise, SVG elements are decorative
		# 	return False

		# Tertiary check: elements with interactive attributes
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.attributes:
			# Check for event handlers or interactive attributes
			# EN: Assign value to interactive_attributes.
			# JP: interactive_attributes に値を代入する。
			interactive_attributes = {'onclick', 'onmousedown', 'onmouseup', 'onkeydown', 'onkeyup', 'tabindex'}
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if any(attr in node.attributes for attr in interactive_attributes):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

			# Check for interactive ARIA roles
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'role' in node.attributes:
				# EN: Assign value to interactive_roles.
				# JP: interactive_roles に値を代入する。
				interactive_roles = {
					'button',
					'link',
					'menuitem',
					'option',
					'radio',
					'checkbox',
					'tab',
					'textbox',
					'combobox',
					'slider',
					'spinbutton',
					'search',
					'searchbox',
				}
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node.attributes['role'] in interactive_roles:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True

		# Quaternary check: accessibility tree roles
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.ax_node and node.ax_node.role:
			# EN: Assign value to interactive_ax_roles.
			# JP: interactive_ax_roles に値を代入する。
			interactive_ax_roles = {
				'button',
				'link',
				'menuitem',
				'option',
				'radio',
				'checkbox',
				'tab',
				'textbox',
				'combobox',
				'slider',
				'spinbutton',
				'listbox',
				'search',
				'searchbox',
			}
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.ax_node.role in interactive_ax_roles:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

		# ICON AND SMALL ELEMENT CHECK: Elements that might be icons
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if (
			node.snapshot_node
			and node.snapshot_node.bounds
			and 10 <= node.snapshot_node.bounds.width <= 50  # Icon-sized elements
			and 10 <= node.snapshot_node.bounds.height <= 50
		):
			# Check if this small element has interactive properties
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.attributes:
				# Small elements with these attributes are likely interactive icons
				# EN: Assign value to icon_attributes.
				# JP: icon_attributes に値を代入する。
				icon_attributes = {'class', 'role', 'onclick', 'data-action', 'aria-label'}
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if any(attr in node.attributes for attr in icon_attributes):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True

		# Final fallback: cursor style indicates interactivity (for cases Chrome missed)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node.snapshot_node and node.snapshot_node.cursor_style and node.snapshot_node.cursor_style == 'pointer':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

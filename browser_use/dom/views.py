# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import hashlib
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import asdict, dataclass, field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from enum import Enum
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.accessibility.commands import GetFullAXTreeReturns
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.accessibility.types import AXPropertyName
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.dom.commands import GetDocumentReturns
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.dom.types import ShadowRootType
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.domsnapshot.commands import CaptureSnapshotReturns
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.target.types import SessionID, TargetID, TargetInfo
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.utils import cap_text_length
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe_debug

# Serializer types
# EN: Assign value to DEFAULT_INCLUDE_ATTRIBUTES.
# JP: DEFAULT_INCLUDE_ATTRIBUTES に値を代入する。
DEFAULT_INCLUDE_ATTRIBUTES = [
	'title',
	'type',
	'checked',
	# 'class',
	'id',
	'name',
	'role',
	'value',
	'placeholder',
	'data-date-format',
	'alt',
	'aria-label',
	'aria-expanded',
	'data-state',
	'aria-checked',
	# Accessibility properties from ax_node (ordered by importance for automation)
	'checked',
	'selected',
	'expanded',
	'pressed',
	'disabled',
	# 'invalid',
	'valuenow',
	'keyshortcuts',
	'haspopup',
	'multiselectable',
	# Less commonly needed (uncomment if required):
	# 'readonly',
	'required',
	'valuetext',
	'level',
	'busy',
	'live',
	# Accessibility name (contains text content for StaticText elements)
	'ax_name',
]

# EN: Assign value to STATIC_ATTRIBUTES.
# JP: STATIC_ATTRIBUTES に値を代入する。
STATIC_ATTRIBUTES = {
	'class',
	'id',
	'name',
	'type',
	'placeholder',
	'aria-label',
	'title',
	# 'aria-expanded',
	'role',
	'data-testid',
	'data-test',
	'data-cy',
	'data-selenium',
	'for',
	'required',
	'disabled',
	'readonly',
	'checked',
	'selected',
	'multiple',
	'href',
	'target',
	'rel',
	'aria-describedby',
	'aria-labelledby',
	'aria-controls',
	'aria-owns',
	'aria-live',
	'aria-atomic',
	'aria-busy',
	'aria-disabled',
	'aria-hidden',
	'aria-pressed',
	'aria-checked',
	'aria-selected',
	'tabindex',
	'alt',
	'src',
	'lang',
	'itemscope',
	'itemtype',
	'itemprop',
}


# EN: Define class `CurrentPageTargets`.
# JP: クラス `CurrentPageTargets` を定義する。
@dataclass
class CurrentPageTargets:
	# EN: Assign annotated value to page_session.
	# JP: page_session に型付きの値を代入する。
	page_session: TargetInfo
	# EN: Assign annotated value to iframe_sessions.
	# JP: iframe_sessions に型付きの値を代入する。
	iframe_sessions: list[TargetInfo]
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Iframe sessions are ALL the iframes sessions of all the pages (not just the current page)
	"""


# EN: Define class `TargetAllTrees`.
# JP: クラス `TargetAllTrees` を定義する。
@dataclass
class TargetAllTrees:
	# EN: Assign annotated value to snapshot.
	# JP: snapshot に型付きの値を代入する。
	snapshot: CaptureSnapshotReturns
	# EN: Assign annotated value to dom_tree.
	# JP: dom_tree に型付きの値を代入する。
	dom_tree: GetDocumentReturns
	# EN: Assign annotated value to ax_tree.
	# JP: ax_tree に型付きの値を代入する。
	ax_tree: GetFullAXTreeReturns
	# EN: Assign annotated value to device_pixel_ratio.
	# JP: device_pixel_ratio に型付きの値を代入する。
	device_pixel_ratio: float
	# EN: Assign annotated value to cdp_timing.
	# JP: cdp_timing に型付きの値を代入する。
	cdp_timing: dict[str, float]


# EN: Define class `PropagatingBounds`.
# JP: クラス `PropagatingBounds` を定義する。
@dataclass(slots=True)
class PropagatingBounds:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Track bounds that propagate from parent elements to filter children."""

	# EN: Assign annotated value to tag.
	# JP: tag に型付きの値を代入する。
	tag: str  # The tag that started propagation ('a' or 'button')
	# EN: Assign annotated value to bounds.
	# JP: bounds に型付きの値を代入する。
	bounds: 'DOMRect'  # The bounding box
	# EN: Assign annotated value to node_id.
	# JP: node_id に型付きの値を代入する。
	node_id: int  # Node ID for debugging
	# EN: Assign annotated value to depth.
	# JP: depth に型付きの値を代入する。
	depth: int  # How deep in tree this started (for debugging)


# EN: Define class `SimplifiedNode`.
# JP: クラス `SimplifiedNode` を定義する。
@dataclass(slots=True)
class SimplifiedNode:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Simplified tree node for optimization."""

	# EN: Assign annotated value to original_node.
	# JP: original_node に型付きの値を代入する。
	original_node: 'EnhancedDOMTreeNode'
	# EN: Assign annotated value to children.
	# JP: children に型付きの値を代入する。
	children: list['SimplifiedNode']
	# EN: Assign annotated value to should_display.
	# JP: should_display に型付きの値を代入する。
	should_display: bool = True
	# EN: Assign annotated value to interactive_index.
	# JP: interactive_index に型付きの値を代入する。
	interactive_index: int | None = None

	# EN: Assign annotated value to is_new.
	# JP: is_new に型付きの値を代入する。
	is_new: bool = False

	# EN: Assign annotated value to ignored_by_paint_order.
	# JP: ignored_by_paint_order に型付きの値を代入する。
	ignored_by_paint_order: bool = False  # More info in dom/serializer/paint_order.py
	# EN: Assign annotated value to excluded_by_parent.
	# JP: excluded_by_parent に型付きの値を代入する。
	excluded_by_parent: bool = False  # New field for bbox filtering
	# EN: Assign annotated value to is_shadow_host.
	# JP: is_shadow_host に型付きの値を代入する。
	is_shadow_host: bool = False  # New field for shadow DOM hosts

	# EN: Define function `_clean_original_node_json`.
	# JP: 関数 `_clean_original_node_json` を定義する。
	def _clean_original_node_json(self, node_json: dict) -> dict:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Recursively remove children_nodes and shadow_roots from original_node JSON."""
		# Remove the fields we don't want in SimplifiedNode serialization
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'children_nodes' in node_json:
			# EN: Delete referenced values.
			# JP: 参照される値を削除する。
			del node_json['children_nodes']
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'shadow_roots' in node_json:
			# EN: Delete referenced values.
			# JP: 参照される値を削除する。
			del node_json['shadow_roots']

		# Clean nested content_document if it exists
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if node_json.get('content_document'):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			node_json['content_document'] = self._clean_original_node_json(node_json['content_document'])

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return node_json

	# EN: Define function `__json__`.
	# JP: 関数 `__json__` を定義する。
	def __json__(self) -> dict:
		# EN: Assign value to original_node_json.
		# JP: original_node_json に値を代入する。
		original_node_json = self.original_node.__json__()
		# Remove children_nodes and shadow_roots to avoid duplication with SimplifiedNode.children
		# EN: Assign value to cleaned_original_node_json.
		# JP: cleaned_original_node_json に値を代入する。
		cleaned_original_node_json = self._clean_original_node_json(original_node_json)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'should_display': self.should_display,
			'interactive_index': self.interactive_index,
			'ignored_by_paint_order': self.ignored_by_paint_order,
			'excluded_by_parent': self.excluded_by_parent,
			'original_node': cleaned_original_node_json,
			'children': [c.__json__() for c in self.children],
		}


# EN: Define class `NodeType`.
# JP: クラス `NodeType` を定義する。
class NodeType(int, Enum):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""DOM node types based on the DOM specification."""

	# EN: Assign value to ELEMENT_NODE.
	# JP: ELEMENT_NODE に値を代入する。
	ELEMENT_NODE = 1
	# EN: Assign value to ATTRIBUTE_NODE.
	# JP: ATTRIBUTE_NODE に値を代入する。
	ATTRIBUTE_NODE = 2
	# EN: Assign value to TEXT_NODE.
	# JP: TEXT_NODE に値を代入する。
	TEXT_NODE = 3
	# EN: Assign value to CDATA_SECTION_NODE.
	# JP: CDATA_SECTION_NODE に値を代入する。
	CDATA_SECTION_NODE = 4
	# EN: Assign value to ENTITY_REFERENCE_NODE.
	# JP: ENTITY_REFERENCE_NODE に値を代入する。
	ENTITY_REFERENCE_NODE = 5
	# EN: Assign value to ENTITY_NODE.
	# JP: ENTITY_NODE に値を代入する。
	ENTITY_NODE = 6
	# EN: Assign value to PROCESSING_INSTRUCTION_NODE.
	# JP: PROCESSING_INSTRUCTION_NODE に値を代入する。
	PROCESSING_INSTRUCTION_NODE = 7
	# EN: Assign value to COMMENT_NODE.
	# JP: COMMENT_NODE に値を代入する。
	COMMENT_NODE = 8
	# EN: Assign value to DOCUMENT_NODE.
	# JP: DOCUMENT_NODE に値を代入する。
	DOCUMENT_NODE = 9
	# EN: Assign value to DOCUMENT_TYPE_NODE.
	# JP: DOCUMENT_TYPE_NODE に値を代入する。
	DOCUMENT_TYPE_NODE = 10
	# EN: Assign value to DOCUMENT_FRAGMENT_NODE.
	# JP: DOCUMENT_FRAGMENT_NODE に値を代入する。
	DOCUMENT_FRAGMENT_NODE = 11
	# EN: Assign value to NOTATION_NODE.
	# JP: NOTATION_NODE に値を代入する。
	NOTATION_NODE = 12


# EN: Define class `DOMRect`.
# JP: クラス `DOMRect` を定義する。
@dataclass(slots=True)
class DOMRect:
	# EN: Assign annotated value to x.
	# JP: x に型付きの値を代入する。
	x: float
	# EN: Assign annotated value to y.
	# JP: y に型付きの値を代入する。
	y: float
	# EN: Assign annotated value to width.
	# JP: width に型付きの値を代入する。
	width: float
	# EN: Assign annotated value to height.
	# JP: height に型付きの値を代入する。
	height: float

	# EN: Define function `to_dict`.
	# JP: 関数 `to_dict` を定義する。
	def to_dict(self) -> dict[str, Any]:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'x': self.x,
			'y': self.y,
			'width': self.width,
			'height': self.height,
		}

	# EN: Define function `__json__`.
	# JP: 関数 `__json__` を定義する。
	def __json__(self) -> dict:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.to_dict()


# EN: Define class `EnhancedAXProperty`.
# JP: クラス `EnhancedAXProperty` を定義する。
@dataclass(slots=True)
class EnhancedAXProperty:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""we don't need `sources` and `related_nodes` for now (not sure how to use them)

	TODO: there is probably some way to determine whether it has a value or related nodes or not, but for now it's kinda fine idk
	"""

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: AXPropertyName
	# EN: Assign annotated value to value.
	# JP: value に型付きの値を代入する。
	value: str | bool | None
	# related_nodes: list[EnhancedAXRelatedNode] | None


# EN: Define class `EnhancedAXNode`.
# JP: クラス `EnhancedAXNode` を定義する。
@dataclass(slots=True)
class EnhancedAXNode:
	# EN: Assign annotated value to ax_node_id.
	# JP: ax_node_id に型付きの値を代入する。
	ax_node_id: str
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Not to be confused the DOM node_id. Only useful for AX node tree"""
	# EN: Assign annotated value to ignored.
	# JP: ignored に型付きの値を代入する。
	ignored: bool
	# we don't need ignored_reasons as we anyway ignore the node otherwise
	# EN: Assign annotated value to role.
	# JP: role に型付きの値を代入する。
	role: str | None
	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str | None
	# EN: Assign annotated value to description.
	# JP: description に型付きの値を代入する。
	description: str | None

	# EN: Assign annotated value to properties.
	# JP: properties に型付きの値を代入する。
	properties: list[EnhancedAXProperty] | None


# EN: Define class `EnhancedSnapshotNode`.
# JP: クラス `EnhancedSnapshotNode` を定義する。
@dataclass(slots=True)
class EnhancedSnapshotNode:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Snapshot data extracted from DOMSnapshot for enhanced functionality."""

	# EN: Assign annotated value to is_clickable.
	# JP: is_clickable に型付きの値を代入する。
	is_clickable: bool | None
	# EN: Assign annotated value to cursor_style.
	# JP: cursor_style に型付きの値を代入する。
	cursor_style: str | None
	# EN: Assign annotated value to bounds.
	# JP: bounds に型付きの値を代入する。
	bounds: DOMRect | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Document coordinates (origin = top-left of the page, ignores current scroll).
	Equivalent JS API: layoutNode.boundingBox in the older API.
	Typical use: Quick hit-test that doesn't care about scroll position.
	"""

	# EN: Assign annotated value to clientRects.
	# JP: clientRects に型付きの値を代入する。
	clientRects: DOMRect | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Viewport coordinates (origin = top-left of the visible scrollport).
	Equivalent JS API: element.getClientRects() / getBoundingClientRect().
	Typical use: Pixel-perfect hit-testing on screen, taking current scroll into account.
	"""

	# EN: Assign annotated value to scrollRects.
	# JP: scrollRects に型付きの値を代入する。
	scrollRects: DOMRect | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Scrollable area of the element.
	"""

	# EN: Assign annotated value to computed_styles.
	# JP: computed_styles に型付きの値を代入する。
	computed_styles: dict[str, str] | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Computed styles from the layout tree"""
	# EN: Assign annotated value to paint_order.
	# JP: paint_order に型付きの値を代入する。
	paint_order: int | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Paint order from the layout tree"""
	# EN: Assign annotated value to stacking_contexts.
	# JP: stacking_contexts に型付きの値を代入する。
	stacking_contexts: int | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Stacking contexts from the layout tree"""


# @dataclass(slots=True)
# class SuperSelector:
# 	node_id: int
# 	backend_node_id: int
# 	frame_id: str | None
# 	target_id: TargetID

# 	node_type: NodeType
# 	node_name: str

# 	# is_visible: bool | None
# 	# is_scrollable: bool | None

# 	element_index: int | None


# EN: Define class `EnhancedDOMTreeNode`.
# JP: クラス `EnhancedDOMTreeNode` を定義する。
@dataclass(slots=True)
class EnhancedDOMTreeNode:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Enhanced DOM tree node that contains information from AX, DOM, and Snapshot trees. It's mostly based on the types on DOM node type with enhanced data from AX and Snapshot trees.

	@dev when serializing check if the value is a valid value first!

	Learn more about the fields:
	- (DOM node) https://chromedevtools.github.io/devtools-protocol/tot/DOM/#type-BackendNode
	- (AX node) https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/#type-AXNode
	- (Snapshot node) https://chromedevtools.github.io/devtools-protocol/tot/DOMSnapshot/#type-DOMNode
	"""

	# region - DOM Node data

	# EN: Assign annotated value to node_id.
	# JP: node_id に型付きの値を代入する。
	node_id: int
	# EN: Assign annotated value to backend_node_id.
	# JP: backend_node_id に型付きの値を代入する。
	backend_node_id: int

	# EN: Assign annotated value to node_type.
	# JP: node_type に型付きの値を代入する。
	node_type: NodeType
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Node types, defined in `NodeType` enum."""
	# EN: Assign annotated value to node_name.
	# JP: node_name に型付きの値を代入する。
	node_name: str
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Only applicable for `NodeType.ELEMENT_NODE`"""
	# EN: Assign annotated value to node_value.
	# JP: node_value に型付きの値を代入する。
	node_value: str
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""this is where the value from `NodeType.TEXT_NODE` is stored usually"""
	# EN: Assign annotated value to attributes.
	# JP: attributes に型付きの値を代入する。
	attributes: dict[str, str]
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""slightly changed from the original attributes to be more readable"""
	# EN: Assign annotated value to is_scrollable.
	# JP: is_scrollable に型付きの値を代入する。
	is_scrollable: bool | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Whether the node is scrollable.
	"""
	# EN: Assign annotated value to is_visible.
	# JP: is_visible に型付きの値を代入する。
	is_visible: bool | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Whether the node is visible according to the upper most frame node.
	"""

	# EN: Assign annotated value to absolute_position.
	# JP: absolute_position に型付きの値を代入する。
	absolute_position: DOMRect | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Absolute position of the node in the document according to the top-left of the page.
	"""

	# frames
	# EN: Assign annotated value to target_id.
	# JP: target_id に型付きの値を代入する。
	target_id: TargetID
	# EN: Assign annotated value to frame_id.
	# JP: frame_id に型付きの値を代入する。
	frame_id: str | None
	# EN: Assign annotated value to session_id.
	# JP: session_id に型付きの値を代入する。
	session_id: SessionID | None
	# EN: Assign annotated value to content_document.
	# JP: content_document に型付きの値を代入する。
	content_document: 'EnhancedDOMTreeNode | None'
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Content document is the document inside a new iframe.
	"""
	# Shadow DOM
	# EN: Assign annotated value to shadow_root_type.
	# JP: shadow_root_type に型付きの値を代入する。
	shadow_root_type: ShadowRootType | None
	# EN: Assign annotated value to shadow_roots.
	# JP: shadow_roots に型付きの値を代入する。
	shadow_roots: list['EnhancedDOMTreeNode'] | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Shadow roots are the shadow DOMs of the element.
	"""

	# Navigation
	# EN: Assign annotated value to parent_node.
	# JP: parent_node に型付きの値を代入する。
	parent_node: 'EnhancedDOMTreeNode | None'
	# EN: Assign annotated value to children_nodes.
	# JP: children_nodes に型付きの値を代入する。
	children_nodes: list['EnhancedDOMTreeNode'] | None

	# endregion - DOM Node data

	# region - AX Node data
	# EN: Assign annotated value to ax_node.
	# JP: ax_node に型付きの値を代入する。
	ax_node: EnhancedAXNode | None

	# endregion - AX Node data

	# region - Snapshot Node data
	# EN: Assign annotated value to snapshot_node.
	# JP: snapshot_node に型付きの値を代入する。
	snapshot_node: EnhancedSnapshotNode | None

	# endregion - Snapshot Node data

	# Interactive element index
	# EN: Assign annotated value to element_index.
	# JP: element_index に型付きの値を代入する。
	element_index: int | None = None

	# EN: Assign annotated value to uuid.
	# JP: uuid に型付きの値を代入する。
	uuid: str = field(default_factory=uuid7str)

	# EN: Define function `parent`.
	# JP: 関数 `parent` を定義する。
	@property
	def parent(self) -> 'EnhancedDOMTreeNode | None':
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.parent_node

	# EN: Define function `children`.
	# JP: 関数 `children` を定義する。
	@property
	def children(self) -> list['EnhancedDOMTreeNode']:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.children_nodes or []

	# EN: Define function `children_and_shadow_roots`.
	# JP: 関数 `children_and_shadow_roots` を定義する。
	@property
	def children_and_shadow_roots(self) -> list['EnhancedDOMTreeNode']:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Returns all children nodes, including shadow roots
		"""
		# EN: Assign value to children.
		# JP: children に値を代入する。
		children = self.children_nodes or []
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.shadow_roots:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			children.extend(self.shadow_roots)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return children

	# EN: Define function `tag_name`.
	# JP: 関数 `tag_name` を定義する。
	@property
	def tag_name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.node_name.lower()

	# EN: Define function `xpath`.
	# JP: 関数 `xpath` を定義する。
	@property
	def xpath(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Generate XPath for this DOM node, stopping at shadow boundaries or iframes."""
		# EN: Assign value to segments.
		# JP: segments に値を代入する。
		segments = []
		# EN: Assign value to current_element.
		# JP: current_element に値を代入する。
		current_element = self

		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while current_element and (
			current_element.node_type == NodeType.ELEMENT_NODE or current_element.node_type == NodeType.DOCUMENT_FRAGMENT_NODE
		):
			# just pass through shadow roots
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_element.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
				# EN: Assign value to current_element.
				# JP: current_element に値を代入する。
				current_element = current_element.parent_node
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# stop ONLY if we hit iframe
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_element.parent_node and current_element.parent_node.node_name.lower() == 'iframe':
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break

			# EN: Assign value to position.
			# JP: position に値を代入する。
			position = self._get_element_position(current_element)
			# EN: Assign value to tag_name.
			# JP: tag_name に値を代入する。
			tag_name = current_element.node_name.lower()
			# EN: Assign value to xpath_index.
			# JP: xpath_index に値を代入する。
			xpath_index = f'[{position}]' if position > 0 else ''
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			segments.insert(0, f'{tag_name}{xpath_index}')

			# EN: Assign value to current_element.
			# JP: current_element に値を代入する。
			current_element = current_element.parent_node

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '/'.join(segments)

	# EN: Define function `_get_element_position`.
	# JP: 関数 `_get_element_position` を定義する。
	def _get_element_position(self, element: 'EnhancedDOMTreeNode') -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the position of an element among its siblings with the same tag name.
		Returns 0 if it's the only element of its type, otherwise returns 1-based index."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not element.parent_node or not element.parent_node.children_nodes:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 0

		# EN: Assign value to same_tag_siblings.
		# JP: same_tag_siblings に値を代入する。
		same_tag_siblings = [
			child
			for child in element.parent_node.children_nodes
			if child.node_type == NodeType.ELEMENT_NODE and child.node_name.lower() == element.node_name.lower()
		]

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(same_tag_siblings) <= 1:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 0  # No index needed if it's the only one

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# XPath is 1-indexed
			# EN: Assign value to position.
			# JP: position に値を代入する。
			position = same_tag_siblings.index(element) + 1
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return position
		except ValueError:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 0

	# EN: Define function `__json__`.
	# JP: 関数 `__json__` を定義する。
	def __json__(self) -> dict:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Serializes the node and its descendants to a dictionary, omitting parent references."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'node_id': self.node_id,
			'backend_node_id': self.backend_node_id,
			'node_type': self.node_type.name,
			'node_name': self.node_name,
			'node_value': self.node_value,
			'is_visible': self.is_visible,
			'attributes': self.attributes,
			'is_scrollable': self.is_scrollable,
			'session_id': self.session_id,
			'target_id': self.target_id,
			'frame_id': self.frame_id,
			'content_document': self.content_document.__json__() if self.content_document else None,
			'shadow_root_type': self.shadow_root_type,
			'ax_node': asdict(self.ax_node) if self.ax_node else None,
			'snapshot_node': asdict(self.snapshot_node) if self.snapshot_node else None,
			# these two in the end, so it's easier to read json
			'shadow_roots': [r.__json__() for r in self.shadow_roots] if self.shadow_roots else [],
			'children_nodes': [c.__json__() for c in self.children_nodes] if self.children_nodes else [],
		}

	# EN: Define function `get_all_children_text`.
	# JP: 関数 `get_all_children_text` を定義する。
	def get_all_children_text(self, max_depth: int = -1) -> str:
		# EN: Assign value to text_parts.
		# JP: text_parts に値を代入する。
		text_parts = []

		# EN: Define function `collect_text`.
		# JP: 関数 `collect_text` を定義する。
		def collect_text(node: EnhancedDOMTreeNode, current_depth: int) -> None:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if max_depth != -1 and current_depth > max_depth:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Skip this branch if we hit a highlighted element (except for the current node)
			# TODO: think whether if makese sense to add text until the next clickable element or everything from children
			# if node.node_type == NodeType.ELEMENT_NODE
			# if isinstance(node, DOMElementNode) and node != self and node.highlight_index is not None:
			# 	return

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.node_type == NodeType.TEXT_NODE:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				text_parts.append(node.node_value)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif node.node_type == NodeType.ELEMENT_NODE:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for child in node.children:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					collect_text(child, current_depth + 1)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		collect_text(self, 0)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(text_parts).strip()

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		@DEV ! don't display this to the LLM, it's SUPER long
		"""
		# EN: Assign value to attributes.
		# JP: attributes に値を代入する。
		attributes = ', '.join([f'{k}={v}' for k, v in self.attributes.items()])
		# EN: Assign value to is_scrollable.
		# JP: is_scrollable に値を代入する。
		is_scrollable = getattr(self, 'is_scrollable', False)
		# EN: Assign value to num_children.
		# JP: num_children に値を代入する。
		num_children = len(self.children_nodes or [])
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (
			f'<{self.tag_name} {attributes} is_scrollable={is_scrollable} '
			f'num_children={num_children} >{self.node_value}</{self.tag_name}>'
		)

	# EN: Define function `llm_representation`.
	# JP: 関数 `llm_representation` を定義する。
	def llm_representation(self, max_text_length: int = 100) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Token friendly representation of the node, used in the LLM
		"""

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'<{self.tag_name}>{cap_text_length(self.get_all_children_text(), max_text_length) or ""}'

	# EN: Define function `get_meaningful_text_for_llm`.
	# JP: 関数 `get_meaningful_text_for_llm` を定義する。
	def get_meaningful_text_for_llm(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Get the meaningful text content that the LLM actually sees for this element.
		This matches exactly what goes into the DOMTreeSerializer output.
		"""
		# EN: Assign value to meaningful_text.
		# JP: meaningful_text に値を代入する。
		meaningful_text = ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, 'attributes') and self.attributes:
			# Priority order: value, aria-label, title, placeholder, alt, text content
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for attr in ['value', 'aria-label', 'title', 'placeholder', 'alt']:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if attr in self.attributes and self.attributes[attr]:
					# EN: Assign value to meaningful_text.
					# JP: meaningful_text に値を代入する。
					meaningful_text = self.attributes[attr]
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break

		# Fallback to text content if no meaningful attributes
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not meaningful_text:
			# EN: Assign value to meaningful_text.
			# JP: meaningful_text に値を代入する。
			meaningful_text = self.get_all_children_text()

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return meaningful_text.strip()

	# EN: Define function `is_actually_scrollable`.
	# JP: 関数 `is_actually_scrollable` を定義する。
	@property
	def is_actually_scrollable(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Enhanced scroll detection that combines CDP detection with CSS analysis.

		This detects scrollable elements that Chrome's CDP might miss, which is common
		in iframes and dynamically sized containers.
		"""
		# First check if CDP already detected it as scrollable
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.is_scrollable:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Enhanced detection for elements CDP missed
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.snapshot_node:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Check scroll vs client rects - this is the most reliable indicator
		# EN: Assign value to scroll_rects.
		# JP: scroll_rects に値を代入する。
		scroll_rects = self.snapshot_node.scrollRects
		# EN: Assign value to client_rects.
		# JP: client_rects に値を代入する。
		client_rects = self.snapshot_node.clientRects

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if scroll_rects and client_rects:
			# Content is larger than visible area = scrollable
			# EN: Assign value to has_vertical_scroll.
			# JP: has_vertical_scroll に値を代入する。
			has_vertical_scroll = scroll_rects.height > client_rects.height + 1  # +1 for rounding
			# EN: Assign value to has_horizontal_scroll.
			# JP: has_horizontal_scroll に値を代入する。
			has_horizontal_scroll = scroll_rects.width > client_rects.width + 1

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if has_vertical_scroll or has_horizontal_scroll:
				# Also check CSS to make sure scrolling is allowed
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.snapshot_node.computed_styles:
					# EN: Assign value to styles.
					# JP: styles に値を代入する。
					styles = self.snapshot_node.computed_styles

					# EN: Assign value to overflow.
					# JP: overflow に値を代入する。
					overflow = styles.get('overflow', 'visible').lower()
					# EN: Assign value to overflow_x.
					# JP: overflow_x に値を代入する。
					overflow_x = styles.get('overflow-x', overflow).lower()
					# EN: Assign value to overflow_y.
					# JP: overflow_y に値を代入する。
					overflow_y = styles.get('overflow-y', overflow).lower()

					# Only allow scrolling if overflow is explicitly set to auto, scroll, or overlay
					# Do NOT consider 'visible' overflow as scrollable - this was causing the issue
					# EN: Assign value to allows_scroll.
					# JP: allows_scroll に値を代入する。
					allows_scroll = (
						overflow in ['auto', 'scroll', 'overlay']
						or overflow_x in ['auto', 'scroll', 'overlay']
						or overflow_y in ['auto', 'scroll', 'overlay']
					)

					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return allows_scroll
				else:
					# No CSS info, but content overflows - be more conservative
					# Only consider it scrollable if it's a common scrollable container element
					# EN: Assign value to scrollable_tags.
					# JP: scrollable_tags に値を代入する。
					scrollable_tags = {'div', 'main', 'section', 'article', 'aside', 'body', 'html'}
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return self.tag_name.lower() in scrollable_tags

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `should_show_scroll_info`.
	# JP: 関数 `should_show_scroll_info` を定義する。
	@property
	def should_show_scroll_info(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Simple check: show scroll info only if this element is scrollable
		and doesn't have a scrollable parent (to avoid nested scroll spam).

		Special case for iframes: Always show scroll info since Chrome might not
		always detect iframe scrollability correctly (scrollHeight: 0 issue).
		"""
		# Special case: Always show scroll info for iframe elements
		# Even if not detected as scrollable, they might have scrollable content
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.tag_name.lower() == 'iframe':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Must be scrollable first for non-iframe elements
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not (self.is_scrollable or self.is_actually_scrollable):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Always show for iframe content documents (body/html)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.tag_name.lower() in {'body', 'html'}:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Don't show if parent is already scrollable (avoid nested spam)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.parent_node and (self.parent_node.is_scrollable or self.parent_node.is_actually_scrollable):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Define function `_find_html_in_content_document`.
	# JP: 関数 `_find_html_in_content_document` を定義する。
	def _find_html_in_content_document(self) -> 'EnhancedDOMTreeNode | None':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Find HTML element in iframe content document."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.content_document:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Check if content document itself is HTML
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.content_document.tag_name.lower() == 'html':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.content_document

		# Look through children for HTML element
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.content_document.children_nodes:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for child in self.content_document.children_nodes:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if child.tag_name.lower() == 'html':
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return child

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `scroll_info`.
	# JP: 関数 `scroll_info` を定義する。
	@property
	def scroll_info(self) -> dict[str, Any] | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Calculate scroll information for this element if it's scrollable."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.is_actually_scrollable or not self.snapshot_node:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Get scroll and client rects from snapshot data
		# EN: Assign value to scroll_rects.
		# JP: scroll_rects に値を代入する。
		scroll_rects = self.snapshot_node.scrollRects
		# EN: Assign value to client_rects.
		# JP: client_rects に値を代入する。
		client_rects = self.snapshot_node.clientRects
		# EN: Assign value to bounds.
		# JP: bounds に値を代入する。
		bounds = self.snapshot_node.bounds

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not scroll_rects or not client_rects:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Calculate scroll position and percentages
		# EN: Assign value to scroll_top.
		# JP: scroll_top に値を代入する。
		scroll_top = scroll_rects.y
		# EN: Assign value to scroll_left.
		# JP: scroll_left に値を代入する。
		scroll_left = scroll_rects.x

		# Total scrollable height and width
		# EN: Assign value to scrollable_height.
		# JP: scrollable_height に値を代入する。
		scrollable_height = scroll_rects.height
		# EN: Assign value to scrollable_width.
		# JP: scrollable_width に値を代入する。
		scrollable_width = scroll_rects.width

		# Visible (client) dimensions
		# EN: Assign value to visible_height.
		# JP: visible_height に値を代入する。
		visible_height = client_rects.height
		# EN: Assign value to visible_width.
		# JP: visible_width に値を代入する。
		visible_width = client_rects.width

		# Calculate how much content is above/below/left/right of current view
		# EN: Assign value to content_above.
		# JP: content_above に値を代入する。
		content_above = max(0, scroll_top)
		# EN: Assign value to content_below.
		# JP: content_below に値を代入する。
		content_below = max(0, scrollable_height - visible_height - scroll_top)
		# EN: Assign value to content_left.
		# JP: content_left に値を代入する。
		content_left = max(0, scroll_left)
		# EN: Assign value to content_right.
		# JP: content_right に値を代入する。
		content_right = max(0, scrollable_width - visible_width - scroll_left)

		# Calculate scroll percentages
		# EN: Assign value to vertical_scroll_percentage.
		# JP: vertical_scroll_percentage に値を代入する。
		vertical_scroll_percentage = 0
		# EN: Assign value to horizontal_scroll_percentage.
		# JP: horizontal_scroll_percentage に値を代入する。
		horizontal_scroll_percentage = 0

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if scrollable_height > visible_height:
			# EN: Assign value to max_scroll_top.
			# JP: max_scroll_top に値を代入する。
			max_scroll_top = scrollable_height - visible_height
			# EN: Assign value to vertical_scroll_percentage.
			# JP: vertical_scroll_percentage に値を代入する。
			vertical_scroll_percentage = (scroll_top / max_scroll_top) * 100 if max_scroll_top > 0 else 0

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if scrollable_width > visible_width:
			# EN: Assign value to max_scroll_left.
			# JP: max_scroll_left に値を代入する。
			max_scroll_left = scrollable_width - visible_width
			# EN: Assign value to horizontal_scroll_percentage.
			# JP: horizontal_scroll_percentage に値を代入する。
			horizontal_scroll_percentage = (scroll_left / max_scroll_left) * 100 if max_scroll_left > 0 else 0

		# Calculate pages equivalent (using visible height as page unit)
		# EN: Assign value to pages_above.
		# JP: pages_above に値を代入する。
		pages_above = content_above / visible_height if visible_height > 0 else 0
		# EN: Assign value to pages_below.
		# JP: pages_below に値を代入する。
		pages_below = content_below / visible_height if visible_height > 0 else 0
		# EN: Assign value to total_pages.
		# JP: total_pages に値を代入する。
		total_pages = scrollable_height / visible_height if visible_height > 0 else 1

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'scroll_top': scroll_top,
			'scroll_left': scroll_left,
			'scrollable_height': scrollable_height,
			'scrollable_width': scrollable_width,
			'visible_height': visible_height,
			'visible_width': visible_width,
			'content_above': content_above,
			'content_below': content_below,
			'content_left': content_left,
			'content_right': content_right,
			'vertical_scroll_percentage': round(vertical_scroll_percentage, 1),
			'horizontal_scroll_percentage': round(horizontal_scroll_percentage, 1),
			'pages_above': round(pages_above, 1),
			'pages_below': round(pages_below, 1),
			'total_pages': round(total_pages, 1),
			'can_scroll_up': content_above > 0,
			'can_scroll_down': content_below > 0,
			'can_scroll_left': content_left > 0,
			'can_scroll_right': content_right > 0,
		}

	# EN: Define function `get_scroll_info_text`.
	# JP: 関数 `get_scroll_info_text` を定義する。
	def get_scroll_info_text(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get human-readable scroll information text for this element."""
		# Special case for iframes: check content document for scroll info
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.tag_name.lower() == 'iframe':
			# Try to get scroll info from the HTML document inside the iframe
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.content_document:
				# Look for HTML element in content document
				# EN: Assign value to html_element.
				# JP: html_element に値を代入する。
				html_element = self._find_html_in_content_document()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if html_element and html_element.scroll_info:
					# EN: Assign value to info.
					# JP: info に値を代入する。
					info = html_element.scroll_info
					# Provide minimal but useful scroll info
					# EN: Assign value to pages_below.
					# JP: pages_below に値を代入する。
					pages_below = info.get('pages_below', 0)
					# EN: Assign value to pages_above.
					# JP: pages_above に値を代入する。
					pages_above = info.get('pages_above', 0)
					# EN: Assign value to v_pct.
					# JP: v_pct に値を代入する。
					v_pct = int(info.get('vertical_scroll_percentage', 0))

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if pages_below > 0 or pages_above > 0:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return f'scroll: {pages_above:.1f}↑ {pages_below:.1f}↓ {v_pct}%'

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'scroll'

		# EN: Assign value to scroll_info.
		# JP: scroll_info に値を代入する。
		scroll_info = self.scroll_info
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not scroll_info:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ''

		# EN: Assign value to parts.
		# JP: parts に値を代入する。
		parts = []

		# Vertical scroll info (concise format)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if scroll_info['scrollable_height'] > scroll_info['visible_height']:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(f'{scroll_info["pages_above"]:.1f} pages above, {scroll_info["pages_below"]:.1f} pages below')

		# Horizontal scroll info (concise format)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if scroll_info['scrollable_width'] > scroll_info['visible_width']:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(f'horizontal {scroll_info["horizontal_scroll_percentage"]:.0f}%')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ' '.join(parts)

	# EN: Define function `element_hash`.
	# JP: 関数 `element_hash` を定義する。
	@property
	def element_hash(self) -> int:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return hash(self)

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'[<{self.tag_name}>#{self.frame_id[-4:] if self.frame_id else "?"}:{self.element_index}]'

	# EN: Define function `__hash__`.
	# JP: 関数 `__hash__` を定義する。
	def __hash__(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Hash the element based on its parent branch path and attributes.

		TODO: migrate this to use only backendNodeId + current SessionId
		"""

		# Get parent branch path
		# EN: Assign value to parent_branch_path.
		# JP: parent_branch_path に値を代入する。
		parent_branch_path = self._get_parent_branch_path()
		# EN: Assign value to parent_branch_path_string.
		# JP: parent_branch_path_string に値を代入する。
		parent_branch_path_string = '/'.join(parent_branch_path)

		# EN: Assign value to attributes_string.
		# JP: attributes_string に値を代入する。
		attributes_string = ''.join(
			f'{k}={v}' for k, v in sorted((k, v) for k, v in self.attributes.items() if k in STATIC_ATTRIBUTES)
		)

		# Combine both for final hash
		# EN: Assign value to combined_string.
		# JP: combined_string に値を代入する。
		combined_string = f'{parent_branch_path_string}|{attributes_string}'
		# EN: Assign value to element_hash.
		# JP: element_hash に値を代入する。
		element_hash = hashlib.sha256(combined_string.encode()).hexdigest()

		# Convert to int for __hash__ return type - use first 16 chars and convert from hex to int
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return int(element_hash[:16], 16)

	# EN: Define function `parent_branch_hash`.
	# JP: 関数 `parent_branch_hash` を定義する。
	def parent_branch_hash(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Hash the element based on its parent branch path and attributes.
		"""
		# EN: Assign value to parent_branch_path.
		# JP: parent_branch_path に値を代入する。
		parent_branch_path = self._get_parent_branch_path()
		# EN: Assign value to parent_branch_path_string.
		# JP: parent_branch_path_string に値を代入する。
		parent_branch_path_string = '/'.join(parent_branch_path)
		# EN: Assign value to element_hash.
		# JP: element_hash に値を代入する。
		element_hash = hashlib.sha256(parent_branch_path_string.encode()).hexdigest()

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return int(element_hash[:16], 16)

	# EN: Define function `_get_parent_branch_path`.
	# JP: 関数 `_get_parent_branch_path` を定義する。
	def _get_parent_branch_path(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the parent branch path as a list of tag names from root to current element."""
		# EN: Assign annotated value to parents.
		# JP: parents に型付きの値を代入する。
		parents: list['EnhancedDOMTreeNode'] = []
		# EN: Assign annotated value to current_element.
		# JP: current_element に型付きの値を代入する。
		current_element: 'EnhancedDOMTreeNode | None' = self

		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while current_element is not None:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_element.node_type == NodeType.ELEMENT_NODE:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				parents.append(current_element)
			# EN: Assign value to current_element.
			# JP: current_element に値を代入する。
			current_element = current_element.parent_node

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		parents.reverse()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [parent.tag_name for parent in parents]


# EN: Assign value to DOMSelectorMap.
# JP: DOMSelectorMap に値を代入する。
DOMSelectorMap = dict[int, EnhancedDOMTreeNode]


# EN: Define class `SerializedDOMState`.
# JP: クラス `SerializedDOMState` を定義する。
@dataclass
class SerializedDOMState:
	# EN: Assign annotated value to _root.
	# JP: _root に型付きの値を代入する。
	_root: SimplifiedNode | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Not meant to be used directly, use `llm_representation` instead"""

	# EN: Assign annotated value to selector_map.
	# JP: selector_map に型付きの値を代入する。
	selector_map: DOMSelectorMap

	# EN: Define function `llm_representation`.
	# JP: 関数 `llm_representation` を定義する。
	@observe_debug(ignore_input=True, ignore_output=True, name='llm_representation')
	def llm_representation(
		self,
		include_attributes: list[str] | None = None,
	) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Kinda ugly, but leaving this as an internal method because include_attributes are a parameter on the agent, so we need to leave it as a 2 step process"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.dom.serializer.serializer import DOMTreeSerializer

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._root:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Empty DOM tree (you might have to wait for the page to load)'

		# EN: Assign value to include_attributes.
		# JP: include_attributes に値を代入する。
		include_attributes = include_attributes or DEFAULT_INCLUDE_ATTRIBUTES

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return DOMTreeSerializer.serialize_tree(self._root, include_attributes)


# EN: Define class `DOMInteractedElement`.
# JP: クラス `DOMInteractedElement` を定義する。
@dataclass
class DOMInteractedElement:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	DOMInteractedElement is a class that represents a DOM element that has been interacted with.
	It is used to store the DOM element that has been interacted with and to store the DOM element that has been interacted with.

	TODO: this is a bit of a hack, we should probably have a better way to do this
	"""

	# EN: Assign annotated value to node_id.
	# JP: node_id に型付きの値を代入する。
	node_id: int
	# EN: Assign annotated value to backend_node_id.
	# JP: backend_node_id に型付きの値を代入する。
	backend_node_id: int
	# EN: Assign annotated value to frame_id.
	# JP: frame_id に型付きの値を代入する。
	frame_id: str | None

	# EN: Assign annotated value to node_type.
	# JP: node_type に型付きの値を代入する。
	node_type: NodeType
	# EN: Assign annotated value to node_value.
	# JP: node_value に型付きの値を代入する。
	node_value: str
	# EN: Assign annotated value to node_name.
	# JP: node_name に型付きの値を代入する。
	node_name: str
	# EN: Assign annotated value to attributes.
	# JP: attributes に型付きの値を代入する。
	attributes: dict[str, str] | None

	# EN: Assign annotated value to bounds.
	# JP: bounds に型付きの値を代入する。
	bounds: DOMRect | None

	# EN: Assign annotated value to x_path.
	# JP: x_path に型付きの値を代入する。
	x_path: str

	# EN: Assign annotated value to element_hash.
	# JP: element_hash に型付きの値を代入する。
	element_hash: int

	# EN: Define function `to_dict`.
	# JP: 関数 `to_dict` を定義する。
	def to_dict(self) -> dict[str, Any]:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'node_id': self.node_id,
			'backend_node_id': self.backend_node_id,
			'frame_id': self.frame_id,
			'node_type': self.node_type.value,
			'node_value': self.node_value,
			'node_name': self.node_name,
			'attributes': self.attributes,
			'x_path': self.x_path,
			'element_hash': self.element_hash,
			'bounds': self.bounds.to_dict() if self.bounds else None,
		}

	# EN: Define function `load_from_enhanced_dom_tree`.
	# JP: 関数 `load_from_enhanced_dom_tree` を定義する。
	@classmethod
	def load_from_enhanced_dom_tree(cls, enhanced_dom_tree: EnhancedDOMTreeNode) -> 'DOMInteractedElement':
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls(
			node_id=enhanced_dom_tree.node_id,
			backend_node_id=enhanced_dom_tree.backend_node_id,
			frame_id=enhanced_dom_tree.frame_id,
			node_type=enhanced_dom_tree.node_type,
			node_value=enhanced_dom_tree.node_value,
			node_name=enhanced_dom_tree.node_name,
			attributes=enhanced_dom_tree.attributes,
			bounds=enhanced_dom_tree.snapshot_node.bounds if enhanced_dom_tree.snapshot_node else None,
			x_path=enhanced_dom_tree.xpath,
			element_hash=hash(enhanced_dom_tree),
		)

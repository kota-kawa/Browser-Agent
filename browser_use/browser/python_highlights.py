# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Python-based highlighting system for drawing bounding boxes on screenshots.

This module replaces JavaScript-based highlighting with fast Python image processing
to draw bounding boxes around interactive elements directly on screenshots.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import base64
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import io
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from PIL import Image, ImageDraw, ImageFont

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import DOMSelectorMap, EnhancedDOMTreeNode
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe_debug
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import time_execution_async

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)

# Font cache to prevent repeated font loading and reduce memory usage
# EN: Assign annotated value to _FONT_CACHE.
# JP: _FONT_CACHE に型付きの値を代入する。
_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont | None] = {}

# Cross-platform font paths
# EN: Assign value to _FONT_PATHS.
# JP: _FONT_PATHS に値を代入する。
_FONT_PATHS = [
	'/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux (Debian/Ubuntu)
	'/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',  # Linux (Arch/Fedora)
	'/System/Library/Fonts/Arial.ttf',  # macOS
	'C:\\Windows\\Fonts\\arial.ttf',  # Windows
	'arial.ttf',  # Windows (system path)
	'Arial Bold.ttf',  # macOS alternative
	'/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',  # Linux alternative
]


# EN: Define function `get_cross_platform_font`.
# JP: 関数 `get_cross_platform_font` を定義する。
def get_cross_platform_font(font_size: int) -> ImageFont.FreeTypeFont | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get a cross-platform compatible font with caching to prevent memory leaks.

	Args:
	    font_size: Size of the font to load

	Returns:
	    ImageFont object or None if no system fonts are available
	"""
	# Use cache key based on font size
	# EN: Assign value to cache_key.
	# JP: cache_key に値を代入する。
	cache_key = ('system_font', font_size)

	# Return cached font if available
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if cache_key in _FONT_CACHE:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _FONT_CACHE[cache_key]

	# Try to load a system font
	# EN: Assign value to font.
	# JP: font に値を代入する。
	font = None
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for font_path in _FONT_PATHS:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to font.
			# JP: font に値を代入する。
			font = ImageFont.truetype(font_path, font_size)
			# EN: Exit the current loop.
			# JP: 現在のループを終了する。
			break
		except OSError:
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue

	# Cache the result (even if None) to avoid repeated attempts
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	_FONT_CACHE[cache_key] = font
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return font


# EN: Define function `cleanup_font_cache`.
# JP: 関数 `cleanup_font_cache` を定義する。
def cleanup_font_cache() -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Clean up the font cache to prevent memory leaks in long-running applications."""
	# EN: Execute this statement.
	# JP: この文を実行する。
	global _FONT_CACHE
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	_FONT_CACHE.clear()


# Color scheme for different element types
# EN: Assign value to ELEMENT_COLORS.
# JP: ELEMENT_COLORS に値を代入する。
ELEMENT_COLORS = {
	'button': '#FF6B6B',  # Red for buttons
	'input': '#4ECDC4',  # Teal for inputs
	'select': '#45B7D1',  # Blue for dropdowns
	'a': '#96CEB4',  # Green for links
	'textarea': '#FF8C42',  # Orange for text areas (was yellow, now more visible)
	'default': '#DDA0DD',  # Light purple for other interactive elements
}

# Element type mappings
# EN: Assign value to ELEMENT_TYPE_MAP.
# JP: ELEMENT_TYPE_MAP に値を代入する。
ELEMENT_TYPE_MAP = {
	'button': 'button',
	'input': 'input',
	'select': 'select',
	'a': 'a',
	'textarea': 'textarea',
}


# EN: Define function `get_element_color`.
# JP: 関数 `get_element_color` を定義する。
def get_element_color(tag_name: str, element_type: str | None = None) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get color for element based on tag name and type."""
	# Check input type first
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if tag_name == 'input' and element_type:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if element_type in ['button', 'submit']:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ELEMENT_COLORS['button']

	# Use tag-based color
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return ELEMENT_COLORS.get(tag_name.lower(), ELEMENT_COLORS['default'])


# EN: Define function `should_show_index_overlay`.
# JP: 関数 `should_show_index_overlay` を定義する。
def should_show_index_overlay(element_index: int | None) -> bool:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Determine if index overlay should be shown."""
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return element_index is not None


# EN: Define function `draw_enhanced_bounding_box_with_text`.
# JP: 関数 `draw_enhanced_bounding_box_with_text` を定義する。
def draw_enhanced_bounding_box_with_text(
	draw,  # ImageDraw.Draw - avoiding type annotation due to PIL typing issues
	bbox: tuple[int, int, int, int],
	color: str,
	text: str | None = None,
	font: ImageFont.FreeTypeFont | None = None,
	element_type: str = 'div',
	image_size: tuple[int, int] = (2000, 1500),
	device_pixel_ratio: float = 1.0,
) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Draw an enhanced bounding box with much bigger index containers and dashed borders."""
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	x1, y1, x2, y2 = bbox

	# Draw dashed bounding box with pattern: 1 line, 2 spaces, 1 line, 2 spaces...
	# EN: Assign value to dash_length.
	# JP: dash_length に値を代入する。
	dash_length = 4
	# EN: Assign value to gap_length.
	# JP: gap_length に値を代入する。
	gap_length = 8
	# EN: Assign value to line_width.
	# JP: line_width に値を代入する。
	line_width = 2

	# Helper function to draw dashed line
	# EN: Define function `draw_dashed_line`.
	# JP: 関数 `draw_dashed_line` を定義する。
	def draw_dashed_line(start_x, start_y, end_x, end_y):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if start_x == end_x:  # Vertical line
			# EN: Assign value to y.
			# JP: y に値を代入する。
			y = start_y
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while y < end_y:
				# EN: Assign value to dash_end.
				# JP: dash_end に値を代入する。
				dash_end = min(y + dash_length, end_y)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				draw.line([(start_x, y), (start_x, dash_end)], fill=color, width=line_width)
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				y += dash_length + gap_length
		else:  # Horizontal line
			# EN: Assign value to x.
			# JP: x に値を代入する。
			x = start_x
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while x < end_x:
				# EN: Assign value to dash_end.
				# JP: dash_end に値を代入する。
				dash_end = min(x + dash_length, end_x)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				draw.line([(x, start_y), (dash_end, start_y)], fill=color, width=line_width)
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				x += dash_length + gap_length

	# Draw dashed rectangle
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	draw_dashed_line(x1, y1, x2, y1)  # Top
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	draw_dashed_line(x2, y1, x2, y2)  # Right
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	draw_dashed_line(x2, y2, x1, y2)  # Bottom
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	draw_dashed_line(x1, y2, x1, y1)  # Left

	# Draw much bigger index overlay if we have index text
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if text:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Scale font size for appropriate sizing across different resolutions
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			img_width, img_height = image_size

			# EN: Assign value to css_width.
			# JP: css_width に値を代入する。
			css_width = img_width  # / device_pixel_ratio
			# Much smaller scaling - 1% of CSS viewport width, max 16px to prevent huge highlights
			# EN: Assign value to base_font_size.
			# JP: base_font_size に値を代入する。
			base_font_size = max(10, min(20, int(css_width * 0.01)))
			# Use shared font loading function with caching
			# EN: Assign value to big_font.
			# JP: big_font に値を代入する。
			big_font = get_cross_platform_font(base_font_size)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if big_font is None:
				# EN: Assign value to big_font.
				# JP: big_font に値を代入する。
				big_font = font  # Fallback to original font if no system fonts found

			# Get text size with bigger font
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if big_font:
				# EN: Assign value to bbox_text.
				# JP: bbox_text に値を代入する。
				bbox_text = draw.textbbox((0, 0), text, font=big_font)
				# EN: Assign value to text_width.
				# JP: text_width に値を代入する。
				text_width = bbox_text[2] - bbox_text[0]
				# EN: Assign value to text_height.
				# JP: text_height に値を代入する。
				text_height = bbox_text[3] - bbox_text[1]
			else:
				# Fallback for default font
				# EN: Assign value to bbox_text.
				# JP: bbox_text に値を代入する。
				bbox_text = draw.textbbox((0, 0), text)
				# EN: Assign value to text_width.
				# JP: text_width に値を代入する。
				text_width = bbox_text[2] - bbox_text[0]
				# EN: Assign value to text_height.
				# JP: text_height に値を代入する。
				text_height = bbox_text[3] - bbox_text[1]

			# Scale padding appropriately for different resolutions
			# EN: Assign value to padding.
			# JP: padding に値を代入する。
			padding = max(4, min(10, int(css_width * 0.005)))  # 0.3% of CSS width, max 4px
			# EN: Assign value to element_width.
			# JP: element_width に値を代入する。
			element_width = x2 - x1
			# EN: Assign value to element_height.
			# JP: element_height に値を代入する。
			element_height = y2 - y1

			# Container dimensions
			# EN: Assign value to container_width.
			# JP: container_width に値を代入する。
			container_width = text_width + padding * 2
			# EN: Assign value to container_height.
			# JP: container_height に値を代入する。
			container_height = text_height + padding * 2

			# Position in top center - for small elements, place further up to avoid blocking content
			# Center horizontally within the element
			# EN: Assign value to bg_x1.
			# JP: bg_x1 に値を代入する。
			bg_x1 = x1 + (element_width - container_width) // 2

			# Simple rule: if element is small, place index further up to avoid blocking icons
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if element_width < 60 or element_height < 30:
				# Small element: place well above to avoid blocking content
				# EN: Assign value to bg_y1.
				# JP: bg_y1 に値を代入する。
				bg_y1 = max(0, y1 - container_height - 5)
			else:
				# Regular element: place inside with small offset
				# EN: Assign value to bg_y1.
				# JP: bg_y1 に値を代入する。
				bg_y1 = y1 + 2

			# EN: Assign value to bg_x2.
			# JP: bg_x2 に値を代入する。
			bg_x2 = bg_x1 + container_width
			# EN: Assign value to bg_y2.
			# JP: bg_y2 に値を代入する。
			bg_y2 = bg_y1 + container_height

			# Center the number within the index box with proper baseline handling
			# EN: Assign value to text_x.
			# JP: text_x に値を代入する。
			text_x = bg_x1 + (container_width - text_width) // 2
			# Add extra vertical space to prevent clipping
			# EN: Assign value to text_y.
			# JP: text_y に値を代入する。
			text_y = bg_y1 + (container_height - text_height) // 2 - bbox_text[1]  # Subtract top offset

			# Ensure container stays within image bounds
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			img_width, img_height = image_size
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if bg_x1 < 0:
				# EN: Assign value to offset.
				# JP: offset に値を代入する。
				offset = -bg_x1
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				bg_x1 += offset
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				bg_x2 += offset
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				text_x += offset
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if bg_y1 < 0:
				# EN: Assign value to offset.
				# JP: offset に値を代入する。
				offset = -bg_y1
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				bg_y1 += offset
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				bg_y2 += offset
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				text_y += offset
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if bg_x2 > img_width:
				# EN: Assign value to offset.
				# JP: offset に値を代入する。
				offset = bg_x2 - img_width
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				bg_x1 -= offset
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				bg_x2 -= offset
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				text_x -= offset
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if bg_y2 > img_height:
				# EN: Assign value to offset.
				# JP: offset に値を代入する。
				offset = bg_y2 - img_height
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				bg_y1 -= offset
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				bg_y2 -= offset
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				text_y -= offset

			# Draw bigger background rectangle with thicker border
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=color, outline='white', width=2)

			# Draw white text centered in the index box
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			draw.text((text_x, text_y), text, fill='white', font=big_font or font)

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Failed to draw enhanced text overlay: {e}')


# EN: Define function `draw_bounding_box_with_text`.
# JP: 関数 `draw_bounding_box_with_text` を定義する。
def draw_bounding_box_with_text(
	draw,  # ImageDraw.Draw - avoiding type annotation due to PIL typing issues
	bbox: tuple[int, int, int, int],
	color: str,
	text: str | None = None,
	font: ImageFont.FreeTypeFont | None = None,
) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Draw a bounding box with optional text overlay."""
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	x1, y1, x2, y2 = bbox

	# Draw dashed bounding box
	# EN: Assign value to dash_length.
	# JP: dash_length に値を代入する。
	dash_length = 2
	# EN: Assign value to gap_length.
	# JP: gap_length に値を代入する。
	gap_length = 6

	# Top edge
	# EN: Assign value to x.
	# JP: x に値を代入する。
	x = x1
	# EN: Repeat logic while a condition is true.
	# JP: 条件が真の間、処理を繰り返す。
	while x < x2:
		# EN: Assign value to end_x.
		# JP: end_x に値を代入する。
		end_x = min(x + dash_length, x2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.line([(x, y1), (end_x, y1)], fill=color, width=2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.line([(x, y1 + 1), (end_x, y1 + 1)], fill=color, width=2)
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		x += dash_length + gap_length

	# Bottom edge
	# EN: Assign value to x.
	# JP: x に値を代入する。
	x = x1
	# EN: Repeat logic while a condition is true.
	# JP: 条件が真の間、処理を繰り返す。
	while x < x2:
		# EN: Assign value to end_x.
		# JP: end_x に値を代入する。
		end_x = min(x + dash_length, x2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.line([(x, y2), (end_x, y2)], fill=color, width=2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.line([(x, y2 - 1), (end_x, y2 - 1)], fill=color, width=2)
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		x += dash_length + gap_length

	# Left edge
	# EN: Assign value to y.
	# JP: y に値を代入する。
	y = y1
	# EN: Repeat logic while a condition is true.
	# JP: 条件が真の間、処理を繰り返す。
	while y < y2:
		# EN: Assign value to end_y.
		# JP: end_y に値を代入する。
		end_y = min(y + dash_length, y2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.line([(x1, y), (x1, end_y)], fill=color, width=2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.line([(x1 + 1, y), (x1 + 1, end_y)], fill=color, width=2)
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		y += dash_length + gap_length

	# Right edge
	# EN: Assign value to y.
	# JP: y に値を代入する。
	y = y1
	# EN: Repeat logic while a condition is true.
	# JP: 条件が真の間、処理を繰り返す。
	while y < y2:
		# EN: Assign value to end_y.
		# JP: end_y に値を代入する。
		end_y = min(y + dash_length, y2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.line([(x2, y), (x2, end_y)], fill=color, width=2)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.line([(x2 - 1, y), (x2 - 1, end_y)], fill=color, width=2)
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		y += dash_length + gap_length

	# Draw index overlay if we have index text
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if text:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get text size
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if font:
				# EN: Assign value to bbox_text.
				# JP: bbox_text に値を代入する。
				bbox_text = draw.textbbox((0, 0), text, font=font)
				# EN: Assign value to text_width.
				# JP: text_width に値を代入する。
				text_width = bbox_text[2] - bbox_text[0]
				# EN: Assign value to text_height.
				# JP: text_height に値を代入する。
				text_height = bbox_text[3] - bbox_text[1]
			else:
				# Fallback for default font
				# EN: Assign value to bbox_text.
				# JP: bbox_text に値を代入する。
				bbox_text = draw.textbbox((0, 0), text)
				# EN: Assign value to text_width.
				# JP: text_width に値を代入する。
				text_width = bbox_text[2] - bbox_text[0]
				# EN: Assign value to text_height.
				# JP: text_height に値を代入する。
				text_height = bbox_text[3] - bbox_text[1]

			# Smart positioning based on element size
			# EN: Assign value to padding.
			# JP: padding に値を代入する。
			padding = 5
			# EN: Assign value to element_width.
			# JP: element_width に値を代入する。
			element_width = x2 - x1
			# EN: Assign value to element_height.
			# JP: element_height に値を代入する。
			element_height = y2 - y1
			# EN: Assign value to element_area.
			# JP: element_area に値を代入する。
			element_area = element_width * element_height
			# EN: Assign value to index_box_area.
			# JP: index_box_area に値を代入する。
			index_box_area = (text_width + padding * 2) * (text_height + padding * 2)

			# Calculate size ratio to determine positioning strategy
			# EN: Assign value to size_ratio.
			# JP: size_ratio に値を代入する。
			size_ratio = element_area / max(index_box_area, 1)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if size_ratio < 4:
				# Very small elements: place outside in bottom-right corner
				# EN: Assign value to text_x.
				# JP: text_x に値を代入する。
				text_x = x2 + padding
				# EN: Assign value to text_y.
				# JP: text_y に値を代入する。
				text_y = y2 - text_height
				# Ensure it doesn't go off screen
				# EN: Assign value to text_x.
				# JP: text_x に値を代入する。
				text_x = min(text_x, 1200 - text_width - padding)
				# EN: Assign value to text_y.
				# JP: text_y に値を代入する。
				text_y = max(text_y, 0)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif size_ratio < 16:
				# Medium elements: place in bottom-right corner inside
				# EN: Assign value to text_x.
				# JP: text_x に値を代入する。
				text_x = x2 - text_width - padding
				# EN: Assign value to text_y.
				# JP: text_y に値を代入する。
				text_y = y2 - text_height - padding
			else:
				# Large elements: place in center
				# EN: Assign value to text_x.
				# JP: text_x に値を代入する。
				text_x = x1 + (element_width - text_width) // 2
				# EN: Assign value to text_y.
				# JP: text_y に値を代入する。
				text_y = y1 + (element_height - text_height) // 2

			# Ensure text stays within bounds
			# EN: Assign value to text_x.
			# JP: text_x に値を代入する。
			text_x = max(0, min(text_x, 1200 - text_width))
			# EN: Assign value to text_y.
			# JP: text_y に値を代入する。
			text_y = max(0, min(text_y, 800 - text_height))

			# Draw background rectangle for maximum contrast
			# EN: Assign value to bg_x1.
			# JP: bg_x1 に値を代入する。
			bg_x1 = text_x - padding
			# EN: Assign value to bg_y1.
			# JP: bg_y1 に値を代入する。
			bg_y1 = text_y - padding
			# EN: Assign value to bg_x2.
			# JP: bg_x2 に値を代入する。
			bg_x2 = text_x + text_width + padding
			# EN: Assign value to bg_y2.
			# JP: bg_y2 に値を代入する。
			bg_y2 = text_y + text_height + padding

			# Use white background with thick black border for maximum visibility
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill='white', outline='black', width=2)

			# Draw bold dark text on light background for best contrast
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			draw.text((text_x, text_y), text, fill='black', font=font)

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Failed to draw text overlay: {e}')


# EN: Define function `process_element_highlight`.
# JP: 関数 `process_element_highlight` を定義する。
def process_element_highlight(
	element_id: int,
	element: EnhancedDOMTreeNode,
	draw,
	device_pixel_ratio: float,
	font,
	filter_highlight_ids: bool,
	image_size: tuple[int, int],
) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Process a single element for highlighting."""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Use absolute_position coordinates directly
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not element.absolute_position:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to bounds.
		# JP: bounds に値を代入する。
		bounds = element.absolute_position

		# Scale coordinates from CSS pixels to device pixels for screenshot
		# The screenshot is captured at device pixel resolution, but coordinates are in CSS pixels
		# EN: Assign value to x1.
		# JP: x1 に値を代入する。
		x1 = int(bounds.x * device_pixel_ratio)
		# EN: Assign value to y1.
		# JP: y1 に値を代入する。
		y1 = int(bounds.y * device_pixel_ratio)
		# EN: Assign value to x2.
		# JP: x2 に値を代入する。
		x2 = int((bounds.x + bounds.width) * device_pixel_ratio)
		# EN: Assign value to y2.
		# JP: y2 に値を代入する。
		y2 = int((bounds.y + bounds.height) * device_pixel_ratio)

		# Ensure coordinates are within image bounds
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		img_width, img_height = image_size
		# EN: Assign value to x1.
		# JP: x1 に値を代入する。
		x1 = max(0, min(x1, img_width))
		# EN: Assign value to y1.
		# JP: y1 に値を代入する。
		y1 = max(0, min(y1, img_height))
		# EN: Assign value to x2.
		# JP: x2 に値を代入する。
		x2 = max(x1, min(x2, img_width))
		# EN: Assign value to y2.
		# JP: y2 に値を代入する。
		y2 = max(y1, min(y2, img_height))

		# Skip if bounding box is too small or invalid
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if x2 - x1 < 2 or y2 - y1 < 2:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Get element color based on type
		# EN: Assign value to tag_name.
		# JP: tag_name に値を代入する。
		tag_name = element.tag_name if hasattr(element, 'tag_name') else 'div'
		# EN: Assign value to element_type.
		# JP: element_type に値を代入する。
		element_type = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(element, 'attributes') and element.attributes:
			# EN: Assign value to element_type.
			# JP: element_type に値を代入する。
			element_type = element.attributes.get('type')

		# EN: Assign value to color.
		# JP: color に値を代入する。
		color = get_element_color(tag_name, element_type)

		# Get element index for overlay and apply filtering
		# EN: Assign value to element_index.
		# JP: element_index に値を代入する。
		element_index = getattr(element, 'element_index', None)
		# EN: Assign value to index_text.
		# JP: index_text に値を代入する。
		index_text = None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if element_index is not None:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if filter_highlight_ids:
				# Use the meaningful text that matches what the LLM sees
				# EN: Assign value to meaningful_text.
				# JP: meaningful_text に値を代入する。
				meaningful_text = element.get_meaningful_text_for_llm()
				# Show ID only if meaningful text is less than 5 characters
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if len(meaningful_text) < 3:
					# EN: Assign value to index_text.
					# JP: index_text に値を代入する。
					index_text = str(element_index)
			else:
				# Always show ID when filter is disabled
				# EN: Assign value to index_text.
				# JP: index_text に値を代入する。
				index_text = str(element_index)

		# Draw enhanced bounding box with bigger index
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw_enhanced_bounding_box_with_text(
			draw, (x1, y1, x2, y2), color, index_text, font, tag_name, image_size, device_pixel_ratio
		)

	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Failed to draw highlight for element {element_id}: {e}')


# EN: Define async function `create_highlighted_screenshot`.
# JP: 非同期関数 `create_highlighted_screenshot` を定義する。
@observe_debug(ignore_input=True, ignore_output=True, name='create_highlighted_screenshot')
@time_execution_async('create_highlighted_screenshot')
async def create_highlighted_screenshot(
	screenshot_b64: str,
	selector_map: DOMSelectorMap,
	device_pixel_ratio: float = 1.0,
	viewport_offset_x: int = 0,
	viewport_offset_y: int = 0,
	filter_highlight_ids: bool = True,
) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Create a highlighted screenshot with bounding boxes around interactive elements.

	Args:
	    screenshot_b64: Base64 encoded screenshot
	    selector_map: Map of interactive elements with their positions
	    device_pixel_ratio: Device pixel ratio for scaling coordinates
	    viewport_offset_x: X offset for viewport positioning
	    viewport_offset_y: Y offset for viewport positioning

	Returns:
	    Base64 encoded highlighted screenshot
	"""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Decode screenshot
		# EN: Assign value to screenshot_data.
		# JP: screenshot_data に値を代入する。
		screenshot_data = base64.b64decode(screenshot_b64)
		# EN: Assign value to image.
		# JP: image に値を代入する。
		image = Image.open(io.BytesIO(screenshot_data)).convert('RGBA')

		# Create drawing context
		# EN: Assign value to draw.
		# JP: draw に値を代入する。
		draw = ImageDraw.Draw(image)

		# Load font using shared function with caching
		# EN: Assign value to font.
		# JP: font に値を代入する。
		font = get_cross_platform_font(12)
		# If no system fonts found, font remains None and will use default font

		# Process elements sequentially to avoid ImageDraw thread safety issues
		# PIL ImageDraw is not thread-safe, so we process elements one by one
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for element_id, element in selector_map.items():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			process_element_highlight(element_id, element, draw, device_pixel_ratio, font, filter_highlight_ids, image.size)

		# Convert back to base64
		# EN: Assign value to output_buffer.
		# JP: output_buffer に値を代入する。
		output_buffer = io.BytesIO()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			image.save(output_buffer, format='PNG')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			output_buffer.seek(0)
			# EN: Assign value to highlighted_b64.
			# JP: highlighted_b64 に値を代入する。
			highlighted_b64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Successfully created highlighted screenshot with {len(selector_map)} elements')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return highlighted_b64
		finally:
			# Explicit cleanup to prevent memory leaks
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			output_buffer.close()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'image' in locals():
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				image.close()

	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.error(f'Failed to create highlighted screenshot: {e}')
		# Clean up on error as well
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'image' in locals():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			image.close()
		# Return original screenshot on error
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return screenshot_b64


# EN: Define async function `get_viewport_info_from_cdp`.
# JP: 非同期関数 `get_viewport_info_from_cdp` を定義する。
async def get_viewport_info_from_cdp(cdp_session) -> tuple[float, int, int]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get viewport information from CDP session.

	Returns:
	    Tuple of (device_pixel_ratio, scroll_x, scroll_y)
	"""
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Get layout metrics which includes viewport info and device pixel ratio
		# EN: Assign value to metrics.
		# JP: metrics に値を代入する。
		metrics = await cdp_session.cdp_client.send.Page.getLayoutMetrics(session_id=cdp_session.session_id)

		# Extract viewport information
		# EN: Assign value to visual_viewport.
		# JP: visual_viewport に値を代入する。
		visual_viewport = metrics.get('visualViewport', {})
		# EN: Assign value to css_visual_viewport.
		# JP: css_visual_viewport に値を代入する。
		css_visual_viewport = metrics.get('cssVisualViewport', {})
		# EN: Assign value to css_layout_viewport.
		# JP: css_layout_viewport に値を代入する。
		css_layout_viewport = metrics.get('cssLayoutViewport', {})

		# Calculate device pixel ratio
		# EN: Assign value to css_width.
		# JP: css_width に値を代入する。
		css_width = css_visual_viewport.get('clientWidth', css_layout_viewport.get('clientWidth', 1280.0))
		# EN: Assign value to device_width.
		# JP: device_width に値を代入する。
		device_width = visual_viewport.get('clientWidth', css_width)
		# EN: Assign value to device_pixel_ratio.
		# JP: device_pixel_ratio に値を代入する。
		device_pixel_ratio = device_width / css_width if css_width > 0 else 1.0

		# Get scroll position in CSS pixels
		# EN: Assign value to scroll_x.
		# JP: scroll_x に値を代入する。
		scroll_x = int(css_visual_viewport.get('pageX', 0))
		# EN: Assign value to scroll_y.
		# JP: scroll_y に値を代入する。
		scroll_y = int(css_visual_viewport.get('pageY', 0))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return float(device_pixel_ratio), scroll_x, scroll_y

	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Failed to get viewport info from CDP: {e}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 1.0, 0, 0


# EN: Define async function `create_highlighted_screenshot_async`.
# JP: 非同期関数 `create_highlighted_screenshot_async` を定義する。
@time_execution_async('create_highlighted_screenshot_async')
async def create_highlighted_screenshot_async(
	screenshot_b64: str, selector_map: DOMSelectorMap, cdp_session=None, filter_highlight_ids: bool = True
) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Async wrapper for creating highlighted screenshots.

	Args:
	    screenshot_b64: Base64 encoded screenshot
	    selector_map: Map of interactive elements
	    cdp_session: CDP session for getting viewport info
	    filter_highlight_ids: Whether to filter element IDs based on meaningful text

	Returns:
	    Base64 encoded highlighted screenshot
	"""
	# Get viewport information if CDP session is available
	# EN: Assign value to device_pixel_ratio.
	# JP: device_pixel_ratio に値を代入する。
	device_pixel_ratio = 1.0
	# EN: Assign value to viewport_offset_x.
	# JP: viewport_offset_x に値を代入する。
	viewport_offset_x = 0
	# EN: Assign value to viewport_offset_y.
	# JP: viewport_offset_y に値を代入する。
	viewport_offset_y = 0

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if cdp_session:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			device_pixel_ratio, viewport_offset_x, viewport_offset_y = await get_viewport_info_from_cdp(cdp_session)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Failed to get viewport info from CDP: {e}')

	# Create highlighted screenshot with async processing
	# EN: Assign value to final_screenshot.
	# JP: final_screenshot に値を代入する。
	final_screenshot = await create_highlighted_screenshot(
		screenshot_b64, selector_map, device_pixel_ratio, viewport_offset_x, viewport_offset_y, filter_highlight_ids
	)

	# EN: Assign value to filename.
	# JP: filename に値を代入する。
	filename = os.getenv('BROWSER_USE_SCREENSHOT_FILE')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if filename:

		# EN: Define function `_write_screenshot`.
		# JP: 関数 `_write_screenshot` を定義する。
		def _write_screenshot():
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with open(filename, 'wb') as f:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					f.write(base64.b64decode(final_screenshot))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('Saved screenshot to ' + str(filename))
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.warning(f'Failed to save screenshot to {filename}: {e}')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await asyncio.to_thread(_write_screenshot)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return final_screenshot


# Export the cleanup function for external use in long-running applications
# EN: Assign value to __all__.
# JP: __all__ に値を代入する。
__all__ = ['create_highlighted_screenshot', 'create_highlighted_screenshot_async', 'cleanup_font_cache']

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

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
import platform
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import AgentHistoryList
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import PLACEHOLDER_4PX_SCREENSHOT
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from PIL import Image, ImageFont

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define function `decode_unicode_escapes_to_utf8`.
# JP: 関数 `decode_unicode_escapes_to_utf8` を定義する。
def decode_unicode_escapes_to_utf8(text: str) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Handle decoding any unicode escape sequences embedded in a string (needed to render non-ASCII languages like chinese or arabic in the GIF overlay text)"""

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if r'\u' not in text:
		# doesn't have any escape sequences that need to be decoded
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return text

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Try to decode Unicode escape sequences
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return text.encode('latin1').decode('unicode_escape')
	except (UnicodeEncodeError, UnicodeDecodeError):
		# logger.debug(f"Failed to decode unicode escape sequences while generating gif text: {text}")
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return text


# EN: Define function `create_history_gif`.
# JP: 関数 `create_history_gif` を定義する。
def create_history_gif(
	task: str,
	history: AgentHistoryList,
	#
	output_path: str = 'agent_history.gif',
	duration: int = 3000,
	show_goals: bool = True,
	show_task: bool = True,
	show_logo: bool = False,
	font_size: int = 40,
	title_font_size: int = 56,
	goal_font_size: int = 44,
	margin: int = 40,
	line_spacing: float = 1.5,
) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Create a GIF from the agent's history with overlaid task and goal text."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not history.history:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('No history to create GIF from')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from PIL import Image, ImageFont

	# EN: Assign value to images.
	# JP: images に値を代入する。
	images = []

	# if history is empty, we can't create a gif
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not history.history:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('No history to create GIF from')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# Get all screenshots from history (including None placeholders)
	# EN: Assign value to screenshots.
	# JP: screenshots に値を代入する。
	screenshots = history.screenshots(return_none_if_not_screenshot=True)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not screenshots:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('No screenshots found in history')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# Find the first non-placeholder screenshot
	# A screenshot is considered a placeholder if:
	# 1. It's the exact 4px placeholder for about:blank pages, OR
	# 2. It comes from a new tab page (chrome://newtab/, about:blank, etc.)
	# EN: Assign value to first_real_screenshot.
	# JP: first_real_screenshot に値を代入する。
	first_real_screenshot = None
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for screenshot in screenshots:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if screenshot and screenshot != PLACEHOLDER_4PX_SCREENSHOT:
			# EN: Assign value to first_real_screenshot.
			# JP: first_real_screenshot に値を代入する。
			first_real_screenshot = screenshot
			# EN: Exit the current loop.
			# JP: 現在のループを終了する。
			break

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not first_real_screenshot:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('No valid screenshots found (all are placeholders or from new tab pages)')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# Try to load nicer fonts
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Try different font options in order of preference
		# ArialUni is a font that comes with Office and can render most non-alphabet characters
		# EN: Assign value to font_options.
		# JP: font_options に値を代入する。
		font_options = [
			'PingFang',
			'STHeiti Medium',
			'Microsoft YaHei',  # 微软雅黑
			'SimHei',  # 黑体
			'SimSun',  # 宋体
			'Noto Sans CJK SC',  # 思源黑体
			'WenQuanYi Micro Hei',  # 文泉驿微米黑
			'Helvetica',
			'Arial',
			'DejaVuSans',
			'Verdana',
		]
		# EN: Assign value to font_loaded.
		# JP: font_loaded に値を代入する。
		font_loaded = False

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for font_name in font_options:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if platform.system() == 'Windows':
					# Need to specify the abs font path on Windows
					# EN: Assign value to font_name.
					# JP: font_name に値を代入する。
					font_name = os.path.join(CONFIG.WIN_FONT_DIR, font_name + '.ttf')
				# EN: Assign value to regular_font.
				# JP: regular_font に値を代入する。
				regular_font = ImageFont.truetype(font_name, font_size)
				# EN: Assign value to title_font.
				# JP: title_font に値を代入する。
				title_font = ImageFont.truetype(font_name, title_font_size)
				# EN: Assign value to goal_font.
				# JP: goal_font に値を代入する。
				goal_font = ImageFont.truetype(font_name, goal_font_size)
				# EN: Assign value to font_loaded.
				# JP: font_loaded に値を代入する。
				font_loaded = True
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break
			except OSError:
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not font_loaded:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise OSError('No preferred fonts found')

	except OSError:
		# EN: Assign value to regular_font.
		# JP: regular_font に値を代入する。
		regular_font = ImageFont.load_default()
		# EN: Assign value to title_font.
		# JP: title_font に値を代入する。
		title_font = ImageFont.load_default()

		# EN: Assign value to goal_font.
		# JP: goal_font に値を代入する。
		goal_font = regular_font

	# Load logo if requested
	# EN: Assign value to logo.
	# JP: logo に値を代入する。
	logo = None
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if show_logo:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to logo.
			# JP: logo に値を代入する。
			logo = Image.open('./static/browser-use.png')
			# Resize logo to be small (e.g., 40px height)
			# EN: Assign value to logo_height.
			# JP: logo_height に値を代入する。
			logo_height = 150
			# EN: Assign value to aspect_ratio.
			# JP: aspect_ratio に値を代入する。
			aspect_ratio = logo.width / logo.height
			# EN: Assign value to logo_width.
			# JP: logo_width に値を代入する。
			logo_width = int(logo_height * aspect_ratio)
			# EN: Assign value to logo.
			# JP: logo に値を代入する。
			logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(f'Could not load logo: {e}')

	# Create task frame if requested
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if show_task and task:
		# Find the first non-placeholder screenshot for the task frame
		# EN: Assign value to first_real_screenshot.
		# JP: first_real_screenshot に値を代入する。
		first_real_screenshot = None
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for item in history.history:
			# EN: Assign value to screenshot_b64.
			# JP: screenshot_b64 に値を代入する。
			screenshot_b64 = item.state.get_screenshot()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if screenshot_b64 and screenshot_b64 != PLACEHOLDER_4PX_SCREENSHOT:
				# EN: Assign value to first_real_screenshot.
				# JP: first_real_screenshot に値を代入する。
				first_real_screenshot = screenshot_b64
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if first_real_screenshot:
			# EN: Assign value to task_frame.
			# JP: task_frame に値を代入する。
			task_frame = _create_task_frame(
				task,
				first_real_screenshot,
				title_font,  # type: ignore
				regular_font,  # type: ignore
				logo,
				line_spacing,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			images.append(task_frame)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning('No real screenshots found for task frame, skipping task frame')

	# Process each history item with its corresponding screenshot
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for i, (item, screenshot) in enumerate(zip(history.history, screenshots), 1):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not screenshot:
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue

		# Skip placeholder screenshots from about:blank pages
		# These are 4x4 white PNGs encoded as a specific base64 string
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if screenshot == PLACEHOLDER_4PX_SCREENSHOT:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Skipping placeholder screenshot from about:blank page at step {i}')
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue

		# Skip screenshots from new tab pages
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.utils import is_new_tab_page

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_new_tab_page(item.state.url):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Skipping screenshot from new tab page ({item.state.url}) at step {i}')
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue

		# Convert base64 screenshot to PIL Image
		# EN: Assign value to img_data.
		# JP: img_data に値を代入する。
		img_data = base64.b64decode(screenshot)
		# EN: Assign value to image.
		# JP: image に値を代入する。
		image = Image.open(io.BytesIO(img_data))

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if show_goals and item.model_output:
			# EN: Assign value to image.
			# JP: image に値を代入する。
			image = _add_overlay_to_image(
				image=image,
				step_number=i,
				goal_text=item.model_output.current_state.next_goal,
				regular_font=regular_font,  # type: ignore
				title_font=title_font,  # type: ignore
				margin=margin,
				logo=logo,
			)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		images.append(image)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if images:
		# Save the GIF
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		images[0].save(
			output_path,
			save_all=True,
			append_images=images[1:],
			duration=duration,
			loop=0,
			optimize=False,
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'Created GIF at {output_path}')
	else:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('No images found in history to create GIF')


# EN: Define function `_create_task_frame`.
# JP: 関数 `_create_task_frame` を定義する。
def _create_task_frame(
	task: str,
	first_screenshot: str,
	title_font: ImageFont.FreeTypeFont,
	regular_font: ImageFont.FreeTypeFont,
	logo: Image.Image | None = None,
	line_spacing: float = 1.5,
) -> Image.Image:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Create initial frame showing the task."""
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from PIL import Image, ImageDraw, ImageFont

	# EN: Assign value to img_data.
	# JP: img_data に値を代入する。
	img_data = base64.b64decode(first_screenshot)
	# EN: Assign value to template.
	# JP: template に値を代入する。
	template = Image.open(io.BytesIO(img_data))
	# EN: Assign value to image.
	# JP: image に値を代入する。
	image = Image.new('RGB', template.size, (0, 0, 0))
	# EN: Assign value to draw.
	# JP: draw に値を代入する。
	draw = ImageDraw.Draw(image)

	# Calculate vertical center of image
	# EN: Assign value to center_y.
	# JP: center_y に値を代入する。
	center_y = image.height // 2

	# Draw task text with dynamic font size based on task length
	# EN: Assign value to margin.
	# JP: margin に値を代入する。
	margin = 140  # Increased margin
	# EN: Assign value to max_width.
	# JP: max_width に値を代入する。
	max_width = image.width - (2 * margin)

	# Dynamic font size calculation based on task length
	# Start with base font size (regular + 16)
	# EN: Assign value to base_font_size.
	# JP: base_font_size に値を代入する。
	base_font_size = regular_font.size + 16
	# EN: Assign value to min_font_size.
	# JP: min_font_size に値を代入する。
	min_font_size = max(regular_font.size - 10, 16)  # Don't go below 16pt
	# EN: Assign value to max_font_size.
	# JP: max_font_size に値を代入する。
	max_font_size = base_font_size  # Cap at the base font size

	# Calculate dynamic font size based on text length and complexity
	# Longer texts get progressively smaller fonts
	# EN: Assign value to text_length.
	# JP: text_length に値を代入する。
	text_length = len(task)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if text_length > 200:
		# For very long text, reduce font size logarithmically
		# EN: Assign value to font_size.
		# JP: font_size に値を代入する。
		font_size = max(base_font_size - int(10 * (text_length / 200)), min_font_size)
	else:
		# EN: Assign value to font_size.
		# JP: font_size に値を代入する。
		font_size = base_font_size

	# Try to create a larger font, but fall back to regular font if it fails
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to larger_font.
		# JP: larger_font に値を代入する。
		larger_font = ImageFont.truetype(regular_font.path, font_size)  # type: ignore
	except (OSError, AttributeError):
		# Fall back to regular font if .path is not available or font loading fails
		# EN: Assign value to larger_font.
		# JP: larger_font に値を代入する。
		larger_font = regular_font

	# Generate wrapped text with the calculated font size
	# EN: Assign value to wrapped_text.
	# JP: wrapped_text に値を代入する。
	wrapped_text = _wrap_text(task, larger_font, max_width)

	# Calculate line height with spacing
	# EN: Assign value to line_height.
	# JP: line_height に値を代入する。
	line_height = larger_font.size * line_spacing

	# Split text into lines and draw with custom spacing
	# EN: Assign value to lines.
	# JP: lines に値を代入する。
	lines = wrapped_text.split('\n')
	# EN: Assign value to total_height.
	# JP: total_height に値を代入する。
	total_height = line_height * len(lines)

	# Start position for first line
	# EN: Assign value to text_y.
	# JP: text_y に値を代入する。
	text_y = center_y - (total_height / 2) + 50  # Shifted down slightly

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for line in lines:
		# Get line width for centering
		# EN: Assign value to line_bbox.
		# JP: line_bbox に値を代入する。
		line_bbox = draw.textbbox((0, 0), line, font=larger_font)
		# EN: Assign value to text_x.
		# JP: text_x に値を代入する。
		text_x = (image.width - (line_bbox[2] - line_bbox[0])) // 2

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.text(
			(text_x, text_y),
			line,
			font=larger_font,
			fill=(255, 255, 255),
		)
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		text_y += line_height

	# Add logo if provided (top right corner)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if logo:
		# EN: Assign value to logo_margin.
		# JP: logo_margin に値を代入する。
		logo_margin = 20
		# EN: Assign value to logo_x.
		# JP: logo_x に値を代入する。
		logo_x = image.width - logo.width - logo_margin
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		image.paste(logo, (logo_x, logo_margin), logo if logo.mode == 'RGBA' else None)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return image


# EN: Define function `_add_overlay_to_image`.
# JP: 関数 `_add_overlay_to_image` を定義する。
def _add_overlay_to_image(
	image: Image.Image,
	step_number: int,
	goal_text: str,
	regular_font: ImageFont.FreeTypeFont,
	title_font: ImageFont.FreeTypeFont,
	margin: int,
	logo: Image.Image | None = None,
	display_step: bool = True,
	text_color: tuple[int, int, int, int] = (255, 255, 255, 255),
	text_box_color: tuple[int, int, int, int] = (0, 0, 0, 255),
) -> Image.Image:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Add step number and goal overlay to an image."""

	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from PIL import Image, ImageDraw

	# EN: Assign value to goal_text.
	# JP: goal_text に値を代入する。
	goal_text = decode_unicode_escapes_to_utf8(goal_text)
	# EN: Assign value to image.
	# JP: image に値を代入する。
	image = image.convert('RGBA')
	# EN: Assign value to txt_layer.
	# JP: txt_layer に値を代入する。
	txt_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
	# EN: Assign value to draw.
	# JP: draw に値を代入する。
	draw = ImageDraw.Draw(txt_layer)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if display_step:
		# Add step number (bottom left)
		# EN: Assign value to step_text.
		# JP: step_text に値を代入する。
		step_text = str(step_number)
		# EN: Assign value to step_bbox.
		# JP: step_bbox に値を代入する。
		step_bbox = draw.textbbox((0, 0), step_text, font=title_font)
		# EN: Assign value to step_width.
		# JP: step_width に値を代入する。
		step_width = step_bbox[2] - step_bbox[0]
		# EN: Assign value to step_height.
		# JP: step_height に値を代入する。
		step_height = step_bbox[3] - step_bbox[1]

		# Position step number in bottom left
		# EN: Assign value to x_step.
		# JP: x_step に値を代入する。
		x_step = margin + 10  # Slight additional offset from edge
		# EN: Assign value to y_step.
		# JP: y_step に値を代入する。
		y_step = image.height - margin - step_height - 10  # Slight offset from bottom

		# Draw rounded rectangle background for step number
		# EN: Assign value to padding.
		# JP: padding に値を代入する。
		padding = 20  # Increased padding
		# EN: Assign value to step_bg_bbox.
		# JP: step_bg_bbox に値を代入する。
		step_bg_bbox = (
			x_step - padding,
			y_step - padding,
			x_step + step_width + padding,
			y_step + step_height + padding,
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.rounded_rectangle(
			step_bg_bbox,
			radius=15,  # Add rounded corners
			fill=text_box_color,
		)

		# Draw step number
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		draw.text(
			(x_step, y_step),
			step_text,
			font=title_font,
			fill=text_color,
		)

	# Draw goal text (centered, bottom)
	# EN: Assign value to max_width.
	# JP: max_width に値を代入する。
	max_width = image.width - (4 * margin)
	# EN: Assign value to wrapped_goal.
	# JP: wrapped_goal に値を代入する。
	wrapped_goal = _wrap_text(goal_text, title_font, max_width)
	# EN: Assign value to goal_bbox.
	# JP: goal_bbox に値を代入する。
	goal_bbox = draw.multiline_textbbox((0, 0), wrapped_goal, font=title_font)
	# EN: Assign value to goal_width.
	# JP: goal_width に値を代入する。
	goal_width = goal_bbox[2] - goal_bbox[0]
	# EN: Assign value to goal_height.
	# JP: goal_height に値を代入する。
	goal_height = goal_bbox[3] - goal_bbox[1]

	# Center goal text horizontally, place above step number
	# EN: Assign value to x_goal.
	# JP: x_goal に値を代入する。
	x_goal = (image.width - goal_width) // 2
	# EN: Assign value to y_goal.
	# JP: y_goal に値を代入する。
	y_goal = y_step - goal_height - padding * 4  # More space between step and goal

	# Draw rounded rectangle background for goal
	# EN: Assign value to padding_goal.
	# JP: padding_goal に値を代入する。
	padding_goal = 25  # Increased padding for goal
	# EN: Assign value to goal_bg_bbox.
	# JP: goal_bg_bbox に値を代入する。
	goal_bg_bbox = (
		x_goal - padding_goal,  # Remove extra space for logo
		y_goal - padding_goal,
		x_goal + goal_width + padding_goal,
		y_goal + goal_height + padding_goal,
	)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	draw.rounded_rectangle(
		goal_bg_bbox,
		radius=15,  # Add rounded corners
		fill=text_box_color,
	)

	# Draw goal text
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	draw.multiline_text(
		(x_goal, y_goal),
		wrapped_goal,
		font=title_font,
		fill=text_color,
		align='center',
	)

	# Add logo if provided (top right corner)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if logo:
		# EN: Assign value to logo_layer.
		# JP: logo_layer に値を代入する。
		logo_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
		# EN: Assign value to logo_margin.
		# JP: logo_margin に値を代入する。
		logo_margin = 20
		# EN: Assign value to logo_x.
		# JP: logo_x に値を代入する。
		logo_x = image.width - logo.width - logo_margin
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logo_layer.paste(logo, (logo_x, logo_margin), logo if logo.mode == 'RGBA' else None)
		# EN: Assign value to txt_layer.
		# JP: txt_layer に値を代入する。
		txt_layer = Image.alpha_composite(logo_layer, txt_layer)

	# Composite and convert
	# EN: Assign value to result.
	# JP: result に値を代入する。
	result = Image.alpha_composite(image, txt_layer)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return result.convert('RGB')


# EN: Define function `_wrap_text`.
# JP: 関数 `_wrap_text` を定義する。
def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Wrap text to fit within a given width.

	Args:
	    text: Text to wrap
	    font: Font to use for text
	    max_width: Maximum width in pixels

	Returns:
	    Wrapped text with newlines
	"""
	# EN: Assign value to text.
	# JP: text に値を代入する。
	text = decode_unicode_escapes_to_utf8(text)
	# EN: Assign value to words.
	# JP: words に値を代入する。
	words = text.split()
	# EN: Assign value to lines.
	# JP: lines に値を代入する。
	lines = []
	# EN: Assign value to current_line.
	# JP: current_line に値を代入する。
	current_line = []

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for word in words:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		current_line.append(word)
		# EN: Assign value to line.
		# JP: line に値を代入する。
		line = ' '.join(current_line)
		# EN: Assign value to bbox.
		# JP: bbox に値を代入する。
		bbox = font.getbbox(line)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if bbox[2] > max_width:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(current_line) == 1:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(current_line.pop())
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				current_line.pop()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(' '.join(current_line))
				# EN: Assign value to current_line.
				# JP: current_line に値を代入する。
				current_line = [word]

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if current_line:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append(' '.join(current_line))

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return '\n'.join(lines)

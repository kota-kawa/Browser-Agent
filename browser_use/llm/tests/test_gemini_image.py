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
import random

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from PIL import Image, ImageDraw, ImageFont

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.google.chat import ChatGoogle
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	BaseMessage,
	ContentPartImageParam,
	ContentPartTextParam,
	ImageURL,
	SystemMessage,
	UserMessage,
)


# EN: Define function `create_random_text_image`.
# JP: 関数 `create_random_text_image` を定義する。
def create_random_text_image(text: str = 'hello world', width: int = 4000, height: int = 4000) -> str:
	# Create image with random background color
	# EN: Assign value to bg_color.
	# JP: bg_color に値を代入する。
	bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
	# EN: Assign value to image.
	# JP: image に値を代入する。
	image = Image.new('RGB', (width, height), bg_color)
	# EN: Assign value to draw.
	# JP: draw に値を代入する。
	draw = ImageDraw.Draw(image)

	# Try to use a default font, fallback to default if not available
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to font.
		# JP: font に値を代入する。
		font = ImageFont.truetype('arial.ttf', 24)
	except Exception:
		# EN: Assign value to font.
		# JP: font に値を代入する。
		font = ImageFont.load_default()

	# Calculate text position to center it
	# EN: Assign value to bbox.
	# JP: bbox に値を代入する。
	bbox = draw.textbbox((0, 0), text, font=font)
	# EN: Assign value to text_width.
	# JP: text_width に値を代入する。
	text_width = bbox[2] - bbox[0]
	# EN: Assign value to text_height.
	# JP: text_height に値を代入する。
	text_height = bbox[3] - bbox[1]
	# EN: Assign value to x.
	# JP: x に値を代入する。
	x = (width - text_width) // 2
	# EN: Assign value to y.
	# JP: y に値を代入する。
	y = (height - text_height) // 2

	# Draw text with contrasting color
	# EN: Assign value to text_color.
	# JP: text_color に値を代入する。
	text_color = (255 - bg_color[0], 255 - bg_color[1], 255 - bg_color[2])
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	draw.text((x, y), text, fill=text_color, font=font)

	# Convert to base64
	# EN: Assign value to buffer.
	# JP: buffer に値を代入する。
	buffer = io.BytesIO()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	image.save(buffer, format='PNG')
	# EN: Assign value to img_data.
	# JP: img_data に値を代入する。
	img_data = base64.b64encode(buffer.getvalue()).decode()

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return f'data:image/png;base64,{img_data}'


# EN: Define async function `test_gemini_image_vision`.
# JP: 非同期関数 `test_gemini_image_vision` を定義する。
async def test_gemini_image_vision():
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Test Gemini's ability to see and describe images."""

	# Create the LLM
	# EN: Assign value to llm.
	# JP: llm に値を代入する。
	llm = ChatGoogle(model='gemini-2.5-flash-lite')

	# Create a random image with text
	# EN: Assign value to image_data_url.
	# JP: image_data_url に値を代入する。
	image_data_url = create_random_text_image('Hello Gemini! Can you see this text?')

	# Create messages with image
	# EN: Assign annotated value to messages.
	# JP: messages に型付きの値を代入する。
	messages: list[BaseMessage] = [
		SystemMessage(content='You are a helpful assistant that can see and describe images.'),
		UserMessage(
			content=[
				ContentPartTextParam(text='What do you see in this image? Please describe the text and any visual elements.'),
				ContentPartImageParam(image_url=ImageURL(url=image_data_url)),
			]
		),
	]

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('Testing Gemini image vision...')

	# Make the API call
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await llm.ainvoke(messages)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('\n=== Gemini Response ===')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(response.completion)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(response.usage)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('=======================')
	except Exception as e:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'Error calling Gemini: {e}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'Error type: {type(e)}')


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(test_gemini_image_vision())

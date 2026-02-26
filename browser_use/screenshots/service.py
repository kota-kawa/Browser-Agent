# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Screenshot storage service for browser-use agents.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import base64
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import anyio


# EN: Define class `ScreenshotService`.
# JP: クラス `ScreenshotService` を定義する。
class ScreenshotService:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Simple screenshot storage service that saves screenshots to disk"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, agent_directory: str | Path):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize with agent directory path"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.agent_directory = Path(agent_directory) if isinstance(agent_directory, str) else agent_directory

		# Create screenshots subdirectory
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.screenshots_dir = self.agent_directory / 'screenshots'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.screenshots_dir.mkdir(parents=True, exist_ok=True)

	# EN: Define async function `store_screenshot`.
	# JP: 非同期関数 `store_screenshot` を定義する。
	async def store_screenshot(self, screenshot_b64: str, step_number: int) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Store screenshot to disk and return the full path as string"""
		# EN: Assign value to screenshot_filename.
		# JP: screenshot_filename に値を代入する。
		screenshot_filename = f'step_{step_number}.png'
		# EN: Assign value to screenshot_path.
		# JP: screenshot_path に値を代入する。
		screenshot_path = self.screenshots_dir / screenshot_filename

		# Decode base64 and save to disk
		# EN: Assign value to screenshot_data.
		# JP: screenshot_data に値を代入する。
		screenshot_data = base64.b64decode(screenshot_b64)

		# EN: Execute async logic with managed resources.
		# JP: リソース管理付きで非同期処理を実行する。
		async with await anyio.open_file(screenshot_path, 'wb') as f:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await f.write(screenshot_data)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(screenshot_path)

	# EN: Define async function `get_screenshot`.
	# JP: 非同期関数 `get_screenshot` を定義する。
	async def get_screenshot(self, screenshot_path: str) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load screenshot from disk path and return as base64"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not screenshot_path:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to path.
		# JP: path に値を代入する。
		path = Path(screenshot_path)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not path.exists():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Load from disk and encode to base64
		# EN: Execute async logic with managed resources.
		# JP: リソース管理付きで非同期処理を実行する。
		async with await anyio.open_file(path, 'rb') as f:
			# EN: Assign value to screenshot_data.
			# JP: screenshot_data に値を代入する。
			screenshot_data = await f.read()

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return base64.b64encode(screenshot_data).decode('utf-8')

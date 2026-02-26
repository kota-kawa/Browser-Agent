# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Screenshot watchdog for handling screenshot requests using CDP."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, Any, ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.page import CaptureScreenshotParameters

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import ScreenshotEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `ScreenshotWatchdog`.
# JP: クラス `ScreenshotWatchdog` を定義する。
class ScreenshotWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Handles screenshot requests using CDP."""

	# Events this watchdog listens to
	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent[Any]]]] = [ScreenshotEvent]

	# Events this watchdog emits
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent[Any]]]] = []

	# EN: Define async function `on_ScreenshotEvent`.
	# JP: 非同期関数 `on_ScreenshotEvent` を定義する。
	async def on_ScreenshotEvent(self, event: ScreenshotEvent) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle screenshot request using CDP.

		Args:
			event: ScreenshotEvent with optional full_page and clip parameters

		Returns:
			Dict with 'screenshot' key containing base64-encoded screenshot or None
		"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('[ScreenshotWatchdog] Handler START - on_ScreenshotEvent called')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get CDP client and session for current target
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.get_or_create_cdp_session()

			# Prepare screenshot parameters
			# EN: Assign value to params.
			# JP: params に値を代入する。
			params = CaptureScreenshotParameters(format='png', captureBeyondViewport=False)

			# Take screenshot using CDP
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[ScreenshotWatchdog] Taking screenshot with params: {params}')
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await cdp_session.cdp_client.send.Page.captureScreenshot(params=params, session_id=cdp_session.session_id)

			# Return base64-encoded screenshot data
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if result and 'data' in result:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('[ScreenshotWatchdog] Screenshot captured successfully')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return result['data']

			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise BrowserError('[ScreenshotWatchdog] Screenshot result missing data')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[ScreenshotWatchdog] Screenshot failed: {e}')
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise
		finally:
			# Try to remove highlights even on failure
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.browser_session.remove_highlights()
			except Exception:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass

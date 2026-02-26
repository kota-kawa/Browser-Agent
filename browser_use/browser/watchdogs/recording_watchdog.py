# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Recording Watchdog for Browser Use Sessions."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.page.events import ScreencastFrameEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import BrowserConnectedEvent, BrowserStopEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.profile import ViewportSize
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.video_recorder import VideoRecorderService
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog


# EN: Define class `RecordingWatchdog`.
# JP: クラス `RecordingWatchdog` を定義する。
class RecordingWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Manages video recording of a browser session using CDP screencasting.
	"""

	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [BrowserConnectedEvent, BrowserStopEvent]
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent]]] = []

	# EN: Assign annotated value to _recorder.
	# JP: _recorder に型付きの値を代入する。
	_recorder: VideoRecorderService | None = None

	# EN: Define async function `on_BrowserConnectedEvent`.
	# JP: 非同期関数 `on_BrowserConnectedEvent` を定義する。
	async def on_BrowserConnectedEvent(self, event: BrowserConnectedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Starts video recording if it is configured in the browser profile.
		"""
		# EN: Assign value to profile.
		# JP: profile に値を代入する。
		profile = self.browser_session.browser_profile
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not profile.record_video_dir:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Dynamically determine video size
		# EN: Assign value to size.
		# JP: size に値を代入する。
		size = profile.record_video_size
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not size:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('record_video_size not specified, detecting viewport size...')
			# EN: Assign value to size.
			# JP: size に値を代入する。
			size = await self._get_current_viewport_size()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not size:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('Cannot start video recording: viewport size could not be determined.')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to video_format.
		# JP: video_format に値を代入する。
		video_format = getattr(profile, 'record_video_format', 'mp4').strip('.')
		# EN: Assign value to output_path.
		# JP: output_path に値を代入する。
		output_path = Path(profile.record_video_dir) / f'{uuid7str()}.{video_format}'

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'Initializing video recorder for format: {video_format}')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._recorder = VideoRecorderService(output_path=output_path, size=size, framerate=profile.record_video_framerate)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._recorder.start()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._recorder._is_active:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._recorder = None
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.browser_session.cdp_client.register.Page.screencastFrame(self.on_screencastFrame)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.get_or_create_cdp_session()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.cdp_client.send.Page.startScreencast(
				params={
					'format': 'png',
					'quality': 90,
					'maxWidth': size['width'],
					'maxHeight': size['height'],
					'everyNthFrame': 1,
				},
				session_id=cdp_session.session_id,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.info(f'📹 Started video recording to {output_path}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'Failed to start screencast via CDP: {e}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._recorder:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._recorder.stop_and_save()
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._recorder = None

	# EN: Define async function `_get_current_viewport_size`.
	# JP: 非同期関数 `_get_current_viewport_size` を定義する。
	async def _get_current_viewport_size(self) -> ViewportSize | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Gets the current viewport size directly from the browser via CDP."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.get_or_create_cdp_session()
			# EN: Assign value to metrics.
			# JP: metrics に値を代入する。
			metrics = await cdp_session.cdp_client.send.Page.getLayoutMetrics(session_id=cdp_session.session_id)

			# Use cssVisualViewport for the most accurate representation of the visible area
			# EN: Assign value to viewport.
			# JP: viewport に値を代入する。
			viewport = metrics.get('cssVisualViewport', {})
			# EN: Assign value to width.
			# JP: width に値を代入する。
			width = viewport.get('clientWidth')
			# EN: Assign value to height.
			# JP: height に値を代入する。
			height = viewport.get('clientHeight')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if width and height:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'Detected viewport size: {width}x{height}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ViewportSize(width=int(width), height=int(height))
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'Failed to get viewport size from browser: {e}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `on_screencastFrame`.
	# JP: 関数 `on_screencastFrame` を定義する。
	def on_screencastFrame(self, event: ScreencastFrameEvent, session_id: str | None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Synchronous handler for incoming screencast frames.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._recorder:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._recorder.add_frame(event['data'])
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		asyncio.create_task(self._ack_screencast_frame(event, session_id))

	# EN: Define async function `_ack_screencast_frame`.
	# JP: 非同期関数 `_ack_screencast_frame` を定義する。
	async def _ack_screencast_frame(self, event: ScreencastFrameEvent, session_id: str | None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Asynchronously acknowledges a screencast frame.
		"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.browser_session.cdp_client.send.Page.screencastFrameAck(
				params={'sessionId': event['sessionId']}, session_id=session_id
			)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Failed to acknowledge screencast frame: {e}')

	# EN: Define async function `on_BrowserStopEvent`.
	# JP: 非同期関数 `on_BrowserStopEvent` を定義する。
	async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Stops the video recording and finalizes the video file.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._recorder:
			# EN: Assign value to recorder.
			# JP: recorder に値を代入する。
			recorder = self._recorder
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._recorder = None

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('Stopping video recording and saving file...')
			# EN: Assign value to loop.
			# JP: loop に値を代入する。
			loop = asyncio.get_event_loop()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await loop.run_in_executor(None, recorder.stop_and_save)

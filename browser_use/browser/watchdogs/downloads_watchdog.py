# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Downloads watchdog for monitoring and handling file downloads."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import tempfile
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, Any, ClassVar
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.parse import urlparse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import anyio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.browser import DownloadProgressEvent, DownloadWillBeginEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.target import SessionID, TargetID
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import PrivateAttr

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	BrowserLaunchEvent,
	BrowserStateRequestEvent,
	BrowserStoppedEvent,
	FileDownloadedEvent,
	NavigationCompleteEvent,
	TabClosedEvent,
	TabCreatedEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `DownloadsWatchdog`.
# JP: クラス `DownloadsWatchdog` を定義する。
class DownloadsWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Monitors downloads and handles file download events."""

	# Events this watchdog listens to (for documentation)
	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent[Any]]]] = [
		BrowserLaunchEvent,
		BrowserStateRequestEvent,
		BrowserStoppedEvent,
		TabCreatedEvent,
		TabClosedEvent,
		NavigationCompleteEvent,
	]

	# Events this watchdog emits
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent[Any]]]] = [
		FileDownloadedEvent,
	]

	# Private state
	# EN: Assign annotated value to _sessions_with_listeners.
	# JP: _sessions_with_listeners に型付きの値を代入する。
	_sessions_with_listeners: set[str] = PrivateAttr(default_factory=set)  # Track sessions that already have download listeners
	# EN: Assign annotated value to _active_downloads.
	# JP: _active_downloads に型付きの値を代入する。
	_active_downloads: dict[str, Any] = PrivateAttr(default_factory=dict)
	# EN: Assign annotated value to _pdf_viewer_cache.
	# JP: _pdf_viewer_cache に型付きの値を代入する。
	_pdf_viewer_cache: dict[str, bool] = PrivateAttr(default_factory=dict)  # Cache PDF viewer status by target URL
	# EN: Assign annotated value to _download_cdp_session_setup.
	# JP: _download_cdp_session_setup に型付きの値を代入する。
	_download_cdp_session_setup: bool = PrivateAttr(default=False)  # Track if CDP session is set up
	# EN: Assign annotated value to _download_cdp_session.
	# JP: _download_cdp_session に型付きの値を代入する。
	_download_cdp_session: Any = PrivateAttr(default=None)  # Store CDP session reference
	# EN: Assign annotated value to _cdp_event_tasks.
	# JP: _cdp_event_tasks に型付きの値を代入する。
	_cdp_event_tasks: set[asyncio.Task] = PrivateAttr(default_factory=set)  # Track CDP event handler tasks
	# EN: Assign annotated value to _cdp_downloads_info.
	# JP: _cdp_downloads_info に型付きの値を代入する。
	_cdp_downloads_info: dict[str, dict[str, Any]] = PrivateAttr(default_factory=dict)  # Map guid -> info
	# EN: Assign annotated value to _use_js_fetch_for_local.
	# JP: _use_js_fetch_for_local に型付きの値を代入する。
	_use_js_fetch_for_local: bool = PrivateAttr(default=False)  # Guard JS fetch path for local regular downloads

	# EN: Define async function `on_BrowserLaunchEvent`.
	# JP: 非同期関数 `on_BrowserLaunchEvent` を定義する。
	async def on_BrowserLaunchEvent(self, event: BrowserLaunchEvent) -> None:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[DownloadsWatchdog] Received BrowserLaunchEvent, EventBus ID: {id(self.event_bus)}')
		# Ensure downloads directory exists
		# EN: Assign value to downloads_path.
		# JP: downloads_path に値を代入する。
		downloads_path = self.browser_session.browser_profile.downloads_path
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if downloads_path:
			# EN: Assign value to expanded_path.
			# JP: expanded_path に値を代入する。
			expanded_path = Path(downloads_path).expanduser().resolve()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			expanded_path.mkdir(parents=True, exist_ok=True)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Ensured downloads directory exists: {expanded_path}')

	# EN: Define async function `on_TabCreatedEvent`.
	# JP: 非同期関数 `on_TabCreatedEvent` を定義する。
	async def on_TabCreatedEvent(self, event: TabCreatedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Monitor new tabs for downloads."""
		# logger.info(f'[DownloadsWatchdog] TabCreatedEvent received for tab {event.target_id[-4:]}: {event.url}')

		# Assert downloads path is configured (should always be set by BrowserProfile default)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session.browser_profile.downloads_path is not None, 'Downloads path must be configured'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.target_id:
			# logger.info(f'[DownloadsWatchdog] Found target for tab {event.target_id}, calling attach_to_target')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.attach_to_target(event.target_id)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'[DownloadsWatchdog] No target found for tab {event.target_id}')

	# EN: Define async function `on_TabClosedEvent`.
	# JP: 非同期関数 `on_TabClosedEvent` を定義する。
	async def on_TabClosedEvent(self, event: TabClosedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Stop monitoring closed tabs."""
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass  # No cleanup needed, browser context handles target lifecycle

	# EN: Define async function `on_BrowserStateRequestEvent`.
	# JP: 非同期関数 `on_BrowserStateRequestEvent` を定義する。
	async def on_BrowserStateRequestEvent(self, event: BrowserStateRequestEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle browser state request events."""
		# EN: Assign value to cdp_session.
		# JP: cdp_session に値を代入する。
		cdp_session = self.browser_session.agent_focus
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not cdp_session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = await self.browser_session.get_current_page_url()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to target_id.
		# JP: target_id に値を代入する。
		target_id = cdp_session.target_id
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.event_bus.dispatch(
			NavigationCompleteEvent(
				event_type='NavigationCompleteEvent',
				url=url,
				target_id=target_id,
				event_parent_id=event.event_id,
			)
		)

	# EN: Define async function `on_BrowserStoppedEvent`.
	# JP: 非同期関数 `on_BrowserStoppedEvent` を定義する。
	async def on_BrowserStoppedEvent(self, event: BrowserStoppedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clean up when browser stops."""
		# Cancel all CDP event handler tasks
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for task in list(self._cdp_event_tasks):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not task.done():
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				task.cancel()
		# Wait for all tasks to complete cancellation
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._cdp_event_tasks:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.gather(*self._cdp_event_tasks, return_exceptions=True)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._cdp_event_tasks.clear()

		# Clean up CDP session
		# CDP sessions are now cached and managed by BrowserSession
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._download_cdp_session = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._download_cdp_session_setup = False

		# Clear other state
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._sessions_with_listeners.clear()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._active_downloads.clear()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._pdf_viewer_cache.clear()

	# EN: Define async function `on_NavigationCompleteEvent`.
	# JP: 非同期関数 `on_NavigationCompleteEvent` を定義する。
	async def on_NavigationCompleteEvent(self, event: NavigationCompleteEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check for PDFs after navigation completes."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[DownloadsWatchdog] NavigationCompleteEvent received for {event.url}, tab #{event.target_id[-4:]}')

		# Clear PDF cache for the navigated URL since content may have changed
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if event.url in self._pdf_viewer_cache:
			# EN: Delete referenced values.
			# JP: 参照される値を削除する。
			del self._pdf_viewer_cache[event.url]

		# Check if auto-download is enabled
		# EN: Assign value to auto_download_enabled.
		# JP: auto_download_enabled に値を代入する。
		auto_download_enabled = self._is_auto_download_enabled()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not auto_download_enabled:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# Note: Using network-based PDF detection that doesn't require JavaScript

		# EN: Assign value to target_id.
		# JP: target_id に値を代入する。
		target_id = event.target_id
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[DownloadsWatchdog] Got target_id={target_id} for tab #{event.target_id[-4:]}')

		# EN: Assign value to is_pdf.
		# JP: is_pdf に値を代入する。
		is_pdf = await self.check_for_pdf_viewer(target_id)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_pdf:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] 📄 PDF detected at {event.url}, triggering auto-download...')
			# EN: Assign value to download_path.
			# JP: download_path に値を代入する。
			download_path = await self.trigger_pdf_download(target_id)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not download_path:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'[DownloadsWatchdog] ⚠️ PDF download failed for {event.url}')

	# EN: Define function `_is_auto_download_enabled`.
	# JP: 関数 `_is_auto_download_enabled` を定義する。
	def _is_auto_download_enabled(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if auto-download PDFs is enabled in browser profile."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.browser_session.browser_profile.auto_download_pdfs

	# EN: Define async function `attach_to_target`.
	# JP: 非同期関数 `attach_to_target` を定義する。
	async def attach_to_target(self, target_id: TargetID) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set up download monitoring for a specific target."""

		# Define CDP event handlers outside of try to avoid indentation/scope issues
		# EN: Define async function `download_will_begin_handler`.
		# JP: 非同期関数 `download_will_begin_handler` を定義する。
		async def download_will_begin_handler(event: DownloadWillBeginEvent, session_id: SessionID | None):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Download will begin: {event}')
			# Cache info for later completion event handling (esp. remote browsers)
			# EN: Assign value to guid.
			# JP: guid に値を代入する。
			guid = event.get('guid', '')
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to suggested_filename.
				# JP: suggested_filename に値を代入する。
				suggested_filename = event.get('suggestedFilename')
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert suggested_filename, 'CDP DownloadWillBegin missing suggestedFilename'
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._cdp_downloads_info[guid] = {
					'url': event.get('url', ''),
					'suggested_filename': suggested_filename,
					'handled': False,
				}
			except (AssertionError, KeyError):
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass
			# Create and track the task
			# EN: Assign value to task.
			# JP: task に値を代入する。
			task = asyncio.create_task(self._handle_cdp_download(event, target_id, session_id))
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._cdp_event_tasks.add(task)
			# Remove from set when done
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			task.add_done_callback(lambda t: self._cdp_event_tasks.discard(t))

		# EN: Define async function `download_progress_handler`.
		# JP: 非同期関数 `download_progress_handler` を定義する。
		async def download_progress_handler(event: DownloadProgressEvent, session_id: SessionID | None):
			# Check if download is complete
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if event.get('state') == 'completed':
				# EN: Assign value to file_path.
				# JP: file_path に値を代入する。
				file_path = event.get('filePath')
				# EN: Assign value to guid.
				# JP: guid に値を代入する。
				guid = event.get('guid', '')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.browser_session.is_local:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if file_path:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'[DownloadsWatchdog] Download completed: {file_path}')
						# Track the download
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self._track_download(file_path)
						# Mark as handled to prevent fallback duplicate dispatch
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if guid in self._cdp_downloads_info:
								# EN: Assign value to target variable.
								# JP: target variable に値を代入する。
								self._cdp_downloads_info[guid]['handled'] = True
						except (KeyError, AttributeError):
							# EN: Keep a placeholder statement.
							# JP: プレースホルダー文を維持する。
							pass
					else:
						# No local file path provided, local polling in _handle_cdp_download will handle it
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(
							'[DownloadsWatchdog] No filePath in progress event (local); polling will handle detection'
						)
				else:
					# Remote browser: do not touch local filesystem. Fallback to downloadPath+suggestedFilename
					# EN: Assign value to info.
					# JP: info に値を代入する。
					info = self._cdp_downloads_info.get(guid, {})
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to suggested_filename.
						# JP: suggested_filename に値を代入する。
						suggested_filename = info.get('suggested_filename') or (Path(file_path).name if file_path else 'download')
						# EN: Assign value to downloads_path.
						# JP: downloads_path に値を代入する。
						downloads_path = str(self.browser_session.browser_profile.downloads_path or '')
						# EN: Assign value to effective_path.
						# JP: effective_path に値を代入する。
						effective_path = file_path or str(Path(downloads_path) / suggested_filename)
						# EN: Assign value to file_name.
						# JP: file_name に値を代入する。
						file_name = Path(effective_path).name
						# EN: Assign value to file_ext.
						# JP: file_ext に値を代入する。
						file_ext = Path(file_name).suffix.lower().lstrip('.')
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.event_bus.dispatch(
							FileDownloadedEvent(
								url=info.get('url', ''),
								path=str(effective_path),
								file_name=file_name,
								file_size=0,
								file_type=file_ext if file_ext else None,
							)
						)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'[DownloadsWatchdog] ✅ (remote) Download completed: {effective_path}')
					finally:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if guid in self._cdp_downloads_info:
							# EN: Delete referenced values.
							# JP: 参照される値を削除する。
							del self._cdp_downloads_info[guid]

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to downloads_path_raw.
			# JP: downloads_path_raw に値を代入する。
			downloads_path_raw = self.browser_session.browser_profile.downloads_path
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not downloads_path_raw:
				# logger.info(f'[DownloadsWatchdog] No downloads path configured, skipping target: {target_id}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return  # No downloads path configured

			# Check if we already have a download listener on this session
			# to prevent duplicate listeners from being added
			# Note: Since download listeners are set up once per browser session, not per target,
			# we just track if we've set up the browser-level listener
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._download_cdp_session_setup:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('[DownloadsWatchdog] Download listener already set up for browser session')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# logger.debug(f'[DownloadsWatchdog] Setting up CDP download listener for target: {target_id}')

			# Use CDP session for download events but store reference in watchdog
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self._download_cdp_session_setup:
				# Set up CDP session for downloads (only once per browser session)
				# EN: Assign value to cdp_client.
				# JP: cdp_client に値を代入する。
				cdp_client = self.browser_session.cdp_client

				# Set download behavior to allow downloads and enable events
				# EN: Assign value to downloads_path.
				# JP: downloads_path に値を代入する。
				downloads_path = self.browser_session.browser_profile.downloads_path
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not downloads_path:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning('[DownloadsWatchdog] No downloads path configured, skipping CDP download setup')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return
				# Ensure path is properly expanded (~ -> absolute path)
				# EN: Assign value to expanded_downloads_path.
				# JP: expanded_downloads_path に値を代入する。
				expanded_downloads_path = Path(downloads_path).expanduser().resolve()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await cdp_client.send.Browser.setDownloadBehavior(
					params={
						'behavior': 'allow',
						'downloadPath': str(expanded_downloads_path),  # Use expanded absolute path
						'eventsEnabled': True,
					}
				)

				# Register the handlers with CDP
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				cdp_client.register.Browser.downloadWillBegin(download_will_begin_handler)  # type: ignore[arg-type]
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				cdp_client.register.Browser.downloadProgress(download_progress_handler)  # type: ignore[arg-type]

				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._download_cdp_session_setup = True
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('[DownloadsWatchdog] Set up CDP download listeners')

			# No need to track individual targets since download listener is browser-level
			# logger.debug(f'[DownloadsWatchdog] Successfully set up CDP download listener for target: {target_id}')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'[DownloadsWatchdog] Failed to set up CDP download listener for target {target_id}: {e}')

	# EN: Define function `_track_download`.
	# JP: 関数 `_track_download` を定義する。
	def _track_download(self, file_path: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Track a completed download and dispatch the appropriate event.

		Args:
			file_path: The path to the downloaded file
		"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get file info
			# EN: Assign value to path.
			# JP: path に値を代入する。
			path = Path(file_path)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if path.exists():
				# EN: Assign value to file_size.
				# JP: file_size に値を代入する。
				file_size = path.stat().st_size
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] Tracked download: {path.name} ({file_size} bytes)')

				# Dispatch download event
				# EN: Import required modules.
				# JP: 必要なモジュールをインポートする。
				from browser_use.browser.events import FileDownloadedEvent

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.event_bus.dispatch(
					FileDownloadedEvent(
						url=str(path),  # Use the file path as URL for local files
						path=str(path),
						file_name=path.name,
						file_size=file_size,
					)
				)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'[DownloadsWatchdog] Downloaded file not found: {file_path}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[DownloadsWatchdog] Error tracking download: {e}')

	# EN: Define async function `_handle_cdp_download`.
	# JP: 非同期関数 `_handle_cdp_download` を定義する。
	async def _handle_cdp_download(
		self, event: DownloadWillBeginEvent, target_id: TargetID, session_id: SessionID | None
	) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle a CDP Page.downloadWillBegin event."""
		# EN: Assign value to downloads_dir.
		# JP: downloads_dir に値を代入する。
		downloads_dir = (
			Path(
				self.browser_session.browser_profile.downloads_path
				or f'{tempfile.gettempdir()}/browser_use_downloads.{str(self.browser_session.id)[-4:]}'
			)
			.expanduser()
			.resolve()
		)  # Ensure path is properly expanded

		# Initialize variables that may be used outside try blocks
		# EN: Assign value to unique_filename.
		# JP: unique_filename に値を代入する。
		unique_filename = None
		# EN: Assign value to file_size.
		# JP: file_size に値を代入する。
		file_size = 0
		# EN: Assign value to expected_path.
		# JP: expected_path に値を代入する。
		expected_path = None
		# EN: Assign value to download_result.
		# JP: download_result に値を代入する。
		download_result = None
		# EN: Assign value to download_url.
		# JP: download_url に値を代入する。
		download_url = event.get('url', '')
		# EN: Assign value to suggested_filename.
		# JP: suggested_filename に値を代入する。
		suggested_filename = event.get('suggestedFilename', 'download')
		# EN: Assign value to guid.
		# JP: guid に値を代入する。
		guid = event.get('guid', '')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] ⬇️ File download starting: {suggested_filename} from {download_url[:100]}...')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Full CDP event: {event}')

			# Since Browser.setDownloadBehavior is already configured, the browser will download the file
			# We just need to wait for it to appear in the downloads directory
			# EN: Assign value to expected_path.
			# JP: expected_path に値を代入する。
			expected_path = downloads_dir / suggested_filename

			# Debug: List current directory contents
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Downloads directory: {downloads_dir}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if downloads_dir.exists():
				# EN: Assign value to files_before.
				# JP: files_before に値を代入する。
				files_before = list(downloads_dir.iterdir())
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] Files before download: {[f.name for f in files_before]}')

			# Try manual JavaScript fetch as a fallback for local browsers (disabled for regular local downloads)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session.is_local and self._use_js_fetch_for_local:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] Attempting JS fetch fallback for {download_url}')

				# EN: Assign value to unique_filename.
				# JP: unique_filename に値を代入する。
				unique_filename = None
				# EN: Assign value to file_size.
				# JP: file_size に値を代入する。
				file_size = None
				# EN: Assign value to download_result.
				# JP: download_result に値を代入する。
				download_result = None
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# Escape the URL for JavaScript
					# EN: Import required modules.
					# JP: 必要なモジュールをインポートする。
					import json

					# EN: Assign value to escaped_url.
					# JP: escaped_url に値を代入する。
					escaped_url = json.dumps(download_url)

					# Get the proper session for the frame that initiated the download
					# EN: Assign value to cdp_session.
					# JP: cdp_session に値を代入する。
					cdp_session = await self.browser_session.cdp_client_for_frame(event.get('frameId'))
					# EN: Validate a required condition.
					# JP: 必須条件を検証する。
					assert cdp_session

					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = await cdp_session.cdp_client.send.Runtime.evaluate(
						params={
							'expression': f"""
						(async () => {{
							try {{
								const response = await fetch({escaped_url});
								if (!response.ok) {{
									throw new Error(`HTTP error! status: ${{response.status}}`);
								}}
								const blob = await response.blob();
								const arrayBuffer = await blob.arrayBuffer();
								const uint8Array = new Uint8Array(arrayBuffer);
								return {{
									data: Array.from(uint8Array),
									size: uint8Array.length,
									contentType: response.headers.get('content-type') || 'application/octet-stream'
								}};
							}} catch (error) {{
								throw new Error(`Fetch failed: ${{error.message}}`);
							}}
						}})()
						""",
							'awaitPromise': True,
							'returnByValue': True,
						},
						session_id=cdp_session.session_id,
					)
					# EN: Assign value to download_result.
					# JP: download_result に値を代入する。
					download_result = result.get('result', {}).get('value')

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if download_result and download_result.get('data'):
						# Save the file
						# EN: Assign value to file_data.
						# JP: file_data に値を代入する。
						file_data = bytes(download_result['data'])
						# EN: Assign value to file_size.
						# JP: file_size に値を代入する。
						file_size = len(file_data)

						# Ensure unique filename
						# EN: Assign value to unique_filename.
						# JP: unique_filename に値を代入する。
						unique_filename = await self._get_unique_filename(str(downloads_dir), suggested_filename)
						# EN: Assign value to final_path.
						# JP: final_path に値を代入する。
						final_path = downloads_dir / unique_filename

						# Write the file
						# EN: Import required modules.
						# JP: 必要なモジュールをインポートする。
						import anyio

						# EN: Execute async logic with managed resources.
						# JP: リソース管理付きで非同期処理を実行する。
						async with await anyio.open_file(final_path, 'wb') as f:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await f.write(file_data)

						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'[DownloadsWatchdog] ✅ Downloaded and saved file: {final_path} ({file_size} bytes)')
						# EN: Assign value to expected_path.
						# JP: expected_path に値を代入する。
						expected_path = final_path
						# Emit download event immediately
						# EN: Assign value to file_ext.
						# JP: file_ext に値を代入する。
						file_ext = expected_path.suffix.lower().lstrip('.')
						# EN: Assign value to file_type.
						# JP: file_type に値を代入する。
						file_type = file_ext if file_ext else None
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.event_bus.dispatch(
							FileDownloadedEvent(
								url=download_url,
								path=str(expected_path),
								file_name=unique_filename or expected_path.name,
								file_size=file_size or 0,
								file_type=file_type,
								mime_type=(download_result.get('contentType') if download_result else None),
								from_cache=False,
								auto_download=False,
							)
						)
						# Mark as handled to prevent duplicate dispatch from progress/polling paths
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if guid in self._cdp_downloads_info:
								# EN: Assign value to target variable.
								# JP: target variable に値を代入する。
								self._cdp_downloads_info[guid]['handled'] = True
						except (KeyError, AttributeError):
							# EN: Keep a placeholder statement.
							# JP: プレースホルダー文を維持する。
							pass
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(
							f'[DownloadsWatchdog] ✅ File download completed via CDP: {suggested_filename} ({file_size} bytes) saved to {expected_path}'
						)
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.error('[DownloadsWatchdog] ❌ No data received from fetch')

				except Exception as fetch_error:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'[DownloadsWatchdog] ❌ Failed to download file via fetch: {fetch_error}')

			# For remote browsers, don't poll local filesystem; downloadProgress handler will emit the event
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.browser_session.is_local:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[DownloadsWatchdog] ❌ Error handling CDP download: {type(e).__name__} {e}')

		# If we reach here, the fetch method failed, so wait for native download
		# Poll the downloads directory for new files
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[DownloadsWatchdog] Checking if browser auto-download saved the file for us: {suggested_filename}')

		# Get initial list of files in downloads directory
		# EN: Assign value to initial_files.
		# JP: initial_files に値を代入する。
		initial_files = set()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if Path(downloads_dir).exists():
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for f in Path(downloads_dir).iterdir():
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if f.is_file() and not f.name.startswith('.'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					initial_files.add(f.name)

		# Poll for new files
		# EN: Assign value to max_wait.
		# JP: max_wait に値を代入する。
		max_wait = 20  # seconds
		# EN: Assign value to start_time.
		# JP: start_time に値を代入する。
		start_time = asyncio.get_event_loop().time()

		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while asyncio.get_event_loop().time() - start_time < max_wait:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.sleep(5.0)  # Check every 5 seconds

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if Path(downloads_dir).exists():
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for file_path in Path(downloads_dir).iterdir():
					# Skip hidden files and files that were already there
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if file_path.is_file() and not file_path.name.startswith('.') and file_path.name not in initial_files:
						# Check if file has content (> 4 bytes)
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Assign value to file_size.
							# JP: file_size に値を代入する。
							file_size = file_path.stat().st_size
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if file_size > 4:
								# Found a new download!
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								self.logger.debug(
									f'[DownloadsWatchdog] ✅ Found downloaded file: {file_path} ({file_size} bytes)'
								)

								# Determine file type from extension
								# EN: Assign value to file_ext.
								# JP: file_ext に値を代入する。
								file_ext = file_path.suffix.lower().lstrip('.')
								# EN: Assign value to file_type.
								# JP: file_type に値を代入する。
								file_type = file_ext if file_ext else None

								# Dispatch download event
								# Skip if already handled by progress/JS fetch
								# EN: Assign value to info.
								# JP: info に値を代入する。
								info = self._cdp_downloads_info.get(guid, {})
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if info.get('handled'):
									# EN: Return a value from the function.
									# JP: 関数から値を返す。
									return
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								self.event_bus.dispatch(
									FileDownloadedEvent(
										url=download_url,
										path=str(file_path),
										file_name=file_path.name,
										file_size=file_size,
										file_type=file_type,
									)
								)
								# Mark as handled after dispatch
								# EN: Handle exceptions around this block.
								# JP: このブロックで例外処理を行う。
								try:
									# EN: Branch logic based on a condition.
									# JP: 条件に応じて処理を分岐する。
									if guid in self._cdp_downloads_info:
										# EN: Assign value to target variable.
										# JP: target variable に値を代入する。
										self._cdp_downloads_info[guid]['handled'] = True
								except (KeyError, AttributeError):
									# EN: Keep a placeholder statement.
									# JP: プレースホルダー文を維持する。
									pass
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return
						except Exception as e:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug(f'[DownloadsWatchdog] Error checking file {file_path}: {e}')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.warning(f'[DownloadsWatchdog] Download did not complete within {max_wait} seconds')

	# EN: Define async function `_handle_download`.
	# JP: 非同期関数 `_handle_download` を定義する。
	async def _handle_download(self, download: Any) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle a download event."""
		# EN: Assign value to download_id.
		# JP: download_id に値を代入する。
		download_id = f'{id(download)}'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._active_downloads[download_id] = download
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[DownloadsWatchdog] ⬇️ Handling download: {download.suggested_filename} from {download.url[:100]}...')

		# Debug: Check if download is already being handled elsewhere
		# EN: Assign value to failure.
		# JP: failure に値を代入する。
		failure = (
			await download.failure()
		)  # TODO: it always fails for some reason, figure out why connect_over_cdp makes accept_downloads not work
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.warning(f'[DownloadsWatchdog] ❌ Download state - canceled: {failure}, url: {download.url}')
		# logger.info(f'[DownloadsWatchdog] Active downloads count: {len(self._active_downloads)}')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to current_step.
			# JP: current_step に値を代入する。
			current_step = 'getting_download_info'
			# Get download info immediately
			# EN: Assign value to url.
			# JP: url に値を代入する。
			url = download.url
			# EN: Assign value to suggested_filename.
			# JP: suggested_filename に値を代入する。
			suggested_filename = download.suggested_filename

			# EN: Assign value to current_step.
			# JP: current_step に値を代入する。
			current_step = 'determining_download_directory'
			# Determine download directory from browser profile
			# EN: Assign value to downloads_dir.
			# JP: downloads_dir に値を代入する。
			downloads_dir = self.browser_session.browser_profile.downloads_path
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not downloads_dir:
				# EN: Assign value to downloads_dir.
				# JP: downloads_dir に値を代入する。
				downloads_dir = str(Path.home() / 'Downloads')
			else:
				# EN: Assign value to downloads_dir.
				# JP: downloads_dir に値を代入する。
				downloads_dir = str(downloads_dir)  # Ensure it's a string

			# Check if Playwright already auto-downloaded the file (due to CDP setup)
			# EN: Assign value to original_path.
			# JP: original_path に値を代入する。
			original_path = Path(downloads_dir) / suggested_filename
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if original_path.exists() and original_path.stat().st_size > 0:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'[DownloadsWatchdog] File already downloaded by Playwright: {original_path} ({original_path.stat().st_size} bytes)'
				)

				# Use the existing file instead of creating a duplicate
				# EN: Assign value to download_path.
				# JP: download_path に値を代入する。
				download_path = original_path
				# EN: Assign value to file_size.
				# JP: file_size に値を代入する。
				file_size = original_path.stat().st_size
				# EN: Assign value to unique_filename.
				# JP: unique_filename に値を代入する。
				unique_filename = suggested_filename
			else:
				# EN: Assign value to current_step.
				# JP: current_step に値を代入する。
				current_step = 'generating_unique_filename'
				# Ensure unique filename
				# EN: Assign value to unique_filename.
				# JP: unique_filename に値を代入する。
				unique_filename = await self._get_unique_filename(downloads_dir, suggested_filename)
				# EN: Assign value to download_path.
				# JP: download_path に値を代入する。
				download_path = Path(downloads_dir) / unique_filename

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] Download started: {unique_filename} from {url[:100]}...')

				# EN: Assign value to current_step.
				# JP: current_step に値を代入する。
				current_step = 'calling_save_as'
				# Save the download using Playwright's save_as method
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] Saving download to: {download_path}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] Download path exists: {download_path.parent.exists()}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] Download path writable: {os.access(download_path.parent, os.W_OK)}')

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('[DownloadsWatchdog] About to call download.save_as()...')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await download.save_as(str(download_path))
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'[DownloadsWatchdog] Successfully saved download to: {download_path}')
					# EN: Assign value to current_step.
					# JP: current_step に値を代入する。
					current_step = 'save_as_completed'
				except Exception as save_error:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'[DownloadsWatchdog] save_as() failed with error: {save_error}')
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise save_error

				# Get file info
				# EN: Assign value to file_size.
				# JP: file_size に値を代入する。
				file_size = download_path.stat().st_size if download_path.exists() else 0

			# Determine file type from extension
			# EN: Assign value to file_ext.
			# JP: file_ext に値を代入する。
			file_ext = download_path.suffix.lower().lstrip('.')
			# EN: Assign value to file_type.
			# JP: file_type に値を代入する。
			file_type = file_ext if file_ext else None

			# Try to get MIME type from response headers if available
			# EN: Assign value to mime_type.
			# JP: mime_type に値を代入する。
			mime_type = None
			# Note: Playwright doesn't expose response headers directly from Download object

			# Check if this was a PDF auto-download
			# EN: Assign value to auto_download.
			# JP: auto_download に値を代入する。
			auto_download = False
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if file_type == 'pdf':
				# EN: Assign value to auto_download.
				# JP: auto_download に値を代入する。
				auto_download = self._is_auto_download_enabled()

			# Emit download event
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				FileDownloadedEvent(
					url=url,
					path=str(download_path),
					file_name=suggested_filename,
					file_size=file_size,
					file_type=file_type,
					mime_type=mime_type,
					from_cache=False,
					auto_download=auto_download,
				)
			)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'[DownloadsWatchdog] ✅ Download completed: {suggested_filename} ({file_size} bytes) saved to {download_path}'
			)

			# File is now tracked on filesystem, no need to track in memory

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(
				f'[DownloadsWatchdog] Error handling download at step "{locals().get("current_step", "unknown")}", error: {e}'
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(
				f'[DownloadsWatchdog] Download state - URL: {download.url}, filename: {download.suggested_filename}'
			)
		finally:
			# Clean up tracking
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if download_id in self._active_downloads:
				# EN: Delete referenced values.
				# JP: 参照される値を削除する。
				del self._active_downloads[download_id]

	# EN: Define async function `check_for_pdf_viewer`.
	# JP: 非同期関数 `check_for_pdf_viewer` を定義する。
	async def check_for_pdf_viewer(self, target_id: TargetID) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if the current target is a PDF using network-based detection.

		This method avoids JavaScript execution that can crash WebSocket connections.
		Returns True if a PDF is detected and should be downloaded.
		"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[DownloadsWatchdog] Checking if target {target_id} is PDF viewer...')

		# Get target info to get URL
		# EN: Assign value to cdp_client.
		# JP: cdp_client に値を代入する。
		cdp_client = self.browser_session.cdp_client
		# EN: Assign value to targets.
		# JP: targets に値を代入する。
		targets = await cdp_client.send.Target.getTargets()
		# EN: Assign value to target_info.
		# JP: target_info に値を代入する。
		target_info = next((t for t in targets['targetInfos'] if t['targetId'] == target_id), None)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not target_info:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'[DownloadsWatchdog] No target info found for {target_id}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Assign value to page_url.
		# JP: page_url に値を代入する。
		page_url = target_info.get('url', '')

		# Check cache first
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if page_url in self._pdf_viewer_cache:
			# EN: Assign value to cached_result.
			# JP: cached_result に値を代入する。
			cached_result = self._pdf_viewer_cache[page_url]
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Using cached PDF check result for {page_url}: {cached_result}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return cached_result

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Method 1: Check URL patterns (fastest, most reliable)
			# EN: Assign value to url_is_pdf.
			# JP: url_is_pdf に値を代入する。
			url_is_pdf = self._check_url_for_pdf(page_url)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if url_is_pdf:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] PDF detected via URL pattern: {page_url}')
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._pdf_viewer_cache[page_url] = True
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

			# Method 2: Check network response headers via CDP (safer than JavaScript)
			# EN: Assign value to header_is_pdf.
			# JP: header_is_pdf に値を代入する。
			header_is_pdf = await self._check_network_headers_for_pdf(target_id)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if header_is_pdf:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] PDF detected via network headers: {page_url}')
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._pdf_viewer_cache[page_url] = True
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

			# Method 3: Check Chrome's PDF viewer specific URLs
			# EN: Assign value to chrome_pdf_viewer.
			# JP: chrome_pdf_viewer に値を代入する。
			chrome_pdf_viewer = self._is_chrome_pdf_viewer_url(page_url)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if chrome_pdf_viewer:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[DownloadsWatchdog] Chrome PDF viewer detected: {page_url}')
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._pdf_viewer_cache[page_url] = True
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

			# Not a PDF
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._pdf_viewer_cache[page_url] = False
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'[DownloadsWatchdog] ❌ Error checking for PDF viewer: {e}')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._pdf_viewer_cache[page_url] = False
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# EN: Define function `_check_url_for_pdf`.
	# JP: 関数 `_check_url_for_pdf` を定義する。
	def _check_url_for_pdf(self, url: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if URL indicates a PDF file."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Assign value to url_lower.
		# JP: url_lower に値を代入する。
		url_lower = url.lower()

		# Direct PDF file extensions
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if url_lower.endswith('.pdf'):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# PDF in path
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if '.pdf' in url_lower:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# PDF MIME type in URL parameters
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if any(
			param in url_lower
			for param in [
				'content-type=application/pdf',
				'content-type=application%2fpdf',
				'mimetype=application/pdf',
				'type=application/pdf',
			]
		):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `_is_chrome_pdf_viewer_url`.
	# JP: 関数 `_is_chrome_pdf_viewer_url` を定義する。
	def _is_chrome_pdf_viewer_url(self, url: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if this is Chrome's internal PDF viewer URL."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Assign value to url_lower.
		# JP: url_lower に値を代入する。
		url_lower = url.lower()

		# Chrome PDF viewer uses chrome-extension:// URLs
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'chrome-extension://' in url_lower and 'pdf' in url_lower:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Chrome PDF viewer internal URLs
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if url_lower.startswith('chrome://') and 'pdf' in url_lower:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define async function `_check_network_headers_for_pdf`.
	# JP: 非同期関数 `_check_network_headers_for_pdf` を定義する。
	async def _check_network_headers_for_pdf(self, target_id: TargetID) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Infer PDF via navigation history/URL; headers are not available post-navigation in this context."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import asyncio

			# Get CDP session
			# EN: Assign value to temp_session.
			# JP: temp_session に値を代入する。
			temp_session = await self.browser_session.get_or_create_cdp_session(target_id, focus=False)

			# Get navigation history to find the main resource
			# EN: Assign value to history.
			# JP: history に値を代入する。
			history = await asyncio.wait_for(
				temp_session.cdp_client.send.Page.getNavigationHistory(session_id=temp_session.session_id), timeout=3.0
			)

			# EN: Assign value to current_entry.
			# JP: current_entry に値を代入する。
			current_entry = history.get('entries', [])
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if current_entry:
				# EN: Assign value to current_index.
				# JP: current_index に値を代入する。
				current_index = history.get('currentIndex', 0)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 0 <= current_index < len(current_entry):
					# EN: Assign value to current_url.
					# JP: current_url に値を代入する。
					current_url = current_entry[current_index].get('url', '')

					# Check if the URL itself suggests PDF
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self._check_url_for_pdf(current_url):
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return True

			# Note: CDP doesn't easily expose response headers for completed navigations
			# For more complex cases, we'd need to set up Network.responseReceived listeners
			# before navigation, but that's overkill for most PDF detection cases

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Network headers check failed (non-critical): {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# EN: Define async function `trigger_pdf_download`.
	# JP: 非同期関数 `trigger_pdf_download` を定義する。
	async def trigger_pdf_download(self, target_id: TargetID) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Trigger download of a PDF from Chrome's PDF viewer.

		Returns the download path if successful, None otherwise.
		"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[DownloadsWatchdog] trigger_pdf_download called for target_id={target_id}')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session.browser_profile.downloads_path:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('[DownloadsWatchdog] ❌ No downloads path configured, cannot save PDF download')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to downloads_path.
		# JP: downloads_path に値を代入する。
		downloads_path = self.browser_session.browser_profile.downloads_path
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'[DownloadsWatchdog] Downloads path: {downloads_path}')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Create a temporary CDP session for this target without switching focus
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import asyncio

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Creating CDP session for PDF download from target {target_id}')
			# EN: Assign value to temp_session.
			# JP: temp_session に値を代入する。
			temp_session = await self.browser_session.get_or_create_cdp_session(target_id, focus=False)

			# Try to get the PDF URL with timeout
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await asyncio.wait_for(
				temp_session.cdp_client.send.Runtime.evaluate(
					params={
						'expression': """
				(() => {
					// For Chrome's PDF viewer, the actual URL is in window.location.href
					// The embed element's src is often "about:blank"
					const embedElement = document.querySelector('embed[type="application/x-google-chrome-pdf"]') ||
										document.querySelector('embed[type="application/pdf"]');
					if (embedElement) {
						// Chrome PDF viewer detected - use the page URL
						return { url: window.location.href };
					}
					// Fallback to window.location.href anyway
					return { url: window.location.href };
				})()
				""",
						'returnByValue': True,
					},
					session_id=temp_session.session_id,
				),
				timeout=5.0,  # 5 second timeout to prevent hanging
			)
			# EN: Assign value to pdf_info.
			# JP: pdf_info に値を代入する。
			pdf_info = result.get('result', {}).get('value', {})

			# EN: Assign value to pdf_url.
			# JP: pdf_url に値を代入する。
			pdf_url = pdf_info.get('url', '')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not pdf_url:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'[DownloadsWatchdog] ❌ Could not determine PDF URL for download {pdf_info}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

			# Generate filename from URL
			# EN: Assign value to pdf_filename.
			# JP: pdf_filename に値を代入する。
			pdf_filename = os.path.basename(pdf_url.split('?')[0])  # Remove query params
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not pdf_filename or not pdf_filename.endswith('.pdf'):
				# EN: Assign value to parsed.
				# JP: parsed に値を代入する。
				parsed = urlparse(pdf_url)
				# EN: Assign value to pdf_filename.
				# JP: pdf_filename に値を代入する。
				pdf_filename = os.path.basename(parsed.path) or 'document.pdf'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not pdf_filename.endswith('.pdf'):
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					pdf_filename += '.pdf'

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Generated filename: {pdf_filename}')

			# Check if already downloaded by looking in the downloads directory
			# EN: Assign value to downloads_dir.
			# JP: downloads_dir に値を代入する。
			downloads_dir = str(self.browser_session.browser_profile.downloads_path)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if os.path.exists(downloads_dir):
				# EN: Assign value to existing_files.
				# JP: existing_files に値を代入する。
				existing_files = os.listdir(downloads_dir)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if pdf_filename in existing_files:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'[DownloadsWatchdog] PDF already downloaded: {pdf_filename}')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[DownloadsWatchdog] Starting PDF download from: {pdf_url[:100]}...')

			# Download using JavaScript fetch to leverage browser cache
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Properly escape the URL to prevent JavaScript injection
				# EN: Assign value to escaped_pdf_url.
				# JP: escaped_pdf_url に値を代入する。
				escaped_pdf_url = json.dumps(pdf_url)

				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await asyncio.wait_for(
					temp_session.cdp_client.send.Runtime.evaluate(
						params={
							'expression': f"""
					(async () => {{
						try {{
							// Use fetch with cache: 'force-cache' to prioritize cached version
							const response = await fetch({escaped_pdf_url}, {{
								cache: 'force-cache'
							}});
							if (!response.ok) {{
								throw new Error(`HTTP error! status: ${{response.status}}`);
							}}
							const blob = await response.blob();
							const arrayBuffer = await blob.arrayBuffer();
							const uint8Array = new Uint8Array(arrayBuffer);
							
							// Check if served from cache
							const fromCache = response.headers.has('age') || 
											 !response.headers.has('date');
											 
							return {{ 
								data: Array.from(uint8Array),
								fromCache: fromCache,
								responseSize: uint8Array.length,
								transferSize: response.headers.get('content-length') || 'unknown'
							}};
						}} catch (error) {{
							throw new Error(`Fetch failed: ${{error.message}}`);
						}}
					}})()
					""",
							'awaitPromise': True,
							'returnByValue': True,
						},
						session_id=temp_session.session_id,
					),
					timeout=10.0,  # 10 second timeout for download operation
				)
				# EN: Assign value to download_result.
				# JP: download_result に値を代入する。
				download_result = result.get('result', {}).get('value', {})

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if download_result and download_result.get('data') and len(download_result['data']) > 0:
					# Ensure unique filename
					# EN: Assign value to downloads_dir.
					# JP: downloads_dir に値を代入する。
					downloads_dir = str(self.browser_session.browser_profile.downloads_path)
					# Ensure downloads directory exists
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					os.makedirs(downloads_dir, exist_ok=True)
					# EN: Assign value to unique_filename.
					# JP: unique_filename に値を代入する。
					unique_filename = await self._get_unique_filename(downloads_dir, pdf_filename)
					# EN: Assign value to download_path.
					# JP: download_path に値を代入する。
					download_path = os.path.join(downloads_dir, unique_filename)

					# Save the PDF asynchronously
					# EN: Execute async logic with managed resources.
					# JP: リソース管理付きで非同期処理を実行する。
					async with await anyio.open_file(download_path, 'wb') as f:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await f.write(bytes(download_result['data']))

					# Verify file was written successfully
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if os.path.exists(download_path):
						# EN: Assign value to actual_size.
						# JP: actual_size に値を代入する。
						actual_size = os.path.getsize(download_path)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(
							f'[DownloadsWatchdog] PDF file written successfully: {download_path} ({actual_size} bytes)'
						)
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.error(f'[DownloadsWatchdog] ❌ Failed to write PDF file to: {download_path}')
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return None

					# Log cache information
					# EN: Assign value to cache_status.
					# JP: cache_status に値を代入する。
					cache_status = 'from cache' if download_result.get('fromCache') else 'from network'
					# EN: Assign value to response_size.
					# JP: response_size に値を代入する。
					response_size = download_result.get('responseSize', 0)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(
						f'[DownloadsWatchdog] ✅ Auto-downloaded PDF ({cache_status}, {response_size:,} bytes): {download_path}'
					)

					# Emit file downloaded event
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'[DownloadsWatchdog] Dispatching FileDownloadedEvent for {unique_filename}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.event_bus.dispatch(
						FileDownloadedEvent(
							url=pdf_url,
							path=download_path,
							file_name=unique_filename,
							file_size=response_size,
							file_type='pdf',
							mime_type='application/pdf',
							from_cache=download_result.get('fromCache', False),
							auto_download=True,
						)
					)

					# No need to detach - session is cached
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return download_path
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'[DownloadsWatchdog] No data received when downloading PDF from {pdf_url}')
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None

			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.warning(f'[DownloadsWatchdog] Failed to auto-download PDF from {pdf_url}: {type(e).__name__}: {e}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

		except TimeoutError:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('[DownloadsWatchdog] PDF download operation timed out')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[DownloadsWatchdog] Error in PDF download: {type(e).__name__}: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

	# EN: Define async function `_get_unique_filename`.
	# JP: 非同期関数 `_get_unique_filename` を定義する。
	@staticmethod
	async def _get_unique_filename(directory: str, filename: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Generate a unique filename for downloads by appending (1), (2), etc., if a file already exists."""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		base, ext = os.path.splitext(filename)
		# EN: Assign value to counter.
		# JP: counter に値を代入する。
		counter = 1
		# EN: Assign value to new_filename.
		# JP: new_filename に値を代入する。
		new_filename = filename
		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while os.path.exists(os.path.join(directory, new_filename)):
			# EN: Assign value to new_filename.
			# JP: new_filename に値を代入する。
			new_filename = f'{base} ({counter}){ext}'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			counter += 1
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return new_filename


# Fix Pydantic circular dependency - this will be called from session.py after BrowserSession is defined

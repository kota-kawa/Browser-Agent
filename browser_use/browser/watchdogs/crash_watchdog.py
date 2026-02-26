# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Browser watchdog for monitoring crashes and network timeouts using CDP."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import psutil
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.target import SessionID, TargetID
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.target.events import TargetCrashedEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import Field, PrivateAttr

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.constants import DEFAULT_NEW_TAB_URL
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	BrowserConnectedEvent,
	BrowserErrorEvent,
	BrowserStoppedEvent,
	TabCreatedEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import is_default_new_tab_url, is_new_tab_page

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `NetworkRequestTracker`.
# JP: クラス `NetworkRequestTracker` を定義する。
class NetworkRequestTracker:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Tracks ongoing network requests."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, request_id: str, start_time: float, url: str, method: str, resource_type: str | None = None):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.request_id = request_id
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.start_time = start_time
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.url = url
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.method = method
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.resource_type = resource_type


# EN: Define class `CrashWatchdog`.
# JP: クラス `CrashWatchdog` を定義する。
class CrashWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Monitors browser health for crashes and network timeouts using CDP."""

	# Event contracts
	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [
		BrowserConnectedEvent,
		BrowserStoppedEvent,
		TabCreatedEvent,
	]
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent]]] = [BrowserErrorEvent]

	# Configuration
	# EN: Assign annotated value to network_timeout_seconds.
	# JP: network_timeout_seconds に型付きの値を代入する。
	network_timeout_seconds: float = Field(default=10.0)
	# EN: Assign annotated value to check_interval_seconds.
	# JP: check_interval_seconds に型付きの値を代入する。
	check_interval_seconds: float = Field(default=5.0)  # Reduced frequency to reduce noise

	# Private state
	# EN: Assign annotated value to _active_requests.
	# JP: _active_requests に型付きの値を代入する。
	_active_requests: dict[str, NetworkRequestTracker] = PrivateAttr(default_factory=dict)
	# EN: Assign annotated value to _monitoring_task.
	# JP: _monitoring_task に型付きの値を代入する。
	_monitoring_task: asyncio.Task | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _last_responsive_checks.
	# JP: _last_responsive_checks に型付きの値を代入する。
	_last_responsive_checks: dict[str, float] = PrivateAttr(default_factory=dict)  # target_url -> timestamp
	# EN: Assign annotated value to _cdp_event_tasks.
	# JP: _cdp_event_tasks に型付きの値を代入する。
	_cdp_event_tasks: set[asyncio.Task] = PrivateAttr(default_factory=set)  # Track CDP event handler tasks
	# EN: Assign annotated value to _sessions_with_listeners.
	# JP: _sessions_with_listeners に型付きの値を代入する。
	_sessions_with_listeners: set[str] = PrivateAttr(default_factory=set)  # Track sessions that already have event listeners

	# EN: Define async function `on_BrowserConnectedEvent`.
	# JP: 非同期関数 `on_BrowserConnectedEvent` を定義する。
	async def on_BrowserConnectedEvent(self, event: BrowserConnectedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Start monitoring when browser is connected."""
		# logger.debug('[CrashWatchdog] Browser connected event received, beginning monitoring')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		asyncio.create_task(self._start_monitoring())
		# logger.debug(f'[CrashWatchdog] Monitoring task started: {self._monitoring_task and not self._monitoring_task.done()}')

	# EN: Define async function `on_BrowserStoppedEvent`.
	# JP: 非同期関数 `on_BrowserStoppedEvent` を定義する。
	async def on_BrowserStoppedEvent(self, event: BrowserStoppedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Stop monitoring when browser stops."""
		# logger.debug('[CrashWatchdog] Browser stopped, ending monitoring')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._stop_monitoring()

	# EN: Define async function `on_TabCreatedEvent`.
	# JP: 非同期関数 `on_TabCreatedEvent` を定義する。
	async def on_TabCreatedEvent(self, event: TabCreatedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Attach to new tab."""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session.agent_focus is not None, 'No current target ID'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.attach_to_target(self.browser_session.agent_focus.target_id)

	# EN: Define async function `attach_to_target`.
	# JP: 非同期関数 `attach_to_target` を定義する。
	async def attach_to_target(self, target_id: TargetID) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set up crash monitoring for a specific target using CDP."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Create temporary session for monitoring without switching focus
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.get_or_create_cdp_session(target_id, focus=False)

			# Check if we already have listeners for this session
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cdp_session.session_id in self._sessions_with_listeners:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[CrashWatchdog] Event listeners already exist for session: {cdp_session.session_id}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Set up network event handlers
			# def on_request_will_be_sent(event):
			# 	# Create and track the task
			# 	task = asyncio.create_task(self._on_request_cdp(event))
			# 	self._cdp_event_tasks.add(task)
			# 	# Remove from set when done
			# 	task.add_done_callback(lambda t: self._cdp_event_tasks.discard(t))

			# def on_response_received(event):
			# 	self._on_response_cdp(event)

			# def on_loading_failed(event):
			# 	self._on_request_failed_cdp(event)

			# def on_loading_finished(event):
			# 	self._on_request_finished_cdp(event)

			# Register event handlers
			# TEMPORARILY DISABLED: Network events causing too much logging
			# cdp_client.on('Network.requestWillBeSent', on_request_will_be_sent, session_id=session_id)
			# cdp_client.on('Network.responseReceived', on_response_received, session_id=session_id)
			# cdp_client.on('Network.loadingFailed', on_loading_failed, session_id=session_id)
			# cdp_client.on('Network.loadingFinished', on_loading_finished, session_id=session_id)

			# EN: Define function `on_target_crashed`.
			# JP: 関数 `on_target_crashed` を定義する。
			def on_target_crashed(event: TargetCrashedEvent, session_id: SessionID | None = None):
				# Create and track the task
				# EN: Assign value to task.
				# JP: task に値を代入する。
				task = asyncio.create_task(self._on_target_crash_cdp(target_id))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._cdp_event_tasks.add(task)
				# Remove from set when done
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				task.add_done_callback(lambda t: self._cdp_event_tasks.discard(t))

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cdp_session.cdp_client.register.Target.targetCrashed(on_target_crashed)

			# Track that we've added listeners to this session
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._sessions_with_listeners.add(cdp_session.session_id)

			# Get target info for logging
			# EN: Assign value to targets.
			# JP: targets に値を代入する。
			targets = await cdp_session.cdp_client.send.Target.getTargets()
			# EN: Assign value to target_info.
			# JP: target_info に値を代入する。
			target_info = next((t for t in targets['targetInfos'] if t['targetId'] == target_id), None)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if target_info:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[CrashWatchdog] Added target to monitoring: {target_info.get("url", "unknown")}')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'[CrashWatchdog] Failed to attach to target {target_id}: {e}')

	# EN: Define async function `_on_request_cdp`.
	# JP: 非同期関数 `_on_request_cdp` を定義する。
	async def _on_request_cdp(self, event: dict) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Track new network request from CDP event."""
		# EN: Assign value to request_id.
		# JP: request_id に値を代入する。
		request_id = event.get('requestId', '')
		# EN: Assign value to request.
		# JP: request に値を代入する。
		request = event.get('request', {})

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._active_requests[request_id] = NetworkRequestTracker(
			request_id=request_id,
			start_time=time.time(),
			url=request.get('url', ''),
			method=request.get('method', ''),
			resource_type=event.get('type'),
		)
		# logger.debug(f'[CrashWatchdog] Tracking request: {request.get("method", "")} {request.get("url", "")[:50]}...')

	# EN: Define function `_on_response_cdp`.
	# JP: 関数 `_on_response_cdp` を定義する。
	def _on_response_cdp(self, event: dict) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Remove request from tracking on response."""
		# EN: Assign value to request_id.
		# JP: request_id に値を代入する。
		request_id = event.get('requestId', '')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if request_id in self._active_requests:
			# EN: Assign value to elapsed.
			# JP: elapsed に値を代入する。
			elapsed = time.time() - self._active_requests[request_id].start_time
			# EN: Assign value to response.
			# JP: response に値を代入する。
			response = event.get('response', {})
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[CrashWatchdog] Request completed in {elapsed:.2f}s: {response.get("url", "")[:50]}...')
			# Don't remove yet - wait for loadingFinished

	# EN: Define function `_on_request_failed_cdp`.
	# JP: 関数 `_on_request_failed_cdp` を定義する。
	def _on_request_failed_cdp(self, event: dict) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Remove request from tracking on failure."""
		# EN: Assign value to request_id.
		# JP: request_id に値を代入する。
		request_id = event.get('requestId', '')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if request_id in self._active_requests:
			# EN: Assign value to elapsed.
			# JP: elapsed に値を代入する。
			elapsed = time.time() - self._active_requests[request_id].start_time
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'[CrashWatchdog] Request failed after {elapsed:.2f}s: {self._active_requests[request_id].url[:50]}...'
			)
			# EN: Delete referenced values.
			# JP: 参照される値を削除する。
			del self._active_requests[request_id]

	# EN: Define function `_on_request_finished_cdp`.
	# JP: 関数 `_on_request_finished_cdp` を定義する。
	def _on_request_finished_cdp(self, event: dict) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Remove request from tracking when loading is finished."""
		# EN: Assign value to request_id.
		# JP: request_id に値を代入する。
		request_id = event.get('requestId', '')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._active_requests.pop(request_id, None)

	# EN: Define async function `_on_target_crash_cdp`.
	# JP: 非同期関数 `_on_target_crash_cdp` を定義する。
	async def _on_target_crash_cdp(self, target_id: TargetID) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle target crash detected via CDP."""
		# Remove crashed session from pool
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if session := self.browser_session._cdp_session_pool.pop(target_id, None):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await session.disconnect()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[CrashWatchdog] Removed crashed session from pool: {target_id}')

		# Get target info
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
		if (
			target_info
			and self.browser_session.agent_focus
			and target_info['targetId'] == self.browser_session.agent_focus.target_id
		):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.browser_session.agent_focus.target_id = None  # type: ignore
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.browser_session.agent_focus.session_id = None  # type: ignore
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(
				f'[CrashWatchdog] 💥 Target crashed, navigating Agent to a new tab: {target_info.get("url", "unknown")}'
			)

		# Also emit generic browser error
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.event_bus.dispatch(
			BrowserErrorEvent(
				error_type='TargetCrash',
				message=f'Target crashed: {target_id}',
				details={
					# 'url': target_url,  # TODO: add url to details
					'target_id': target_id,
				},
			)
		)

	# EN: Define async function `_start_monitoring`.
	# JP: 非同期関数 `_start_monitoring` を定義する。
	async def _start_monitoring(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Start the monitoring loop."""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_session.cdp_client is not None, 'Root CDP client not initialized - browser may not be connected yet'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._monitoring_task and not self._monitoring_task.done():
			# logger.info('[CrashWatchdog] Monitoring already running')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._monitoring_task = asyncio.create_task(self._monitoring_loop())
		# logger.debug('[CrashWatchdog] Monitoring loop created and started')

	# EN: Define async function `_stop_monitoring`.
	# JP: 非同期関数 `_stop_monitoring` を定義する。
	async def _stop_monitoring(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Stop the monitoring loop."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._monitoring_task and not self._monitoring_task.done():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._monitoring_task.cancel()
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._monitoring_task
			except asyncio.CancelledError:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('[CrashWatchdog] Monitoring loop stopped')

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

		# Clear tracking (CDP sessions are cached and managed by BrowserSession)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._active_requests.clear()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._sessions_with_listeners.clear()

	# EN: Define async function `_monitoring_loop`.
	# JP: 非同期関数 `_monitoring_loop` を定義する。
	async def _monitoring_loop(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Main monitoring loop."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await asyncio.sleep(10)  # give browser time to start up and load the first page after first LLM call
		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while True:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._check_network_timeouts()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._check_browser_health()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(self.check_interval_seconds)
			except asyncio.CancelledError:
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(f'[CrashWatchdog] Error in monitoring loop: {e}')

	# EN: Define async function `_check_network_timeouts`.
	# JP: 非同期関数 `_check_network_timeouts` を定義する。
	async def _check_network_timeouts(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check for network requests exceeding timeout."""
		# EN: Assign value to current_time.
		# JP: current_time に値を代入する。
		current_time = time.time()
		# EN: Assign value to timed_out_requests.
		# JP: timed_out_requests に値を代入する。
		timed_out_requests = []

		# Debug logging
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._active_requests:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'[CrashWatchdog] Checking {len(self._active_requests)} active requests for timeouts (threshold: {self.network_timeout_seconds}s)'
			)

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for request_id, tracker in self._active_requests.items():
			# EN: Assign value to elapsed.
			# JP: elapsed に値を代入する。
			elapsed = current_time - tracker.start_time
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'[CrashWatchdog] Request {tracker.url[:30]}... elapsed: {elapsed:.1f}s, timeout: {self.network_timeout_seconds}s'
			)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if elapsed >= self.network_timeout_seconds:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				timed_out_requests.append((request_id, tracker))

		# Emit events for timed out requests
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for request_id, tracker in timed_out_requests:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(
				f'[CrashWatchdog] Network request timeout after {self.network_timeout_seconds}s: '
				f'{tracker.method} {tracker.url[:100]}...'
			)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='NetworkTimeout',
					message=f'Network request timed out after {self.network_timeout_seconds}s',
					details={
						'url': tracker.url,
						'method': tracker.method,
						'resource_type': tracker.resource_type,
						'elapsed_seconds': current_time - tracker.start_time,
					},
				)
			)

			# Remove from tracking
			# EN: Delete referenced values.
			# JP: 参照される値を削除する。
			del self._active_requests[request_id]

	# EN: Define async function `_check_browser_health`.
	# JP: 非同期関数 `_check_browser_health` を定義する。
	async def _check_browser_health(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if browser and targets are still responsive."""

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[CrashWatchdog] Checking browser health for target {self.browser_session.agent_focus}')
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = await self.browser_session.get_or_create_cdp_session()
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'[CrashWatchdog] Checking browser health for target {self.browser_session.agent_focus} error: {type(e).__name__}: {e}'
				)
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				self.agent_focus = cdp_session = await self.browser_session.get_or_create_cdp_session(
					target_id=self.agent_focus.target_id, new_socket=False, focus=True
				)

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for target in (await self.browser_session.cdp_client.send.Target.getTargets()).get('targetInfos', []):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if target.get('type') == 'page':
					# EN: Assign value to cdp_session.
					# JP: cdp_session に値を代入する。
					cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=target.get('targetId'))
					# EN: Assign value to target_url.
					# JP: target_url に値を代入する。
					target_url = target.get('url')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if is_new_tab_page(target_url) and not is_default_new_tab_url(target_url):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(
							f'[CrashWatchdog] Redirecting chrome://new-tab-page/ to {DEFAULT_NEW_TAB_URL} {target.get("url")}'
						)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await cdp_session.cdp_client.send.Page.navigate(
							params={'url': DEFAULT_NEW_TAB_URL}, session_id=cdp_session.session_id
						)

			# Quick ping to check if session is alive
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[CrashWatchdog] Attempting to run simple JS test expression in session {cdp_session} 1+1')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.wait_for(
				cdp_session.cdp_client.send.Runtime.evaluate(params={'expression': '1+1'}, session_id=cdp_session.session_id),
				timeout=1.0,
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[CrashWatchdog] Browser health check passed for target {self.browser_session.agent_focus}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(
				f'[CrashWatchdog] ❌ Crashed session detected for target {self.browser_session.agent_focus} error: {type(e).__name__}: {e}'
			)
			# Remove crashed session from pool
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session.agent_focus and (target_id := self.browser_session.agent_focus.target_id):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if session := self.browser_session._cdp_session_pool.pop(target_id, None):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await session.disconnect()
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'[CrashWatchdog] Removed crashed session from pool: {target_id}')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.browser_session.agent_focus.target_id = None  # type: ignore

		# Check browser process if we have PID
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session._local_browser_watchdog and (proc := self.browser_session._local_browser_watchdog._subprocess):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if proc.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'[CrashWatchdog] Browser process {proc.pid} has crashed')
					# Clear all sessions from pool when browser crashes
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for session in self.browser_session._cdp_session_pool.values():
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await session.disconnect()
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.browser_session._cdp_session_pool.clear()
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('[CrashWatchdog] Cleared all sessions from pool due to browser crash')

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.event_bus.dispatch(
						BrowserErrorEvent(
							error_type='BrowserProcessCrashed',
							message=f'Browser process {proc.pid} has crashed',
							details={'pid': proc.pid, 'status': proc.status()},
						)
					)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._stop_monitoring()
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return
			except Exception:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass  # psutil not available or process doesn't exist

	# EN: Define function `_is_new_tab_page`.
	# JP: 関数 `_is_new_tab_page` を定義する。
	@staticmethod
	def _is_new_tab_page(url: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Backwards compatibility helper for legacy imports."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return is_new_tab_page(url)

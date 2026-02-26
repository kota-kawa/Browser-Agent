# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Storage state watchdog for managing browser cookies and storage persistence."""

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
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from cdp_use.cdp.network import Cookie
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import Field, PrivateAttr

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	BrowserConnectedEvent,
	BrowserStopEvent,
	LoadStorageStateEvent,
	SaveStorageStateEvent,
	StorageStateLoadedEvent,
	StorageStateSavedEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog


# EN: Define class `StorageStateWatchdog`.
# JP: クラス `StorageStateWatchdog` を定義する。
class StorageStateWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Monitors and persists browser storage state including cookies and localStorage."""

	# Event contracts
	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [
		BrowserConnectedEvent,
		BrowserStopEvent,
		SaveStorageStateEvent,
		LoadStorageStateEvent,
	]
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent]]] = [
		StorageStateSavedEvent,
		StorageStateLoadedEvent,
	]

	# Configuration
	# EN: Assign annotated value to auto_save_interval.
	# JP: auto_save_interval に型付きの値を代入する。
	auto_save_interval: float = Field(default=30.0)  # Auto-save every 30 seconds
	# EN: Assign annotated value to save_on_change.
	# JP: save_on_change に型付きの値を代入する。
	save_on_change: bool = Field(default=True)  # Save immediately when cookies change

	# Private state
	# EN: Assign annotated value to _monitoring_task.
	# JP: _monitoring_task に型付きの値を代入する。
	_monitoring_task: asyncio.Task | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _last_cookie_state.
	# JP: _last_cookie_state に型付きの値を代入する。
	_last_cookie_state: list[dict] = PrivateAttr(default_factory=list)
	# EN: Assign annotated value to _save_lock.
	# JP: _save_lock に型付きの値を代入する。
	_save_lock: asyncio.Lock = PrivateAttr(default_factory=asyncio.Lock)

	# EN: Define async function `on_BrowserConnectedEvent`.
	# JP: 非同期関数 `on_BrowserConnectedEvent` を定義する。
	async def on_BrowserConnectedEvent(self, event: BrowserConnectedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Start monitoring when browser starts."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('[StorageStateWatchdog] 🍪 Initializing auth/cookies sync <-> with storage_state.json file')

		# Start monitoring
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._start_monitoring()

		# Automatically load storage state after browser start
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.event_bus.dispatch(LoadStorageStateEvent())

	# EN: Define async function `on_BrowserStopEvent`.
	# JP: 非同期関数 `on_BrowserStopEvent` を定義する。
	async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Stop monitoring when browser stops."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('[StorageStateWatchdog] Stopping storage_state monitoring')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._stop_monitoring()

	# EN: Define async function `on_SaveStorageStateEvent`.
	# JP: 非同期関数 `on_SaveStorageStateEvent` を定義する。
	async def on_SaveStorageStateEvent(self, event: SaveStorageStateEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle storage state save request."""
		# Use provided path or fall back to profile default
		# EN: Assign value to path.
		# JP: path に値を代入する。
		path = event.path
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if path is None:
			# Use profile default path if available
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session.browser_profile.storage_state:
				# EN: Assign value to path.
				# JP: path に値を代入する。
				path = str(self.browser_session.browser_profile.storage_state)
			else:
				# EN: Assign value to path.
				# JP: path に値を代入する。
				path = None  # Skip saving if no path available
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._save_storage_state(path)

	# EN: Define async function `on_LoadStorageStateEvent`.
	# JP: 非同期関数 `on_LoadStorageStateEvent` を定義する。
	async def on_LoadStorageStateEvent(self, event: LoadStorageStateEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle storage state load request."""
		# Use provided path or fall back to profile default
		# EN: Assign value to path.
		# JP: path に値を代入する。
		path = event.path
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if path is None:
			# Use profile default path if available
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session.browser_profile.storage_state:
				# EN: Assign value to path.
				# JP: path に値を代入する。
				path = str(self.browser_session.browser_profile.storage_state)
			else:
				# EN: Assign value to path.
				# JP: path に値を代入する。
				path = None  # Skip loading if no path available
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._load_storage_state(path)

	# EN: Define async function `_start_monitoring`.
	# JP: 非同期関数 `_start_monitoring` を定義する。
	async def _start_monitoring(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Start the monitoring task."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._monitoring_task and not self._monitoring_task.done():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session.cdp_client is None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('[StorageStateWatchdog] CDP client not ready; skipping monitor start')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._monitoring_task = asyncio.create_task(self._monitor_storage_changes())
		# self.logger'[StorageStateWatchdog] Started storage monitoring task')

	# EN: Define async function `_stop_monitoring`.
	# JP: 非同期関数 `_stop_monitoring` を定義する。
	async def _stop_monitoring(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Stop the monitoring task."""
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
			# self.logger.debug('[StorageStateWatchdog] Stopped storage monitoring task')

	# EN: Define async function `_check_for_cookie_changes_cdp`.
	# JP: 非同期関数 `_check_for_cookie_changes_cdp` を定義する。
	async def _check_for_cookie_changes_cdp(self, event: dict) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if a CDP network event indicates cookie changes.

		This would be called by Network.responseReceivedExtraInfo events
		if we set up CDP event listeners.
		"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Check for Set-Cookie headers in the response
			# EN: Assign value to headers.
			# JP: headers に値を代入する。
			headers = event.get('headers', {})
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'set-cookie' in headers or 'Set-Cookie' in headers:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('[StorageStateWatchdog] Cookie change detected via CDP')

				# If save on change is enabled, trigger save immediately
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.save_on_change:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._save_storage_state()
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'[StorageStateWatchdog] Error checking for cookie changes: {e}')

	# EN: Define async function `_monitor_storage_changes`.
	# JP: 非同期関数 `_monitor_storage_changes` を定義する。
	async def _monitor_storage_changes(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Periodically check for storage changes and auto-save."""
		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while True:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(self.auto_save_interval)

				# Skip if CDP is not connected yet (e.g., during reconnect loops)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not self.browser_session.cdp_client:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# Check if cookies have changed
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if await self._have_cookies_changed():
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('[StorageStateWatchdog] Detected changes to sync with storage_state.json')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._save_storage_state()

			except asyncio.CancelledError:
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break
			except Exception as e:
				# Avoid noisy logs while CDP is unavailable during long reconnects
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'cdp client not initialized' in str(e).lower():
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('[StorageStateWatchdog] CDP not ready; retrying after backoff')
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(f'[StorageStateWatchdog] Error in monitoring loop: {e}')

	# EN: Define async function `_have_cookies_changed`.
	# JP: 非同期関数 `_have_cookies_changed` を定義する。
	async def _have_cookies_changed(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if cookies have changed since last save."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session.cdp_client:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get current cookies using CDP
			# EN: Assign value to current_cookies.
			# JP: current_cookies に値を代入する。
			current_cookies = await self.browser_session._cdp_get_cookies()

			# Convert to comparable format, using .get() for optional fields
			# EN: Assign value to current_cookie_set.
			# JP: current_cookie_set に値を代入する。
			current_cookie_set = {
				(c.get('name', ''), c.get('domain', ''), c.get('path', '')): c.get('value', '') for c in current_cookies
			}

			# EN: Assign value to last_cookie_set.
			# JP: last_cookie_set に値を代入する。
			last_cookie_set = {
				(c.get('name', ''), c.get('domain', ''), c.get('path', '')): c.get('value', '') for c in self._last_cookie_state
			}

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return current_cookie_set != last_cookie_set
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[StorageStateWatchdog] Error comparing cookies: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# EN: Define async function `_save_storage_state`.
	# JP: 非同期関数 `_save_storage_state` を定義する。
	async def _save_storage_state(self, path: str | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Save browser storage state to file."""
		# EN: Execute async logic with managed resources.
		# JP: リソース管理付きで非同期処理を実行する。
		async with self._save_lock:
			# Check if CDP client is available
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.browser_session.cdp_client:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('[StorageStateWatchdog] No CDP client available for saving; skipping')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.browser_session.get_or_create_cdp_session(target_id=None, new_socket=False)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('[StorageStateWatchdog] Unable to create CDP session for saving; skipping')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Assign value to save_path.
			# JP: save_path に値を代入する。
			save_path = path or self.browser_session.browser_profile.storage_state
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not save_path:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Skip saving if the storage state is already a dict (indicates it was loaded from memory)
			# We only save to file if it started as a file path
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(save_path, dict):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('[StorageStateWatchdog] Storage state is already a dict, skipping file save')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Get current storage state using CDP
				# EN: Assign value to storage_state.
				# JP: storage_state に値を代入する。
				storage_state = await self.browser_session._cdp_get_storage_state()

				# Update our last known state
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._last_cookie_state = storage_state.get('cookies', []).copy()

				# Convert path to Path object
				# EN: Assign value to json_path.
				# JP: json_path に値を代入する。
				json_path = Path(save_path).expanduser().resolve()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				json_path.parent.mkdir(parents=True, exist_ok=True)

				# Merge with existing state if file exists
				# EN: Assign value to merged_state.
				# JP: merged_state に値を代入する。
				merged_state = storage_state
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if json_path.exists():
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to existing_state.
						# JP: existing_state に値を代入する。
						existing_state = json.loads(json_path.read_text())
						# EN: Assign value to merged_state.
						# JP: merged_state に値を代入する。
						merged_state = self._merge_storage_states(existing_state, dict(storage_state))
					except Exception as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.error(f'[StorageStateWatchdog] Failed to merge with existing state: {e}')

				# Write atomically
				# EN: Assign value to temp_path.
				# JP: temp_path に値を代入する。
				temp_path = json_path.with_suffix('.json.tmp')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				temp_path.write_text(json.dumps(merged_state, indent=4))

				# Backup existing file
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if json_path.exists():
					# EN: Assign value to backup_path.
					# JP: backup_path に値を代入する。
					backup_path = json_path.with_suffix('.json.bak')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					json_path.replace(backup_path)

				# Move temp to final
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				temp_path.replace(json_path)

				# Emit success event
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.event_bus.dispatch(
					StorageStateSavedEvent(
						path=str(json_path),
						cookies_count=len(merged_state.get('cookies', [])),
						origins_count=len(merged_state.get('origins', [])),
					)
				)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'[StorageStateWatchdog] Saved storage state to {json_path} '
					f'({len(merged_state.get("cookies", []))} cookies, '
					f'{len(merged_state.get("origins", []))} origins)'
				)

			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(f'[StorageStateWatchdog] Failed to save storage state: {e}')

	# EN: Define async function `_load_storage_state`.
	# JP: 非同期関数 `_load_storage_state` を定義する。
	async def _load_storage_state(self, path: str | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load browser storage state from file."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session.cdp_client:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('[StorageStateWatchdog] No CDP client available for loading; skipping')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to load_path.
		# JP: load_path に値を代入する。
		load_path = path or self.browser_session.browser_profile.storage_state
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not load_path or not os.path.exists(str(load_path)):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Read the storage state file asynchronously
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import anyio

			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = await anyio.Path(str(load_path)).read_text()
			# EN: Assign value to storage.
			# JP: storage に値を代入する。
			storage = json.loads(content)

			# Apply cookies if present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'cookies' in storage and storage['cookies']:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.browser_session._cdp_set_cookies(storage['cookies'])
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._last_cookie_state = storage['cookies'].copy()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[StorageStateWatchdog] Added {len(storage["cookies"])} cookies from storage state')

			# Apply origins (localStorage/sessionStorage) if present
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'origins' in storage and storage['origins']:
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for origin in storage['origins']:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'localStorage' in origin:
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for item in origin['localStorage']:
							# EN: Assign value to script.
							# JP: script に値を代入する。
							script = f"""
								window.localStorage.setItem({json.dumps(item['name'])}, {json.dumps(item['value'])});
							"""
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await self.browser_session._cdp_add_init_script(script)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'sessionStorage' in origin:
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for item in origin['sessionStorage']:
							# EN: Assign value to script.
							# JP: script に値を代入する。
							script = f"""
								window.sessionStorage.setItem({json.dumps(item['name'])}, {json.dumps(item['value'])});
							"""
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await self.browser_session._cdp_add_init_script(script)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'[StorageStateWatchdog] Applied localStorage/sessionStorage from {len(storage["origins"])} origins'
				)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				StorageStateLoadedEvent(
					path=str(load_path),
					cookies_count=len(storage.get('cookies', [])),
					origins_count=len(storage.get('origins', [])),
				)
			)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[StorageStateWatchdog] Loaded storage state from: {load_path}')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[StorageStateWatchdog] Failed to load storage state: {e}')

	# EN: Define function `_merge_storage_states`.
	# JP: 関数 `_merge_storage_states` を定義する。
	@staticmethod
	def _merge_storage_states(existing: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Merge two storage states, with new values taking precedence."""
		# EN: Assign value to merged.
		# JP: merged に値を代入する。
		merged = existing.copy()

		# Merge cookies
		# EN: Assign value to existing_cookies.
		# JP: existing_cookies に値を代入する。
		existing_cookies = {(c['name'], c['domain'], c['path']): c for c in existing.get('cookies', [])}

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for cookie in new.get('cookies', []):
			# EN: Assign value to key.
			# JP: key に値を代入する。
			key = (cookie['name'], cookie['domain'], cookie['path'])
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			existing_cookies[key] = cookie

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		merged['cookies'] = list(existing_cookies.values())

		# Merge origins
		# EN: Assign value to existing_origins.
		# JP: existing_origins に値を代入する。
		existing_origins = {origin['origin']: origin for origin in existing.get('origins', [])}

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for origin in new.get('origins', []):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			existing_origins[origin['origin']] = origin

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		merged['origins'] = list(existing_origins.values())

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return merged

	# EN: Define async function `get_current_cookies`.
	# JP: 非同期関数 `get_current_cookies` を定義する。
	async def get_current_cookies(self) -> list[dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get current cookies using CDP."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session.cdp_client:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to cookies.
			# JP: cookies に値を代入する。
			cookies = await self.browser_session._cdp_get_cookies()
			# Cookie is a TypedDict, cast to dict for compatibility
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return [dict(cookie) for cookie in cookies]
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[StorageStateWatchdog] Failed to get cookies: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []

	# EN: Define async function `add_cookies`.
	# JP: 非同期関数 `add_cookies` を定義する。
	async def add_cookies(self, cookies: list[dict[str, Any]]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Add cookies using CDP."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_session.cdp_client:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning('[StorageStateWatchdog] No CDP client available for adding cookies')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Convert dicts to Cookie objects
			# EN: Assign value to cookie_objects.
			# JP: cookie_objects に値を代入する。
			cookie_objects = [Cookie(**cookie_dict) if isinstance(cookie_dict, dict) else cookie_dict for cookie_dict in cookies]
			# Set cookies using CDP
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.browser_session._cdp_set_cookies(cookie_objects)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[StorageStateWatchdog] Added {len(cookies)} cookies')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[StorageStateWatchdog] Failed to add cookies: {e}')

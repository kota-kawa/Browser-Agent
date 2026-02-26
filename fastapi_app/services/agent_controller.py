from __future__ import annotations

import asyncio
import atexit
import copy
import inspect
import logging
import os
import threading
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bubus import EventBus

from ..core.env import _DEFAULT_START_URL, _env_int, _normalize_start_url
from ..core.exceptions import AgentControllerError
from .formatting import _format_step_plan
from .history_store import _append_history_message
from .llm_factory import _create_selected_llm
from ..prompts.system_prompt import (
	_DEFAULT_MAX_ACTIONS_PER_STEP,
	_LANGUAGE_EXTENSION,
	_build_custom_system_prompt,
	_should_disable_vision,
)

try:
	from browser_use import Agent, BrowserProfile, BrowserSession, Tools
except ModuleNotFoundError:
	import sys

	ROOT_DIR = Path(__file__).resolve().parents[2]
	if str(ROOT_DIR) not in sys.path:
		sys.path.insert(0, str(ROOT_DIR))
	from browser_use import Agent, BrowserProfile, BrowserSession, Tools

from browser_use.agent.views import AgentHistoryList, AgentOutput
from browser_use.browser.events import TabClosedEvent
from browser_use.browser.profile import ViewportSize
from browser_use.browser.views import BrowserStateSummary
from browser_use.model_selection import _load_selection


# EN: Define class `AgentRunResult`.
# JP: クラス `AgentRunResult` を定義する。
@dataclass
class AgentRunResult:
	history: AgentHistoryList
	step_message_ids: dict[int, int] = field(default_factory=dict)
	filtered_history: AgentHistoryList | None = None


# EN: Define class `BrowserAgentController`.
# JP: クラス `BrowserAgentController` を定義する。
class BrowserAgentController:
	"""Manage a long-lived browser session controlled by browser-use."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		cdp_url: str | None,
		max_steps: int,
		cdp_cleanup: Callable[[], None] | None = None,
	) -> None:
		self._cdp_url = cdp_url
		self._max_steps = max_steps
		# JP: 同期APIから安全に呼び出すため、専用イベントループをバックグラウンドで起動する
		# EN: Spin up a dedicated event loop thread so sync callers can schedule coroutines safely
		self._loop = asyncio.new_event_loop()
		self._thread = threading.Thread(
			target=self._run_loop,
			name='browser-use-agent-loop',
			daemon=True,
		)
		self._thread.start()
		self._lock = threading.Lock()
		self._state_lock = threading.Lock()
		self._browser_session: BrowserSession | None = None
		self._shutdown = False
		self._logger = logging.getLogger('browser_use.web.agent')
		self._cdp_cleanup = cdp_cleanup
		self._llm = _create_selected_llm()
		self._agent: Agent | None = None
		self._current_agent: Agent | None = None
		self._is_running = False
		self._paused = False
		self._vision_enabled = True
		self._step_message_ids: dict[int, int] = {}
		self._step_message_lock = threading.Lock()
		self._resume_url: str | None = None
		self._session_recreated = False
		self._start_page_ready = False
		self._initial_prompt_handled = False
		# JP: プロセス終了時にクリーンアップを行う
		# EN: Ensure cleanup on process exit
		atexit.register(self.shutdown)

	# EN: Define function `loop`.
	# JP: 関数 `loop` を定義する。
	@property
	def loop(self) -> asyncio.AbstractEventLoop:
		return self._loop

	# EN: Define function `_resolve_step_timeout`.
	# JP: 関数 `_resolve_step_timeout` を定義する。
	@staticmethod
	def _resolve_step_timeout() -> int | None:
		"""Resolve step timeout from environment.

		Returns:
		    int | None: Timeout in seconds, or None/<=0 to disable.
		"""

		# JP: 環境変数で明示指定がない場合はタイムアウト無し
		# EN: No timeout unless explicitly configured via env var
		raw = os.environ.get('BROWSER_USE_STEP_TIMEOUT')
		if raw is None:
			# Default: disable step timeout to allow long-running tasks.
			return None

		raw = raw.strip().lower()
		if raw in {'', 'none', 'no', 'off', 'false', '0'}:
			return None

		try:
			value = int(raw)
			return value if value > 0 else None
		except ValueError:
			# Fall back to no timeout on invalid input.
			return None

	# EN: Define function `_run_loop`.
	# JP: 関数 `_run_loop` を定義する。
	def _run_loop(self) -> None:
		# JP: 専用スレッド内のイベントループを永続稼働させる
		# EN: Keep the dedicated event loop running forever
		asyncio.set_event_loop(self._loop)
		self._loop.run_forever()

	# EN: Define async function `_ensure_browser_session`.
	# JP: 非同期関数 `_ensure_browser_session` を定義する。
	async def _ensure_browser_session(self) -> BrowserSession:
		# JP: 既存セッションがあれば再利用し、無ければ新規作成する
		# EN: Reuse an existing session when available; otherwise create a new one
		if self._browser_session is not None:
			with self._state_lock:
				self._session_recreated = False
			return self._browser_session

		# JP: CDP URL が未設定なら即エラー（ブラウザに接続できない）
		# EN: Fail fast when CDP URL is missing (no browser connection)
		if not self._cdp_url:
			raise AgentControllerError('Chrome DevToolsのCDP URLが検出できませんでした。BROWSER_USE_CDP_URL を設定してください。')

		# EN: Define function `_viewport_from_env`.
		# JP: 関数 `_viewport_from_env` を定義する。
		def _viewport_from_env(
			width_key: str,
			height_key: str,
			default_width: int,
			default_height: int,
		) -> ViewportSize | None:
			"""Create a viewport from environment variables if either is defined."""

			# JP: 幅/高さのどちらかが設定されている場合のみ有効化
			# EN: Enable only when at least one of width/height is provided
			width_raw = os.environ.get(width_key)
			height_raw = os.environ.get(height_key)

			if width_raw is None and height_raw is None:
				return None

			width = _env_int(width_key, default_width)
			height = _env_int(height_key, default_height)

			return ViewportSize(width=width, height=height)

		window_size: ViewportSize | None = None
		screen_size: ViewportSize | None = None

		# JP: BROWSER_WINDOW_* を優先し、無ければ Selenium 互換の変数を見る
		# EN: Prefer BROWSER_WINDOW_*; fall back to Selenium-compatible env vars
		browser_window = _viewport_from_env('BROWSER_WINDOW_WIDTH', 'BROWSER_WINDOW_HEIGHT', 1920, 1080)
		if browser_window is not None:
			window_size = browser_window
			screen_size = browser_window
		else:
			selenium_window = _viewport_from_env('SE_SCREEN_WIDTH', 'SE_SCREEN_HEIGHT', 1920, 1080)
			if selenium_window is not None:
				window_size = selenium_window
				screen_size = selenium_window

		# JP: keep_alive=True でセッションを継続し、同一ブラウザを再利用する
		# EN: keep_alive=True keeps the browser session warm across runs
		profile = BrowserProfile(
			cdp_url=self._cdp_url,
			keep_alive=True,
			highlight_elements=True,
			wait_between_actions=0.4,
			window_size=window_size,
			screen=screen_size,
		)
		session = BrowserSession(browser_profile=profile)
		with self._state_lock:
			self._browser_session = session
			self._session_recreated = True
			self._start_page_ready = False
		return session

	# EN: Define function `_consume_session_recreated`.
	# JP: 関数 `_consume_session_recreated` を定義する。
	def _consume_session_recreated(self) -> bool:
		with self._state_lock:
			recreated = self._session_recreated
			self._session_recreated = False
		return recreated

	# EN: Define async function `_run_agent`.
	# JP: 非同期関数 `_run_agent` を定義する。
	async def _run_agent(
		self,
		task: str,
		record_history: bool = True,
		additional_system_message: str | None = None,
		max_steps_override: int | None = None,
	) -> AgentRunResult:
		session = await self._ensure_browser_session()
		session_recreated = self._consume_session_recreated()
		effective_max_steps = max_steps_override if max_steps_override and max_steps_override > 0 else self._max_steps

		step_message_ids: dict[int, int] = {}
		starting_step_number = 1
		history_start_index = 0

		# EN: Define function `handle_new_step`.
		# JP: 関数 `handle_new_step` を定義する。
		def handle_new_step(
			state_summary: BrowserStateSummary,
			model_output: AgentOutput,
			step_number: int,
		) -> None:
			# JP: ステップごとの要約を履歴へ追記し、UI更新用IDを保持する
			# EN: Append per-step summaries to history and track message IDs for UI updates
			if not record_history:
				return
			try:
				relative_step = step_number - starting_step_number + 1
				if relative_step < 1:
					relative_step = 1
				content = _format_step_plan(relative_step, state_summary, model_output)
				message = _append_history_message('assistant', content)
				message_id = int(message['id'])
				step_message_ids[relative_step] = message_id
				self.remember_step_message_id(relative_step, message_id)
			except Exception:
				self._logger.debug('Failed to broadcast step update', exc_info=True)

		register_callback = handle_new_step if record_history else None

		# EN: Define function `_create_new_agent`.
		# JP: 関数 `_create_new_agent` を定義する。
		def _create_new_agent(initial_task: str) -> Agent:
			# JP: モデル選択とプロバイダ情報を読み取り、Vision 有効可否を判断する
			# EN: Load model selection/provider and decide whether vision can be enabled
			selection = _load_selection('browser')
			provider = selection.get('provider', '')
			model = str(selection.get('model', ''))
			provider_from_llm = getattr(self._llm, 'provider', '') or provider
			model_from_llm = str(getattr(self._llm, 'model', model) or model)

			with self._state_lock:
				vision_pref = self._vision_enabled

			vision_disabled = (not vision_pref) or _should_disable_vision(provider_from_llm, model_from_llm)
			if vision_disabled:
				self._logger.info(
					'Disabling vision because provider/model are not in the supported list: provider=%s model=%s',
					provider_from_llm,
					model_from_llm,
				)

			# JP: システムプロンプトはカスタムがあれば上書きし、無ければ拡張メッセージに連結
			# EN: Use a custom system prompt if available; otherwise extend the default message
			custom_system_prompt = _build_custom_system_prompt(
				force_disable_vision=vision_disabled,
				provider=provider_from_llm,
				model=model_from_llm,
			)
			if custom_system_prompt:
				if additional_system_message:
					custom_system_prompt += f'\n\n{additional_system_message}'
				extend_system_message = None
			else:
				base_extension = _LANGUAGE_EXTENSION
				if additional_system_message:
					base_extension += f'\n\n{additional_system_message}'
				extend_system_message = base_extension

			# JP: 危険なアクションを除外して安全側に寄せる
			# EN: Exclude risky actions to keep the agent safer by default
			tools = Tools(exclude_actions=['read_file', 'search_google'])
			step_timeout = self._resolve_step_timeout()
			fresh_agent = Agent(
				task=initial_task,
				browser_session=session,
				llm=self._llm,
				tools=tools,
				register_new_step_callback=register_callback,
				max_actions_per_step=_DEFAULT_MAX_ACTIONS_PER_STEP,
				override_system_message=custom_system_prompt,
				extend_system_message=extend_system_message,
				max_history_items=6,
				use_vision=not vision_disabled,
				step_timeout=step_timeout,
			)
			# JP: 初期URLが未指定なら開始ページへ移動するアクションを追加
			# EN: If no initial URL is set, add a navigation action to the start page
			start_url = self._get_resume_url() or _DEFAULT_START_URL
			if start_url and not fresh_agent.initial_actions:
				try:
					fresh_agent.initial_url = start_url
					fresh_agent.initial_actions = fresh_agent._convert_initial_actions(
						[{'go_to_url': {'url': start_url, 'new_tab': False}}]
					)
				except Exception:
					self._logger.debug(
						'Failed to apply start URL %s',
						start_url,
						exc_info=True,
					)
			return fresh_agent

		with self._state_lock:
			existing_agent = self._agent
			agent_running = self._is_running

		# JP: 実行中の二重起動を防止
		# EN: Prevent concurrent runs
		if agent_running:
			raise AgentControllerError('エージェントは実行中です。')

		if existing_agent is None:
			agent = _create_new_agent(task)
			with self._state_lock:
				self._agent = agent
		else:
			# JP: 既存エージェントをフォローアップとして再利用する
			# EN: Reuse the existing agent for a follow-up task
			agent = existing_agent
			agent.browser_session = session
			agent.register_new_step_callback = register_callback
			try:
				agent.add_new_task(task)
				self._prepare_agent_for_follow_up(agent, force_resume_navigation=session_recreated)
			except (AssertionError, ValueError) as exc:
				self._logger.exception('Failed to apply follow-up task %r; recreating agent.', task)
				with self._state_lock:
					self._agent = None
					self._current_agent = None
				agent = _create_new_agent(task)
				with self._state_lock:
					self._agent = agent
				self._logger.info('Recreated agent after failure and retrying task %r.', task)
			except Exception as exc:
				raise AgentControllerError(f'追加の指示の適用に失敗しました: {exc}') from exc

		# JP: 既存履歴の末尾を記録して差分だけを抽出できるようにする
		# EN: Capture history tail position so we can filter new entries only
		history_items = getattr(agent, 'history', None)
		if history_items is not None:
			history_start_index = len(history_items.history)
		starting_step_number = getattr(getattr(agent, 'state', None), 'n_steps', 1) or 1
		self._clear_step_message_ids()

		attach_watchdogs = getattr(session, 'attach_all_watchdogs', None)
		if attach_watchdogs is not None:
			try:
				await attach_watchdogs()
			except Exception:
				self._logger.debug('Failed to pre-attach browser watchdogs', exc_info=True)

		# JP: 実行状態フラグを更新して実行中として扱う
		# EN: Mark controller as running before invoking the agent
		with self._state_lock:
			self._current_agent = agent
			self._is_running = True
			self._paused = False
		try:
			history = await agent.run(max_steps=effective_max_steps)
			self._update_resume_url_from_history(history)
			new_entries = history.history[history_start_index:]
			filtered_entries = [
				entry
				for entry in new_entries
				if not getattr(entry, 'metadata', None) or getattr(entry.metadata, 'step_number', None) != 0
			]
			if filtered_entries or not new_entries:
				relevant_entries = filtered_entries
			else:
				relevant_entries = new_entries
			if isinstance(history, AgentHistoryList):
				history_kwargs = {'history': relevant_entries}
				if hasattr(history, 'usage'):
					history_kwargs['usage'] = getattr(history, 'usage')
				filtered_history = history.__class__(**history_kwargs)
				if hasattr(history, '_output_model_schema'):
					filtered_history._output_model_schema = history._output_model_schema
			else:
				filtered_history = copy.copy(history)
				setattr(filtered_history, 'history', relevant_entries)
			return AgentRunResult(
				history=history,
				step_message_ids=step_message_ids,
				filtered_history=filtered_history,
			)
		finally:
			# JP: keep_alive セッションではイベントバスを掃除し、問題があればローテーション
			# EN: For keep_alive sessions, drain the event bus; rotate on failure
			keep_alive = session.browser_profile.keep_alive
			rotate_session = False
			if keep_alive:
				drain_method = getattr(type(session), 'drain_event_bus', None)
				if callable(drain_method):
					try:
						drained_cleanly = await drain_method(session)
					except Exception:
						rotate_session = True
						self._logger.warning(
							'Failed to drain browser event bus; rotating for safety.',
							exc_info=True,
						)
					else:
						if not drained_cleanly:
							rotate_session = True
							self._logger.warning(
								'Browser event bus rotated after drain timeout; pending events cleared.',
							)
				else:
					self._logger.debug(
						'Browser session implementation does not expose drain_event_bus(); applying compatibility cleanup.',
					)
					with suppress(Exception):
						await session.event_bus.stop(clear=True, timeout=1.0)

					# EN: Define function `_resync_agent_event_bus`.
					# JP: 関数 `_resync_agent_event_bus` を定義する。
					def _resync_agent_event_bus() -> None:
						# JP: 既存エージェントとセッションの EventBus を同期し直す
						# EN: Resynchronize the agent's EventBus with the session
						with self._state_lock:
							candidate = self._agent or self._current_agent
						if candidate is None:
							return
						if getattr(candidate, 'browser_session', None) is not session:
							return

						reset_agent_bus = getattr(candidate, '_reset_eventbus', None)
						if callable(reset_agent_bus):
							try:
								reset_agent_bus()
							except Exception:
								self._logger.warning(
									'Failed to reset agent event bus after legacy session refresh; attempting manual synchronisation.',
									exc_info=True,
								)
							else:
								return

						refresh_agent_bus = getattr(
							candidate,
							'_refresh_browser_session_eventbus',
							None,
						)
						if callable(refresh_agent_bus):
							try:
								refresh_agent_bus(reset_watchdogs=True)
							except Exception:
								self._logger.warning(
									'Failed to refresh agent event bus after legacy session refresh.',
									exc_info=True,
								)

					reset_method = getattr(session, '_reset_event_bus_state', None)
					if callable(reset_method):
						try:
							reset_method()
						except Exception:
							self._logger.debug(
								'Legacy browser session failed to reset event bus state cleanly.',
								exc_info=True,
							)
						else:
							_resync_agent_event_bus()
					else:
						self._logger.debug(
							'Legacy browser session missing _reset_event_bus_state(); refreshing EventBus manually.',
						)
						try:
							session.event_bus = EventBus()
							try:
								session._watchdogs_attached = False  # type: ignore[attr-defined]
							except Exception:
								self._logger.debug(
									'Unable to reset watchdog attachment flag during manual event bus refresh.',
									exc_info=True,
								)
							for attribute in (
								'_crash_watchdog',
								'_downloads_watchdog',
								'_aboutblank_watchdog',
								'_security_watchdog',
								'_storage_state_watchdog',
								'_local_browser_watchdog',
								'_default_action_watchdog',
								'_dom_watchdog',
								'_screenshot_watchdog',
								'_permissions_watchdog',
								'_recording_watchdog',
							):
								if hasattr(session, attribute):
									try:
										setattr(session, attribute, None)
									except Exception:
										self._logger.debug(
											'Unable to clear %s during manual event bus refresh.',
											attribute,
											exc_info=True,
										)
							session.model_post_init(None)
						except Exception:
							rotate_session = True
							self._logger.warning(
								'Failed to refresh EventBus on legacy browser session; scheduling full rotation.',
								exc_info=True,
							)
						else:
							_resync_agent_event_bus()
			else:
				with suppress(Exception):
					await session.stop()

			if rotate_session:
				# JP: 完全にセッションを回収して次回に新規作成させる
				# EN: Fully retire the session so the next run starts fresh
				with suppress(Exception):
					await session.stop()
				kill_method = getattr(session, 'kill', None)
				if callable(kill_method):
					with suppress(Exception):
						maybe_kill = kill_method()
						if inspect.isawaitable(maybe_kill):
							await maybe_kill

			with self._state_lock:
				if self._browser_session is session:
					if rotate_session:
						self._browser_session = None
						self._logger.info(
							'Browser session rotated after event bus drain failure; a fresh session will be created on the next run.',
						)
					elif keep_alive:
						self._logger.debug(
							'Browser session kept alive for follow-up runs.',
						)
					else:
						self._logger.debug(
							'Browser session stopped; a new session will be created on the next run.',
						)
						self._browser_session = None
				self._current_agent = None
				self._is_running = False
				self._paused = False

	# EN: Define function `_pop_browser_session`.
	# JP: 関数 `_pop_browser_session` を定義する。
	def _pop_browser_session(self) -> BrowserSession | None:
		# JP: 共有セッション参照を外し、次回は新規作成させる
		# EN: Drop the shared session reference so a new one will be created
		with self._state_lock:
			session = self._browser_session
			self._browser_session = None
			self._session_recreated = False
			self._start_page_ready = False
		return session

	# EN: Define function `_stop_browser_session`.
	# JP: 関数 `_stop_browser_session` を定義する。
	def _stop_browser_session(self) -> None:
		session = self._pop_browser_session()
		if session is None:
			return

		# JP: 既存イベントループ上で停止処理を実行する
		# EN: Stop the session on the dedicated event loop
		async def _shutdown() -> None:
			with suppress(Exception):
				await session.stop()

		future = asyncio.run_coroutine_threadsafe(_shutdown(), self._loop)
		try:
			future.result(timeout=5)
		except Exception:
			future.cancel()
			self._logger.warning(
				'Failed to stop browser session cleanly; a fresh session will be created on the next run.',
				exc_info=True,
			)

	# EN: Define async function `_async_shutdown`.
	# JP: 非同期関数 `_async_shutdown` を定義する。
	async def _async_shutdown(self) -> None:
		# JP: コントローラー停止時にセッションとLLMを順に閉じる
		# EN: Close session and LLM in order during controller shutdown
		session = self._pop_browser_session()
		if session is not None:
			with suppress(Exception):
				await session.stop()
		await self._close_llm()

	# EN: Define async function `_close_llm`.
	# JP: 非同期関数 `_close_llm` を定義する。
	async def _close_llm(self) -> None:
		"""Close the shared LLM client to avoid late AsyncClient cleanup errors."""

		llm = self._llm
		if llm is None:
			return

		aclose = getattr(llm, 'aclose', None)
		if not callable(aclose):
			return

		try:
			await aclose()
			self._llm = None
		except RuntimeError as exc:
			# httpx/anyio will raise if the event loop is already shutting down.
			if 'Event loop is closed' in str(exc):
				self._logger.debug('LLM client close skipped because event loop is closed.')
			else:
				self._logger.debug('Failed to close LLM client cleanly', exc_info=True)
		except Exception:
			self._logger.debug('Unexpected error while closing LLM client', exc_info=True)

	# EN: Define function `_call_in_loop`.
	# JP: 関数 `_call_in_loop` を定義する。
	def _call_in_loop(self, func: Callable[[], None]) -> None:
		# JP: 同期関数をイベントループで実行して結果を待つ
		# EN: Execute a sync function inside the event loop and wait for completion
		async def _invoke() -> None:
			func()

		future = asyncio.run_coroutine_threadsafe(_invoke(), self._loop)
		future.result()

	# EN: Define function `enqueue_follow_up`.
	# JP: 関数 `enqueue_follow_up` を定義する。
	def enqueue_follow_up(self, task: str) -> None:
		with self._state_lock:
			agent = self._current_agent
			running = self._is_running

		# JP: 実行中でない場合はフォローアップを受け付けない
		# EN: Reject follow-up instructions when the agent is not running
		if not agent or not running:
			raise AgentControllerError('エージェントは実行中ではありません。')

		# EN: Define function `_apply`.
		# JP: 関数 `_apply` を定義する。
		def _apply() -> None:
			agent.add_new_task(task)

		try:
			self._call_in_loop(_apply)
		except AgentControllerError:
			raise
		except Exception as exc:
			raise AgentControllerError(f'追加の指示の適用に失敗しました: {exc}') from exc

	# EN: Define function `_prepare_agent_for_follow_up`.
	# JP: 関数 `_prepare_agent_for_follow_up` を定義する。
	def _prepare_agent_for_follow_up(self, agent: Agent, *, force_resume_navigation: bool = False) -> None:
		"""Clear completion flags so follow-up runs can execute new steps."""

		# JP: 完了フラグをリセットして次の指示を実行可能にする
		# EN: Reset completion flags so the next run can proceed
		cleared = False

		with suppress(AttributeError):
			cleared = agent.reset_completion_state()
			agent.state.stopped = False
			agent.state.paused = False

		if cleared:
			self._logger.debug('Cleared completion state for follow-up agent run.')

		resume_url = self._get_resume_url()
		prepared_resume = False

		# JP: セッション再作成時は直前のURLへ戻すことで継続性を確保
		# EN: After session recreation, resume at the last known URL for continuity
		if force_resume_navigation and resume_url:
			try:
				agent.initial_url = resume_url
				agent.initial_actions = agent._convert_initial_actions([{'go_to_url': {'url': resume_url, 'new_tab': False}}])
				agent.state.follow_up_task = False
				prepared_resume = True
				self._logger.debug('Prepared follow-up run to resume at %s.', resume_url)
			except Exception:
				self._logger.debug(
					'Failed to prepare resume navigation to %s',
					resume_url,
					exc_info=True,
				)
				agent.initial_actions = None

		if not prepared_resume:
			agent.initial_url = None
			agent.initial_actions = None
			agent.state.follow_up_task = True

	# EN: Define function `_record_step_message_id`.
	# JP: 関数 `_record_step_message_id` を定義する。
	def _record_step_message_id(self, step_number: int, message_id: int) -> None:
		# JP: ステップ番号と履歴メッセージIDの対応を記録する
		# EN: Store mapping between step number and history message ID
		with self._step_message_lock:
			self._step_message_ids[step_number] = message_id

	# EN: Define function `_lookup_step_message_id`.
	# JP: 関数 `_lookup_step_message_id` を定義する。
	def _lookup_step_message_id(self, step_number: int) -> int | None:
		with self._step_message_lock:
			return self._step_message_ids.get(step_number)

	# EN: Define function `_clear_step_message_ids`.
	# JP: 関数 `_clear_step_message_ids` を定義する。
	def _clear_step_message_ids(self) -> None:
		# JP: 直近実行のメッセージIDをクリアする
		# EN: Clear cached message IDs from the last run
		with self._step_message_lock:
			self._step_message_ids.clear()

	# EN: Define function `_set_resume_url`.
	# JP: 関数 `_set_resume_url` を定義する。
	def _set_resume_url(self, url: str | None) -> None:
		with self._state_lock:
			self._resume_url = url

	# EN: Define function `set_start_page`.
	# JP: 関数 `set_start_page` を定義する。
	def set_start_page(self, url: str | None) -> None:
		"""Override the next start/resume URL and reset warmup state."""

		# JP: URLを正規化し、次回起動時の開始ページに反映する
		# EN: Normalize the URL and apply it as the next start page
		normalized = _normalize_start_url(url) if url else None
		with self._state_lock:
			self._resume_url = normalized
			self._start_page_ready = False
		if normalized:
			self._logger.debug('Start page overridden for next run: %s', normalized)
		else:
			self._logger.debug('Start page override cleared; default will be used.')

	# EN: Define function `_get_resume_url`.
	# JP: 関数 `_get_resume_url` を定義する。
	def _get_resume_url(self) -> str | None:
		with self._state_lock:
			return self._resume_url

	# EN: Define function `_update_resume_url_from_history`.
	# JP: 関数 `_update_resume_url_from_history` を定義する。
	def _update_resume_url_from_history(self, history: AgentHistoryList) -> None:
		# JP: about:/chrome:// などの内部URLは再開対象から除外する
		# EN: Skip internal URLs (about:/chrome://) when deriving resume targets
		resume_url: str | None = None
		try:
			for entry in reversed(history.history):
				state = getattr(entry, 'state', None)
				if state is None:
					continue
				url = getattr(state, 'url', None)
				if not url:
					continue
				normalized = url.strip()
				if not normalized:
					continue
				lowered = normalized.lower()
				if lowered.startswith('about:') or lowered.startswith('chrome-error://'):
					continue
				if lowered.startswith('chrome://') or lowered.startswith('devtools://'):
					continue
				resume_url = normalized
				break
		except Exception:
			self._logger.debug('Failed to derive resume URL from agent history.', exc_info=True)
			return

		self._set_resume_url(resume_url)
		if resume_url:
			self._logger.debug('Recorded resume URL for follow-up runs: %s', resume_url)

	# EN: Define function `remember_step_message_id`.
	# JP: 関数 `remember_step_message_id` を定義する。
	def remember_step_message_id(self, step_number: int, message_id: int) -> None:
		self._record_step_message_id(step_number, message_id)

	# EN: Define function `get_step_message_id`.
	# JP: 関数 `get_step_message_id` を定義する。
	def get_step_message_id(self, step_number: int) -> int | None:
		return self._lookup_step_message_id(step_number)

	# EN: Define function `pause`.
	# JP: 関数 `pause` を定義する。
	def pause(self) -> None:
		with self._state_lock:
			agent = self._current_agent
			running = self._is_running
			already_paused = self._paused

		if not agent or not running:
			raise AgentControllerError('エージェントは実行されていません。')
		if already_paused:
			raise AgentControllerError('エージェントは既に一時停止中です。')

		try:
			self._call_in_loop(agent.pause)
		except Exception as exc:
			raise AgentControllerError(f'一時停止に失敗しました: {exc}') from exc

		with self._state_lock:
			self._paused = True

	# EN: Define function `resume`.
	# JP: 関数 `resume` を定義する。
	def resume(self) -> None:
		with self._state_lock:
			agent = self._current_agent
			running = self._is_running
			paused = self._paused

		if not agent or not running:
			raise AgentControllerError('エージェントは実行されていません。')
		if not paused:
			raise AgentControllerError('エージェントは一時停止状態ではありません。')

		try:
			self._call_in_loop(agent.resume)
		except Exception as exc:
			raise AgentControllerError(f'再開に失敗しました: {exc}') from exc

		with self._state_lock:
			self._paused = False

	# EN: Define function `is_running`.
	# JP: 関数 `is_running` を定義する。
	def is_running(self) -> bool:
		with self._state_lock:
			return self._is_running

	# EN: Define function `is_paused`.
	# JP: 関数 `is_paused` を定義する。
	def is_paused(self) -> bool:
		with self._state_lock:
			return self._paused

	# EN: Define function `ensure_start_page_ready`.
	# JP: 関数 `ensure_start_page_ready` を定義する。
	def ensure_start_page_ready(self) -> None:
		"""Ensure the embedded browser session opens the configured start URL."""

		# JP: UI表示用の開始ページを事前に起動しておく
		# EN: Warm up the start page so the embedded UI is ready
		start_url = self._get_resume_url() or _DEFAULT_START_URL
		if not start_url:
			return

		with self._state_lock:
			if self._start_page_ready and self._browser_session is not None:
				return
			running = self._is_running
			shutdown = self._shutdown

		if running or shutdown:
			return

		# JP: 非同期でブラウザを起動し開始ページへ移動する
		# EN: Start the browser asynchronously and navigate to the start page
		async def _warmup() -> str | None:
			session = await self._ensure_browser_session()
			try:
				await session.start()
			except Exception:
				self._logger.debug('Failed to start browser session during warmup', exc_info=True)
				raise

			try:
				await session.attach_all_watchdogs()
			except Exception:
				self._logger.debug('Failed to pre-attach browser watchdogs during warmup', exc_info=True)

			try:
				await session.navigate_to(start_url, new_tab=False)
			except Exception:
				self._logger.debug('Failed to warm up start URL %s', start_url, exc_info=True)
				raise

			try:
				return await session.get_current_page_url()
			except Exception:
				self._logger.debug('Failed to verify browser location after warmup', exc_info=True)
				return None

		try:
			future = asyncio.run_coroutine_threadsafe(_warmup(), self._loop)
			current_url = future.result(timeout=20)
		except Exception:
			self._logger.debug('Failed to prepare browser start page', exc_info=True)
			return

		if current_url and current_url.rstrip('/') != start_url.rstrip('/'):
			self._logger.debug(
				'Browser start page warmup navigated to %s instead of configured %s',
				current_url,
				start_url,
			)

		with self._state_lock:
			if self._browser_session is not None:
				self._start_page_ready = True

	# EN: Define function `close_additional_tabs`.
	# JP: 関数 `close_additional_tabs` を定義する。
	def close_additional_tabs(self, refresh_url: str | None = None) -> None:
		"""
		Close all open tabs except the current focus and optionally refresh that tab.

		This is primarily used by the WebArena runner to guarantee that each task
		starts from a single, freshly loaded page even if the previous task spawned
		extra tabs.
		"""

		# JP: WebArena 実行前に不要なタブを閉じて安定性を確保する
		# EN: Close extra tabs before WebArena runs to keep the session stable
		async def _close() -> None:
			session = await self._ensure_browser_session()
			# Enumerate tabs using the CDP helper for speed
			try:
				tabs = await session.get_tabs()
			except Exception:
				self._logger.debug('Failed to enumerate tabs before cleanup', exc_info=True)
				return

			current_target_id = session.agent_focus.target_id if session.agent_focus else None

			for tab in tabs:
				target_id = getattr(tab, 'target_id', None)
				if not target_id:
					continue
				if current_target_id and target_id == current_target_id:
					continue

				with suppress(Exception):
					await session._cdp_close_page(target_id)
					await session.event_bus.dispatch(TabClosedEvent(target_id=target_id))

			# If requested, reload the retained tab to ensure a fresh state
			if refresh_url:
				try:
					await session.navigate_to(refresh_url, new_tab=False)
				except Exception:
					self._logger.debug('Failed to refresh start page after tab cleanup', exc_info=True)

		future = asyncio.run_coroutine_threadsafe(_close(), self._loop)
		try:
			future.result(timeout=10)
		except Exception:
			self._logger.debug('Tab cleanup encountered an error', exc_info=True)

	# EN: Define function `update_llm`.
	# JP: 関数 `update_llm` を定義する。
	def update_llm(self) -> None:
		"""Update the LLM instance based on current global settings."""
		# JP: 設定を読み直して新しい LLM を差し替える
		# EN: Reload settings and swap in a new LLM instance
		try:
			new_llm = _create_selected_llm()
		except Exception as exc:
			raise AgentControllerError(f'新しいモデルの作成に失敗しました: {exc}') from exc

		# EN: Define async function `_apply_update`.
		# JP: 非同期関数 `_apply_update` を定義する。
		async def _apply_update() -> None:
			with self._state_lock:
				old_llm = self._llm
				self._llm = new_llm

				if self._agent:
					self._agent.llm = new_llm
				if self._current_agent and self._current_agent is not self._agent:
					self._current_agent.llm = new_llm

			if old_llm:
				aclose = getattr(old_llm, 'aclose', None)
				if callable(aclose):
					with suppress(Exception):
						await aclose()

		future = asyncio.run_coroutine_threadsafe(_apply_update(), self._loop)
		try:
			future.result(timeout=10)
		except Exception as exc:
			raise AgentControllerError(f'モデルの更新処理に失敗しました: {exc}') from exc

	# EN: Define function `reset`.
	# JP: 関数 `reset` を定義する。
	def reset(self) -> None:
		# JP: 実行中でなければセッションと状態を完全に初期化する
		# EN: Fully reset session and state when not running
		with self._state_lock:
			if self._is_running:
				raise AgentControllerError('エージェント実行中はリセットできません。')
		self._stop_browser_session()
		with self._state_lock:
			self._agent = None
			self._current_agent = None
			self._paused = False
			self._initial_prompt_handled = False
		self._set_resume_url(None)
		self._clear_step_message_ids()

	# EN: Define function `set_vision_enabled`.
	# JP: 関数 `set_vision_enabled` を定義する。
	def set_vision_enabled(self, enabled: bool) -> None:
		with self._state_lock:
			self._vision_enabled = bool(enabled)

	# EN: Define function `is_vision_enabled`.
	# JP: 関数 `is_vision_enabled` を定義する。
	def is_vision_enabled(self) -> bool:
		with self._state_lock:
			return self._vision_enabled

	# EN: Define function `prepare_for_new_task`.
	# JP: 関数 `prepare_for_new_task` を定義する。
	def prepare_for_new_task(self) -> None:
		# JP: 新規タスク開始前にエージェント状態をクリアする
		# EN: Clear agent state before starting a new task
		with self._state_lock:
			if self._is_running:
				raise AgentControllerError('エージェント実行中は新しいタスクを開始できません。')
			self._agent = None
			self._current_agent = None
			self._paused = False
			self._initial_prompt_handled = False
		self._clear_step_message_ids()

	# EN: Define function `run`.
	# JP: 関数 `run` を定義する。
	def run(
		self,
		task: str,
		record_history: bool = True,
		additional_system_message: str | None = None,
		max_steps: int | None = None,
		background: bool = False,
		completion_callback: Callable[[AgentRunResult | Exception], None] | None = None,
	) -> AgentRunResult | None:
		# JP: 同期APIから非同期実行を起動し、必要ならバックグラウンドで返す
		# EN: Launch async execution from a sync API, optionally returning immediately
		if self._shutdown:
			raise AgentControllerError('エージェントコントローラーは停止済みです。')

		with self._lock:
			future = asyncio.run_coroutine_threadsafe(
				self._run_agent(
					task,
					record_history=record_history,
					additional_system_message=additional_system_message,
					max_steps_override=max_steps,
				),
				self._loop,
			)
			with self._state_lock:
				self._initial_prompt_handled = True

			if background:

				# EN: Define function `_on_complete`.
				# JP: 関数 `_on_complete` を定義する。
				def _on_complete(f: Any) -> None:
					# JP: バックグラウンド完了時にコールバックへ通知する
					# EN: Notify completion callback when background run finishes
					if not completion_callback:
						return
					try:
						result = f.result()
						completion_callback(result)
					except Exception as exc:
						completion_callback(exc)

				future.add_done_callback(_on_complete)
				return None

			try:
				return future.result()
			except AgentControllerError:
				raise
			except Exception as exc:
				raise AgentControllerError(str(exc)) from exc

	# EN: Define function `has_handled_initial_prompt`.
	# JP: 関数 `has_handled_initial_prompt` を定義する。
	def has_handled_initial_prompt(self) -> bool:
		with self._state_lock:
			return self._initial_prompt_handled

	# EN: Define function `evaluate_in_browser`.
	# JP: 関数 `evaluate_in_browser` を定義する。
	def evaluate_in_browser(self, script: str) -> Any:
		"""Execute JavaScript in the current browser session."""
		# JP: CDP 経由で JS を評価し、値だけを返す
		# EN: Evaluate JS via CDP and return the raw value
		if not self._browser_session:
			raise AgentControllerError('ブラウザセッションが存在しません。')

		# EN: Define async function `_eval`.
		# JP: 非同期関数 `_eval` を定義する。
		async def _eval() -> Any:
			try:
				session = await self._ensure_browser_session()
				# Ensure we have an active CDP session
				cdp_session = await session.get_or_create_cdp_session()
				result = await cdp_session.cdp_client.send.Runtime.evaluate(
					params={'expression': script, 'returnByValue': True, 'awaitPromise': True}, session_id=cdp_session.session_id
				)
				if 'exceptionDetails' in result:
					raise Exception(f'JS Evaluation failed: {result["exceptionDetails"]}')
				return result.get('result', {}).get('value')
			except Exception as e:
				self._logger.error(f'Failed to evaluate javascript: {e}')
				raise

		future = asyncio.run_coroutine_threadsafe(_eval(), self._loop)
		try:
			return future.result(timeout=10)
		except Exception as exc:
			raise AgentControllerError(f'JavaScriptの実行に失敗しました: {exc}') from exc

	# EN: Define function `mark_initial_prompt_handled`.
	# JP: 関数 `mark_initial_prompt_handled` を定義する。
	def mark_initial_prompt_handled(self) -> None:
		with self._state_lock:
			self._initial_prompt_handled = True

	# EN: Define function `shutdown`.
	# JP: 関数 `shutdown` を定義する。
	def shutdown(self) -> None:
		# JP: シャットダウンフラグを立て、スレッド/セッションを安全に停止する
		# EN: Mark shutdown and safely stop thread/session resources
		if self._shutdown:
			return
		self._shutdown = True
		with self._state_lock:
			self._agent = None
			self._current_agent = None
			self._paused = False
		self._set_resume_url(None)
		self._clear_step_message_ids()

		if self._loop.is_running():
			try:
				future = asyncio.run_coroutine_threadsafe(self._async_shutdown(), self._loop)
				future.result(timeout=5)
			except Exception:
				self._logger.debug('Failed to shut down agent loop cleanly', exc_info=True)
			finally:
				if self._loop.is_running():
					self._loop.call_soon_threadsafe(self._loop.stop)

		if self._thread.is_alive():
			self._thread.join(timeout=2)

		if self._cdp_cleanup:
			try:
				self._cdp_cleanup()
			finally:
				self._cdp_cleanup = None

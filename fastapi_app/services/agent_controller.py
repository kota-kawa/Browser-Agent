# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import atexit
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import copy
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import inspect
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import threading
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Callable
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from contextlib import suppress
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass, field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import EventBus

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.env import _DEFAULT_START_URL, _env_int, _normalize_start_url
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.exceptions import AgentControllerError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .formatting import _format_step_plan
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .history_store import _append_history_message
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .llm_factory import _create_selected_llm
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..prompts.system_prompt import (
	_DEFAULT_MAX_ACTIONS_PER_STEP,
	_LANGUAGE_EXTENSION,
	_build_custom_system_prompt,
	_should_disable_vision,
)

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use import Agent, BrowserProfile, BrowserSession, Tools
except ModuleNotFoundError:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import sys

	# EN: Assign value to ROOT_DIR.
	# JP: ROOT_DIR に値を代入する。
	ROOT_DIR = Path(__file__).resolve().parents[2]
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if str(ROOT_DIR) not in sys.path:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.path.insert(0, str(ROOT_DIR))
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use import Agent, BrowserProfile, BrowserSession, Tools

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import AgentHistoryList, AgentOutput
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import TabClosedEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.profile import ViewportSize
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserStateSummary
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.model_selection import _load_selection


# EN: Define class `AgentRunResult`.
# JP: クラス `AgentRunResult` を定義する。
@dataclass
class AgentRunResult:
	# EN: Assign annotated value to history.
	# JP: history に型付きの値を代入する。
	history: AgentHistoryList
	# EN: Assign annotated value to step_message_ids.
	# JP: step_message_ids に型付きの値を代入する。
	step_message_ids: dict[int, int] = field(default_factory=dict)
	# EN: Assign annotated value to filtered_history.
	# JP: filtered_history に型付きの値を代入する。
	filtered_history: AgentHistoryList | None = None


# EN: Define class `BrowserAgentController`.
# JP: クラス `BrowserAgentController` を定義する。
class BrowserAgentController:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Manage a long-lived browser session controlled by browser-use."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		cdp_url: str | None,
		max_steps: int,
		cdp_cleanup: Callable[[], None] | None = None,
	) -> None:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cdp_url = cdp_url
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._max_steps = max_steps
		# JP: 同期APIから安全に呼び出すため、専用イベントループをバックグラウンドで起動する
		# EN: Spin up a dedicated event loop thread so sync callers can schedule coroutines safely
		self._loop = asyncio.new_event_loop()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._thread = threading.Thread(
			target=self._run_loop,
			name='browser-use-agent-loop',
			daemon=True,
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._thread.start()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._lock = threading.Lock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._state_lock = threading.Lock()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._browser_session: BrowserSession | None = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._shutdown = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._logger = logging.getLogger('browser_use.web.agent')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cdp_cleanup = cdp_cleanup
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._llm = _create_selected_llm()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._agent: Agent | None = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._current_agent: Agent | None = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._is_running = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._paused = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._vision_enabled = True
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._step_message_ids: dict[int, int] = {}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._step_message_lock = threading.Lock()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._resume_url: str | None = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._session_recreated = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._start_page_ready = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._initial_prompt_handled = False
		# JP: プロセス終了時にクリーンアップを行う
		# EN: Ensure cleanup on process exit
		atexit.register(self.shutdown)

	# EN: Define function `loop`.
	# JP: 関数 `loop` を定義する。
	@property
	def loop(self) -> asyncio.AbstractEventLoop:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._loop

	# EN: Define function `_resolve_step_timeout`.
	# JP: 関数 `_resolve_step_timeout` を定義する。
	@staticmethod
	def _resolve_step_timeout() -> int | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Resolve step timeout from environment.

		Returns:
		    int | None: Timeout in seconds, or None/<=0 to disable.
		"""

		# JP: 環境変数で明示指定がない場合はタイムアウト無し
		# EN: No timeout unless explicitly configured via env var
		raw = os.environ.get('BROWSER_USE_STEP_TIMEOUT')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if raw is None:
			# Default: disable step timeout to allow long-running tasks.
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to raw.
		# JP: raw に値を代入する。
		raw = raw.strip().lower()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if raw in {'', 'none', 'no', 'off', 'false', '0'}:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to value.
			# JP: value に値を代入する。
			value = int(raw)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return value if value > 0 else None
		except ValueError:
			# Fall back to no timeout on invalid input.
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

	# EN: Define function `_run_loop`.
	# JP: 関数 `_run_loop` を定義する。
	def _run_loop(self) -> None:
		# JP: 専用スレッド内のイベントループを永続稼働させる
		# EN: Keep the dedicated event loop running forever
		asyncio.set_event_loop(self._loop)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._loop.run_forever()

	# EN: Define async function `_ensure_browser_session`.
	# JP: 非同期関数 `_ensure_browser_session` を定義する。
	async def _ensure_browser_session(self) -> BrowserSession:
		# JP: 既存セッションがあれば再利用し、無ければ新規作成する
		# EN: Reuse an existing session when available; otherwise create a new one
		if self._browser_session is not None:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with self._state_lock:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._session_recreated = False
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._browser_session

		# JP: CDP URL が未設定なら即エラー（ブラウザに接続できない）
		# EN: Fail fast when CDP URL is missing (no browser connection)
		if not self._cdp_url:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('Chrome DevToolsのCDP URLが検出できませんでした。BROWSER_USE_CDP_URL を設定してください。')

		# EN: Define function `_viewport_from_env`.
		# JP: 関数 `_viewport_from_env` を定義する。
		def _viewport_from_env(
			width_key: str,
			height_key: str,
			default_width: int,
			default_height: int,
		) -> ViewportSize | None:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Create a viewport from environment variables if either is defined."""

			# JP: 幅/高さのどちらかが設定されている場合のみ有効化
			# EN: Enable only when at least one of width/height is provided
			width_raw = os.environ.get(width_key)
			# EN: Assign value to height_raw.
			# JP: height_raw に値を代入する。
			height_raw = os.environ.get(height_key)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if width_raw is None and height_raw is None:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

			# EN: Assign value to width.
			# JP: width に値を代入する。
			width = _env_int(width_key, default_width)
			# EN: Assign value to height.
			# JP: height に値を代入する。
			height = _env_int(height_key, default_height)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ViewportSize(width=width, height=height)

		# EN: Assign annotated value to window_size.
		# JP: window_size に型付きの値を代入する。
		window_size: ViewportSize | None = None
		# EN: Assign annotated value to screen_size.
		# JP: screen_size に型付きの値を代入する。
		screen_size: ViewportSize | None = None

		# JP: BROWSER_WINDOW_* を優先し、無ければ Selenium 互換の変数を見る
		# EN: Prefer BROWSER_WINDOW_*; fall back to Selenium-compatible env vars
		browser_window = _viewport_from_env('BROWSER_WINDOW_WIDTH', 'BROWSER_WINDOW_HEIGHT', 1920, 1080)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_window is not None:
			# EN: Assign value to window_size.
			# JP: window_size に値を代入する。
			window_size = browser_window
			# EN: Assign value to screen_size.
			# JP: screen_size に値を代入する。
			screen_size = browser_window
		else:
			# EN: Assign value to selenium_window.
			# JP: selenium_window に値を代入する。
			selenium_window = _viewport_from_env('SE_SCREEN_WIDTH', 'SE_SCREEN_HEIGHT', 1920, 1080)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if selenium_window is not None:
				# EN: Assign value to window_size.
				# JP: window_size に値を代入する。
				window_size = selenium_window
				# EN: Assign value to screen_size.
				# JP: screen_size に値を代入する。
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
		# EN: Assign value to session.
		# JP: session に値を代入する。
		session = BrowserSession(browser_profile=profile)
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._browser_session = session
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._session_recreated = True
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._start_page_ready = False
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return session

	# EN: Define function `_consume_session_recreated`.
	# JP: 関数 `_consume_session_recreated` を定義する。
	def _consume_session_recreated(self) -> bool:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to recreated.
			# JP: recreated に値を代入する。
			recreated = self._session_recreated
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._session_recreated = False
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
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
		# EN: Assign value to session.
		# JP: session に値を代入する。
		session = await self._ensure_browser_session()
		# EN: Assign value to session_recreated.
		# JP: session_recreated に値を代入する。
		session_recreated = self._consume_session_recreated()
		# EN: Assign value to effective_max_steps.
		# JP: effective_max_steps に値を代入する。
		effective_max_steps = max_steps_override if max_steps_override and max_steps_override > 0 else self._max_steps

		# EN: Assign annotated value to step_message_ids.
		# JP: step_message_ids に型付きの値を代入する。
		step_message_ids: dict[int, int] = {}
		# EN: Assign value to starting_step_number.
		# JP: starting_step_number に値を代入する。
		starting_step_number = 1
		# EN: Assign value to history_start_index.
		# JP: history_start_index に値を代入する。
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
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to relative_step.
				# JP: relative_step に値を代入する。
				relative_step = step_number - starting_step_number + 1
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if relative_step < 1:
					# EN: Assign value to relative_step.
					# JP: relative_step に値を代入する。
					relative_step = 1
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = _format_step_plan(relative_step, state_summary, model_output)
				# EN: Assign value to message.
				# JP: message に値を代入する。
				message = _append_history_message('assistant', content)
				# EN: Assign value to message_id.
				# JP: message_id に値を代入する。
				message_id = int(message['id'])
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				step_message_ids[relative_step] = message_id
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.remember_step_message_id(relative_step, message_id)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to broadcast step update', exc_info=True)

		# EN: Assign value to register_callback.
		# JP: register_callback に値を代入する。
		register_callback = handle_new_step if record_history else None

		# EN: Define function `_create_new_agent`.
		# JP: 関数 `_create_new_agent` を定義する。
		def _create_new_agent(initial_task: str) -> Agent:
			# JP: モデル選択とプロバイダ情報を読み取り、Vision 有効可否を判断する
			# EN: Load model selection/provider and decide whether vision can be enabled
			selection = _load_selection('browser')
			# EN: Assign value to provider.
			# JP: provider に値を代入する。
			provider = selection.get('provider', '')
			# EN: Assign value to model.
			# JP: model に値を代入する。
			model = str(selection.get('model', ''))
			# EN: Assign value to provider_from_llm.
			# JP: provider_from_llm に値を代入する。
			provider_from_llm = getattr(self._llm, 'provider', '') or provider
			# EN: Assign value to model_from_llm.
			# JP: model_from_llm に値を代入する。
			model_from_llm = str(getattr(self._llm, 'model', model) or model)

			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with self._state_lock:
				# EN: Assign value to vision_pref.
				# JP: vision_pref に値を代入する。
				vision_pref = self._vision_enabled

			# EN: Assign value to vision_disabled.
			# JP: vision_disabled に値を代入する。
			vision_disabled = (not vision_pref) or _should_disable_vision(provider_from_llm, model_from_llm)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if vision_disabled:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
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
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if custom_system_prompt:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if additional_system_message:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					custom_system_prompt += f'\n\n{additional_system_message}'
				# EN: Assign value to extend_system_message.
				# JP: extend_system_message に値を代入する。
				extend_system_message = None
			else:
				# EN: Assign value to base_extension.
				# JP: base_extension に値を代入する。
				base_extension = _LANGUAGE_EXTENSION
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if additional_system_message:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					base_extension += f'\n\n{additional_system_message}'
				# EN: Assign value to extend_system_message.
				# JP: extend_system_message に値を代入する。
				extend_system_message = base_extension

			# JP: 危険なアクションを除外して安全側に寄せる
			# EN: Exclude risky actions to keep the agent safer by default
			tools = Tools(exclude_actions=['read_file', 'search_google'])
			# EN: Assign value to step_timeout.
			# JP: step_timeout に値を代入する。
			step_timeout = self._resolve_step_timeout()
			# EN: Assign value to fresh_agent.
			# JP: fresh_agent に値を代入する。
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
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if start_url and not fresh_agent.initial_actions:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					fresh_agent.initial_url = start_url
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					fresh_agent.initial_actions = fresh_agent._convert_initial_actions(
						[{'go_to_url': {'url': start_url, 'new_tab': False}}]
					)
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._logger.debug(
						'Failed to apply start URL %s',
						start_url,
						exc_info=True,
					)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return fresh_agent

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to existing_agent.
			# JP: existing_agent に値を代入する。
			existing_agent = self._agent
			# EN: Assign value to agent_running.
			# JP: agent_running に値を代入する。
			agent_running = self._is_running

		# JP: 実行中の二重起動を防止
		# EN: Prevent concurrent runs
		if agent_running:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('エージェントは実行中です。')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if existing_agent is None:
			# EN: Assign value to agent.
			# JP: agent に値を代入する。
			agent = _create_new_agent(task)
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with self._state_lock:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._agent = agent
		else:
			# JP: 既存エージェントをフォローアップとして再利用する
			# EN: Reuse the existing agent for a follow-up task
			agent = existing_agent
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent.browser_session = session
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent.register_new_step_callback = register_callback
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				agent.add_new_task(task)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._prepare_agent_for_follow_up(agent, force_resume_navigation=session_recreated)
			except (AssertionError, ValueError) as exc:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.exception('Failed to apply follow-up task %r; recreating agent.', task)
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with self._state_lock:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._agent = None
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._current_agent = None
				# EN: Assign value to agent.
				# JP: agent に値を代入する。
				agent = _create_new_agent(task)
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with self._state_lock:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._agent = agent
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.info('Recreated agent after failure and retrying task %r.', task)
			except Exception as exc:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise AgentControllerError(f'追加の指示の適用に失敗しました: {exc}') from exc

		# JP: 既存履歴の末尾を記録して差分だけを抽出できるようにする
		# EN: Capture history tail position so we can filter new entries only
		history_items = getattr(agent, 'history', None)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if history_items is not None:
			# EN: Assign value to history_start_index.
			# JP: history_start_index に値を代入する。
			history_start_index = len(history_items.history)
		# EN: Assign value to starting_step_number.
		# JP: starting_step_number に値を代入する。
		starting_step_number = getattr(getattr(agent, 'state', None), 'n_steps', 1) or 1
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._clear_step_message_ids()

		# EN: Assign value to attach_watchdogs.
		# JP: attach_watchdogs に値を代入する。
		attach_watchdogs = getattr(session, 'attach_all_watchdogs', None)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if attach_watchdogs is not None:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await attach_watchdogs()
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to pre-attach browser watchdogs', exc_info=True)

		# JP: 実行状態フラグを更新して実行中として扱う
		# EN: Mark controller as running before invoking the agent
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._current_agent = agent
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._is_running = True
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._paused = False
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to history.
			# JP: history に値を代入する。
			history = await agent.run(max_steps=effective_max_steps)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._update_resume_url_from_history(history)
			# EN: Assign value to new_entries.
			# JP: new_entries に値を代入する。
			new_entries = history.history[history_start_index:]
			# EN: Assign value to filtered_entries.
			# JP: filtered_entries に値を代入する。
			filtered_entries = [
				entry
				for entry in new_entries
				if not getattr(entry, 'metadata', None) or getattr(entry.metadata, 'step_number', None) != 0
			]
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if filtered_entries or not new_entries:
				# EN: Assign value to relevant_entries.
				# JP: relevant_entries に値を代入する。
				relevant_entries = filtered_entries
			else:
				# EN: Assign value to relevant_entries.
				# JP: relevant_entries に値を代入する。
				relevant_entries = new_entries
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(history, AgentHistoryList):
				# EN: Assign value to history_kwargs.
				# JP: history_kwargs に値を代入する。
				history_kwargs = {'history': relevant_entries}
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(history, 'usage'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					history_kwargs['usage'] = getattr(history, 'usage')
				# EN: Assign value to filtered_history.
				# JP: filtered_history に値を代入する。
				filtered_history = history.__class__(**history_kwargs)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(history, '_output_model_schema'):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					filtered_history._output_model_schema = history._output_model_schema
			else:
				# EN: Assign value to filtered_history.
				# JP: filtered_history に値を代入する。
				filtered_history = copy.copy(history)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				setattr(filtered_history, 'history', relevant_entries)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return AgentRunResult(
				history=history,
				step_message_ids=step_message_ids,
				filtered_history=filtered_history,
			)
		finally:
			# JP: keep_alive セッションではイベントバスを掃除し、問題があればローテーション
			# EN: For keep_alive sessions, drain the event bus; rotate on failure
			keep_alive = session.browser_profile.keep_alive
			# EN: Assign value to rotate_session.
			# JP: rotate_session に値を代入する。
			rotate_session = False
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if keep_alive:
				# EN: Assign value to drain_method.
				# JP: drain_method に値を代入する。
				drain_method = getattr(type(session), 'drain_event_bus', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if callable(drain_method):
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to drained_cleanly.
						# JP: drained_cleanly に値を代入する。
						drained_cleanly = await drain_method(session)
					except Exception:
						# EN: Assign value to rotate_session.
						# JP: rotate_session に値を代入する。
						rotate_session = True
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self._logger.warning(
							'Failed to drain browser event bus; rotating for safety.',
							exc_info=True,
						)
					else:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if not drained_cleanly:
							# EN: Assign value to rotate_session.
							# JP: rotate_session に値を代入する。
							rotate_session = True
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self._logger.warning(
								'Browser event bus rotated after drain timeout; pending events cleared.',
							)
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._logger.debug(
						'Browser session implementation does not expose drain_event_bus(); applying compatibility cleanup.',
					)
					# EN: Execute logic with managed resources.
					# JP: リソース管理付きで処理を実行する。
					with suppress(Exception):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await session.event_bus.stop(clear=True, timeout=1.0)

					# EN: Define function `_resync_agent_event_bus`.
					# JP: 関数 `_resync_agent_event_bus` を定義する。
					def _resync_agent_event_bus() -> None:
						# JP: 既存エージェントとセッションの EventBus を同期し直す
						# EN: Resynchronize the agent's EventBus with the session
						with self._state_lock:
							# EN: Assign value to candidate.
							# JP: candidate に値を代入する。
							candidate = self._agent or self._current_agent
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if candidate is None:
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if getattr(candidate, 'browser_session', None) is not session:
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return

						# EN: Assign value to reset_agent_bus.
						# JP: reset_agent_bus に値を代入する。
						reset_agent_bus = getattr(candidate, '_reset_eventbus', None)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if callable(reset_agent_bus):
							# EN: Handle exceptions around this block.
							# JP: このブロックで例外処理を行う。
							try:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								reset_agent_bus()
							except Exception:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								self._logger.warning(
									'Failed to reset agent event bus after legacy session refresh; attempting manual synchronisation.',
									exc_info=True,
								)
							else:
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return

						# EN: Assign value to refresh_agent_bus.
						# JP: refresh_agent_bus に値を代入する。
						refresh_agent_bus = getattr(
							candidate,
							'_refresh_browser_session_eventbus',
							None,
						)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if callable(refresh_agent_bus):
							# EN: Handle exceptions around this block.
							# JP: このブロックで例外処理を行う。
							try:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								refresh_agent_bus(reset_watchdogs=True)
							except Exception:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								self._logger.warning(
									'Failed to refresh agent event bus after legacy session refresh.',
									exc_info=True,
								)

					# EN: Assign value to reset_method.
					# JP: reset_method に値を代入する。
					reset_method = getattr(session, '_reset_event_bus_state', None)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if callable(reset_method):
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							reset_method()
						except Exception:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self._logger.debug(
								'Legacy browser session failed to reset event bus state cleanly.',
								exc_info=True,
							)
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							_resync_agent_event_bus()
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self._logger.debug(
							'Legacy browser session missing _reset_event_bus_state(); refreshing EventBus manually.',
						)
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							session.event_bus = EventBus()
							# EN: Handle exceptions around this block.
							# JP: このブロックで例外処理を行う。
							try:
								# EN: Assign value to target variable.
								# JP: target variable に値を代入する。
								session._watchdogs_attached = False  # type: ignore[attr-defined]
							except Exception:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								self._logger.debug(
									'Unable to reset watchdog attachment flag during manual event bus refresh.',
									exc_info=True,
								)
							# EN: Iterate over items in a loop.
							# JP: ループで要素を順に処理する。
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
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if hasattr(session, attribute):
									# EN: Handle exceptions around this block.
									# JP: このブロックで例外処理を行う。
									try:
										# EN: Evaluate an expression.
										# JP: 式を評価する。
										setattr(session, attribute, None)
									except Exception:
										# EN: Evaluate an expression.
										# JP: 式を評価する。
										self._logger.debug(
											'Unable to clear %s during manual event bus refresh.',
											attribute,
											exc_info=True,
										)
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							session.model_post_init(None)
						except Exception:
							# EN: Assign value to rotate_session.
							# JP: rotate_session に値を代入する。
							rotate_session = True
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self._logger.warning(
								'Failed to refresh EventBus on legacy browser session; scheduling full rotation.',
								exc_info=True,
							)
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							_resync_agent_event_bus()
			else:
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with suppress(Exception):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await session.stop()

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if rotate_session:
				# JP: 完全にセッションを回収して次回に新規作成させる
				# EN: Fully retire the session so the next run starts fresh
				with suppress(Exception):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await session.stop()
				# EN: Assign value to kill_method.
				# JP: kill_method に値を代入する。
				kill_method = getattr(session, 'kill', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if callable(kill_method):
					# EN: Execute logic with managed resources.
					# JP: リソース管理付きで処理を実行する。
					with suppress(Exception):
						# EN: Assign value to maybe_kill.
						# JP: maybe_kill に値を代入する。
						maybe_kill = kill_method()
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if inspect.isawaitable(maybe_kill):
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await maybe_kill

			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with self._state_lock:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._browser_session is session:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if rotate_session:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						self._browser_session = None
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self._logger.info(
							'Browser session rotated after event bus drain failure; a fresh session will be created on the next run.',
						)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif keep_alive:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self._logger.debug(
							'Browser session kept alive for follow-up runs.',
						)
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self._logger.debug(
							'Browser session stopped; a new session will be created on the next run.',
						)
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						self._browser_session = None
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._current_agent = None
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._is_running = False
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._paused = False

	# EN: Define function `_pop_browser_session`.
	# JP: 関数 `_pop_browser_session` を定義する。
	def _pop_browser_session(self) -> BrowserSession | None:
		# JP: 共有セッション参照を外し、次回は新規作成させる
		# EN: Drop the shared session reference so a new one will be created
		with self._state_lock:
			# EN: Assign value to session.
			# JP: session に値を代入する。
			session = self._browser_session
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._browser_session = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._session_recreated = False
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._start_page_ready = False
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return session

	# EN: Define function `_stop_browser_session`.
	# JP: 関数 `_stop_browser_session` を定義する。
	def _stop_browser_session(self) -> None:
		# EN: Assign value to session.
		# JP: session に値を代入する。
		session = self._pop_browser_session()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if session is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# JP: 既存イベントループ上で停止処理を実行する
		# EN: Stop the session on the dedicated event loop
		async def _shutdown() -> None:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with suppress(Exception):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.stop()

		# EN: Assign value to future.
		# JP: future に値を代入する。
		future = asyncio.run_coroutine_threadsafe(_shutdown(), self._loop)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			future.result(timeout=5)
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			future.cancel()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
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
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if session is not None:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with suppress(Exception):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.stop()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self._close_llm()

	# EN: Define async function `_close_llm`.
	# JP: 非同期関数 `_close_llm` を定義する。
	async def _close_llm(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close the shared LLM client to avoid late AsyncClient cleanup errors."""

		# EN: Assign value to llm.
		# JP: llm に値を代入する。
		llm = self._llm
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if llm is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to aclose.
		# JP: aclose に値を代入する。
		aclose = getattr(llm, 'aclose', None)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not callable(aclose):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await aclose()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._llm = None
		except RuntimeError as exc:
			# httpx/anyio will raise if the event loop is already shutting down.
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'Event loop is closed' in str(exc):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('LLM client close skipped because event loop is closed.')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to close LLM client cleanly', exc_info=True)
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug('Unexpected error while closing LLM client', exc_info=True)

	# EN: Define function `_call_in_loop`.
	# JP: 関数 `_call_in_loop` を定義する。
	def _call_in_loop(self, func: Callable[[], None]) -> None:
		# JP: 同期関数をイベントループで実行して結果を待つ
		# EN: Execute a sync function inside the event loop and wait for completion
		async def _invoke() -> None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			func()

		# EN: Assign value to future.
		# JP: future に値を代入する。
		future = asyncio.run_coroutine_threadsafe(_invoke(), self._loop)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		future.result()

	# EN: Define function `enqueue_follow_up`.
	# JP: 関数 `enqueue_follow_up` を定義する。
	def enqueue_follow_up(self, task: str) -> None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to agent.
			# JP: agent に値を代入する。
			agent = self._current_agent
			# EN: Assign value to running.
			# JP: running に値を代入する。
			running = self._is_running

		# JP: 実行中でない場合はフォローアップを受け付けない
		# EN: Reject follow-up instructions when the agent is not running
		if not agent or not running:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('エージェントは実行中ではありません。')

		# EN: Define function `_apply`.
		# JP: 関数 `_apply` を定義する。
		def _apply() -> None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			agent.add_new_task(task)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._call_in_loop(_apply)
		except AgentControllerError:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise
		except Exception as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError(f'追加の指示の適用に失敗しました: {exc}') from exc

	# EN: Define function `_prepare_agent_for_follow_up`.
	# JP: 関数 `_prepare_agent_for_follow_up` を定義する。
	def _prepare_agent_for_follow_up(self, agent: Agent, *, force_resume_navigation: bool = False) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear completion flags so follow-up runs can execute new steps."""

		# JP: 完了フラグをリセットして次の指示を実行可能にする
		# EN: Reset completion flags so the next run can proceed
		cleared = False

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with suppress(AttributeError):
			# EN: Assign value to cleared.
			# JP: cleared に値を代入する。
			cleared = agent.reset_completion_state()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent.state.stopped = False
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent.state.paused = False

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if cleared:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug('Cleared completion state for follow-up agent run.')

		# EN: Assign value to resume_url.
		# JP: resume_url に値を代入する。
		resume_url = self._get_resume_url()
		# EN: Assign value to prepared_resume.
		# JP: prepared_resume に値を代入する。
		prepared_resume = False

		# JP: セッション再作成時は直前のURLへ戻すことで継続性を確保
		# EN: After session recreation, resume at the last known URL for continuity
		if force_resume_navigation and resume_url:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				agent.initial_url = resume_url
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				agent.initial_actions = agent._convert_initial_actions([{'go_to_url': {'url': resume_url, 'new_tab': False}}])
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				agent.state.follow_up_task = False
				# EN: Assign value to prepared_resume.
				# JP: prepared_resume に値を代入する。
				prepared_resume = True
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Prepared follow-up run to resume at %s.', resume_url)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug(
					'Failed to prepare resume navigation to %s',
					resume_url,
					exc_info=True,
				)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				agent.initial_actions = None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not prepared_resume:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent.initial_url = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent.initial_actions = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			agent.state.follow_up_task = True

	# EN: Define function `_record_step_message_id`.
	# JP: 関数 `_record_step_message_id` を定義する。
	def _record_step_message_id(self, step_number: int, message_id: int) -> None:
		# JP: ステップ番号と履歴メッセージIDの対応を記録する
		# EN: Store mapping between step number and history message ID
		with self._step_message_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._step_message_ids[step_number] = message_id

	# EN: Define function `_lookup_step_message_id`.
	# JP: 関数 `_lookup_step_message_id` を定義する。
	def _lookup_step_message_id(self, step_number: int) -> int | None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._step_message_lock:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._step_message_ids.get(step_number)

	# EN: Define function `_clear_step_message_ids`.
	# JP: 関数 `_clear_step_message_ids` を定義する。
	def _clear_step_message_ids(self) -> None:
		# JP: 直近実行のメッセージIDをクリアする
		# EN: Clear cached message IDs from the last run
		with self._step_message_lock:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._step_message_ids.clear()

	# EN: Define function `_set_resume_url`.
	# JP: 関数 `_set_resume_url` を定義する。
	def _set_resume_url(self, url: str | None) -> None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._resume_url = url

	# EN: Define function `set_start_page`.
	# JP: 関数 `set_start_page` を定義する。
	def set_start_page(self, url: str | None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Override the next start/resume URL and reset warmup state."""

		# JP: URLを正規化し、次回起動時の開始ページに反映する
		# EN: Normalize the URL and apply it as the next start page
		normalized = _normalize_start_url(url) if url else None
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._resume_url = normalized
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._start_page_ready = False
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if normalized:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug('Start page overridden for next run: %s', normalized)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug('Start page override cleared; default will be used.')

	# EN: Define function `_get_resume_url`.
	# JP: 関数 `_get_resume_url` を定義する。
	def _get_resume_url(self) -> str | None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._resume_url

	# EN: Define function `_update_resume_url_from_history`.
	# JP: 関数 `_update_resume_url_from_history` を定義する。
	def _update_resume_url_from_history(self, history: AgentHistoryList) -> None:
		# JP: about:/chrome:// などの内部URLは再開対象から除外する
		# EN: Skip internal URLs (about:/chrome://) when deriving resume targets
		resume_url: str | None = None
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for entry in reversed(history.history):
				# EN: Assign value to state.
				# JP: state に値を代入する。
				state = getattr(entry, 'state', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if state is None:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Assign value to url.
				# JP: url に値を代入する。
				url = getattr(state, 'url', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not url:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Assign value to normalized.
				# JP: normalized に値を代入する。
				normalized = url.strip()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not normalized:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Assign value to lowered.
				# JP: lowered に値を代入する。
				lowered = normalized.lower()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if lowered.startswith('about:') or lowered.startswith('chrome-error://'):
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if lowered.startswith('chrome://') or lowered.startswith('devtools://'):
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Assign value to resume_url.
				# JP: resume_url に値を代入する。
				resume_url = normalized
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug('Failed to derive resume URL from agent history.', exc_info=True)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._set_resume_url(resume_url)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if resume_url:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug('Recorded resume URL for follow-up runs: %s', resume_url)

	# EN: Define function `remember_step_message_id`.
	# JP: 関数 `remember_step_message_id` を定義する。
	def remember_step_message_id(self, step_number: int, message_id: int) -> None:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._record_step_message_id(step_number, message_id)

	# EN: Define function `get_step_message_id`.
	# JP: 関数 `get_step_message_id` を定義する。
	def get_step_message_id(self, step_number: int) -> int | None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._lookup_step_message_id(step_number)

	# EN: Define function `pause`.
	# JP: 関数 `pause` を定義する。
	def pause(self) -> None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to agent.
			# JP: agent に値を代入する。
			agent = self._current_agent
			# EN: Assign value to running.
			# JP: running に値を代入する。
			running = self._is_running
			# EN: Assign value to already_paused.
			# JP: already_paused に値を代入する。
			already_paused = self._paused

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not agent or not running:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('エージェントは実行されていません。')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if already_paused:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('エージェントは既に一時停止中です。')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._call_in_loop(agent.pause)
		except Exception as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError(f'一時停止に失敗しました: {exc}') from exc

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._paused = True

	# EN: Define function `resume`.
	# JP: 関数 `resume` を定義する。
	def resume(self) -> None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to agent.
			# JP: agent に値を代入する。
			agent = self._current_agent
			# EN: Assign value to running.
			# JP: running に値を代入する。
			running = self._is_running
			# EN: Assign value to paused.
			# JP: paused に値を代入する。
			paused = self._paused

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not agent or not running:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('エージェントは実行されていません。')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not paused:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('エージェントは一時停止状態ではありません。')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._call_in_loop(agent.resume)
		except Exception as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError(f'再開に失敗しました: {exc}') from exc

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._paused = False

	# EN: Define function `is_running`.
	# JP: 関数 `is_running` を定義する。
	def is_running(self) -> bool:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._is_running

	# EN: Define function `is_paused`.
	# JP: 関数 `is_paused` を定義する。
	def is_paused(self) -> bool:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._paused

	# EN: Define function `ensure_start_page_ready`.
	# JP: 関数 `ensure_start_page_ready` を定義する。
	def ensure_start_page_ready(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Ensure the embedded browser session opens the configured start URL."""

		# JP: UI表示用の開始ページを事前に起動しておく
		# EN: Warm up the start page so the embedded UI is ready
		start_url = self._get_resume_url() or _DEFAULT_START_URL
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not start_url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._start_page_ready and self._browser_session is not None:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return
			# EN: Assign value to running.
			# JP: running に値を代入する。
			running = self._is_running
			# EN: Assign value to shutdown.
			# JP: shutdown に値を代入する。
			shutdown = self._shutdown

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if running or shutdown:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# JP: 非同期でブラウザを起動し開始ページへ移動する
		# EN: Start the browser asynchronously and navigate to the start page
		async def _warmup() -> str | None:
			# EN: Assign value to session.
			# JP: session に値を代入する。
			session = await self._ensure_browser_session()
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.start()
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to start browser session during warmup', exc_info=True)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.attach_all_watchdogs()
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to pre-attach browser watchdogs during warmup', exc_info=True)

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.navigate_to(start_url, new_tab=False)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to warm up start URL %s', start_url, exc_info=True)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await session.get_current_page_url()
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to verify browser location after warmup', exc_info=True)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to future.
			# JP: future に値を代入する。
			future = asyncio.run_coroutine_threadsafe(_warmup(), self._loop)
			# EN: Assign value to current_url.
			# JP: current_url に値を代入する。
			current_url = future.result(timeout=20)
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug('Failed to prepare browser start page', exc_info=True)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if current_url and current_url.rstrip('/') != start_url.rstrip('/'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug(
				'Browser start page warmup navigated to %s instead of configured %s',
				current_url,
				start_url,
			)

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._browser_session is not None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._start_page_ready = True

	# EN: Define function `close_additional_tabs`.
	# JP: 関数 `close_additional_tabs` を定義する。
	def close_additional_tabs(self, refresh_url: str | None = None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Close all open tabs except the current focus and optionally refresh that tab.

		This is primarily used by the WebArena runner to guarantee that each task
		starts from a single, freshly loaded page even if the previous task spawned
		extra tabs.
		"""

		# JP: WebArena 実行前に不要なタブを閉じて安定性を確保する
		# EN: Close extra tabs before WebArena runs to keep the session stable
		async def _close() -> None:
			# EN: Assign value to session.
			# JP: session に値を代入する。
			session = await self._ensure_browser_session()
			# Enumerate tabs using the CDP helper for speed
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to tabs.
				# JP: tabs に値を代入する。
				tabs = await session.get_tabs()
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to enumerate tabs before cleanup', exc_info=True)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Assign value to current_target_id.
			# JP: current_target_id に値を代入する。
			current_target_id = session.agent_focus.target_id if session.agent_focus else None

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for tab in tabs:
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = getattr(tab, 'target_id', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not target_id:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if current_target_id and target_id == current_target_id:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with suppress(Exception):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await session._cdp_close_page(target_id)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await session.event_bus.dispatch(TabClosedEvent(target_id=target_id))

			# If requested, reload the retained tab to ensure a fresh state
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if refresh_url:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await session.navigate_to(refresh_url, new_tab=False)
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._logger.debug('Failed to refresh start page after tab cleanup', exc_info=True)

		# EN: Assign value to future.
		# JP: future に値を代入する。
		future = asyncio.run_coroutine_threadsafe(_close(), self._loop)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			future.result(timeout=10)
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._logger.debug('Tab cleanup encountered an error', exc_info=True)

	# EN: Define function `update_llm`.
	# JP: 関数 `update_llm` を定義する。
	def update_llm(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update the LLM instance based on current global settings."""
		# JP: 設定を読み直して新しい LLM を差し替える
		# EN: Reload settings and swap in a new LLM instance
		try:
			# EN: Assign value to new_llm.
			# JP: new_llm に値を代入する。
			new_llm = _create_selected_llm()
		except Exception as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError(f'新しいモデルの作成に失敗しました: {exc}') from exc

		# EN: Define async function `_apply_update`.
		# JP: 非同期関数 `_apply_update` を定義する。
		async def _apply_update() -> None:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with self._state_lock:
				# EN: Assign value to old_llm.
				# JP: old_llm に値を代入する。
				old_llm = self._llm
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._llm = new_llm

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._agent:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._agent.llm = new_llm
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._current_agent and self._current_agent is not self._agent:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._current_agent.llm = new_llm

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if old_llm:
				# EN: Assign value to aclose.
				# JP: aclose に値を代入する。
				aclose = getattr(old_llm, 'aclose', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if callable(aclose):
					# EN: Execute logic with managed resources.
					# JP: リソース管理付きで処理を実行する。
					with suppress(Exception):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await aclose()

		# EN: Assign value to future.
		# JP: future に値を代入する。
		future = asyncio.run_coroutine_threadsafe(_apply_update(), self._loop)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			future.result(timeout=10)
		except Exception as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError(f'モデルの更新処理に失敗しました: {exc}') from exc

	# EN: Define function `reset`.
	# JP: 関数 `reset` を定義する。
	def reset(self) -> None:
		# JP: 実行中でなければセッションと状態を完全に初期化する
		# EN: Fully reset session and state when not running
		with self._state_lock:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._is_running:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise AgentControllerError('エージェント実行中はリセットできません。')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._stop_browser_session()
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._agent = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._current_agent = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._paused = False
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._initial_prompt_handled = False
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._set_resume_url(None)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._clear_step_message_ids()

	# EN: Define function `set_vision_enabled`.
	# JP: 関数 `set_vision_enabled` を定義する。
	def set_vision_enabled(self, enabled: bool) -> None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._vision_enabled = bool(enabled)

	# EN: Define function `is_vision_enabled`.
	# JP: 関数 `is_vision_enabled` を定義する。
	def is_vision_enabled(self) -> bool:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._vision_enabled

	# EN: Define function `prepare_for_new_task`.
	# JP: 関数 `prepare_for_new_task` を定義する。
	def prepare_for_new_task(self) -> None:
		# JP: 新規タスク開始前にエージェント状態をクリアする
		# EN: Clear agent state before starting a new task
		with self._state_lock:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._is_running:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise AgentControllerError('エージェント実行中は新しいタスクを開始できません。')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._agent = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._current_agent = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._paused = False
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._initial_prompt_handled = False
		# EN: Evaluate an expression.
		# JP: 式を評価する。
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
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('エージェントコントローラーは停止済みです。')

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._lock:
			# EN: Assign value to future.
			# JP: future に値を代入する。
			future = asyncio.run_coroutine_threadsafe(
				self._run_agent(
					task,
					record_history=record_history,
					additional_system_message=additional_system_message,
					max_steps_override=max_steps,
				),
				self._loop,
			)
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with self._state_lock:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._initial_prompt_handled = True

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if background:

				# EN: Define function `_on_complete`.
				# JP: 関数 `_on_complete` を定義する。
				def _on_complete(f: Any) -> None:
					# JP: バックグラウンド完了時にコールバックへ通知する
					# EN: Notify completion callback when background run finishes
					if not completion_callback:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to result.
						# JP: result に値を代入する。
						result = f.result()
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						completion_callback(result)
					except Exception as exc:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						completion_callback(exc)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				future.add_done_callback(_on_complete)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return future.result()
			except AgentControllerError:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise
			except Exception as exc:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise AgentControllerError(str(exc)) from exc

	# EN: Define function `has_handled_initial_prompt`.
	# JP: 関数 `has_handled_initial_prompt` を定義する。
	def has_handled_initial_prompt(self) -> bool:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._initial_prompt_handled

	# EN: Define function `evaluate_in_browser`.
	# JP: 関数 `evaluate_in_browser` を定義する。
	def evaluate_in_browser(self, script: str) -> Any:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute JavaScript in the current browser session."""
		# JP: CDP 経由で JS を評価し、値だけを返す
		# EN: Evaluate JS via CDP and return the raw value
		if not self._browser_session:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('ブラウザセッションが存在しません。')

		# EN: Define async function `_eval`.
		# JP: 非同期関数 `_eval` を定義する。
		async def _eval() -> Any:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to session.
				# JP: session に値を代入する。
				session = await self._ensure_browser_session()
				# Ensure we have an active CDP session
				# EN: Assign value to cdp_session.
				# JP: cdp_session に値を代入する。
				cdp_session = await session.get_or_create_cdp_session()
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await cdp_session.cdp_client.send.Runtime.evaluate(
					params={'expression': script, 'returnByValue': True, 'awaitPromise': True}, session_id=cdp_session.session_id
				)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'exceptionDetails' in result:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise Exception(f'JS Evaluation failed: {result["exceptionDetails"]}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return result.get('result', {}).get('value')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.error(f'Failed to evaluate javascript: {e}')
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise

		# EN: Assign value to future.
		# JP: future に値を代入する。
		future = asyncio.run_coroutine_threadsafe(_eval(), self._loop)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return future.result(timeout=10)
		except Exception as exc:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError(f'JavaScriptの実行に失敗しました: {exc}') from exc

	# EN: Define function `mark_initial_prompt_handled`.
	# JP: 関数 `mark_initial_prompt_handled` を定義する。
	def mark_initial_prompt_handled(self) -> None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._initial_prompt_handled = True

	# EN: Define function `shutdown`.
	# JP: 関数 `shutdown` を定義する。
	def shutdown(self) -> None:
		# JP: シャットダウンフラグを立て、スレッド/セッションを安全に停止する
		# EN: Mark shutdown and safely stop thread/session resources
		if self._shutdown:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._shutdown = True
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._state_lock:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._agent = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._current_agent = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._paused = False
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._set_resume_url(None)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._clear_step_message_ids()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._loop.is_running():
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to future.
				# JP: future に値を代入する。
				future = asyncio.run_coroutine_threadsafe(self._async_shutdown(), self._loop)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				future.result(timeout=5)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._logger.debug('Failed to shut down agent loop cleanly', exc_info=True)
			finally:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._loop.is_running():
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._loop.call_soon_threadsafe(self._loop.stop)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._thread.is_alive():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._thread.join(timeout=2)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._cdp_cleanup:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._cdp_cleanup()
			finally:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._cdp_cleanup = None

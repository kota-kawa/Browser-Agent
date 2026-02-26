# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import EventBus

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.service import Agent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG


# EN: Define class `DummyLLM`.
# JP: クラス `DummyLLM` を定義する。
class DummyLLM:
	# EN: Assign value to model.
	# JP: model に値を代入する。
	model = 'dummy-model'
	# EN: Assign value to _verified_api_keys.
	# JP: _verified_api_keys に値を代入する。
	_verified_api_keys = True

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'dummy'

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'dummy'

	# EN: Define function `model_name`.
	# JP: 関数 `model_name` を定義する。
	@property
	def model_name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.model

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	async def ainvoke(self, messages, output_format=None):  # pragma: no cover - unused by this test
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise NotImplementedError


# EN: Define class `StubBrowserProfile`.
# JP: クラス `StubBrowserProfile` を定義する。
@dataclass
class StubBrowserProfile:
	# EN: Assign annotated value to downloads_path.
	# JP: downloads_path に型付きの値を代入する。
	downloads_path: str | None = None
	# EN: Assign annotated value to keep_alive.
	# JP: keep_alive に型付きの値を代入する。
	keep_alive: bool = True
	# EN: Assign annotated value to allowed_domains.
	# JP: allowed_domains に型付きの値を代入する。
	allowed_domains: list[str] | None = None
	# EN: Assign annotated value to viewport.
	# JP: viewport に型付きの値を代入する。
	viewport: dict[str, int] | None = None
	# EN: Assign annotated value to user_agent.
	# JP: user_agent に型付きの値を代入する。
	user_agent: str = 'stub-agent'
	# EN: Assign annotated value to headless.
	# JP: headless に型付きの値を代入する。
	headless: bool = True
	# EN: Assign annotated value to wait_between_actions.
	# JP: wait_between_actions に型付きの値を代入する。
	wait_between_actions: int = 0


# EN: Define class `FlakyBrowserSession`.
# JP: クラス `FlakyBrowserSession` を定義する。
class FlakyBrowserSession:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""A BrowserSession stub whose handler registration fails on the first attempt."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self) -> None:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.browser_profile = StubBrowserProfile(allowed_domains=[], viewport={'width': 1280, 'height': 720})
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.id = 'flaky-session'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.cdp_url = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.agent_focus = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.event_bus: EventBus = EventBus()
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.downloaded_files: list[str] = []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._watchdogs_attached = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cached_browser_state_summary = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._failures_remaining = 1

		# EN: Define function `_start_handler`.
		# JP: 関数 `_start_handler` を定義する。
		def _start_handler(event):  # pragma: no cover - handler never executed in test
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		_start_handler.__name__ = 'on_BrowserStartEvent'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._start_handler = _start_handler

	# EN: Define async function `start`.
	# JP: 非同期関数 `start` を定義する。
	async def start(self) -> None:  # pragma: no cover - unused by this test
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `kill`.
	# JP: 非同期関数 `kill` を定義する。
	async def kill(self) -> None:  # pragma: no cover - unused by this test
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `model_post_init`.
	# JP: 関数 `model_post_init` を定義する。
	def model_post_init(self, __context) -> None:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._failures_remaining > 0:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			self._failures_remaining -= 1
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError('Simulated duplicate handler registration')

		# EN: Assign value to handlers.
		# JP: handlers に値を代入する。
		handlers = self.event_bus.handlers.setdefault('BrowserStartEvent', [])
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._start_handler not in handlers:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			handlers.append(self._start_handler)

	# EN: Define async function `attach_all_watchdogs`.
	# JP: 非同期関数 `attach_all_watchdogs` を定義する。
	async def attach_all_watchdogs(self) -> None:
		# EN: Assign value to handlers.
		# JP: handlers に値を代入する。
		handlers = self.event_bus.handlers.setdefault('BrowserStartEvent', [])
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._start_handler not in handlers:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			handlers.append(self._start_handler)

	# EN: Define async function `get_browser_state_summary`.
	# JP: 非同期関数 `get_browser_state_summary` を定義する。
	async def get_browser_state_summary(self, *args, **kwargs):
		# EN: Assign value to handlers.
		# JP: handlers に値を代入する。
		handlers = self.event_bus.handlers.get('BrowserStartEvent', [])
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not handlers:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError('Expected at least one handler to handle BrowserStartEvent')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return object()


# EN: Define function `test_browser_session_eventbus_rotates_after_handler_registration_failure`.
# JP: 関数 `test_browser_session_eventbus_rotates_after_handler_registration_failure` を定義する。
def test_browser_session_eventbus_rotates_after_handler_registration_failure():
	# EN: Assign value to original_cloud_sync.
	# JP: original_cloud_sync に値を代入する。
	original_cloud_sync = CONFIG.BROWSER_USE_CLOUD_SYNC
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	CONFIG.BROWSER_USE_CLOUD_SYNC = False

	# EN: Define async function `_exercise`.
	# JP: 非同期関数 `_exercise` を定義する。
	async def _exercise() -> None:
		# EN: Assign value to session.
		# JP: session に値を代入する。
		session = FlakyBrowserSession()
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(
			task='test task',
			llm=DummyLLM(),
			browser_session=session,
			calculate_cost=False,
			directly_open_url=False,
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await session.get_browser_state_summary()

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		session._failures_remaining = 1
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		agent._refresh_browser_session_eventbus()

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await session.get_browser_state_summary()

		# EN: Assign value to handlers.
		# JP: handlers に値を代入する。
		handlers = session.event_bus.handlers.get('BrowserStartEvent', [])
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert handlers, 'Expected BrowserStartEvent handler to be registered after fallback rotation'

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		asyncio.run(_exercise())
	finally:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		CONFIG.BROWSER_USE_CLOUD_SYNC = original_cloud_sync

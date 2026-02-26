from __future__ import annotations

import asyncio
from dataclasses import dataclass

from bubus import EventBus

from browser_use.agent.service import Agent
from browser_use.config import CONFIG


# EN: Define class `DummyLLM`.
# JP: クラス `DummyLLM` を定義する。
class DummyLLM:
	model = 'dummy-model'
	_verified_api_keys = True

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		return 'dummy'

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str:
		return 'dummy'

	# EN: Define function `model_name`.
	# JP: 関数 `model_name` を定義する。
	@property
	def model_name(self) -> str:
		return self.model

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	async def ainvoke(self, messages, output_format=None):  # pragma: no cover - unused by this test
		raise NotImplementedError


# EN: Define class `StubBrowserProfile`.
# JP: クラス `StubBrowserProfile` を定義する。
@dataclass
class StubBrowserProfile:
	downloads_path: str | None = None
	keep_alive: bool = True
	allowed_domains: list[str] | None = None
	viewport: dict[str, int] | None = None
	user_agent: str = 'stub-agent'
	headless: bool = True
	wait_between_actions: int = 0


# EN: Define class `FlakyBrowserSession`.
# JP: クラス `FlakyBrowserSession` を定義する。
class FlakyBrowserSession:
	"""A BrowserSession stub whose handler registration fails on the first attempt."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self) -> None:
		self.browser_profile = StubBrowserProfile(allowed_domains=[], viewport={'width': 1280, 'height': 720})
		self.id = 'flaky-session'
		self.cdp_url = None
		self.agent_focus = None
		self.event_bus: EventBus = EventBus()
		self.downloaded_files: list[str] = []
		self._watchdogs_attached = False
		self._cached_browser_state_summary = None
		self._failures_remaining = 1

		# EN: Define function `_start_handler`.
		# JP: 関数 `_start_handler` を定義する。
		def _start_handler(event):  # pragma: no cover - handler never executed in test
			return None

		_start_handler.__name__ = 'on_BrowserStartEvent'
		self._start_handler = _start_handler

	# EN: Define async function `start`.
	# JP: 非同期関数 `start` を定義する。
	async def start(self) -> None:  # pragma: no cover - unused by this test
		return None

	# EN: Define async function `kill`.
	# JP: 非同期関数 `kill` を定義する。
	async def kill(self) -> None:  # pragma: no cover - unused by this test
		return None

	# EN: Define function `model_post_init`.
	# JP: 関数 `model_post_init` を定義する。
	def model_post_init(self, __context) -> None:
		if self._failures_remaining > 0:
			self._failures_remaining -= 1
			raise RuntimeError('Simulated duplicate handler registration')

		handlers = self.event_bus.handlers.setdefault('BrowserStartEvent', [])
		if self._start_handler not in handlers:
			handlers.append(self._start_handler)

	# EN: Define async function `attach_all_watchdogs`.
	# JP: 非同期関数 `attach_all_watchdogs` を定義する。
	async def attach_all_watchdogs(self) -> None:
		handlers = self.event_bus.handlers.setdefault('BrowserStartEvent', [])
		if self._start_handler not in handlers:
			handlers.append(self._start_handler)

	# EN: Define async function `get_browser_state_summary`.
	# JP: 非同期関数 `get_browser_state_summary` を定義する。
	async def get_browser_state_summary(self, *args, **kwargs):
		handlers = self.event_bus.handlers.get('BrowserStartEvent', [])
		if not handlers:
			raise ValueError('Expected at least one handler to handle BrowserStartEvent')
		return object()


# EN: Define function `test_browser_session_eventbus_rotates_after_handler_registration_failure`.
# JP: 関数 `test_browser_session_eventbus_rotates_after_handler_registration_failure` を定義する。
def test_browser_session_eventbus_rotates_after_handler_registration_failure():
	original_cloud_sync = CONFIG.BROWSER_USE_CLOUD_SYNC
	CONFIG.BROWSER_USE_CLOUD_SYNC = False

	# EN: Define async function `_exercise`.
	# JP: 非同期関数 `_exercise` を定義する。
	async def _exercise() -> None:
		session = FlakyBrowserSession()
		agent = Agent(
			task='test task',
			llm=DummyLLM(),
			browser_session=session,
			calculate_cost=False,
			directly_open_url=False,
		)

		await session.get_browser_state_summary()

		session._failures_remaining = 1
		agent._refresh_browser_session_eventbus()

		await session.get_browser_state_summary()

		handlers = session.event_bus.handlers.get('BrowserStartEvent', [])
		assert handlers, 'Expected BrowserStartEvent handler to be registered after fallback rotation'

	try:
		asyncio.run(_exercise())
	finally:
		CONFIG.BROWSER_USE_CLOUD_SYNC = original_cloud_sync

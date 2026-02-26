# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from types import MethodType

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pytest

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.service import Agent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import ActionResult, AgentHistory
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.constants import DEFAULT_NEW_TAB_URL
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserStateHistory
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
	async def ainvoke(self, messages, output_format=None):  # pragma: no cover - unused by these tests
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise NotImplementedError


# EN: Define class `StubBrowserProfile`.
# JP: クラス `StubBrowserProfile` を定義する。
class StubBrowserProfile:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self) -> None:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.downloads_path = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.keep_alive = True
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.allowed_domains: list[str] = []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.viewport = {'width': 1280, 'height': 720}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.user_agent = 'stub-agent'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.headless = True
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.wait_between_actions = 0


# EN: Define class `StubBrowserSession`.
# JP: クラス `StubBrowserSession` を定義する。
class StubBrowserSession:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self) -> None:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.browser_profile = StubBrowserProfile()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.id = 'stub-session'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.cdp_url = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.agent_focus = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.event_bus = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.downloaded_files: list[str] = []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._watchdogs_attached = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cached_browser_state_summary = None

	# EN: Define async function `start`.
	# JP: 非同期関数 `start` を定義する。
	async def start(self) -> None:  # pragma: no cover - simple stub
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `kill`.
	# JP: 非同期関数 `kill` を定義する。
	async def kill(self) -> None:  # pragma: no cover - simple stub
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `model_post_init`.
	# JP: 関数 `model_post_init` を定義する。
	def model_post_init(self, __context) -> None:  # pragma: no cover - simple stub
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None


# EN: Define function `_history_state`.
# JP: 関数 `_history_state` を定義する。
def _history_state() -> BrowserStateHistory:
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return BrowserStateHistory(
		url='',
		title='',
		tabs=[],
		interacted_element=[],
		screenshot_path=None,
	)


# EN: Define async function `test_follow_up_run_resets_done_flags_and_executes_steps`.
# JP: 非同期関数 `test_follow_up_run_resets_done_flags_and_executes_steps` を定義する。
@pytest.mark.asyncio
async def test_follow_up_run_resets_done_flags_and_executes_steps():
	# EN: Assign value to original_cloud_sync.
	# JP: original_cloud_sync に値を代入する。
	original_cloud_sync = CONFIG.BROWSER_USE_CLOUD_SYNC
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	CONFIG.BROWSER_USE_CLOUD_SYNC = False

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(
			task='initial task',
			llm=DummyLLM(),
			browser_session=StubBrowserSession(),
			calculate_cost=False,
			directly_open_url=False,
		)

		# EN: Define async function `noop_initial_actions`.
		# JP: 非同期関数 `noop_initial_actions` を定義する。
		async def noop_initial_actions(self):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		agent._execute_initial_actions = MethodType(noop_initial_actions, agent)

		# EN: Define async function `first_run_step`.
		# JP: 非同期関数 `first_run_step` を定義する。
		async def first_run_step(self, step_info):
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = [ActionResult(is_done=True, success=True)]
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.state.last_result = result
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.history.add_item(
				AgentHistory(
					model_output=None,
					result=result,
					state=_history_state(),
					metadata=None,
				)
			)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		agent.step = MethodType(first_run_step, agent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await agent.run(max_steps=1)

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.history.is_done()
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.state.last_result[-1].is_done is True
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.history.history[-1].result[-1].is_done is True

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		agent.add_new_task('follow-up instructions')

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.state.follow_up_task is True
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.state.last_result[-1].is_done is False
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.state.last_result[-1].success is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.history.history[-1].result[-1].is_done is False
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.history.history[-1].result[-1].success is None

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.reset_completion_state() is False

		# EN: Assign value to step_calls.
		# JP: step_calls に値を代入する。
		step_calls = {'count': 0}

		# EN: Define async function `failing_step`.
		# JP: 非同期関数 `failing_step` を定義する。
		async def failing_step(self, step_info):
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			step_calls['count'] += 1
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = [ActionResult(error='boom', is_done=False)]
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.state.last_result = result
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.history.add_item(
				AgentHistory(
					model_output=None,
					result=result,
					state=_history_state(),
					metadata=None,
				)
			)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		agent.step = MethodType(failing_step, agent)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await agent.run(max_steps=1)

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert step_calls['count'] == 1
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.state.last_result[-1].error == 'boom'
	finally:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		CONFIG.BROWSER_USE_CLOUD_SYNC = original_cloud_sync


# EN: Define function `test_add_new_task_clears_user_payloads_across_runs`.
# JP: 関数 `test_add_new_task_clears_user_payloads_across_runs` を定義する。
def test_add_new_task_clears_user_payloads_across_runs():
	# EN: Assign value to original_cloud_sync.
	# JP: original_cloud_sync に値を代入する。
	original_cloud_sync = CONFIG.BROWSER_USE_CLOUD_SYNC
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	CONFIG.BROWSER_USE_CLOUD_SYNC = False

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(
			task='initial task',
			llm=DummyLLM(),
			browser_session=StubBrowserSession(),
			calculate_cost=False,
			directly_open_url=False,
		)

		# EN: Assign value to first_result.
		# JP: first_result に値を代入する。
		first_result = [
			ActionResult(
				is_done=True,
				success=True,
				extracted_content='first run content',
				long_term_memory='memory',
				attachments=['file.txt'],
				error='boom',
				metadata={'source': 'first'},
				include_extracted_content_only_once=True,
				include_in_memory=True,
			)
		]

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		agent.state.last_result = first_result
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		agent.history.add_item(
			AgentHistory(
				model_output=None,
				result=first_result,
				state=_history_state(),
				metadata=None,
			)
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		agent.add_new_task('follow-up 1')

		# EN: Assign value to cleared_result.
		# JP: cleared_result に値を代入する。
		cleared_result = agent.state.last_result[-1]
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_result.extracted_content is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_result.long_term_memory is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_result.attachments == []
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_result.error is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_result.metadata is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_result.include_extracted_content_only_once is False
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_result.include_in_memory is False

		# EN: Assign value to history_result.
		# JP: history_result に値を代入する。
		history_result = agent.history.history[-1].result[-1]
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert history_result.extracted_content is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert history_result.long_term_memory is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert history_result.attachments == []
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert history_result.error is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert history_result.metadata is None

		# EN: Assign value to second_result.
		# JP: second_result に値を代入する。
		second_result = [
			ActionResult(
				is_done=True,
				success=True,
				extracted_content='second run content',
				attachments=['second.txt'],
			)
		]

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		agent.state.last_result = second_result
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		agent.history.add_item(
			AgentHistory(
				model_output=None,
				result=second_result,
				state=_history_state(),
				metadata=None,
			)
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		agent.add_new_task('follow-up 2')

		# EN: Assign value to cleared_second_result.
		# JP: cleared_second_result に値を代入する。
		cleared_second_result = agent.state.last_result[-1]
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_second_result.extracted_content is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleared_second_result.attachments == []

		# EN: Assign value to second_history_result.
		# JP: second_history_result に値を代入する。
		second_history_result = agent.history.history[-1].result[-1]
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert second_history_result.extracted_content is None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert second_history_result.attachments == []
	finally:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		CONFIG.BROWSER_USE_CLOUD_SYNC = original_cloud_sync


# EN: Define function `test_add_new_task_rotates_legacy_eventbus_while_running`.
# JP: 関数 `test_add_new_task_rotates_legacy_eventbus_while_running` を定義する。
def test_add_new_task_rotates_legacy_eventbus_while_running():
	# EN: Assign value to original_cloud_sync.
	# JP: original_cloud_sync に値を代入する。
	original_cloud_sync = CONFIG.BROWSER_USE_CLOUD_SYNC
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	CONFIG.BROWSER_USE_CLOUD_SYNC = False

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(
			task='initial task',
			llm=DummyLLM(),
			browser_session=StubBrowserSession(),
			calculate_cost=False,
			directly_open_url=False,
		)

		# EN: Define class `LegacyEventBus`.
		# JP: クラス `LegacyEventBus` を定義する。
		class LegacyEventBus:
			# EN: Define function `__init__`.
			# JP: 関数 `__init__` を定義する。
			def __init__(self) -> None:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.name = 'Agent_000-legacy'
				# EN: Assign annotated value to target variable.
				# JP: target variable に型付きの値を代入する。
				self.handlers: dict[str, list] = {}
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.stop_calls = 0

			# EN: Define async function `stop`.
			# JP: 非同期関数 `stop` を定義する。
			async def stop(self, *, timeout: float = 3.0) -> None:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				self.stop_calls += 1

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		agent.eventbus = LegacyEventBus()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		agent._reserved_eventbus_name = 'Agent_000-legacy'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		agent.running = True

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		agent.add_new_task('follow-up instructions')

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.eventbus.name != 'Agent_000-legacy'
	finally:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		CONFIG.BROWSER_USE_CLOUD_SYNC = original_cloud_sync


# EN: Define function `test_agent_starts_with_yahoo_initial_action`.
# JP: 関数 `test_agent_starts_with_yahoo_initial_action` を定義する。
def test_agent_starts_with_yahoo_initial_action():
	# EN: Assign value to original_cloud_sync.
	# JP: original_cloud_sync に値を代入する。
	original_cloud_sync = CONFIG.BROWSER_USE_CLOUD_SYNC
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	CONFIG.BROWSER_USE_CLOUD_SYNC = False

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(
			task='summarize the latest headlines',
			llm=DummyLLM(),
			browser_session=StubBrowserSession(),
			calculate_cost=False,
		)

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.initial_url == DEFAULT_NEW_TAB_URL
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert agent.initial_actions is not None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(agent.initial_actions) == 1
		# EN: Assign value to action.
		# JP: action に値を代入する。
		action = agent.initial_actions[0]
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert hasattr(action, 'go_to_url')
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert action.go_to_url.url == DEFAULT_NEW_TAB_URL
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert action.go_to_url.new_tab is False
	finally:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		CONFIG.BROWSER_USE_CLOUD_SYNC = original_cloud_sync

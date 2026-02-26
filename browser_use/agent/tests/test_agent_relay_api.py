# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import sys
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import types
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import typing

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pytest
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from starlette.requests import Request

# EN: Assign value to psutil_stub.
# JP: psutil_stub に値を代入する。
psutil_stub = types.ModuleType('psutil')


# EN: Define class `_ProcessStub`.
# JP: クラス `_ProcessStub` を定義する。
class _ProcessStub:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, pid: int):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._pid = pid

	# EN: Define function `cmdline`.
	# JP: 関数 `cmdline` を定義する。
	def cmdline(self):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return []


# EN: Assign value to target variable.
# JP: target variable に値を代入する。
psutil_stub.Process = _ProcessStub
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
psutil_stub.pids = lambda: [1]
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('psutil', psutil_stub)

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if not hasattr(typing, 'Self'):
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	typing.Self = typing.TypeVar('Self')

# Minimal stubs to keep API tests lightweight when optional runtime deps are missing.
# EN: Assign value to bubus_stub.
# JP: bubus_stub に値を代入する。
bubus_stub = types.ModuleType('bubus')


# EN: Define class `_EventBusStub`.
# JP: クラス `_EventBusStub` を定義する。
class _EventBusStub:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, name: str | None = None):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.name = name or 'stub'

	# EN: Define function `_handler_dispatched_ancestor`.
	# JP: 関数 `_handler_dispatched_ancestor` を定義する。
	def _handler_dispatched_ancestor(self, event, handler_id):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 0


# EN: Define class `_BaseEventStub`.
# JP: クラス `_BaseEventStub` を定義する。
class _BaseEventStub:
	# EN: Define function `__class_getitem__`.
	# JP: 関数 `__class_getitem__` を定義する。
	def __class_getitem__(cls, _item):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls


# EN: Assign value to target variable.
# JP: target variable に値を代入する。
bubus_stub.EventBus = _EventBusStub
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
bubus_stub.BaseEvent = _BaseEventStub
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('bubus', bubus_stub)

# EN: Assign value to service_stub.
# JP: service_stub に値を代入する。
service_stub = types.ModuleType('bubus.service')


# EN: Define function `_get_handler_id`.
# JP: 関数 `_get_handler_id` を定義する。
def _get_handler_id(handler, bus=None):
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return f'{getattr(handler, "__name__", "handler")}:stub'


# EN: Define function `_get_handler_name`.
# JP: 関数 `_get_handler_name` を定義する。
def _get_handler_name(handler):
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return getattr(handler, '__name__', 'handler')


# EN: Assign value to target variable.
# JP: target variable に値を代入する。
service_stub.get_handler_id = _get_handler_id
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
service_stub.get_handler_name = _get_handler_name
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
service_stub.logger = logging.getLogger('bubus')
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('bubus.service', service_stub)

# EN: Assign value to models_stub.
# JP: models_stub に値を代入する。
models_stub = types.ModuleType('bubus.models')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
models_stub.T_EventResultType = object
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('bubus.models', models_stub)

# EN: Assign value to uuid_extensions_stub.
# JP: uuid_extensions_stub に値を代入する。
uuid_extensions_stub = types.ModuleType('uuid_extensions')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
uuid_extensions_stub.uuid7str = lambda: '00000000-0000-7000-0000-000000000000'
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('uuid_extensions', uuid_extensions_stub)

# EN: Assign value to cdp_use_stub.
# JP: cdp_use_stub に値を代入する。
cdp_use_stub = types.ModuleType('cdp_use')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_stub.__path__ = []
# EN: Assign value to cdp_use_cdp_stub.
# JP: cdp_use_cdp_stub に値を代入する。
cdp_use_cdp_stub = types.ModuleType('cdp_use.cdp')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_cdp_stub.__path__ = []

# EN: Assign value to cdp_use_accessibility_stub.
# JP: cdp_use_accessibility_stub に値を代入する。
cdp_use_accessibility_stub = types.ModuleType('cdp_use.cdp.accessibility')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_accessibility_stub.__path__ = []
# EN: Assign value to cdp_use_accessibility_commands_stub.
# JP: cdp_use_accessibility_commands_stub に値を代入する。
cdp_use_accessibility_commands_stub = types.ModuleType('cdp_use.cdp.accessibility.commands')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_accessibility_commands_stub.GetFullAXTreeReturns = dict
# EN: Assign value to cdp_use_accessibility_types_stub.
# JP: cdp_use_accessibility_types_stub に値を代入する。
cdp_use_accessibility_types_stub = types.ModuleType('cdp_use.cdp.accessibility.types')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_accessibility_types_stub.AXPropertyName = str
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_accessibility_types_stub.AXNode = dict

# EN: Assign value to cdp_use_dom_stub.
# JP: cdp_use_dom_stub に値を代入する。
cdp_use_dom_stub = types.ModuleType('cdp_use.cdp.dom')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_dom_stub.__path__ = []
# EN: Assign value to cdp_use_dom_commands_stub.
# JP: cdp_use_dom_commands_stub に値を代入する。
cdp_use_dom_commands_stub = types.ModuleType('cdp_use.cdp.dom.commands')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_dom_commands_stub.GetDocumentReturns = dict
# EN: Assign value to cdp_use_dom_types_stub.
# JP: cdp_use_dom_types_stub に値を代入する。
cdp_use_dom_types_stub = types.ModuleType('cdp_use.cdp.dom.types')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_dom_types_stub.ShadowRootType = str
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_dom_types_stub.Node = dict

# EN: Assign value to cdp_use_domsnapshot_stub.
# JP: cdp_use_domsnapshot_stub に値を代入する。
cdp_use_domsnapshot_stub = types.ModuleType('cdp_use.cdp.domsnapshot')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_domsnapshot_stub.__path__ = []
# EN: Assign value to cdp_use_domsnapshot_commands_stub.
# JP: cdp_use_domsnapshot_commands_stub に値を代入する。
cdp_use_domsnapshot_commands_stub = types.ModuleType('cdp_use.cdp.domsnapshot.commands')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_domsnapshot_commands_stub.CaptureSnapshotReturns = dict

# EN: Assign value to cdp_use_target_stub.
# JP: cdp_use_target_stub に値を代入する。
cdp_use_target_stub = types.ModuleType('cdp_use.cdp.target')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_target_stub.TargetID = str
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_target_stub.SessionID = str
# EN: Assign value to cdp_use_target_types_stub.
# JP: cdp_use_target_types_stub に値を代入する。
cdp_use_target_types_stub = types.ModuleType('cdp_use.cdp.target.types')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_target_types_stub.SessionID = str
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_target_types_stub.TargetID = str
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
cdp_use_target_types_stub.TargetInfo = dict

# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use', cdp_use_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp', cdp_use_cdp_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.accessibility', cdp_use_accessibility_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.accessibility.commands', cdp_use_accessibility_commands_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.accessibility.types', cdp_use_accessibility_types_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.dom', cdp_use_dom_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.dom.commands', cdp_use_dom_commands_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.dom.types', cdp_use_dom_types_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.domsnapshot', cdp_use_domsnapshot_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.domsnapshot.commands', cdp_use_domsnapshot_commands_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.target', cdp_use_target_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('cdp_use.cdp.target.types', cdp_use_target_types_stub)

# EN: Assign value to reportlab_stub.
# JP: reportlab_stub に値を代入する。
reportlab_stub = types.ModuleType('reportlab')
# EN: Assign value to reportlab_lib_stub.
# JP: reportlab_lib_stub に値を代入する。
reportlab_lib_stub = types.ModuleType('reportlab.lib')
# EN: Assign value to reportlab_pagesizes_stub.
# JP: reportlab_pagesizes_stub に値を代入する。
reportlab_pagesizes_stub = types.ModuleType('reportlab.lib.pagesizes')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
reportlab_pagesizes_stub.letter = (612, 792)
# EN: Assign value to reportlab_styles_stub.
# JP: reportlab_styles_stub に値を代入する。
reportlab_styles_stub = types.ModuleType('reportlab.lib.styles')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
reportlab_styles_stub.getSampleStyleSheet = lambda: {}
# EN: Assign value to reportlab_platypus_stub.
# JP: reportlab_platypus_stub に値を代入する。
reportlab_platypus_stub = types.ModuleType('reportlab.platypus')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
reportlab_platypus_stub.Paragraph = object
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
reportlab_platypus_stub.SimpleDocTemplate = object
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
reportlab_platypus_stub.Spacer = object

# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('reportlab', reportlab_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('reportlab.lib', reportlab_lib_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('reportlab.lib.pagesizes', reportlab_pagesizes_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('reportlab.lib.styles', reportlab_styles_stub)
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('reportlab.platypus', reportlab_platypus_stub)

# EN: Assign value to browser_use_browser_stub.
# JP: browser_use_browser_stub に値を代入する。
browser_use_browser_stub = types.ModuleType('browser_use.browser')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_browser_stub.__path__ = []


# EN: Define class `_BrowserSessionStub`.
# JP: クラス `_BrowserSessionStub` を定義する。
class _BrowserSessionStub:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_browser_stub.BrowserSession = _BrowserSessionStub
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('browser_use.browser', browser_use_browser_stub)

# EN: Assign value to browser_use_browser_views_stub.
# JP: browser_use_browser_views_stub に値を代入する。
browser_use_browser_views_stub = types.ModuleType('browser_use.browser.views')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_browser_views_stub.BrowserStateHistory = type('BrowserStateHistory', (), {})
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_browser_views_stub.BrowserStateSummary = type('BrowserStateSummary', (), {})
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('browser_use.browser.views', browser_use_browser_views_stub)

# EN: Assign value to browser_use_browser_events_stub.
# JP: browser_use_browser_events_stub に値を代入する。
browser_use_browser_events_stub = types.ModuleType('browser_use.browser.events')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_browser_events_stub.TabClosedEvent = type('TabClosedEvent', (), {})
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('browser_use.browser.events', browser_use_browser_events_stub)

# EN: Assign value to browser_use_browser_profile_stub.
# JP: browser_use_browser_profile_stub に値を代入する。
browser_use_browser_profile_stub = types.ModuleType('browser_use.browser.profile')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_browser_profile_stub.ViewportSize = type('ViewportSize', (), {})
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('browser_use.browser.profile', browser_use_browser_profile_stub)

# EN: Assign value to browser_use_dom_views_stub.
# JP: browser_use_dom_views_stub に値を代入する。
browser_use_dom_views_stub = types.ModuleType('browser_use.dom.views')
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_dom_views_stub.DEFAULT_INCLUDE_ATTRIBUTES = []
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_dom_views_stub.DOMInteractedElement = object
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use_dom_views_stub.DOMSelectorMap = dict
# EN: Evaluate an expression.
# JP: 式を評価する。
sys.modules.setdefault('browser_use.dom.views', browser_use_dom_views_stub)

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import browser_use

# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use.Agent = type('Agent', (), {})
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use.BrowserProfile = type('BrowserProfile', (), {})
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use.BrowserSession = type('BrowserSession', (), {})
# EN: Assign value to target variable.
# JP: target variable に値を代入する。
browser_use.Tools = type('Tools', (), {})

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi_app.routes import api_chat as api_chat_module


# EN: Define class `_StubController`.
# JP: クラス `_StubController` を定義する。
class _StubController:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, *, paused: bool = False):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._paused = paused
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.enqueue_calls: list[str] = []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.resume_called = False

	# EN: Define function `is_running`.
	# JP: 関数 `is_running` を定義する。
	def is_running(self) -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Define function `is_paused`.
	# JP: 関数 `is_paused` を定義する。
	def is_paused(self) -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._paused

	# EN: Define function `enqueue_follow_up`.
	# JP: 関数 `enqueue_follow_up` を定義する。
	def enqueue_follow_up(self, prompt: str) -> None:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.enqueue_calls.append(prompt)

	# EN: Define function `resume`.
	# JP: 関数 `resume` を定義する。
	def resume(self) -> None:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.resume_called = True
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._paused = False


# EN: Define function `_build_request`.
# JP: 関数 `_build_request` を定義する。
def _build_request(payload: dict) -> Request:
	# EN: Assign value to body.
	# JP: body に値を代入する。
	body = json.dumps(payload).encode('utf-8')

	# EN: Define async function `receive`.
	# JP: 非同期関数 `receive` を定義する。
	async def receive():
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {'type': 'http.request', 'body': body, 'more_body': False}

	# EN: Assign value to scope.
	# JP: scope に値を代入する。
	scope = {
		'type': 'http',
		'method': 'POST',
		'path': '/api/agent-relay',
		'headers': [(b'content-type', b'application/json')],
	}
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return Request(scope, receive)


# EN: Define function `_run_async`.
# JP: 関数 `_run_async` を定義する。
def _run_async(coro):
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return asyncio.run(coro)


# EN: Define function `test_agent_relay_enqueues_follow_up_when_running`.
# JP: 関数 `test_agent_relay_enqueues_follow_up_when_running` を定義する。
@pytest.mark.unit
def test_agent_relay_enqueues_follow_up_when_running(monkeypatch):
	# EN: Assign value to controller.
	# JP: controller に値を代入する。
	controller = _StubController()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	monkeypatch.setattr(api_chat_module, 'get_agent_controller', lambda: controller)
	# EN: Assign value to request.
	# JP: request に値を代入する。
	request = _build_request({'prompt': '最新ニュースをチェック'})
	# EN: Assign value to response.
	# JP: response に値を代入する。
	response = _run_async(api_chat_module.agent_relay(request))

	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert response.status_code == 202
	# EN: Assign value to payload.
	# JP: payload に値を代入する。
	payload = json.loads(response.body.decode('utf-8'))
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert payload['status'] == 'follow_up_enqueued'
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert payload['agent_running'] is True
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert payload['queued'] is True
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert controller.enqueue_calls == ['最新ニュースをチェック']
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert controller.resume_called is False


# EN: Define function `test_agent_relay_resumes_when_paused`.
# JP: 関数 `test_agent_relay_resumes_when_paused` を定義する。
@pytest.mark.unit
def test_agent_relay_resumes_when_paused(monkeypatch):
	# EN: Assign value to controller.
	# JP: controller に値を代入する。
	controller = _StubController(paused=True)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	monkeypatch.setattr(api_chat_module, 'get_agent_controller', lambda: controller)
	# EN: Assign value to request.
	# JP: request に値を代入する。
	request = _build_request({'prompt': '追加の操作を開始'})
	# EN: Assign value to response.
	# JP: response に値を代入する。
	response = _run_async(api_chat_module.agent_relay(request))

	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert response.status_code == 202
	# EN: Assign value to payload.
	# JP: payload に値を代入する。
	payload = json.loads(response.body.decode('utf-8'))
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert payload['status'] == 'follow_up_enqueued'
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert payload['agent_running'] is True
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert controller.enqueue_calls == ['追加の操作を開始']
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert controller.resume_called is True

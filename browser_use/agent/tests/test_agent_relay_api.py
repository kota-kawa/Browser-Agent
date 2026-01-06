from __future__ import annotations

import logging
import sys
import types
import typing

import asyncio
import json

import pytest
from starlette.requests import Request

psutil_stub = types.ModuleType('psutil')


class _ProcessStub:
	def __init__(self, pid: int):
		self._pid = pid

	def cmdline(self):
		return []


psutil_stub.Process = _ProcessStub
psutil_stub.pids = lambda: [1]
sys.modules.setdefault('psutil', psutil_stub)

if not hasattr(typing, 'Self'):
	typing.Self = typing.TypeVar('Self')

# Minimal stubs to keep API tests lightweight when optional runtime deps are missing.
bubus_stub = types.ModuleType('bubus')


class _EventBusStub:
	def __init__(self, name: str | None = None):
		self.name = name or 'stub'

	def _handler_dispatched_ancestor(self, event, handler_id):
		return 0


class _BaseEventStub:
	def __class_getitem__(cls, _item):
		return cls


bubus_stub.EventBus = _EventBusStub
bubus_stub.BaseEvent = _BaseEventStub
sys.modules.setdefault('bubus', bubus_stub)

service_stub = types.ModuleType('bubus.service')


def _get_handler_id(handler, bus=None):
	return f'{getattr(handler, "__name__", "handler")}:stub'


def _get_handler_name(handler):
	return getattr(handler, '__name__', 'handler')


service_stub.get_handler_id = _get_handler_id
service_stub.get_handler_name = _get_handler_name
service_stub.logger = logging.getLogger('bubus')
sys.modules.setdefault('bubus.service', service_stub)

models_stub = types.ModuleType('bubus.models')
models_stub.T_EventResultType = object
sys.modules.setdefault('bubus.models', models_stub)

uuid_extensions_stub = types.ModuleType('uuid_extensions')
uuid_extensions_stub.uuid7str = lambda: '00000000-0000-7000-0000-000000000000'
sys.modules.setdefault('uuid_extensions', uuid_extensions_stub)

cdp_use_stub = types.ModuleType('cdp_use')
cdp_use_stub.__path__ = []
cdp_use_cdp_stub = types.ModuleType('cdp_use.cdp')
cdp_use_cdp_stub.__path__ = []

cdp_use_accessibility_stub = types.ModuleType('cdp_use.cdp.accessibility')
cdp_use_accessibility_stub.__path__ = []
cdp_use_accessibility_commands_stub = types.ModuleType('cdp_use.cdp.accessibility.commands')
cdp_use_accessibility_commands_stub.GetFullAXTreeReturns = dict
cdp_use_accessibility_types_stub = types.ModuleType('cdp_use.cdp.accessibility.types')
cdp_use_accessibility_types_stub.AXPropertyName = str
cdp_use_accessibility_types_stub.AXNode = dict

cdp_use_dom_stub = types.ModuleType('cdp_use.cdp.dom')
cdp_use_dom_stub.__path__ = []
cdp_use_dom_commands_stub = types.ModuleType('cdp_use.cdp.dom.commands')
cdp_use_dom_commands_stub.GetDocumentReturns = dict
cdp_use_dom_types_stub = types.ModuleType('cdp_use.cdp.dom.types')
cdp_use_dom_types_stub.ShadowRootType = str
cdp_use_dom_types_stub.Node = dict

cdp_use_domsnapshot_stub = types.ModuleType('cdp_use.cdp.domsnapshot')
cdp_use_domsnapshot_stub.__path__ = []
cdp_use_domsnapshot_commands_stub = types.ModuleType('cdp_use.cdp.domsnapshot.commands')
cdp_use_domsnapshot_commands_stub.CaptureSnapshotReturns = dict

cdp_use_target_stub = types.ModuleType('cdp_use.cdp.target')
cdp_use_target_stub.TargetID = str
cdp_use_target_stub.SessionID = str
cdp_use_target_types_stub = types.ModuleType('cdp_use.cdp.target.types')
cdp_use_target_types_stub.SessionID = str
cdp_use_target_types_stub.TargetID = str
cdp_use_target_types_stub.TargetInfo = dict

sys.modules.setdefault('cdp_use', cdp_use_stub)
sys.modules.setdefault('cdp_use.cdp', cdp_use_cdp_stub)
sys.modules.setdefault('cdp_use.cdp.accessibility', cdp_use_accessibility_stub)
sys.modules.setdefault('cdp_use.cdp.accessibility.commands', cdp_use_accessibility_commands_stub)
sys.modules.setdefault('cdp_use.cdp.accessibility.types', cdp_use_accessibility_types_stub)
sys.modules.setdefault('cdp_use.cdp.dom', cdp_use_dom_stub)
sys.modules.setdefault('cdp_use.cdp.dom.commands', cdp_use_dom_commands_stub)
sys.modules.setdefault('cdp_use.cdp.dom.types', cdp_use_dom_types_stub)
sys.modules.setdefault('cdp_use.cdp.domsnapshot', cdp_use_domsnapshot_stub)
sys.modules.setdefault('cdp_use.cdp.domsnapshot.commands', cdp_use_domsnapshot_commands_stub)
sys.modules.setdefault('cdp_use.cdp.target', cdp_use_target_stub)
sys.modules.setdefault('cdp_use.cdp.target.types', cdp_use_target_types_stub)

reportlab_stub = types.ModuleType('reportlab')
reportlab_lib_stub = types.ModuleType('reportlab.lib')
reportlab_pagesizes_stub = types.ModuleType('reportlab.lib.pagesizes')
reportlab_pagesizes_stub.letter = (612, 792)
reportlab_styles_stub = types.ModuleType('reportlab.lib.styles')
reportlab_styles_stub.getSampleStyleSheet = lambda: {}
reportlab_platypus_stub = types.ModuleType('reportlab.platypus')
reportlab_platypus_stub.Paragraph = object
reportlab_platypus_stub.SimpleDocTemplate = object
reportlab_platypus_stub.Spacer = object

sys.modules.setdefault('reportlab', reportlab_stub)
sys.modules.setdefault('reportlab.lib', reportlab_lib_stub)
sys.modules.setdefault('reportlab.lib.pagesizes', reportlab_pagesizes_stub)
sys.modules.setdefault('reportlab.lib.styles', reportlab_styles_stub)
sys.modules.setdefault('reportlab.platypus', reportlab_platypus_stub)

browser_use_browser_stub = types.ModuleType('browser_use.browser')
browser_use_browser_stub.__path__ = []


class _BrowserSessionStub:
	pass


browser_use_browser_stub.BrowserSession = _BrowserSessionStub
sys.modules.setdefault('browser_use.browser', browser_use_browser_stub)

browser_use_browser_views_stub = types.ModuleType('browser_use.browser.views')
browser_use_browser_views_stub.BrowserStateHistory = type('BrowserStateHistory', (), {})
browser_use_browser_views_stub.BrowserStateSummary = type('BrowserStateSummary', (), {})
sys.modules.setdefault('browser_use.browser.views', browser_use_browser_views_stub)

browser_use_browser_events_stub = types.ModuleType('browser_use.browser.events')
browser_use_browser_events_stub.TabClosedEvent = type('TabClosedEvent', (), {})
sys.modules.setdefault('browser_use.browser.events', browser_use_browser_events_stub)

browser_use_browser_profile_stub = types.ModuleType('browser_use.browser.profile')
browser_use_browser_profile_stub.ViewportSize = type('ViewportSize', (), {})
sys.modules.setdefault('browser_use.browser.profile', browser_use_browser_profile_stub)

browser_use_dom_views_stub = types.ModuleType('browser_use.dom.views')
browser_use_dom_views_stub.DEFAULT_INCLUDE_ATTRIBUTES = []
browser_use_dom_views_stub.DOMInteractedElement = object
browser_use_dom_views_stub.DOMSelectorMap = dict
sys.modules.setdefault('browser_use.dom.views', browser_use_dom_views_stub)

import browser_use

browser_use.Agent = type('Agent', (), {})
browser_use.BrowserProfile = type('BrowserProfile', (), {})
browser_use.BrowserSession = type('BrowserSession', (), {})
browser_use.Tools = type('Tools', (), {})

from flask_app.routes import api_chat as api_chat_module


class _StubController:
	def __init__(self, *, paused: bool = False):
		self._paused = paused
		self.enqueue_calls: list[str] = []
		self.resume_called = False

	def is_running(self) -> bool:
		return True

	def is_paused(self) -> bool:
		return self._paused

	def enqueue_follow_up(self, prompt: str) -> None:
		self.enqueue_calls.append(prompt)

	def resume(self) -> None:
		self.resume_called = True
		self._paused = False


def _build_request(payload: dict) -> Request:
	body = json.dumps(payload).encode('utf-8')

	async def receive():
		return {'type': 'http.request', 'body': body, 'more_body': False}

	scope = {
		'type': 'http',
		'method': 'POST',
		'path': '/api/agent-relay',
		'headers': [(b'content-type', b'application/json')],
	}
	return Request(scope, receive)


def _run_async(coro):
	return asyncio.run(coro)


@pytest.mark.unit
def test_agent_relay_enqueues_follow_up_when_running(monkeypatch):
	controller = _StubController()
	monkeypatch.setattr(api_chat_module, 'get_agent_controller', lambda: controller)
	request = _build_request({'prompt': '最新ニュースをチェック'})
	response = _run_async(api_chat_module.agent_relay(request))

	assert response.status_code == 202
	payload = json.loads(response.body.decode('utf-8'))
	assert payload['status'] == 'follow_up_enqueued'
	assert payload['agent_running'] is True
	assert payload['queued'] is True
	assert controller.enqueue_calls == ['最新ニュースをチェック']
	assert controller.resume_called is False


@pytest.mark.unit
def test_agent_relay_resumes_when_paused(monkeypatch):
	controller = _StubController(paused=True)
	monkeypatch.setattr(api_chat_module, 'get_agent_controller', lambda: controller)
	request = _build_request({'prompt': '追加の操作を開始'})
	response = _run_async(api_chat_module.agent_relay(request))

	assert response.status_code == 202
	payload = json.loads(response.body.decode('utf-8'))
	assert payload['status'] == 'follow_up_enqueued'
	assert payload['agent_running'] is True
	assert controller.enqueue_calls == ['追加の操作を開始']
	assert controller.resume_called is True

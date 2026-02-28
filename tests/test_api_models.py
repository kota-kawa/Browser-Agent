import asyncio
import json

from fastapi_app.routes import api_models


# EN: Define class `_FakeController`.
# JP: クラス `_FakeController` を定義する。
class _FakeController:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        self.update_llm_calls = 0

    # EN: Define function `update_llm`.
    # JP: 関数 `update_llm` を定義する。
    def update_llm(self):
        self.update_llm_calls += 1


# EN: Define class `_FakeBroadcaster`.
# JP: クラス `_FakeBroadcaster` を定義する。
class _FakeBroadcaster:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self):
        self.events = []

    # EN: Define function `publish`.
    # JP: 関数 `publish` を定義する。
    def publish(self, event):
        self.events.append(event)


# EN: Define class `_FakeRequest`.
# JP: クラス `_FakeRequest` を定義する。
class _FakeRequest:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, headers=None):
        self.headers = headers or {}


# EN: Define function `_body`.
# JP: 関数 `_body` を定義する。
def _body(response):
    return json.loads(response.body.decode('utf-8'))


# EN: Define function `test_get_models_returns_available_models_and_current_selection`.
# JP: 関数 `test_get_models_returns_available_models_and_current_selection` を定義する。
def test_get_models_returns_available_models_and_current_selection(monkeypatch):
    monkeypatch.setattr(
        api_models,
        'apply_model_selection',
        lambda *_args, **_kwargs: {
            'provider': 'openai',
            'model': 'gpt-5.1',
            'base_url': 'https://api.openai.example',
        },
    )

    response = api_models.get_models()

    assert response.status_code == 200
    payload = _body(response)
    assert isinstance(payload['models'], list)
    assert payload['current'] == {
        'provider': 'openai',
        'model': 'gpt-5.1',
        'base_url': 'https://api.openai.example',
    }


# EN: Define function `test_set_vision_requires_enabled_flag`.
# JP: 関数 `test_set_vision_requires_enabled_flag` を定義する。
def test_set_vision_requires_enabled_flag(monkeypatch):
    # EN: Define async function `_fake_read_payload`.
    # JP: 非同期関数 `_fake_read_payload` を定義する。
    async def _fake_read_payload(_request):
        return {}

    monkeypatch.setattr(api_models, 'read_json_payload', _fake_read_payload)

    response = asyncio.run(api_models.set_vision(_FakeRequest()))

    assert response.status_code == 400
    assert 'enabled' in _body(response)['error']


# EN: Define function `test_set_vision_success`.
# JP: 関数 `test_set_vision_success` を定義する。
def test_set_vision_success(monkeypatch):
    # EN: Define async function `_fake_read_payload`.
    # JP: 非同期関数 `_fake_read_payload` を定義する。
    async def _fake_read_payload(_request):
        return {'enabled': 1}

    state = {
        'user_enabled': True,
        'model_supported': True,
        'effective': True,
        'provider': 'openai',
        'model': 'gpt-5.1',
    }

    monkeypatch.setattr(api_models, 'read_json_payload', _fake_read_payload)
    monkeypatch.setattr(api_models, 'set_vision_pref', lambda enabled: {**state, 'user_enabled': bool(enabled)})

    response = asyncio.run(api_models.set_vision(_FakeRequest()))

    assert response.status_code == 200
    assert _body(response)['effective'] is True


# EN: Define function `test_update_model_settings_success_updates_controller_and_notifies`.
# JP: 関数 `test_update_model_settings_success_updates_controller_and_notifies` を定義する。
def test_update_model_settings_success_updates_controller_and_notifies(monkeypatch, tmp_path):
    # EN: Define async function `_fake_read_payload`.
    # JP: 非同期関数 `_fake_read_payload` を定義する。
    async def _fake_read_payload(_request):
        return {'provider': 'openai', 'model': 'gpt-5.1', 'base_url': 'https://api.openai.example'}

    controller = _FakeController()
    broadcaster = _FakeBroadcaster()
    notify_calls = []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(api_models, 'read_json_payload', _fake_read_payload)
    monkeypatch.setattr(
        api_models,
        'update_override',
        lambda selection: {
            'provider': selection['provider'],
            'model': selection['model'],
            'base_url': selection['base_url'],
        },
    )
    monkeypatch.setattr(api_models, 'get_controller_if_initialized', lambda: controller)
    monkeypatch.setattr(api_models, '_broadcaster', broadcaster)
    monkeypatch.setattr(api_models, 'find_model_label', lambda provider, model: f'{provider}:{model}')
    monkeypatch.setattr(api_models, 'notify_platform', lambda payload: notify_calls.append(payload))

    response = asyncio.run(api_models.update_model_settings(_FakeRequest(headers={})))

    assert response.status_code == 200
    payload = _body(response)
    assert payload['status'] == 'ok'
    assert controller.update_llm_calls == 1
    assert len(broadcaster.events) == 1
    assert broadcaster.events[0]['type'] == 'model'
    assert notify_calls == [
        {
            'provider': 'openai',
            'model': 'gpt-5.1',
            'base_url': 'https://api.openai.example',
        }
    ]


# EN: Define function `test_update_model_settings_skips_notify_when_propagation_header_is_set`.
# JP: 関数 `test_update_model_settings_skips_notify_when_propagation_header_is_set` を定義する。
def test_update_model_settings_skips_notify_when_propagation_header_is_set(monkeypatch, tmp_path):
    # EN: Define async function `_fake_read_payload`.
    # JP: 非同期関数 `_fake_read_payload` を定義する。
    async def _fake_read_payload(_request):
        return {'provider': 'openai', 'model': 'gpt-5.1'}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(api_models, 'read_json_payload', _fake_read_payload)
    monkeypatch.setattr(api_models, 'update_override', lambda selection: dict(selection))
    monkeypatch.setattr(api_models, 'get_controller_if_initialized', lambda: None)
    monkeypatch.setattr(api_models, '_broadcaster', _FakeBroadcaster())
    monkeypatch.setattr(api_models, 'find_model_label', lambda *_args, **_kwargs: 'label')

    notify_calls = []
    monkeypatch.setattr(api_models, 'notify_platform', lambda payload: notify_calls.append(payload))

    response = asyncio.run(
        api_models.update_model_settings(_FakeRequest(headers={'X-Platform-Propagation': '1'}))
    )

    assert response.status_code == 200
    assert notify_calls == []


# EN: Define function `test_update_model_settings_returns_500_on_error`.
# JP: 関数 `test_update_model_settings_returns_500_on_error` を定義する。
def test_update_model_settings_returns_500_on_error(monkeypatch, tmp_path):
    # EN: Define async function `_fake_read_payload`.
    # JP: 非同期関数 `_fake_read_payload` を定義する。
    async def _fake_read_payload(_request):
        return {'provider': 'openai', 'model': 'gpt-5.1'}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(api_models, 'read_json_payload', _fake_read_payload)

    # Simulate a failure during apply/update.
    monkeypatch.setattr(api_models, 'update_override', lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError('boom')))

    response = asyncio.run(api_models.update_model_settings(_FakeRequest(headers={})))

    assert response.status_code == 500
    assert '失敗' in _body(response)['error']

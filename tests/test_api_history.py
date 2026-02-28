import json

from fastapi_app.routes import api_history


# EN: Define class `_FakeListener`.
# JP: クラス `_FakeListener` を定義する。
class _FakeListener:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, events):
        self._events = iter(events)

    # EN: Define function `get`.
    # JP: 関数 `get` を定義する。
    def get(self):
        return next(self._events)


# EN: Define class `_FakeBroadcaster`.
# JP: クラス `_FakeBroadcaster` を定義する。
class _FakeBroadcaster:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, events):
        self._listener = _FakeListener(events)
        self.unsubscribed = []

    # EN: Define function `subscribe`.
    # JP: 関数 `subscribe` を定義する。
    def subscribe(self):
        return self._listener

    # EN: Define function `unsubscribe`.
    # JP: 関数 `unsubscribe` を定義する。
    def unsubscribe(self, listener):
        self.unsubscribed.append(listener)


# EN: Define class `_FakeStreamingResponse`.
# JP: クラス `_FakeStreamingResponse` を定義する。
class _FakeStreamingResponse:
    # EN: Define function `__init__`.
    # JP: 関数 `__init__` を定義する。
    def __init__(self, body_iterator, media_type=None, headers=None):
        self.body_iterator = body_iterator
        self.media_type = media_type
        self.headers = headers or {}


# EN: Define function `_body`.
# JP: 関数 `_body` を定義する。
def _body(response):
    return json.loads(response.body.decode('utf-8'))


# EN: Define function `test_history_returns_snapshot`.
# JP: 関数 `test_history_returns_snapshot` を定義する。
def test_history_returns_snapshot(monkeypatch):
    monkeypatch.setattr(api_history, '_copy_history', lambda: [{'id': 1, 'role': 'user', 'content': 'hello'}])

    response = api_history.history()

    assert response.status_code == 200
    assert _body(response) == {'messages': [{'id': 1, 'role': 'user', 'content': 'hello'}]}


# EN: Define function `test_stream_emits_sse_payload_and_unsubscribes_on_close`.
# JP: 関数 `test_stream_emits_sse_payload_and_unsubscribes_on_close` を定義する。
def test_stream_emits_sse_payload_and_unsubscribes_on_close(monkeypatch):
    event = {'type': 'status', 'payload': {'agent_running': False, 'run_summary': 'done'}}
    broadcaster = _FakeBroadcaster([event])

    monkeypatch.setattr(api_history, '_broadcaster', broadcaster)
    monkeypatch.setattr(api_history, 'StreamingResponse', _FakeStreamingResponse)

    response = api_history.stream()

    assert response.media_type == 'text/event-stream'
    assert response.headers['Cache-Control'] == 'no-cache'
    assert response.headers['X-Accel-Buffering'] == 'no'

    chunk = next(response.body_iterator)
    assert chunk == f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    response.body_iterator.close()
    assert broadcaster.unsubscribed == [broadcaster._listener]

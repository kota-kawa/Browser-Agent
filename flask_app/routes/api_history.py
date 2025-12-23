from __future__ import annotations

import json
from typing import Any

from flask import Blueprint, Response, jsonify, stream_with_context
from flask.typing import ResponseReturnValue

from ..services.history_store import _broadcaster, _copy_history

api_history_bp = Blueprint('api_history', __name__)


@api_history_bp.get('/api/history')
def history() -> ResponseReturnValue:
	return jsonify({'messages': _copy_history()}), 200


@api_history_bp.get('/api/stream')
def stream() -> ResponseReturnValue:
	listener = _broadcaster.subscribe()

	def event_stream() -> Any:
		try:
			while True:
				event = listener.get()
				yield f'data: {json.dumps(event, ensure_ascii=False)}\n\n'
		except GeneratorExit:
			pass
		finally:
			_broadcaster.unsubscribe(listener)

	headers = {'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
	return Response(stream_with_context(event_stream()), mimetype='text/event-stream', headers=headers)

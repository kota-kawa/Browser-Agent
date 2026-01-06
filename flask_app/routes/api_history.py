from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from ..services.history_store import _broadcaster, _copy_history

router = APIRouter()


@router.get('/api/history')
def history() -> JSONResponse:
	return JSONResponse({'messages': _copy_history()})


@router.get('/api/stream')
def stream() -> StreamingResponse:
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
	return StreamingResponse(event_stream(), media_type='text/event-stream', headers=headers)

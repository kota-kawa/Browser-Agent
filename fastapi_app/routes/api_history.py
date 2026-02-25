from __future__ import annotations

import json
from typing import Any

# JP: 履歴取得と SSE ストリーミング API
# EN: History retrieval and SSE streaming endpoints
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from ..services.history_store import _broadcaster, _copy_history

router = APIRouter()


@router.get('/api/history')
def history() -> JSONResponse:
	# JP: 現在の履歴スナップショットを返す
	# EN: Return a snapshot of current history
	return JSONResponse({'messages': _copy_history()})


@router.get('/api/stream')
def stream() -> StreamingResponse:
	# JP: SSE でイベントを配信（UI へ進捗通知）
	# EN: Stream events via SSE for UI updates
	listener = _broadcaster.subscribe()

	def event_stream() -> Any:
		# JP: キューからイベントを取り出して SSE 形式で送信
		# EN: Pull events from queue and emit SSE frames
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

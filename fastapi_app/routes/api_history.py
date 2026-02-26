# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# JP: 履歴取得と SSE ストリーミング API
# EN: History retrieval and SSE streaming endpoints
from fastapi import APIRouter
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.responses import JSONResponse, StreamingResponse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.history_store import _broadcaster, _copy_history

# EN: Assign value to router.
# JP: router に値を代入する。
router = APIRouter()


# EN: Define function `history`.
# JP: 関数 `history` を定義する。
@router.get('/api/history')
def history() -> JSONResponse:
	# JP: 現在の履歴スナップショットを返す
	# EN: Return a snapshot of current history
	return JSONResponse({'messages': _copy_history()})


# EN: Define function `stream`.
# JP: 関数 `stream` を定義する。
@router.get('/api/stream')
def stream() -> StreamingResponse:
	# JP: SSE でイベントを配信（UI へ進捗通知）
	# EN: Stream events via SSE for UI updates
	listener = _broadcaster.subscribe()

	# EN: Define function `event_stream`.
	# JP: 関数 `event_stream` を定義する。
	def event_stream() -> Any:
		# JP: キューからイベントを取り出して SSE 形式で送信
		# EN: Pull events from queue and emit SSE frames
		try:
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while True:
				# EN: Assign value to event.
				# JP: event に値を代入する。
				event = listener.get()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				yield f'data: {json.dumps(event, ensure_ascii=False)}\n\n'
		except GeneratorExit:
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass
		finally:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_broadcaster.unsubscribe(listener)

	# EN: Assign value to headers.
	# JP: headers に値を代入する。
	headers = {'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return StreamingResponse(event_stream(), media_type='text/event-stream', headers=headers)

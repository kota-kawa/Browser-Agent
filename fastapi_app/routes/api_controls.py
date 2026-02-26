# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# JP: エージェントの制御系 API
# EN: Control endpoints for the agent
from fastapi import APIRouter
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.responses import JSONResponse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.exceptions import AgentControllerError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.agent_runtime import get_controller_if_initialized, get_existing_controller
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.history_store import _reset_history

# EN: Assign value to router.
# JP: router に値を代入する。
router = APIRouter()


# EN: Define function `reset_conversation`.
# JP: 関数 `reset_conversation` を定義する。
@router.post('/api/reset')
def reset_conversation() -> JSONResponse:
	# JP: 既存セッションをリセットし、履歴も初期化
	# EN: Reset controller (if any) and clear history
	controller = get_controller_if_initialized()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if controller is not None:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.reset()
		except AgentControllerError as exc:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'error': str(exc)}, status_code=400)
		except Exception as exc:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.exception('Failed to reset agent controller')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'error': f'エージェントのリセットに失敗しました: {exc}'}, status_code=500)

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to snapshot.
		# JP: snapshot に値を代入する。
		snapshot = _reset_history()
	except Exception as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Failed to reset history')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': f'履歴のリセットに失敗しました: {exc}'}, status_code=500)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse({'messages': snapshot})


# EN: Define function `pause_agent`.
# JP: 関数 `pause_agent` を定義する。
@router.post('/api/pause')
def pause_agent() -> JSONResponse:
	# JP: 実行中のエージェントを一時停止
	# EN: Pause a running agent
	try:
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = get_existing_controller()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		controller.pause()
	except AgentControllerError as exc:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': str(exc)}, status_code=400)
	except Exception as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Failed to pause agent')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': f'一時停止に失敗しました: {exc}'}, status_code=500)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse({'status': 'paused'})


# EN: Define function `resume_agent`.
# JP: 関数 `resume_agent` を定義する。
@router.post('/api/resume')
def resume_agent() -> JSONResponse:
	# JP: 一時停止中のエージェントを再開
	# EN: Resume a paused agent
	try:
		# EN: Assign value to controller.
		# JP: controller に値を代入する。
		controller = get_existing_controller()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		controller.resume()
	except AgentControllerError as exc:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': str(exc)}, status_code=400)
	except Exception as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Failed to resume agent')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': f'再開に失敗しました: {exc}'}, status_code=500)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse({'status': 'resumed'})

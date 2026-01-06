from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..core.config import logger
from ..core.exceptions import AgentControllerError
from ..services.agent_runtime import get_controller_if_initialized, get_existing_controller
from ..services.history_store import _reset_history

router = APIRouter()


@router.post('/api/reset')
def reset_conversation() -> JSONResponse:
	controller = get_controller_if_initialized()
	if controller is not None:
		try:
			controller.reset()
		except AgentControllerError as exc:
			return JSONResponse({'error': str(exc)}, status_code=400)
		except Exception as exc:
			logger.exception('Failed to reset agent controller')
			return JSONResponse({'error': f'エージェントのリセットに失敗しました: {exc}'}, status_code=500)

	try:
		snapshot = _reset_history()
	except Exception as exc:
		logger.exception('Failed to reset history')
		return JSONResponse({'error': f'履歴のリセットに失敗しました: {exc}'}, status_code=500)
	return JSONResponse({'messages': snapshot})


@router.post('/api/pause')
def pause_agent() -> JSONResponse:
	try:
		controller = get_existing_controller()
		controller.pause()
	except AgentControllerError as exc:
		return JSONResponse({'error': str(exc)}, status_code=400)
	except Exception as exc:
		logger.exception('Failed to pause agent')
		return JSONResponse({'error': f'一時停止に失敗しました: {exc}'}, status_code=500)
	return JSONResponse({'status': 'paused'})


@router.post('/api/resume')
def resume_agent() -> JSONResponse:
	try:
		controller = get_existing_controller()
		controller.resume()
	except AgentControllerError as exc:
		return JSONResponse({'error': str(exc)}, status_code=400)
	except Exception as exc:
		logger.exception('Failed to resume agent')
		return JSONResponse({'error': f'再開に失敗しました: {exc}'}, status_code=500)
	return JSONResponse({'status': 'resumed'})

from __future__ import annotations

from flask import Blueprint, jsonify
from flask.typing import ResponseReturnValue

from ..core.config import logger
from ..core.exceptions import AgentControllerError
from ..services.agent_runtime import get_controller_if_initialized, get_existing_controller
from ..services.history_store import _reset_history

api_controls_bp = Blueprint('api_controls', __name__)


@api_controls_bp.post('/api/reset')
def reset_conversation() -> ResponseReturnValue:
	controller = get_controller_if_initialized()
	if controller is not None:
		try:
			controller.reset()
		except AgentControllerError as exc:
			return jsonify({'error': str(exc)}), 400
		except Exception as exc:
			logger.exception('Failed to reset agent controller')
			return jsonify({'error': f'エージェントのリセットに失敗しました: {exc}'}), 500

	try:
		snapshot = _reset_history()
	except Exception as exc:
		logger.exception('Failed to reset history')
		return jsonify({'error': f'履歴のリセットに失敗しました: {exc}'}), 500
	return jsonify({'messages': snapshot}), 200


@api_controls_bp.post('/api/pause')
def pause_agent() -> ResponseReturnValue:
	try:
		controller = get_existing_controller()
		controller.pause()
	except AgentControllerError as exc:
		return jsonify({'error': str(exc)}), 400
	except Exception as exc:
		logger.exception('Failed to pause agent')
		return jsonify({'error': f'一時停止に失敗しました: {exc}'}), 500
	return jsonify({'status': 'paused'}), 200


@api_controls_bp.post('/api/resume')
def resume_agent() -> ResponseReturnValue:
	try:
		controller = get_existing_controller()
		controller.resume()
	except AgentControllerError as exc:
		return jsonify({'error': str(exc)}), 400
	except Exception as exc:
		logger.exception('Failed to resume agent')
		return jsonify({'error': f'再開に失敗しました: {exc}'}), 500
	return jsonify({'status': 'resumed'}), 200

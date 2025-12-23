from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from browser_use.model_selection import apply_model_selection, update_override
from flask import Blueprint, jsonify, request
from flask.typing import ResponseReturnValue

from ..core.config import logger
from ..core.models import SUPPORTED_MODELS
from ..services.agent_runtime import (
	find_model_label,
	get_controller_if_initialized,
	notify_platform,
	set_vision_pref,
	vision_state,
)
from ..services.history_store import _broadcaster

api_models_bp = Blueprint('api_models', __name__)


@api_models_bp.get('/api/models')
def get_models() -> ResponseReturnValue:
	current = apply_model_selection('browser')
	return jsonify(
		{
			'models': SUPPORTED_MODELS,
			'current': {'provider': current['provider'], 'model': current['model'], 'base_url': current.get('base_url', '')},
		}
	)


@api_models_bp.get('/api/vision')
def get_vision() -> ResponseReturnValue:
	"""Return current vision (screenshot) preference and effective status."""

	return jsonify(vision_state())


@api_models_bp.post('/api/vision')
def set_vision() -> ResponseReturnValue:
	payload = request.get_json(silent=True) or {}
	if not isinstance(payload, dict) or 'enabled' not in payload:
		return jsonify({'error': 'enabled フラグを指定してください。'}), 400

	enabled = bool(payload.get('enabled'))
	state = set_vision_pref(enabled)
	return jsonify(state)


@api_models_bp.post('/model_settings')
def update_model_settings() -> ResponseReturnValue:
	"""Update LLM selection and recycle controller without restart."""

	payload = request.get_json(silent=True) or {}
	selection = payload if isinstance(payload, dict) else {}
	applied: dict[str, Any] | None = None
	try:
		# Save selection to local_model_settings.json for persistence
		local_path = Path('local_model_settings.json')
		with open(local_path, 'w', encoding='utf-8') as f:
			json.dump(selection, f, ensure_ascii=False, indent=2)

		applied = update_override(selection if selection else None)

		controller = get_controller_if_initialized()
		if controller is not None:
			controller.update_llm()

		provider = applied.get('provider') if isinstance(applied, dict) else None
		model = applied.get('model') if isinstance(applied, dict) else None
		if provider and model:
			_broadcaster.publish(
				{
					'type': 'model',
					'payload': {
						'provider': provider,
						'model': model,
						'label': find_model_label(provider, model),
						'base_url': applied.get('base_url', ''),
					},
				},
			)

		if request.headers.get('X-Platform-Propagation') != '1' and applied:
			notify_platform(
				{
					'provider': applied.get('provider', ''),
					'model': applied.get('model', ''),
					'base_url': applied.get('base_url', ''),
				},
			)
	except Exception as exc:
		logger.exception('Failed to apply model settings: %s', exc)
		return jsonify({'error': 'モデル設定の更新に失敗しました。'}), 500
	return jsonify({'status': 'ok', 'applied': applied if applied else selection or 'from_file'})

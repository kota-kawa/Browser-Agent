from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from browser_use.model_selection import apply_model_selection, update_override
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

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
from .utils import read_json_payload

router = APIRouter()


@router.get('/api/models')
def get_models() -> JSONResponse:
	current = apply_model_selection('browser')
	return JSONResponse(
		{
			'models': SUPPORTED_MODELS,
			'current': {'provider': current['provider'], 'model': current['model'], 'base_url': current.get('base_url', '')},
		}
	)


@router.get('/api/vision')
def get_vision() -> JSONResponse:
	"""Return current vision (screenshot) preference and effective status."""

	return JSONResponse(vision_state())


@router.post('/api/vision')
async def set_vision(request: Request) -> JSONResponse:
	payload = await read_json_payload(request)
	if not isinstance(payload, dict) or 'enabled' not in payload:
		return JSONResponse({'error': 'enabled フラグを指定してください。'}, status_code=400)

	enabled = bool(payload.get('enabled'))
	state = set_vision_pref(enabled)
	return JSONResponse(state)


@router.post('/model_settings')
async def update_model_settings(request: Request) -> JSONResponse:
	"""Update LLM selection and recycle controller without restart."""

	payload = await read_json_payload(request)
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
		return JSONResponse({'error': 'モデル設定の更新に失敗しました。'}, status_code=500)
	return JSONResponse({'status': 'ok', 'applied': applied if applied else selection or 'from_file'})

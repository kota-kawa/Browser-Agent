from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# JP: モデル選択/ビジョン設定の API
# EN: Endpoints for model selection and vision settings
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


# EN: Define function `get_models`.
# JP: 関数 `get_models` を定義する。
@router.get('/api/models')
def get_models() -> JSONResponse:
	# JP: 選択可能なモデルと現在の選択を返す
	# EN: Return available models and current selection
	current = apply_model_selection('browser')
	return JSONResponse(
		{
			'models': SUPPORTED_MODELS,
			'current': {'provider': current['provider'], 'model': current['model'], 'base_url': current.get('base_url', '')},
		}
	)


# EN: Define function `get_vision`.
# JP: 関数 `get_vision` を定義する。
@router.get('/api/vision')
def get_vision() -> JSONResponse:
	"""Return current vision (screenshot) preference and effective status."""

	# JP: Vision の設定と有効状態を返す
	# EN: Return vision preference and effective status
	return JSONResponse(vision_state())


# EN: Define async function `set_vision`.
# JP: 非同期関数 `set_vision` を定義する。
@router.post('/api/vision')
async def set_vision(request: Request) -> JSONResponse:
	# JP: Vision の有効/無効を更新
	# EN: Update vision preference
	payload = await read_json_payload(request)
	if not isinstance(payload, dict) or 'enabled' not in payload:
		return JSONResponse({'error': 'enabled フラグを指定してください。'}, status_code=400)

	enabled = bool(payload.get('enabled'))
	state = set_vision_pref(enabled)
	return JSONResponse(state)


# EN: Define async function `update_model_settings`.
# JP: 非同期関数 `update_model_settings` を定義する。
@router.post('/model_settings')
async def update_model_settings(request: Request) -> JSONResponse:
	"""Update LLM selection and recycle controller without restart."""

	# JP: モデル設定を保存し、必要ならコントローラーを更新
	# EN: Persist model settings and refresh controller if needed
	payload = await read_json_payload(request)
	selection = payload if isinstance(payload, dict) else {}
	applied: dict[str, Any] | None = None
	try:
		# Save selection to local_model_settings.json for persistence
		local_path = Path('local_model_settings.json')
		with open(local_path, 'w', encoding='utf-8') as f:
			json.dump(selection, f, ensure_ascii=False, indent=2)

		applied = update_override(selection if selection else None)

		# JP: 稼働中のコントローラーには即時反映
		# EN: Apply changes to the running controller
		controller = get_controller_if_initialized()
		if controller is not None:
			controller.update_llm()

		provider = applied.get('provider') if isinstance(applied, dict) else None
		model = applied.get('model') if isinstance(applied, dict) else None
		if provider and model:
			# JP: UI へモデル変更通知
			# EN: Notify UI about model changes
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
			# JP: ループ防止のためヘッダーが無い場合のみ同期
			# EN: Avoid sync loops using the propagation header
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

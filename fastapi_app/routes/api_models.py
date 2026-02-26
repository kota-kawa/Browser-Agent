# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# JP: モデル選択/ビジョン設定の API
# EN: Endpoints for model selection and vision settings
from browser_use.model_selection import apply_model_selection, update_override
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi import APIRouter, Request
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.responses import JSONResponse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.models import SUPPORTED_MODELS
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.agent_runtime import (
	find_model_label,
	get_controller_if_initialized,
	notify_platform,
	set_vision_pref,
	vision_state,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.history_store import _broadcaster
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .utils import read_json_payload

# EN: Assign value to router.
# JP: router に値を代入する。
router = APIRouter()


# EN: Define function `get_models`.
# JP: 関数 `get_models` を定義する。
@router.get('/api/models')
def get_models() -> JSONResponse:
	# JP: 選択可能なモデルと現在の選択を返す
	# EN: Return available models and current selection
	current = apply_model_selection('browser')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
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
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
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
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not isinstance(payload, dict) or 'enabled' not in payload:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': 'enabled フラグを指定してください。'}, status_code=400)

	# EN: Assign value to enabled.
	# JP: enabled に値を代入する。
	enabled = bool(payload.get('enabled'))
	# EN: Assign value to state.
	# JP: state に値を代入する。
	state = set_vision_pref(enabled)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse(state)


# EN: Define async function `update_model_settings`.
# JP: 非同期関数 `update_model_settings` を定義する。
@router.post('/model_settings')
async def update_model_settings(request: Request) -> JSONResponse:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Update LLM selection and recycle controller without restart."""

	# JP: モデル設定を保存し、必要ならコントローラーを更新
	# EN: Persist model settings and refresh controller if needed
	payload = await read_json_payload(request)
	# EN: Assign value to selection.
	# JP: selection に値を代入する。
	selection = payload if isinstance(payload, dict) else {}
	# EN: Assign annotated value to applied.
	# JP: applied に型付きの値を代入する。
	applied: dict[str, Any] | None = None
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Save selection to local_model_settings.json for persistence
		# EN: Assign value to local_path.
		# JP: local_path に値を代入する。
		local_path = Path('local_model_settings.json')
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(local_path, 'w', encoding='utf-8') as f:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			json.dump(selection, f, ensure_ascii=False, indent=2)

		# EN: Assign value to applied.
		# JP: applied に値を代入する。
		applied = update_override(selection if selection else None)

		# JP: 稼働中のコントローラーには即時反映
		# EN: Apply changes to the running controller
		controller = get_controller_if_initialized()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if controller is not None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.update_llm()

		# EN: Assign value to provider.
		# JP: provider に値を代入する。
		provider = applied.get('provider') if isinstance(applied, dict) else None
		# EN: Assign value to model.
		# JP: model に値を代入する。
		model = applied.get('model') if isinstance(applied, dict) else None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
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

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
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
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Failed to apply model settings: %s', exc)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': 'モデル設定の更新に失敗しました。'}, status_code=500)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse({'status': 'ok', 'applied': applied if applied else selection or 'from_file'})

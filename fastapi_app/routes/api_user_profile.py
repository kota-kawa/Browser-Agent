from __future__ import annotations

# JP: ユーザープロファイル管理 API
# EN: User profile management endpoints
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..services.user_profile import load_user_profile, save_user_profile
from .utils import read_json_payload

router = APIRouter()


# EN: Define function `get_user_profile`.
# JP: 関数 `get_user_profile` を定義する。
@router.get('/api/user_profile')
def get_user_profile() -> JSONResponse:
	# JP: 保存済みプロフィールの取得
	# EN: Retrieve stored profile
	return JSONResponse({'text': load_user_profile()})


# EN: Define async function `update_user_profile`.
# JP: 非同期関数 `update_user_profile` を定義する。
@router.post('/api/user_profile')
async def update_user_profile(request: Request) -> JSONResponse:
	# JP: プロフィールの更新
	# EN: Update profile text
	payload = await read_json_payload(request)
	if not isinstance(payload, dict) or 'text' not in payload:
		return JSONResponse({'error': 'text を指定してください。'}, status_code=400)

	text = payload.get('text') or ''
	saved_text = save_user_profile(text)
	return JSONResponse({'status': 'ok', 'text': saved_text})

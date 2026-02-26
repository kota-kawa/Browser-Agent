# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# JP: ユーザープロファイル管理 API
# EN: User profile management endpoints
from fastapi import APIRouter, Request
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.responses import JSONResponse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.user_profile import load_user_profile, save_user_profile
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .utils import read_json_payload

# EN: Assign value to router.
# JP: router に値を代入する。
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
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not isinstance(payload, dict) or 'text' not in payload:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': 'text を指定してください。'}, status_code=400)

	# EN: Assign value to text.
	# JP: text に値を代入する。
	text = payload.get('text') or ''
	# EN: Assign value to saved_text.
	# JP: saved_text に値を代入する。
	saved_text = save_user_profile(text)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse({'status': 'ok', 'text': saved_text})

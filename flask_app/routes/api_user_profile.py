from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..services.user_profile import load_user_profile, save_user_profile
from .utils import read_json_payload

router = APIRouter()


@router.get('/api/user_profile')
def get_user_profile() -> JSONResponse:
	return JSONResponse({'text': load_user_profile()})


@router.post('/api/user_profile')
async def update_user_profile(request: Request) -> JSONResponse:
	payload = await read_json_payload(request)
	if not isinstance(payload, dict) or 'text' not in payload:
		return JSONResponse({'error': 'text を指定してください。'}, status_code=400)

	text = payload.get('text') or ''
	saved_text = save_user_profile(text)
	return JSONResponse({'status': 'ok', 'text': saved_text})

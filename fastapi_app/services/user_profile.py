from __future__ import annotations

import json
from pathlib import Path

# JP: ユーザープロファイル（自由文）の保存/読み込み
# EN: Load/save a free-form user profile
from ..core.config import logger

_USER_PROFILE_PATH = Path('local_user_profile.json')
_MAX_USER_PROFILE_CHARS = 2000


# EN: Define function `_normalize_user_profile`.
# JP: 関数 `_normalize_user_profile` を定義する。
def _normalize_user_profile(text: str | None) -> str:
	# JP: 改行を正規化し、最大長で切り詰める
	# EN: Normalize newlines and truncate to max length
	if not text:
		return ''
	normalized = str(text).replace('\r\n', '\n').replace('\r', '\n').strip()
	if len(normalized) > _MAX_USER_PROFILE_CHARS:
		normalized = normalized[:_MAX_USER_PROFILE_CHARS].rstrip()
	return normalized


# EN: Define function `load_user_profile`.
# JP: 関数 `load_user_profile` を定義する。
def load_user_profile() -> str:
	# JP: ローカル JSON からユーザープロファイルを読み込む
	# EN: Read the profile text from local JSON
	try:
		if _USER_PROFILE_PATH.exists():
			payload = json.loads(_USER_PROFILE_PATH.read_text(encoding='utf-8'))
			if isinstance(payload, dict) and isinstance(payload.get('text'), str):
				return _normalize_user_profile(payload['text'])
	except Exception:
		logger.debug('Failed to load user profile; defaulting to empty', exc_info=True)
	return ''


# EN: Define function `save_user_profile`.
# JP: 関数 `save_user_profile` を定義する。
def save_user_profile(text: str | None) -> str:
	# JP: 空なら削除、値があれば JSON として保存
	# EN: Delete when empty; otherwise persist as JSON
	normalized = _normalize_user_profile(text)
	try:
		if normalized:
			_USER_PROFILE_PATH.write_text(
				json.dumps({'text': normalized}, ensure_ascii=False, indent=2),
				encoding='utf-8',
			)
		elif _USER_PROFILE_PATH.exists():
			_USER_PROFILE_PATH.unlink()
	except Exception:
		logger.debug('Failed to persist user profile', exc_info=True)
	return normalized

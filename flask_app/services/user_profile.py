from __future__ import annotations

import json
from pathlib import Path

from ..core.config import logger

_USER_PROFILE_PATH = Path('local_user_profile.json')
_MAX_USER_PROFILE_CHARS = 2000


def _normalize_user_profile(text: str | None) -> str:
	if not text:
		return ''
	normalized = str(text).replace('\r\n', '\n').replace('\r', '\n').strip()
	if len(normalized) > _MAX_USER_PROFILE_CHARS:
		normalized = normalized[:_MAX_USER_PROFILE_CHARS].rstrip()
	return normalized


def load_user_profile() -> str:
	try:
		if _USER_PROFILE_PATH.exists():
			payload = json.loads(_USER_PROFILE_PATH.read_text(encoding='utf-8'))
			if isinstance(payload, dict) and isinstance(payload.get('text'), str):
				return _normalize_user_profile(payload['text'])
	except Exception:
		logger.debug('Failed to load user profile; defaulting to empty', exc_info=True)
	return ''


def save_user_profile(text: str | None) -> str:
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

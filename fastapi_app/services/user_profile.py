# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path

# JP: ユーザープロファイル（自由文）の保存/読み込み
# EN: Load/save a free-form user profile
from ..core.config import logger

# EN: Assign value to _USER_PROFILE_PATH.
# JP: _USER_PROFILE_PATH に値を代入する。
_USER_PROFILE_PATH = Path('local_user_profile.json')
# EN: Assign value to _MAX_USER_PROFILE_CHARS.
# JP: _MAX_USER_PROFILE_CHARS に値を代入する。
_MAX_USER_PROFILE_CHARS = 2000


# EN: Define function `_normalize_user_profile`.
# JP: 関数 `_normalize_user_profile` を定義する。
def _normalize_user_profile(text: str | None) -> str:
	# JP: 改行を正規化し、最大長で切り詰める
	# EN: Normalize newlines and truncate to max length
	if not text:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''
	# EN: Assign value to normalized.
	# JP: normalized に値を代入する。
	normalized = str(text).replace('\r\n', '\n').replace('\r', '\n').strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if len(normalized) > _MAX_USER_PROFILE_CHARS:
		# EN: Assign value to normalized.
		# JP: normalized に値を代入する。
		normalized = normalized[:_MAX_USER_PROFILE_CHARS].rstrip()
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return normalized


# EN: Define function `load_user_profile`.
# JP: 関数 `load_user_profile` を定義する。
def load_user_profile() -> str:
	# JP: ローカル JSON からユーザープロファイルを読み込む
	# EN: Read the profile text from local JSON
	try:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if _USER_PROFILE_PATH.exists():
			# EN: Assign value to payload.
			# JP: payload に値を代入する。
			payload = json.loads(_USER_PROFILE_PATH.read_text(encoding='utf-8'))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(payload, dict) and isinstance(payload.get('text'), str):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return _normalize_user_profile(payload['text'])
	except Exception:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Failed to load user profile; defaulting to empty', exc_info=True)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return ''


# EN: Define function `save_user_profile`.
# JP: 関数 `save_user_profile` を定義する。
def save_user_profile(text: str | None) -> str:
	# JP: 空なら削除、値があれば JSON として保存
	# EN: Delete when empty; otherwise persist as JSON
	normalized = _normalize_user_profile(text)
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if normalized:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_USER_PROFILE_PATH.write_text(
				json.dumps({'text': normalized}, ensure_ascii=False, indent=2),
				encoding='utf-8',
			)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif _USER_PROFILE_PATH.exists():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_USER_PROFILE_PATH.unlink()
	except Exception:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Failed to persist user profile', exc_info=True)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return normalized

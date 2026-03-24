from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from ..core.env import _get_env_trimmed


# EN: Define function `_extract_bearer_token`.
# JP: 関数 `_extract_bearer_token` を定義する。
def _extract_bearer_token(authorization: str | None) -> str | None:
	# JP: Authorization ヘッダーから Bearer トークンのみ抽出
	# EN: Extract only Bearer token from Authorization header
	if not authorization:
		return None
	scheme, _, token = authorization.partition(' ')
	if scheme.lower() != 'bearer':
		return None
	token = token.strip()
	return token or None


# EN: Define function `require_admin_api_token`.
# JP: 関数 `require_admin_api_token` を定義する。
def require_admin_api_token(
	x_admin_token: str | None = Header(default=None, alias='X-Admin-Token'),
	authorization: str | None = Header(default=None),
) -> None:
	"""
	Protect admin-only endpoints with a static token.

	Allowed headers:
	- X-Admin-Token: <token>
	- Authorization: Bearer <token>
	"""

	# JP: トークン未設定なら fail-closed で管理系 API を停止
	# EN: Fail closed when token is not configured
	expected = _get_env_trimmed('ADMIN_API_TOKEN')
	if not expected:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail='管理者APIトークンが未設定です。ADMIN_API_TOKEN を設定してください。',
		)

	provided = x_admin_token or _extract_bearer_token(authorization)
	if not provided or not hmac.compare_digest(provided, expected):
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail='管理者APIトークンが不正です。',
		)

from __future__ import annotations

# JP: APIルートで共通利用するガード処理（レート制限）
# EN: Shared guard helpers for API routes (rate limiting)
from fastapi import Request
from fastapi.responses import JSONResponse

from ..services.request_limits import is_ip_rate_limited


# EN: Define function `ip_rate_limit_guard`.
# JP: 関数 `ip_rate_limit_guard` を定義する。
def ip_rate_limit_guard(request: Request) -> JSONResponse | None:
	"""Return a standardized 429 response when an IP exceeds request limits."""
	# JP: 現在のリクエスト元IPが制限超過かどうか判定
	# EN: Check whether the current client IP exceeded the request limit
	limited, _client_ip = is_ip_rate_limited(request)
	if not limited:
		return None

	# JP: 制限超過時は共通フォーマットの429レスポンスを返す
	# EN: Return a standardized 429 payload when the limit is exceeded
	return JSONResponse(
		{
			'error': 'リクエスト頻度が高すぎます。しばらく待ってから再試行してください。',
		},
		status_code=429,
	)

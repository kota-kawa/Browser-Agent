from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from ..services.request_limits import is_ip_rate_limited


def ip_rate_limit_guard(request: Request) -> JSONResponse | None:
	"""Return a standardized 429 response when an IP exceeds request limits."""
	limited, _client_ip = is_ip_rate_limited(request)
	if not limited:
		return None

	return JSONResponse(
		{
			'error': 'リクエスト頻度が高すぎます。しばらく待ってから再試行してください。',
		},
		status_code=429,
	)

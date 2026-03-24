from __future__ import annotations

from typing import Any

# JP: API ルート共通の補助関数
# EN: Shared utilities for API routes
from fastapi import Request
from fastapi.responses import JSONResponse

from ..services.runtime_limits import RuntimeSlotGuard


# EN: Define async function `read_json_payload`.
# JP: 非同期関数 `read_json_payload` を定義する。
async def read_json_payload(request: Request) -> dict[str, Any]:
	"""Safely parse JSON payloads, returning an empty dict for invalid bodies."""

	# JP: JSON 以外は空 dict にしてハンドラ側を簡潔化
	# EN: Return {} on invalid JSON to simplify handlers
	try:
		payload = await request.json()
	except Exception:
		return {}

	return payload if isinstance(payload, dict) else {}


# EN: Define function `is_prompt_too_long`.
# JP: 関数 `is_prompt_too_long` を定義する。
def is_prompt_too_long(prompt: str, limit: int) -> bool:
	"""Return True when the prompt exceeds the configured character limit."""

	if limit <= 0:
		return False
	return len(prompt) > limit


# EN: Define function `try_acquire_runtime_slot`.
# JP: 関数 `try_acquire_runtime_slot` を定義する。
def try_acquire_runtime_slot(
	guard: RuntimeSlotGuard,
	*,
	error_message: str = '同時実行数の上限に達しています。しばらく待ってから再試行してください。',
) -> tuple[bool, JSONResponse | None]:
	"""Try to acquire a shared runtime slot and return a standardized 429 response on failure."""

	acquired = guard.acquire()
	if acquired:
		return True, None

	return False, JSONResponse({'error': error_message}, status_code=429)

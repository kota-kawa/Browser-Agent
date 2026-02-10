from __future__ import annotations

from typing import Any

# JP: API ルート共通の補助関数
# EN: Shared utilities for API routes
from fastapi import Request


async def read_json_payload(request: Request) -> dict[str, Any]:
	"""Safely parse JSON payloads, returning an empty dict for invalid bodies."""

	# JP: JSON 以外は空 dict にしてハンドラ側を簡潔化
	# EN: Return {} on invalid JSON to simplify handlers
	try:
		payload = await request.json()
	except Exception:
		return {}

	return payload if isinstance(payload, dict) else {}

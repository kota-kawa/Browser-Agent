from __future__ import annotations

from typing import Any

from fastapi import Request


async def read_json_payload(request: Request) -> dict[str, Any]:
	"""Safely parse JSON payloads, returning an empty dict for invalid bodies."""

	try:
		payload = await request.json()
	except Exception:
		return {}

	return payload if isinstance(payload, dict) else {}

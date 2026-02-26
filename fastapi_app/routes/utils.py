# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# JP: API ルート共通の補助関数
# EN: Shared utilities for API routes
from fastapi import Request


# EN: Define async function `read_json_payload`.
# JP: 非同期関数 `read_json_payload` を定義する。
async def read_json_payload(request: Request) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Safely parse JSON payloads, returning an empty dict for invalid bodies."""

	# JP: JSON 以外は空 dict にしてハンドラ側を簡潔化
	# EN: Return {} on invalid JSON to simplify handlers
	try:
		# EN: Assign value to payload.
		# JP: payload に値を代入する。
		payload = await request.json()
	except Exception:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {}

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return payload if isinstance(payload, dict) else {}

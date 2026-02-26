# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import anyio

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define async function `save_conversation`.
# JP: 非同期関数 `save_conversation` を定義する。
async def save_conversation(
	input_messages: list[BaseMessage],
	response: Any,
	target: str | Path,
	encoding: str | None = None,
) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Save conversation history to file asynchronously."""
	# EN: Assign value to target_path.
	# JP: target_path に値を代入する。
	target_path = Path(target)
	# create folders if not exists
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if target_path.parent:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await anyio.Path(target_path.parent).mkdir(parents=True, exist_ok=True)

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	await anyio.Path(target_path).write_text(
		await _format_conversation(input_messages, response),
		encoding=encoding or 'utf-8',
	)


# EN: Define async function `_format_conversation`.
# JP: 非同期関数 `_format_conversation` を定義する。
async def _format_conversation(messages: list[BaseMessage], response: Any) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Format the conversation including messages and response."""
	# EN: Assign value to lines.
	# JP: lines に値を代入する。
	lines = []

	# Format messages
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for message in messages:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append(f' {message.role} ')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append(message.text)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('')  # Empty line after each message

	# Format response
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	lines.append(' RESPONSE')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	lines.append(json.dumps(json.loads(response.model_dump_json(exclude_unset=True)), indent=2))

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return '\n'.join(lines)


# Note: _write_messages_to_file and _write_response_to_file have been merged into _format_conversation
# This is more efficient for async operations and reduces file I/O

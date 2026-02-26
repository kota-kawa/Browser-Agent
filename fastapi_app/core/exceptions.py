# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations


# JP: エージェント実行に関する例外型
# EN: Exception raised when the browser agent cannot be executed
class AgentControllerError(RuntimeError):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Raised when the browser agent cannot be executed."""

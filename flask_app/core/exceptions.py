from __future__ import annotations


# JP: エージェント実行に関する例外型
# EN: Exception raised when the browser agent cannot be executed
class AgentControllerError(RuntimeError):
	"""Raised when the browser agent cannot be executed."""

from __future__ import annotations

import threading
from contextlib import contextmanager

from ..core.env import _AGENT_MAX_CONCURRENT_RUNS


# EN: Define class `ConcurrencyLimitExceededError`.
# JP: クラス `ConcurrencyLimitExceededError` を定義する。
class ConcurrencyLimitExceededError(RuntimeError):
	"""Raised when no execution slot is available."""


# EN: Define class `RuntimeSlotGuard`.
# JP: クラス `RuntimeSlotGuard` を定義する。
class RuntimeSlotGuard:
	"""Thread-safe fixed-size slot guard for agent runs."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, capacity: int) -> None:
		# JP: 実行スロット数は最低1に補正して保持
		# EN: Clamp capacity to at least 1 and store runtime state
		self._capacity = max(1, capacity)
		self._active = 0
		self._lock = threading.Lock()

	# EN: Define function `acquire`.
	# JP: 関数 `acquire` を定義する。
	def acquire(self) -> bool:
		# JP: 空きスロットがあれば確保し、なければ False を返す
		# EN: Reserve a slot if available; otherwise return False
		with self._lock:
			if self._active >= self._capacity:
				return False
			self._active += 1
			return True

	# EN: Define function `release`.
	# JP: 関数 `release` を定義する。
	def release(self) -> None:
		# JP: active数を0未満にしないように解放
		# EN: Release one slot while preventing negative counters
		with self._lock:
			if self._active > 0:
				self._active -= 1

	# EN: Define function `snapshot`.
	# JP: 関数 `snapshot` を定義する。
	def snapshot(self) -> tuple[int, int]:
		# JP: 現在の使用数と上限を読み取り専用で返す
		# EN: Return current active usage and configured capacity
		with self._lock:
			return (self._active, self._capacity)

	# EN: Define function `hold`.
	# JP: 関数 `hold` を定義する。
	@contextmanager
	def hold(self):
		# JP: with文で acquire/release を対にして扱えるようにする
		# EN: Provide a context manager wrapper for acquire/release pairing
		acquired = self.acquire()
		try:
			yield acquired
		finally:
			if acquired:
				self.release()


# JP: アプリ全体で共有する同時実行スロットガード
# EN: Process-wide runtime slot guard shared across endpoints
_RUNTIME_SLOT_GUARD = RuntimeSlotGuard(_AGENT_MAX_CONCURRENT_RUNS)

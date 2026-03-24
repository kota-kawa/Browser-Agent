from __future__ import annotations

import threading
from contextlib import contextmanager

from ..core.env import _AGENT_MAX_CONCURRENT_RUNS


class ConcurrencyLimitExceededError(RuntimeError):
	"""Raised when no execution slot is available."""


class RuntimeSlotGuard:
	"""Thread-safe fixed-size slot guard for agent runs."""

	def __init__(self, capacity: int) -> None:
		self._capacity = max(1, capacity)
		self._active = 0
		self._lock = threading.Lock()

	def acquire(self) -> bool:
		with self._lock:
			if self._active >= self._capacity:
				return False
			self._active += 1
			return True

	def release(self) -> None:
		with self._lock:
			if self._active > 0:
				self._active -= 1

	def snapshot(self) -> tuple[int, int]:
		with self._lock:
			return (self._active, self._capacity)

	@contextmanager
	def hold(self):
		acquired = self.acquire()
		try:
			yield acquired
		finally:
			if acquired:
				self.release()


_RUNTIME_SLOT_GUARD = RuntimeSlotGuard(_AGENT_MAX_CONCURRENT_RUNS)

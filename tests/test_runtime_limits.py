from fastapi_app.services.runtime_limits import RuntimeSlotGuard


# EN: Define function `test_runtime_slot_guard_enforces_capacity`.
# JP: 関数 `test_runtime_slot_guard_enforces_capacity` を定義する。
def test_runtime_slot_guard_enforces_capacity():
	guard = RuntimeSlotGuard(1)
	assert guard.acquire() is True
	assert guard.acquire() is False
	guard.release()
	assert guard.acquire() is True


# EN: Define function `test_runtime_slot_guard_hold_context_releases`.
# JP: 関数 `test_runtime_slot_guard_hold_context_releases` を定義する。
def test_runtime_slot_guard_hold_context_releases():
	guard = RuntimeSlotGuard(1)
	with guard.hold() as acquired:
		assert acquired is True
		active, cap = guard.snapshot()
		assert (active, cap) == (1, 1)
	active, cap = guard.snapshot()
	assert (active, cap) == (0, 1)

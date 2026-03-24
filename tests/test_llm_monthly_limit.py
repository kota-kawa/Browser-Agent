import asyncio
import importlib
import threading

import pytest
from browser_use.llm.exceptions import ModelRateLimitError


# EN: Define class `_DummyCompletion`.
# JP: クラス `_DummyCompletion` を定義する。
class _DummyCompletion:
	def __init__(self, completion="ok"):
		self.completion = completion


# EN: Define class `_DummyLLM`.
# JP: クラス `_DummyLLM` を定義する。
class _DummyLLM:
	model = 'dummy-model'

	def __init__(self):
		self.calls = 0

	async def ainvoke(self, messages, output_format=None):
		self.calls += 1
		return _DummyCompletion("ok")


# EN: Define function `test_monthly_limit_blocks_after_limit`.
# JP: 関数 `test_monthly_limit_blocks_after_limit` を定義する。
def test_monthly_limit_blocks_after_limit(monkeypatch):
	monkeypatch.setenv('LLM_MONTHLY_API_LIMIT', '2')

	import fastapi_app.core.env as env_mod
	import fastapi_app.services.llm_daily_limit as limit_mod

	env_mod = importlib.reload(env_mod)
	limit_mod = importlib.reload(limit_mod)
	limit_mod._STATE = None

	llm = limit_mod.apply_monthly_llm_limit(_DummyLLM())
	assert getattr(llm, '_monthly_limit_wrapped', False) is True

	asyncio.run(llm.ainvoke([]))
	asyncio.run(llm.ainvoke([]))

	with pytest.raises(ModelRateLimitError):
		asyncio.run(llm.ainvoke([]))

	assert llm.calls == 2


# EN: Define function `test_monthly_limit_rolls_over_on_month_change`.
# JP: 関数 `test_monthly_limit_rolls_over_on_month_change` を定義する。
def test_monthly_limit_rolls_over_on_month_change(monkeypatch):
	monkeypatch.setenv('LLM_MONTHLY_API_LIMIT', '2')

	import fastapi_app.core.env as env_mod
	import fastapi_app.services.llm_daily_limit as limit_mod

	env_mod = importlib.reload(env_mod)
	limit_mod = importlib.reload(limit_mod)
	limit_mod._STATE = None

	llm = limit_mod.apply_monthly_llm_limit(_DummyLLM())
	asyncio.run(llm.ainvoke([]))
	asyncio.run(llm.ainvoke([]))

	state = limit_mod._STATE
	assert state is not None
	prev_year, prev_month = state.year, state.month
	if prev_month == 1:
		state.month = 12
		state.year = prev_year - 1
	else:
		state.month = prev_month - 1
	state.count = 2

	asyncio.run(llm.ainvoke([]))
	assert llm.calls == 3
	assert state.count == 1


# EN: Define function `test_monthly_limit_default_is_1000_when_unset`.
# JP: 関数 `test_monthly_limit_default_is_1000_when_unset` を定義する。
def test_monthly_limit_default_is_1000_when_unset(monkeypatch):
	monkeypatch.delenv('LLM_MONTHLY_API_LIMIT', raising=False)

	import fastapi_app.core.env as env_mod
	import fastapi_app.services.llm_daily_limit as limit_mod

	env_mod = importlib.reload(env_mod)
	limit_mod = importlib.reload(limit_mod)
	limit_mod._STATE = None

	state = limit_mod._get_state()
	assert state is not None
	assert state.limit == 1000


# EN: Define function `test_monthly_limit_invalid_value_falls_back_to_default`.
# JP: 関数 `test_monthly_limit_invalid_value_falls_back_to_default` を定義する。
def test_monthly_limit_invalid_value_falls_back_to_default(monkeypatch):
	monkeypatch.setenv('LLM_MONTHLY_API_LIMIT', 'invalid')

	import fastapi_app.core.env as env_mod
	import fastapi_app.services.llm_daily_limit as limit_mod

	env_mod = importlib.reload(env_mod)
	limit_mod = importlib.reload(limit_mod)
	limit_mod._STATE = None

	state = limit_mod._get_state()
	assert state is not None
	assert state.limit == 1000


# EN: Define function `test_backward_compatible_alias_wraps_monthly`.
# JP: 関数 `test_backward_compatible_alias_wraps_monthly` を定義する。
def test_backward_compatible_alias_wraps_monthly(monkeypatch):
	monkeypatch.setenv('LLM_MONTHLY_API_LIMIT', '5')

	import fastapi_app.core.env as env_mod
	import fastapi_app.services.llm_daily_limit as limit_mod

	env_mod = importlib.reload(env_mod)
	limit_mod = importlib.reload(limit_mod)
	limit_mod._STATE = None

	llm = limit_mod.apply_daily_llm_limit(_DummyLLM())
	assert getattr(llm, '_monthly_limit_wrapped', False) is True


# EN: Define function `test_check_and_increment_is_thread_safe_shape`.
# JP: 関数 `test_check_and_increment_is_thread_safe_shape` を定義する。
def test_check_and_increment_is_thread_safe_shape():
	import fastapi_app.services.llm_daily_limit as limit_mod

	state = limit_mod._MonthlyLimitState(
		limit=1,
		lock=threading.Lock(),
		year=2099,
		month=1,
		count=0,
	)
	limit_mod._check_and_increment(state, 'dummy')
	assert state.count == 1

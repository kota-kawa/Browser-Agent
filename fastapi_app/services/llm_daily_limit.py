from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel

# JP: LLM 呼び出しに月次/日次の制限を適用するラッパー
# EN: Wrapper that applies monthly and daily limits to LLM calls
from browser_use.llm.base import BaseChatModel
from browser_use.llm.exceptions import ModelRateLimitError
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion

from ..core.config import logger
from ..core.env import (
	_LLM_DAILY_API_LIMIT,
	_LLM_DAILY_BUDGET_USD,
	_LLM_DAILY_TOKEN_LIMIT,
	_LLM_ESTIMATED_INPUT_USD_PER_1K,
	_LLM_ESTIMATED_OUTPUT_USD_PER_1K,
	_LLM_MONTHLY_API_LIMIT,
)

T = TypeVar('T', bound=BaseModel)


# EN: Define class `_MonthlyLimitState`.
# JP: クラス `_MonthlyLimitState` を定義する。
@dataclass
class _MonthlyLimitState:
	limit: int
	lock: threading.Lock
	year: int
	month: int
	count: int


# EN: Define class `_DailyBudgetState`.
# JP: クラス `_DailyBudgetState` を定義する。
@dataclass
class _DailyBudgetState:
	api_limit: int
	token_limit: int
	budget_usd: float
	input_cost_per_1k: float
	output_cost_per_1k: float
	lock: threading.Lock
	year: int
	month: int
	day: int
	api_calls: int
	total_tokens: int
	estimated_spend_usd: float


_STATE: _MonthlyLimitState | None = None
_DAILY_STATE: _DailyBudgetState | None = None


# EN: Define function `_current_year_month`.
# JP: 関数 `_current_year_month` を定義する。
def _current_year_month() -> tuple[int, int]:
	# JP: ローカル時刻の年月で月次切り替えを判定
	# EN: Use local year/month for monthly rollover
	now = datetime.now()
	return now.year, now.month


# EN: Define function `_current_year_month_day`.
# JP: 関数 `_current_year_month_day` を定義する。
def _current_year_month_day() -> tuple[int, int, int]:
	# JP: 日次上限のリセット判定に使う年月日を返す
	# EN: Return year/month/day for daily rollover checks
	now = datetime.now()
	return now.year, now.month, now.day


# EN: Define function `_get_state`.
# JP: 関数 `_get_state` を定義する。
def _get_state() -> _MonthlyLimitState | None:
	# JP: 初回アクセス時に月次制限状態を生成
	# EN: Initialize monthly limit state on first access
	global _STATE

	if _STATE is not None:
		return _STATE

	if _LLM_MONTHLY_API_LIMIT <= 0:
		return None

	year, month = _current_year_month()
	_STATE = _MonthlyLimitState(
		limit=_LLM_MONTHLY_API_LIMIT,
		lock=threading.Lock(),
		year=year,
		month=month,
		count=0,
	)
	logger.info('LLM monthly API limit enabled: %s calls/month', _STATE.limit)
	return _STATE


# EN: Define function `_get_daily_state`.
# JP: 関数 `_get_daily_state` を定義する。
def _get_daily_state() -> _DailyBudgetState | None:
	# JP: 初回アクセス時のみ日次制限状態を生成する
	# EN: Lazily initialize daily limit state on first access
	global _DAILY_STATE

	if _DAILY_STATE is not None:
		return _DAILY_STATE

	if _LLM_DAILY_API_LIMIT <= 0 and _LLM_DAILY_TOKEN_LIMIT <= 0 and _LLM_DAILY_BUDGET_USD <= 0:
		return None

	year, month, day = _current_year_month_day()
	_DAILY_STATE = _DailyBudgetState(
		api_limit=_LLM_DAILY_API_LIMIT,
		token_limit=_LLM_DAILY_TOKEN_LIMIT,
		budget_usd=_LLM_DAILY_BUDGET_USD,
		input_cost_per_1k=_LLM_ESTIMATED_INPUT_USD_PER_1K,
		output_cost_per_1k=_LLM_ESTIMATED_OUTPUT_USD_PER_1K,
		lock=threading.Lock(),
		year=year,
		month=month,
		day=day,
		api_calls=0,
		total_tokens=0,
		estimated_spend_usd=0.0,
	)
	logger.info(
		'LLM daily budget enabled: %s calls/day, %s tokens/day, $%.4f/day',
		_DAILY_STATE.api_limit,
		_DAILY_STATE.token_limit,
		_DAILY_STATE.budget_usd,
	)
	return _DAILY_STATE


# EN: Define function `_check_and_increment`.
# JP: 関数 `_check_and_increment` を定義する。
def _check_and_increment(state: _MonthlyLimitState, model: str | None) -> None:
	# JP: 月の切り替えと回数上限チェック
	# EN: Reset counts on new month and enforce the limit
	with state.lock:
		year, month = _current_year_month()
		if year != state.year or month != state.month:
			state.year = year
			state.month = month
			state.count = 0

		if state.count >= state.limit:
			message = f'LLM API monthly limit reached ({state.limit}/month).'
			logger.warning(message)
			raise ModelRateLimitError(message=message, model=model)

		state.count += 1


# EN: Define function `_check_daily_request_allowance`.
# JP: 関数 `_check_daily_request_allowance` を定義する。
def _check_daily_request_allowance(state: _DailyBudgetState, model: str | None) -> None:
	# JP: 呼び出し前にAPI回数上限を判定
	# EN: Enforce API-call cap before invoking the provider
	with state.lock:
		year, month, day = _current_year_month_day()
		if year != state.year or month != state.month or day != state.day:
			state.year = year
			state.month = month
			state.day = day
			state.api_calls = 0
			state.total_tokens = 0
			state.estimated_spend_usd = 0.0

		if state.api_limit > 0 and state.api_calls >= state.api_limit:
			message = f'LLM API daily limit reached ({state.api_limit}/day).'
			logger.warning(message)
			raise ModelRateLimitError(message=message, model=model)


# EN: Define function `_record_daily_usage`.
# JP: 関数 `_record_daily_usage` を定義する。
def _record_daily_usage(
	state: _DailyBudgetState,
	model: str | None,
	usage_tokens: int,
	completion_tokens: int,
) -> None:
	# JP: 呼び出し後にトークン/推定費用を加算し上限を判定
	# EN: Record token usage and estimated spend after invocation
	with state.lock:
		state.api_calls += 1
		state.total_tokens += usage_tokens
		input_tokens = usage_tokens - completion_tokens
		if input_tokens < 0:
			input_tokens = 0

		input_cost = (input_tokens / 1000.0) * state.input_cost_per_1k
		output_cost = (completion_tokens / 1000.0) * state.output_cost_per_1k
		state.estimated_spend_usd += input_cost + output_cost

		if state.token_limit > 0 and state.total_tokens > state.token_limit:
			message = f'LLM daily token limit reached ({state.token_limit}/day).'
			logger.warning(message)
			raise ModelRateLimitError(message=message, model=model)

		if state.budget_usd > 0 and state.estimated_spend_usd > state.budget_usd:
			message = f'LLM daily budget reached (${state.budget_usd:.4f}/day).'
			logger.warning(message)
			raise ModelRateLimitError(message=message, model=model)


# EN: Define function `apply_monthly_llm_limit`.
# JP: 関数 `apply_monthly_llm_limit` を定義する。
def apply_monthly_llm_limit(llm: BaseChatModel) -> BaseChatModel:
	# JP: LLM の ainvoke をラップして回数制限を追加
	# EN: Wrap llm.ainvoke to enforce a monthly call limit
	state = _get_state()
	daily_state = _get_daily_state()
	if state is None and daily_state is None:
		return llm

	if getattr(llm, '_monthly_limit_wrapped', False):
		return llm

	original_ainvoke = llm.ainvoke

	# EN: Define async function `limited_ainvoke`.
	# JP: 非同期関数 `limited_ainvoke` を定義する。
	async def limited_ainvoke(
		messages: list[BaseMessage],
		output_format: type[T] | None = None,
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		model_name = getattr(llm, 'model', None)
		model_label = str(model_name) if model_name is not None else None
		if state is not None:
			_check_and_increment(state, model_label)
		if daily_state is not None:
			_check_daily_request_allowance(daily_state, model_label)

		completion = await original_ainvoke(messages, output_format)
		usage = getattr(completion, 'usage', None)
		usage_total = int(getattr(usage, 'total_tokens', 0) or 0)
		usage_completion = int(getattr(usage, 'completion_tokens', 0) or 0)
		# JP: 応答後の実使用量で日次トークン/予算上限を評価
		# EN: Enforce token/budget caps using post-call usage metrics
		if daily_state is not None:
			_record_daily_usage(daily_state, model_label, usage_total, usage_completion)

		return completion

	setattr(llm, 'ainvoke', limited_ainvoke)
	setattr(llm, '_monthly_limit_wrapped', True)
	return llm


# EN: Define function `apply_daily_llm_limit`.
# JP: 関数 `apply_daily_llm_limit` を定義する。
def apply_daily_llm_limit(llm: BaseChatModel) -> BaseChatModel:
	"""Backward-compatible alias for the previous function name."""

	# JP: 旧API名の互換エイリアスとして同じラッパーを返す
	# EN: Keep backward compatibility by delegating to the same wrapper
	return apply_monthly_llm_limit(llm)

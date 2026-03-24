from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar

# JP: LLM 呼び出し回数に日次制限を適用するラッパー
# EN: Wrapper that applies a monthly limit to LLM calls
from browser_use.llm.base import BaseChatModel
from browser_use.llm.exceptions import ModelRateLimitError
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion
from pydantic import BaseModel

from ..core.config import logger
from ..core.env import _LLM_MONTHLY_API_LIMIT

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


_STATE: _MonthlyLimitState | None = None


# EN: Define function `_current_year_month`.
# JP: 関数 `_current_year_month` を定義する。
def _current_year_month() -> tuple[int, int]:
	# JP: ローカル時刻の年月で月次切り替えを判定
	# EN: Use local year/month for monthly rollover
	now = datetime.now()
	return now.year, now.month


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


# EN: Define function `apply_monthly_llm_limit`.
# JP: 関数 `apply_monthly_llm_limit` を定義する。
def apply_monthly_llm_limit(llm: BaseChatModel) -> BaseChatModel:
	# JP: LLM の ainvoke をラップして回数制限を追加
	# EN: Wrap llm.ainvoke to enforce a monthly call limit
	state = _get_state()
	if state is None:
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
		_check_and_increment(state, str(model_name) if model_name is not None else None)
		return await original_ainvoke(messages, output_format)

	setattr(llm, 'ainvoke', limited_ainvoke)
	setattr(llm, '_monthly_limit_wrapped', True)
	return llm


# EN: Define function `apply_daily_llm_limit`.
# JP: 関数 `apply_daily_llm_limit` を定義する。
def apply_daily_llm_limit(llm: BaseChatModel) -> BaseChatModel:
	"""Backward-compatible alias for the previous function name."""

	return apply_monthly_llm_limit(llm)

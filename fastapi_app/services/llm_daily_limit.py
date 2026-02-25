from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date, datetime
from typing import TypeVar

# JP: LLM 呼び出し回数に日次制限を適用するラッパー
# EN: Wrapper that applies a daily limit to LLM calls
from browser_use.llm.base import BaseChatModel
from browser_use.llm.exceptions import ModelRateLimitError
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion
from pydantic import BaseModel

from ..core.config import logger
from ..core.env import _LLM_DAILY_API_LIMIT

T = TypeVar('T', bound=BaseModel)


@dataclass
class _DailyLimitState:
	limit: int
	lock: threading.Lock
	day: date
	count: int


_STATE: _DailyLimitState | None = None


def _today() -> date:
	# JP: ローカル日付で日次切り替えを判定
	# EN: Use local date for daily rollover
	return datetime.now().date()


def _get_state() -> _DailyLimitState | None:
	# JP: 初回アクセス時に日次制限状態を生成
	# EN: Initialize daily limit state on first access
	global _STATE

	if _STATE is not None:
		return _STATE

	if _LLM_DAILY_API_LIMIT <= 0:
		return None

	_STATE = _DailyLimitState(
		limit=_LLM_DAILY_API_LIMIT,
		lock=threading.Lock(),
		day=_today(),
		count=0,
	)
	logger.info('LLM daily API limit enabled: %s calls/day', _STATE.limit)
	return _STATE


def _check_and_increment(state: _DailyLimitState, model: str | None) -> None:
	# JP: 日付の切り替えと回数上限チェック
	# EN: Reset counts on new day and enforce the limit
	with state.lock:
		today = _today()
		if today != state.day:
			state.day = today
			state.count = 0

		if state.count >= state.limit:
			message = f'LLM API daily limit reached ({state.limit}/day).'
			logger.warning(message)
			raise ModelRateLimitError(message=message, model=model)

		state.count += 1


def apply_daily_llm_limit(llm: BaseChatModel) -> BaseChatModel:
	# JP: LLM の ainvoke をラップして回数制限を追加
	# EN: Wrap llm.ainvoke to enforce a daily call limit
	state = _get_state()
	if state is None:
		return llm

	if getattr(llm, '_daily_limit_wrapped', False):
		return llm

	original_ainvoke = llm.ainvoke

	async def limited_ainvoke(
		messages: list[BaseMessage],
		output_format: type[T] | None = None,
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		model_name = getattr(llm, 'model', None)
		_check_and_increment(state, str(model_name) if model_name is not None else None)
		return await original_ainvoke(messages, output_format)

	setattr(llm, 'ainvoke', limited_ainvoke)
	setattr(llm, '_daily_limit_wrapped', True)
	return llm

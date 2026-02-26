# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import threading
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import date, datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TypeVar

# JP: LLM 呼び出し回数に日次制限を適用するラッパー
# EN: Wrapper that applies a daily limit to LLM calls
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.exceptions import ModelRateLimitError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.env import _LLM_DAILY_API_LIMIT

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `_DailyLimitState`.
# JP: クラス `_DailyLimitState` を定義する。
@dataclass
class _DailyLimitState:
	# EN: Assign annotated value to limit.
	# JP: limit に型付きの値を代入する。
	limit: int
	# EN: Assign annotated value to lock.
	# JP: lock に型付きの値を代入する。
	lock: threading.Lock
	# EN: Assign annotated value to day.
	# JP: day に型付きの値を代入する。
	day: date
	# EN: Assign annotated value to count.
	# JP: count に型付きの値を代入する。
	count: int


# EN: Assign annotated value to _STATE.
# JP: _STATE に型付きの値を代入する。
_STATE: _DailyLimitState | None = None


# EN: Define function `_today`.
# JP: 関数 `_today` を定義する。
def _today() -> date:
	# JP: ローカル日付で日次切り替えを判定
	# EN: Use local date for daily rollover
	return datetime.now().date()


# EN: Define function `_get_state`.
# JP: 関数 `_get_state` を定義する。
def _get_state() -> _DailyLimitState | None:
	# JP: 初回アクセス時に日次制限状態を生成
	# EN: Initialize daily limit state on first access
	global _STATE

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _STATE is not None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _STATE

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _LLM_DAILY_API_LIMIT <= 0:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Assign value to _STATE.
	# JP: _STATE に値を代入する。
	_STATE = _DailyLimitState(
		limit=_LLM_DAILY_API_LIMIT,
		lock=threading.Lock(),
		day=_today(),
		count=0,
	)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.info('LLM daily API limit enabled: %s calls/day', _STATE.limit)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return _STATE


# EN: Define function `_check_and_increment`.
# JP: 関数 `_check_and_increment` を定義する。
def _check_and_increment(state: _DailyLimitState, model: str | None) -> None:
	# JP: 日付の切り替えと回数上限チェック
	# EN: Reset counts on new day and enforce the limit
	with state.lock:
		# EN: Assign value to today.
		# JP: today に値を代入する。
		today = _today()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if today != state.day:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			state.day = today
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			state.count = 0

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if state.count >= state.limit:
			# EN: Assign value to message.
			# JP: message に値を代入する。
			message = f'LLM API daily limit reached ({state.limit}/day).'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(message)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelRateLimitError(message=message, model=model)

		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		state.count += 1


# EN: Define function `apply_daily_llm_limit`.
# JP: 関数 `apply_daily_llm_limit` を定義する。
def apply_daily_llm_limit(llm: BaseChatModel) -> BaseChatModel:
	# JP: LLM の ainvoke をラップして回数制限を追加
	# EN: Wrap llm.ainvoke to enforce a daily call limit
	state = _get_state()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if state is None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return llm

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if getattr(llm, '_daily_limit_wrapped', False):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return llm

	# EN: Assign value to original_ainvoke.
	# JP: original_ainvoke に値を代入する。
	original_ainvoke = llm.ainvoke

	# EN: Define async function `limited_ainvoke`.
	# JP: 非同期関数 `limited_ainvoke` を定義する。
	async def limited_ainvoke(
		messages: list[BaseMessage],
		output_format: type[T] | None = None,
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		# EN: Assign value to model_name.
		# JP: model_name に値を代入する。
		model_name = getattr(llm, 'model', None)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_check_and_increment(state, str(model_name) if model_name is not None else None)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await original_ainvoke(messages, output_format)

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	setattr(llm, 'ainvoke', limited_ainvoke)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	setattr(llm, '_daily_limit_wrapped', True)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return llm

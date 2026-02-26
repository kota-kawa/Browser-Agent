# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, TypeVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, Field

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeUsage

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `TokenUsageEntry`.
# JP: クラス `TokenUsageEntry` を定義する。
class TokenUsageEntry(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Single token usage entry"""

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str
	# EN: Assign annotated value to timestamp.
	# JP: timestamp に型付きの値を代入する。
	timestamp: datetime
	# EN: Assign annotated value to usage.
	# JP: usage に型付きの値を代入する。
	usage: ChatInvokeUsage


# EN: Define class `TokenCostCalculated`.
# JP: クラス `TokenCostCalculated` を定義する。
class TokenCostCalculated(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Token cost"""

	# EN: Assign annotated value to new_prompt_tokens.
	# JP: new_prompt_tokens に型付きの値を代入する。
	new_prompt_tokens: int
	# EN: Assign annotated value to new_prompt_cost.
	# JP: new_prompt_cost に型付きの値を代入する。
	new_prompt_cost: float

	# EN: Assign annotated value to prompt_read_cached_tokens.
	# JP: prompt_read_cached_tokens に型付きの値を代入する。
	prompt_read_cached_tokens: int | None
	# EN: Assign annotated value to prompt_read_cached_cost.
	# JP: prompt_read_cached_cost に型付きの値を代入する。
	prompt_read_cached_cost: float | None

	# EN: Assign annotated value to prompt_cached_creation_tokens.
	# JP: prompt_cached_creation_tokens に型付きの値を代入する。
	prompt_cached_creation_tokens: int | None
	# EN: Assign annotated value to prompt_cache_creation_cost.
	# JP: prompt_cache_creation_cost に型付きの値を代入する。
	prompt_cache_creation_cost: float | None
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Anthropic only: The cost of creating the cache."""

	# EN: Assign annotated value to completion_tokens.
	# JP: completion_tokens に型付きの値を代入する。
	completion_tokens: int
	# EN: Assign annotated value to completion_cost.
	# JP: completion_cost に型付きの値を代入する。
	completion_cost: float

	# EN: Define function `prompt_cost`.
	# JP: 関数 `prompt_cost` を定義する。
	@property
	def prompt_cost(self) -> float:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.new_prompt_cost + (self.prompt_read_cached_cost or 0) + (self.prompt_cache_creation_cost or 0)

	# EN: Define function `total_cost`.
	# JP: 関数 `total_cost` を定義する。
	@property
	def total_cost(self) -> float:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (
			self.new_prompt_cost
			+ (self.prompt_read_cached_cost or 0)
			+ (self.prompt_cache_creation_cost or 0)
			+ self.completion_cost
		)


# EN: Define class `ModelPricing`.
# JP: クラス `ModelPricing` を定義する。
class ModelPricing(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Pricing information for a model"""

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str
	# EN: Assign annotated value to input_cost_per_token.
	# JP: input_cost_per_token に型付きの値を代入する。
	input_cost_per_token: float | None
	# EN: Assign annotated value to output_cost_per_token.
	# JP: output_cost_per_token に型付きの値を代入する。
	output_cost_per_token: float | None

	# EN: Assign annotated value to cache_read_input_token_cost.
	# JP: cache_read_input_token_cost に型付きの値を代入する。
	cache_read_input_token_cost: float | None
	# EN: Assign annotated value to cache_creation_input_token_cost.
	# JP: cache_creation_input_token_cost に型付きの値を代入する。
	cache_creation_input_token_cost: float | None

	# EN: Assign annotated value to max_tokens.
	# JP: max_tokens に型付きの値を代入する。
	max_tokens: int | None
	# EN: Assign annotated value to max_input_tokens.
	# JP: max_input_tokens に型付きの値を代入する。
	max_input_tokens: int | None
	# EN: Assign annotated value to max_output_tokens.
	# JP: max_output_tokens に型付きの値を代入する。
	max_output_tokens: int | None


# EN: Define class `CachedPricingData`.
# JP: クラス `CachedPricingData` を定義する。
class CachedPricingData(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Cached pricing data with timestamp"""

	# EN: Assign annotated value to timestamp.
	# JP: timestamp に型付きの値を代入する。
	timestamp: datetime
	# EN: Assign annotated value to data.
	# JP: data に型付きの値を代入する。
	data: dict[str, Any]


# EN: Define class `ModelUsageStats`.
# JP: クラス `ModelUsageStats` を定義する。
class ModelUsageStats(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Usage statistics for a single model"""

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str
	# EN: Assign annotated value to prompt_tokens.
	# JP: prompt_tokens に型付きの値を代入する。
	prompt_tokens: int = 0
	# EN: Assign annotated value to completion_tokens.
	# JP: completion_tokens に型付きの値を代入する。
	completion_tokens: int = 0
	# EN: Assign annotated value to total_tokens.
	# JP: total_tokens に型付きの値を代入する。
	total_tokens: int = 0
	# EN: Assign annotated value to cost.
	# JP: cost に型付きの値を代入する。
	cost: float = 0.0
	# EN: Assign annotated value to invocations.
	# JP: invocations に型付きの値を代入する。
	invocations: int = 0
	# EN: Assign annotated value to average_tokens_per_invocation.
	# JP: average_tokens_per_invocation に型付きの値を代入する。
	average_tokens_per_invocation: float = 0.0


# EN: Define class `ModelUsageTokens`.
# JP: クラス `ModelUsageTokens` を定義する。
class ModelUsageTokens(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Usage tokens for a single model"""

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str
	# EN: Assign annotated value to prompt_tokens.
	# JP: prompt_tokens に型付きの値を代入する。
	prompt_tokens: int
	# EN: Assign annotated value to prompt_cached_tokens.
	# JP: prompt_cached_tokens に型付きの値を代入する。
	prompt_cached_tokens: int
	# EN: Assign annotated value to completion_tokens.
	# JP: completion_tokens に型付きの値を代入する。
	completion_tokens: int
	# EN: Assign annotated value to total_tokens.
	# JP: total_tokens に型付きの値を代入する。
	total_tokens: int


# EN: Define class `UsageSummary`.
# JP: クラス `UsageSummary` を定義する。
class UsageSummary(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Summary of token usage and costs"""

	# EN: Assign annotated value to total_prompt_tokens.
	# JP: total_prompt_tokens に型付きの値を代入する。
	total_prompt_tokens: int
	# EN: Assign annotated value to total_prompt_cost.
	# JP: total_prompt_cost に型付きの値を代入する。
	total_prompt_cost: float

	# EN: Assign annotated value to total_prompt_cached_tokens.
	# JP: total_prompt_cached_tokens に型付きの値を代入する。
	total_prompt_cached_tokens: int
	# EN: Assign annotated value to total_prompt_cached_cost.
	# JP: total_prompt_cached_cost に型付きの値を代入する。
	total_prompt_cached_cost: float

	# EN: Assign annotated value to total_completion_tokens.
	# JP: total_completion_tokens に型付きの値を代入する。
	total_completion_tokens: int
	# EN: Assign annotated value to total_completion_cost.
	# JP: total_completion_cost に型付きの値を代入する。
	total_completion_cost: float
	# EN: Assign annotated value to total_tokens.
	# JP: total_tokens に型付きの値を代入する。
	total_tokens: int
	# EN: Assign annotated value to total_cost.
	# JP: total_cost に型付きの値を代入する。
	total_cost: float
	# EN: Assign annotated value to entry_count.
	# JP: entry_count に型付きの値を代入する。
	entry_count: int

	# EN: Assign annotated value to by_model.
	# JP: by_model に型付きの値を代入する。
	by_model: dict[str, ModelUsageStats] = Field(default_factory=dict)

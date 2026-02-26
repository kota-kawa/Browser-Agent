from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from browser_use.llm.views import ChatInvokeUsage

T = TypeVar('T', bound=BaseModel)


# EN: Define class `TokenUsageEntry`.
# JP: クラス `TokenUsageEntry` を定義する。
class TokenUsageEntry(BaseModel):
	"""Single token usage entry"""

	model: str
	timestamp: datetime
	usage: ChatInvokeUsage


# EN: Define class `TokenCostCalculated`.
# JP: クラス `TokenCostCalculated` を定義する。
class TokenCostCalculated(BaseModel):
	"""Token cost"""

	new_prompt_tokens: int
	new_prompt_cost: float

	prompt_read_cached_tokens: int | None
	prompt_read_cached_cost: float | None

	prompt_cached_creation_tokens: int | None
	prompt_cache_creation_cost: float | None
	"""Anthropic only: The cost of creating the cache."""

	completion_tokens: int
	completion_cost: float

	# EN: Define function `prompt_cost`.
	# JP: 関数 `prompt_cost` を定義する。
	@property
	def prompt_cost(self) -> float:
		return self.new_prompt_cost + (self.prompt_read_cached_cost or 0) + (self.prompt_cache_creation_cost or 0)

	# EN: Define function `total_cost`.
	# JP: 関数 `total_cost` を定義する。
	@property
	def total_cost(self) -> float:
		return (
			self.new_prompt_cost
			+ (self.prompt_read_cached_cost or 0)
			+ (self.prompt_cache_creation_cost or 0)
			+ self.completion_cost
		)


# EN: Define class `ModelPricing`.
# JP: クラス `ModelPricing` を定義する。
class ModelPricing(BaseModel):
	"""Pricing information for a model"""

	model: str
	input_cost_per_token: float | None
	output_cost_per_token: float | None

	cache_read_input_token_cost: float | None
	cache_creation_input_token_cost: float | None

	max_tokens: int | None
	max_input_tokens: int | None
	max_output_tokens: int | None


# EN: Define class `CachedPricingData`.
# JP: クラス `CachedPricingData` を定義する。
class CachedPricingData(BaseModel):
	"""Cached pricing data with timestamp"""

	timestamp: datetime
	data: dict[str, Any]


# EN: Define class `ModelUsageStats`.
# JP: クラス `ModelUsageStats` を定義する。
class ModelUsageStats(BaseModel):
	"""Usage statistics for a single model"""

	model: str
	prompt_tokens: int = 0
	completion_tokens: int = 0
	total_tokens: int = 0
	cost: float = 0.0
	invocations: int = 0
	average_tokens_per_invocation: float = 0.0


# EN: Define class `ModelUsageTokens`.
# JP: クラス `ModelUsageTokens` を定義する。
class ModelUsageTokens(BaseModel):
	"""Usage tokens for a single model"""

	model: str
	prompt_tokens: int
	prompt_cached_tokens: int
	completion_tokens: int
	total_tokens: int


# EN: Define class `UsageSummary`.
# JP: クラス `UsageSummary` を定義する。
class UsageSummary(BaseModel):
	"""Summary of token usage and costs"""

	total_prompt_tokens: int
	total_prompt_cost: float

	total_prompt_cached_tokens: int
	total_prompt_cached_cost: float

	total_completion_tokens: int
	total_completion_cost: float
	total_tokens: int
	total_cost: float
	entry_count: int

	by_model: dict[str, ModelUsageStats] = Field(default_factory=dict)

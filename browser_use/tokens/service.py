# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Token cost service that tracks LLM token usage and costs.

Fetches pricing data from LiteLLM repository and caches it for 1 day.
Automatically tracks token usage when LLMs are registered and invoked.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime, timedelta
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import aiofiles
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.env_loader import load_secrets_env
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeUsage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tokens.views import (
	CachedPricingData,
	ModelPricing,
	ModelUsageStats,
	ModelUsageTokens,
	TokenCostCalculated,
	TokenUsageEntry,
	UsageSummary,
)

# EN: Evaluate an expression.
# JP: 式を評価する。
load_secrets_env()

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)
# EN: Assign value to cost_logger.
# JP: cost_logger に値を代入する。
cost_logger = logging.getLogger('cost')


# EN: Define function `xdg_cache_home`.
# JP: 関数 `xdg_cache_home` を定義する。
def xdg_cache_home() -> Path:
	# EN: Assign value to default.
	# JP: default に値を代入する。
	default = Path.home() / '.cache'
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if CONFIG.XDG_CACHE_HOME and (path := Path(CONFIG.XDG_CACHE_HOME)).is_absolute():
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return path
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return default


# EN: Define class `TokenCost`.
# JP: クラス `TokenCost` を定義する。
class TokenCost:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Service for tracking token usage and calculating costs"""

	# EN: Assign value to CACHE_DIR_NAME.
	# JP: CACHE_DIR_NAME に値を代入する。
	CACHE_DIR_NAME = 'browser_use/token_cost'
	# EN: Assign value to CACHE_DURATION.
	# JP: CACHE_DURATION に値を代入する。
	CACHE_DURATION = timedelta(days=1)
	# EN: Assign value to PRICING_URL.
	# JP: PRICING_URL に値を代入する。
	PRICING_URL = 'https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json'

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, include_cost: bool = False):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.include_cost = include_cost or os.getenv('BROWSER_USE_CALCULATE_COST', 'false').lower() == 'true'

		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.usage_history: list[TokenUsageEntry] = []
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.registered_llms: dict[str, BaseChatModel] = {}
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._pricing_data: dict[str, Any] | None = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._initialized = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._cache_dir = xdg_cache_home() / self.CACHE_DIR_NAME

	# EN: Define async function `initialize`.
	# JP: 非同期関数 `initialize` を定義する。
	async def initialize(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize the service by loading pricing data"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._initialized:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.include_cost:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._load_pricing_data()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._initialized = True

	# EN: Define async function `_load_pricing_data`.
	# JP: 非同期関数 `_load_pricing_data` を定義する。
	async def _load_pricing_data(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load pricing data from cache or fetch from GitHub"""
		# Try to find a valid cache file
		# EN: Assign value to cache_file.
		# JP: cache_file に値を代入する。
		cache_file = await self._find_valid_cache()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if cache_file:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._load_from_cache(cache_file)
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._fetch_and_cache_pricing_data()

	# EN: Define async function `_find_valid_cache`.
	# JP: 非同期関数 `_find_valid_cache` を定義する。
	async def _find_valid_cache(self) -> Path | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Find the most recent valid cache file"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Ensure cache directory exists
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._cache_dir.mkdir(parents=True, exist_ok=True)

			# List all JSON files in the cache directory
			# EN: Assign value to cache_files.
			# JP: cache_files に値を代入する。
			cache_files = list(self._cache_dir.glob('*.json'))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not cache_files:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

			# Sort by modification time (most recent first)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cache_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

			# Check each file until we find a valid one
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for cache_file in cache_files:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if await self._is_cache_valid(cache_file):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return cache_file
				else:
					# Clean up old cache files
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						os.remove(cache_file)
					except Exception:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None
		except Exception:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

	# EN: Define async function `_is_cache_valid`.
	# JP: 非同期関数 `_is_cache_valid` を定義する。
	async def _is_cache_valid(self, cache_file: Path) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if a specific cache file is valid and not expired"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not cache_file.exists():
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return False

			# Read the cached data
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with aiofiles.open(cache_file, 'r') as f:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = await f.read()
				# EN: Assign value to cached.
				# JP: cached に値を代入する。
				cached = CachedPricingData.model_validate_json(content)

			# Check if cache is still valid
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return datetime.now() - cached.timestamp < self.CACHE_DURATION
		except Exception:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# EN: Define async function `_load_from_cache`.
	# JP: 非同期関数 `_load_from_cache` を定義する。
	async def _load_from_cache(self, cache_file: Path) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load pricing data from a specific cache file"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with aiofiles.open(cache_file, 'r') as f:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = await f.read()
				# EN: Assign value to cached.
				# JP: cached に値を代入する。
				cached = CachedPricingData.model_validate_json(content)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._pricing_data = cached.data
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Error loading cached pricing data from {cache_file}: {e}')
			# Fall back to fetching
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._fetch_and_cache_pricing_data()

	# EN: Define async function `_fetch_and_cache_pricing_data`.
	# JP: 非同期関数 `_fetch_and_cache_pricing_data` を定義する。
	async def _fetch_and_cache_pricing_data(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Fetch pricing data from LiteLLM GitHub and cache it with timestamp"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with httpx.AsyncClient() as client:
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await client.get(self.PRICING_URL, timeout=30)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				response.raise_for_status()

				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._pricing_data = response.json()

			# Create cache object with timestamp
			# EN: Assign value to cached.
			# JP: cached に値を代入する。
			cached = CachedPricingData(timestamp=datetime.now(), data=self._pricing_data or {})

			# Ensure cache directory exists
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._cache_dir.mkdir(parents=True, exist_ok=True)

			# Create cache file with timestamp in filename
			# EN: Assign value to timestamp_str.
			# JP: timestamp_str に値を代入する。
			timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
			# EN: Assign value to cache_file.
			# JP: cache_file に値を代入する。
			cache_file = self._cache_dir / f'pricing_{timestamp_str}.json'

			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with aiofiles.open(cache_file, 'w') as f:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await f.write(cached.model_dump_json(indent=2))

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Error fetching pricing data: {e}')
			# Fall back to empty pricing data
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._pricing_data = {}

	# EN: Define async function `get_model_pricing`.
	# JP: 非同期関数 `get_model_pricing` を定義する。
	async def get_model_pricing(self, model_name: str) -> ModelPricing | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get pricing information for a specific model"""
		# Ensure we're initialized
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._initialized:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.initialize()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._pricing_data or model_name not in self._pricing_data:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to data.
		# JP: data に値を代入する。
		data = self._pricing_data[model_name]
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ModelPricing(
			model=model_name,
			input_cost_per_token=data.get('input_cost_per_token'),
			output_cost_per_token=data.get('output_cost_per_token'),
			max_tokens=data.get('max_tokens'),
			max_input_tokens=data.get('max_input_tokens'),
			max_output_tokens=data.get('max_output_tokens'),
			cache_read_input_token_cost=data.get('cache_read_input_token_cost'),
			cache_creation_input_token_cost=data.get('cache_creation_input_token_cost'),
		)

	# EN: Define async function `calculate_cost`.
	# JP: 非同期関数 `calculate_cost` を定義する。
	async def calculate_cost(self, model: str, usage: ChatInvokeUsage) -> TokenCostCalculated | None:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.include_cost:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to data.
		# JP: data に値を代入する。
		data = await self.get_model_pricing(model)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if data is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to uncached_prompt_tokens.
		# JP: uncached_prompt_tokens に値を代入する。
		uncached_prompt_tokens = usage.prompt_tokens - (usage.prompt_cached_tokens or 0)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return TokenCostCalculated(
			new_prompt_tokens=usage.prompt_tokens,
			new_prompt_cost=uncached_prompt_tokens * (data.input_cost_per_token or 0),
			# Cached tokens
			prompt_read_cached_tokens=usage.prompt_cached_tokens,
			prompt_read_cached_cost=usage.prompt_cached_tokens * data.cache_read_input_token_cost
			if usage.prompt_cached_tokens and data.cache_read_input_token_cost
			else None,
			# Cache creation tokens
			prompt_cached_creation_tokens=usage.prompt_cache_creation_tokens,
			prompt_cache_creation_cost=usage.prompt_cache_creation_tokens * data.cache_creation_input_token_cost
			if data.cache_creation_input_token_cost and usage.prompt_cache_creation_tokens
			else None,
			# Completion tokens
			completion_tokens=usage.completion_tokens,
			completion_cost=usage.completion_tokens * float(data.output_cost_per_token or 0),
		)

	# EN: Define function `add_usage`.
	# JP: 関数 `add_usage` を定義する。
	def add_usage(self, model: str, usage: ChatInvokeUsage) -> TokenUsageEntry:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Add token usage entry to history (without calculating cost)"""
		# EN: Assign value to entry.
		# JP: entry に値を代入する。
		entry = TokenUsageEntry(
			model=model,
			timestamp=datetime.now(),
			usage=usage,
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.usage_history.append(entry)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return entry

	# async def _log_non_usage_llm(self, llm: BaseChatModel) -> None:
	# 	"""Log non-usage to the logger"""
	# 	C_CYAN = '\033[96m'
	# 	C_RESET = '\033[0m'

	# 	cost_logger.debug(f'🧠 llm : {C_CYAN}{llm.model}{C_RESET} (no usage found)')

	# EN: Define async function `_log_usage`.
	# JP: 非同期関数 `_log_usage` を定義する。
	async def _log_usage(self, model: str, usage: TokenUsageEntry) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log usage to the logger"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._initialized:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.initialize()

		# ANSI color codes
		# EN: Assign value to C_CYAN.
		# JP: C_CYAN に値を代入する。
		C_CYAN = '\033[96m'
		# EN: Assign value to C_YELLOW.
		# JP: C_YELLOW に値を代入する。
		C_YELLOW = '\033[93m'
		# EN: Assign value to C_GREEN.
		# JP: C_GREEN に値を代入する。
		C_GREEN = '\033[92m'
		# EN: Assign value to C_BLUE.
		# JP: C_BLUE に値を代入する。
		C_BLUE = '\033[94m'
		# EN: Assign value to C_RESET.
		# JP: C_RESET に値を代入する。
		C_RESET = '\033[0m'

		# Always get cost breakdown for token details (even if not showing costs)
		# EN: Assign value to cost.
		# JP: cost に値を代入する。
		cost = await self.calculate_cost(model, usage.usage)

		# Build input tokens breakdown
		# EN: Assign value to input_part.
		# JP: input_part に値を代入する。
		input_part = self._build_input_tokens_display(usage.usage, cost)

		# Build output tokens display
		# EN: Assign value to completion_tokens_fmt.
		# JP: completion_tokens_fmt に値を代入する。
		completion_tokens_fmt = self._format_tokens(usage.usage.completion_tokens)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.include_cost and cost and cost.completion_cost > 0:
			# EN: Assign value to output_part.
			# JP: output_part に値を代入する。
			output_part = f'📤 {C_GREEN}{completion_tokens_fmt} (${cost.completion_cost:.4f}){C_RESET}'
		else:
			# EN: Assign value to output_part.
			# JP: output_part に値を代入する。
			output_part = f'📤 {C_GREEN}{completion_tokens_fmt}{C_RESET}'

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		cost_logger.debug(f'🧠 {C_CYAN}{model}{C_RESET} | {input_part} | {output_part}')

	# EN: Define function `_build_input_tokens_display`.
	# JP: 関数 `_build_input_tokens_display` を定義する。
	def _build_input_tokens_display(self, usage: ChatInvokeUsage, cost: TokenCostCalculated | None) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Build a clear display of input tokens breakdown with emojis and optional costs"""
		# EN: Assign value to C_YELLOW.
		# JP: C_YELLOW に値を代入する。
		C_YELLOW = '\033[93m'
		# EN: Assign value to C_BLUE.
		# JP: C_BLUE に値を代入する。
		C_BLUE = '\033[94m'
		# EN: Assign value to C_RESET.
		# JP: C_RESET に値を代入する。
		C_RESET = '\033[0m'

		# EN: Assign value to parts.
		# JP: parts に値を代入する。
		parts = []

		# Always show token breakdown if we have cache information, regardless of cost tracking
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if usage.prompt_cached_tokens or usage.prompt_cache_creation_tokens:
			# Calculate actual new tokens (non-cached)
			# EN: Assign value to new_tokens.
			# JP: new_tokens に値を代入する。
			new_tokens = usage.prompt_tokens - (usage.prompt_cached_tokens or 0)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if new_tokens > 0:
				# EN: Assign value to new_tokens_fmt.
				# JP: new_tokens_fmt に値を代入する。
				new_tokens_fmt = self._format_tokens(new_tokens)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.include_cost and cost and cost.new_prompt_cost > 0:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					parts.append(f'🆕 {C_YELLOW}{new_tokens_fmt} (${cost.new_prompt_cost:.4f}){C_RESET}')
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					parts.append(f'🆕 {C_YELLOW}{new_tokens_fmt}{C_RESET}')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if usage.prompt_cached_tokens:
				# EN: Assign value to cached_tokens_fmt.
				# JP: cached_tokens_fmt に値を代入する。
				cached_tokens_fmt = self._format_tokens(usage.prompt_cached_tokens)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.include_cost and cost and cost.prompt_read_cached_cost:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					parts.append(f'💾 {C_BLUE}{cached_tokens_fmt} (${cost.prompt_read_cached_cost:.4f}){C_RESET}')
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					parts.append(f'💾 {C_BLUE}{cached_tokens_fmt}{C_RESET}')

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if usage.prompt_cache_creation_tokens:
				# EN: Assign value to creation_tokens_fmt.
				# JP: creation_tokens_fmt に値を代入する。
				creation_tokens_fmt = self._format_tokens(usage.prompt_cache_creation_tokens)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.include_cost and cost and cost.prompt_cache_creation_cost:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					parts.append(f'🔧 {C_BLUE}{creation_tokens_fmt} (${cost.prompt_cache_creation_cost:.4f}){C_RESET}')
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					parts.append(f'🔧 {C_BLUE}{creation_tokens_fmt}{C_RESET}')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not parts:
			# Fallback to simple display when no cache information available
			# EN: Assign value to total_tokens_fmt.
			# JP: total_tokens_fmt に値を代入する。
			total_tokens_fmt = self._format_tokens(usage.prompt_tokens)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.include_cost and cost and cost.new_prompt_cost > 0:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				parts.append(f'📥 {C_YELLOW}{total_tokens_fmt} (${cost.new_prompt_cost:.4f}){C_RESET}')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				parts.append(f'📥 {C_YELLOW}{total_tokens_fmt}{C_RESET}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ' + '.join(parts)

	# EN: Define function `register_llm`.
	# JP: 関数 `register_llm` を定義する。
	def register_llm(self, llm: BaseChatModel) -> BaseChatModel:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Register an LLM to automatically track its token usage

		@dev Guarantees that the same instance is not registered multiple times
		"""
		# Use instance ID as key to avoid collisions between multiple instances
		# EN: Assign value to instance_id.
		# JP: instance_id に値を代入する。
		instance_id = str(id(llm))

		# Check if this exact instance is already registered
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if instance_id in self.registered_llms:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'LLM instance {instance_id} ({llm.provider}_{llm.model}) is already registered')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return llm

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.registered_llms[instance_id] = llm

		# Store the original method
		# EN: Assign value to original_ainvoke.
		# JP: original_ainvoke に値を代入する。
		original_ainvoke = llm.ainvoke
		# Store reference to self for use in the closure
		# EN: Assign value to token_cost_service.
		# JP: token_cost_service に値を代入する。
		token_cost_service = self

		# Create a wrapped version that tracks usage
		# EN: Define async function `tracked_ainvoke`.
		# JP: 非同期関数 `tracked_ainvoke` を定義する。
		async def tracked_ainvoke(messages, output_format=None):
			# Call the original method
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await original_ainvoke(messages, output_format)

			# Track usage if available (no await needed since add_usage is now sync)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if result.usage:
				# EN: Assign value to usage.
				# JP: usage に値を代入する。
				usage = token_cost_service.add_usage(llm.model, result.usage)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Token cost service: {usage}')

				# EN: Define async function `_safe_log_usage`.
				# JP: 非同期関数 `_safe_log_usage` を定義する。
				async def _safe_log_usage():
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await token_cost_service._log_usage(llm.model, usage)
					except Exception:
						# Ignore errors during background usage logging (e.g. if loop is closed)
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				asyncio.create_task(_safe_log_usage())

			# else:
			# 	await token_cost_service._log_non_usage_llm(llm)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return result

		# Replace the method with our tracked version
		# Using setattr to avoid type checking issues with overloaded methods
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		setattr(llm, 'ainvoke', tracked_ainvoke)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return llm

	# EN: Define function `get_usage_tokens_for_model`.
	# JP: 関数 `get_usage_tokens_for_model` を定義する。
	def get_usage_tokens_for_model(self, model: str) -> ModelUsageTokens:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get usage tokens for a specific model"""
		# EN: Assign value to filtered_usage.
		# JP: filtered_usage に値を代入する。
		filtered_usage = [u for u in self.usage_history if u.model == model]

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ModelUsageTokens(
			model=model,
			prompt_tokens=sum(u.usage.prompt_tokens for u in filtered_usage),
			prompt_cached_tokens=sum(u.usage.prompt_cached_tokens or 0 for u in filtered_usage),
			completion_tokens=sum(u.usage.completion_tokens for u in filtered_usage),
			total_tokens=sum(u.usage.prompt_tokens + u.usage.completion_tokens for u in filtered_usage),
		)

	# EN: Define async function `get_usage_summary`.
	# JP: 非同期関数 `get_usage_summary` を定義する。
	async def get_usage_summary(self, model: str | None = None, since: datetime | None = None) -> UsageSummary:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get summary of token usage and costs (costs calculated on-the-fly)"""
		# EN: Assign value to filtered_usage.
		# JP: filtered_usage に値を代入する。
		filtered_usage = self.usage_history

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if model:
			# EN: Assign value to filtered_usage.
			# JP: filtered_usage に値を代入する。
			filtered_usage = [u for u in filtered_usage if u.model == model]

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if since:
			# EN: Assign value to filtered_usage.
			# JP: filtered_usage に値を代入する。
			filtered_usage = [u for u in filtered_usage if u.timestamp >= since]

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not filtered_usage:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return UsageSummary(
				total_prompt_tokens=0,
				total_prompt_cost=0.0,
				total_prompt_cached_tokens=0,
				total_prompt_cached_cost=0.0,
				total_completion_tokens=0,
				total_completion_cost=0.0,
				total_tokens=0,
				total_cost=0.0,
				entry_count=0,
			)

		# Calculate totals
		# EN: Assign value to total_prompt.
		# JP: total_prompt に値を代入する。
		total_prompt = sum(u.usage.prompt_tokens for u in filtered_usage)
		# EN: Assign value to total_completion.
		# JP: total_completion に値を代入する。
		total_completion = sum(u.usage.completion_tokens for u in filtered_usage)
		# EN: Assign value to total_tokens.
		# JP: total_tokens に値を代入する。
		total_tokens = total_prompt + total_completion
		# EN: Assign value to total_prompt_cached.
		# JP: total_prompt_cached に値を代入する。
		total_prompt_cached = sum(u.usage.prompt_cached_tokens or 0 for u in filtered_usage)
		# EN: Assign value to models.
		# JP: models に値を代入する。
		models = list({u.model for u in filtered_usage})

		# Calculate per-model stats with record-by-record cost calculation
		# EN: Assign annotated value to model_stats.
		# JP: model_stats に型付きの値を代入する。
		model_stats: dict[str, ModelUsageStats] = {}
		# EN: Assign value to total_prompt_cost.
		# JP: total_prompt_cost に値を代入する。
		total_prompt_cost = 0.0
		# EN: Assign value to total_completion_cost.
		# JP: total_completion_cost に値を代入する。
		total_completion_cost = 0.0
		# EN: Assign value to total_prompt_cached_cost.
		# JP: total_prompt_cached_cost に値を代入する。
		total_prompt_cached_cost = 0.0

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for entry in filtered_usage:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry.model not in model_stats:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				model_stats[entry.model] = ModelUsageStats(model=entry.model)

			# EN: Assign value to stats.
			# JP: stats に値を代入する。
			stats = model_stats[entry.model]
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			stats.prompt_tokens += entry.usage.prompt_tokens
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			stats.completion_tokens += entry.usage.completion_tokens
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			stats.total_tokens += entry.usage.prompt_tokens + entry.usage.completion_tokens
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			stats.invocations += 1

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.include_cost:
				# Calculate cost record by record using the updated calculate_cost function
				# EN: Assign value to cost.
				# JP: cost に値を代入する。
				cost = await self.calculate_cost(entry.model, entry.usage)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if cost:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					stats.cost += cost.total_cost
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					total_prompt_cost += cost.prompt_cost
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					total_completion_cost += cost.completion_cost
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					total_prompt_cached_cost += cost.prompt_read_cached_cost or 0

		# Calculate averages
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for stats in model_stats.values():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if stats.invocations > 0:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				stats.average_tokens_per_invocation = stats.total_tokens / stats.invocations

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return UsageSummary(
			total_prompt_tokens=total_prompt,
			total_prompt_cost=total_prompt_cost,
			total_prompt_cached_tokens=total_prompt_cached,
			total_prompt_cached_cost=total_prompt_cached_cost,
			total_completion_tokens=total_completion,
			total_completion_cost=total_completion_cost,
			total_tokens=total_tokens,
			total_cost=total_prompt_cost + total_completion_cost + total_prompt_cached_cost,
			entry_count=len(filtered_usage),
			by_model=model_stats,
		)

	# EN: Define function `_format_tokens`.
	# JP: 関数 `_format_tokens` を定義する。
	def _format_tokens(self, tokens: int) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Format token count with k suffix for thousands"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tokens >= 1000000000:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'{tokens / 1000000000:.1f}B'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tokens >= 1000000:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'{tokens / 1000000:.1f}M'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tokens >= 1000:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'{tokens / 1000:.1f}k'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(tokens)

	# EN: Define async function `log_usage_summary`.
	# JP: 非同期関数 `log_usage_summary` を定義する。
	async def log_usage_summary(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log a comprehensive usage summary per model with colors and nice formatting"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.usage_history:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to summary.
		# JP: summary に値を代入する。
		summary = await self.get_usage_summary()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if summary.entry_count == 0:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# ANSI color codes
		# EN: Assign value to C_CYAN.
		# JP: C_CYAN に値を代入する。
		C_CYAN = '\033[96m'
		# EN: Assign value to C_YELLOW.
		# JP: C_YELLOW に値を代入する。
		C_YELLOW = '\033[93m'
		# EN: Assign value to C_GREEN.
		# JP: C_GREEN に値を代入する。
		C_GREEN = '\033[92m'
		# EN: Assign value to C_BLUE.
		# JP: C_BLUE に値を代入する。
		C_BLUE = '\033[94m'
		# EN: Assign value to C_MAGENTA.
		# JP: C_MAGENTA に値を代入する。
		C_MAGENTA = '\033[95m'
		# EN: Assign value to C_RESET.
		# JP: C_RESET に値を代入する。
		C_RESET = '\033[0m'
		# EN: Assign value to C_BOLD.
		# JP: C_BOLD に値を代入する。
		C_BOLD = '\033[1m'

		# Log overall summary
		# EN: Assign value to total_tokens_fmt.
		# JP: total_tokens_fmt に値を代入する。
		total_tokens_fmt = self._format_tokens(summary.total_tokens)
		# EN: Assign value to prompt_tokens_fmt.
		# JP: prompt_tokens_fmt に値を代入する。
		prompt_tokens_fmt = self._format_tokens(summary.total_prompt_tokens)
		# EN: Assign value to completion_tokens_fmt.
		# JP: completion_tokens_fmt に値を代入する。
		completion_tokens_fmt = self._format_tokens(summary.total_completion_tokens)

		# Format cost breakdowns for input and output (only if cost tracking is enabled)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.include_cost and summary.total_cost > 0:
			# EN: Assign value to total_cost_part.
			# JP: total_cost_part に値を代入する。
			total_cost_part = f' (${C_MAGENTA}{summary.total_cost:.4f}{C_RESET})'
			# EN: Assign value to prompt_cost_part.
			# JP: prompt_cost_part に値を代入する。
			prompt_cost_part = f' (${summary.total_prompt_cost:.4f})'
			# EN: Assign value to completion_cost_part.
			# JP: completion_cost_part に値を代入する。
			completion_cost_part = f' (${summary.total_completion_cost:.4f})'
		else:
			# EN: Assign value to total_cost_part.
			# JP: total_cost_part に値を代入する。
			total_cost_part = ''
			# EN: Assign value to prompt_cost_part.
			# JP: prompt_cost_part に値を代入する。
			prompt_cost_part = ''
			# EN: Assign value to completion_cost_part.
			# JP: completion_cost_part に値を代入する。
			completion_cost_part = ''

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(summary.by_model) > 1:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cost_logger.debug(
				f'💲 {C_BOLD}Total Usage Summary{C_RESET}: {C_BLUE}{total_tokens_fmt} tokens{C_RESET}{total_cost_part} | '
				f'⬅️ {C_YELLOW}{prompt_tokens_fmt}{prompt_cost_part}{C_RESET} | ➡️ {C_GREEN}{completion_tokens_fmt}{completion_cost_part}{C_RESET}'
			)

		# Log per-model breakdown
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		cost_logger.debug(f'📊 {C_BOLD}Per-Model Usage Breakdown{C_RESET}:')

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for model, stats in summary.by_model.items():
			# Format tokens
			# EN: Assign value to model_total_fmt.
			# JP: model_total_fmt に値を代入する。
			model_total_fmt = self._format_tokens(stats.total_tokens)
			# EN: Assign value to model_prompt_fmt.
			# JP: model_prompt_fmt に値を代入する。
			model_prompt_fmt = self._format_tokens(stats.prompt_tokens)
			# EN: Assign value to model_completion_fmt.
			# JP: model_completion_fmt に値を代入する。
			model_completion_fmt = self._format_tokens(stats.completion_tokens)
			# EN: Assign value to avg_tokens_fmt.
			# JP: avg_tokens_fmt に値を代入する。
			avg_tokens_fmt = self._format_tokens(int(stats.average_tokens_per_invocation))

			# Format cost display (only if cost tracking is enabled)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.include_cost:
				# Calculate per-model costs on-the-fly
				# EN: Assign value to total_model_cost.
				# JP: total_model_cost に値を代入する。
				total_model_cost = 0.0
				# EN: Assign value to model_prompt_cost.
				# JP: model_prompt_cost に値を代入する。
				model_prompt_cost = 0.0
				# EN: Assign value to model_completion_cost.
				# JP: model_completion_cost に値を代入する。
				model_completion_cost = 0.0

				# Calculate costs for this model
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for entry in self.usage_history:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if entry.model == model:
						# EN: Assign value to cost.
						# JP: cost に値を代入する。
						cost = await self.calculate_cost(entry.model, entry.usage)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if cost:
							# EN: Update variable with augmented assignment.
							# JP: 複合代入で変数を更新する。
							model_prompt_cost += cost.prompt_cost
							# EN: Update variable with augmented assignment.
							# JP: 複合代入で変数を更新する。
							model_completion_cost += cost.completion_cost

				# EN: Assign value to total_model_cost.
				# JP: total_model_cost に値を代入する。
				total_model_cost = model_prompt_cost + model_completion_cost

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if total_model_cost > 0:
					# EN: Assign value to cost_part.
					# JP: cost_part に値を代入する。
					cost_part = f' (${C_MAGENTA}{total_model_cost:.4f}{C_RESET})'
					# EN: Assign value to prompt_part.
					# JP: prompt_part に値を代入する。
					prompt_part = f'{C_YELLOW}{model_prompt_fmt} (${model_prompt_cost:.4f}){C_RESET}'
					# EN: Assign value to completion_part.
					# JP: completion_part に値を代入する。
					completion_part = f'{C_GREEN}{model_completion_fmt} (${model_completion_cost:.4f}){C_RESET}'
				else:
					# EN: Assign value to cost_part.
					# JP: cost_part に値を代入する。
					cost_part = ''
					# EN: Assign value to prompt_part.
					# JP: prompt_part に値を代入する。
					prompt_part = f'{C_YELLOW}{model_prompt_fmt}{C_RESET}'
					# EN: Assign value to completion_part.
					# JP: completion_part に値を代入する。
					completion_part = f'{C_GREEN}{model_completion_fmt}{C_RESET}'
			else:
				# EN: Assign value to cost_part.
				# JP: cost_part に値を代入する。
				cost_part = ''
				# EN: Assign value to prompt_part.
				# JP: prompt_part に値を代入する。
				prompt_part = f'{C_YELLOW}{model_prompt_fmt}{C_RESET}'
				# EN: Assign value to completion_part.
				# JP: completion_part に値を代入する。
				completion_part = f'{C_GREEN}{model_completion_fmt}{C_RESET}'

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cost_logger.debug(
				f'  🤖 {C_CYAN}{model}{C_RESET}: {C_BLUE}{model_total_fmt} tokens{C_RESET}{cost_part} | '
				f'⬅️ {prompt_part} | ➡️ {completion_part} | '
				f'📞 {stats.invocations} calls | 📈 {avg_tokens_fmt}/call'
			)

	# EN: Define async function `get_cost_by_model`.
	# JP: 非同期関数 `get_cost_by_model` を定義する。
	async def get_cost_by_model(self) -> dict[str, ModelUsageStats]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get cost breakdown by model"""
		# EN: Assign value to summary.
		# JP: summary に値を代入する。
		summary = await self.get_usage_summary()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return summary.by_model

	# EN: Define function `clear_history`.
	# JP: 関数 `clear_history` を定義する。
	def clear_history(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear usage history"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.usage_history = []

	# EN: Define async function `refresh_pricing_data`.
	# JP: 非同期関数 `refresh_pricing_data` を定義する。
	async def refresh_pricing_data(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Force refresh of pricing data from GitHub"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.include_cost:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._fetch_and_cache_pricing_data()

	# EN: Define async function `clean_old_caches`.
	# JP: 非同期関数 `clean_old_caches` を定義する。
	async def clean_old_caches(self, keep_count: int = 3) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clean up old cache files, keeping only the most recent ones"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# List all JSON files in the cache directory
			# EN: Assign value to cache_files.
			# JP: cache_files に値を代入する。
			cache_files = list(self._cache_dir.glob('*.json'))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(cache_files) <= keep_count:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Sort by modification time (oldest first)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cache_files.sort(key=lambda f: f.stat().st_mtime)

			# Remove all but the most recent files
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for cache_file in cache_files[:-keep_count]:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					os.remove(cache_file)
				except Exception:
					# EN: Keep a placeholder statement.
					# JP: プレースホルダー文を維持する。
					pass
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Error cleaning old cache files: {e}')

	# EN: Define async function `ensure_pricing_loaded`.
	# JP: 非同期関数 `ensure_pricing_loaded` を定義する。
	async def ensure_pricing_loaded(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Ensure pricing data is loaded in the background. Call this after creating the service."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._initialized and self.include_cost:
			# This will run in the background and won't block
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.initialize()

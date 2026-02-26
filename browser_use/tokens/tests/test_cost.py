# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Simple test for token cost tracking with real LLM calls.

Tests ChatOpenAI and ChatGoogle by iteratively generating countries.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm import ChatOpenAI
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import AssistantMessage, SystemMessage, UserMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tokens.service import TokenCost

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)
# EN: Evaluate an expression.
# JP: 式を評価する。
logger.setLevel(logging.INFO)


# EN: Define async function `test_iterative_country_generation`.
# JP: 非同期関数 `test_iterative_country_generation` を定義する。
async def test_iterative_country_generation():
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Test token cost tracking with iterative country generation"""

	# Initialize token cost service
	# EN: Assign value to tc.
	# JP: tc に値を代入する。
	tc = TokenCost(include_cost=True)

	# System prompt that explains the iterative task
	# EN: Assign value to system_prompt.
	# JP: system_prompt に値を代入する。
	system_prompt = """You are a country name generator. When asked, you will provide exactly ONE country name and nothing else.
Each time you're asked to continue, provide the next country name that hasn't been mentioned yet.
Keep track of which countries you've already said and don't repeat them.
Only output the country name, no numbers, no punctuation, just the name."""

	# Test with different models
	# EN: Assign value to models.
	# JP: models に値を代入する。
	models = [
		ChatOpenAI(model='gpt-4.1'),
		# ChatGoogle(model='gemini-2.0-flash-exp'),
	]

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('\n🌍 Iterative Country Generation Test')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('=' * 80)

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for llm in models:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'\n📍 Testing {llm.model}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('-' * 60)

		# Register the LLM for automatic tracking
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		tc.register_llm(llm)

		# Initialize conversation
		# EN: Assign value to messages.
		# JP: messages に値を代入する。
		messages = [SystemMessage(content=system_prompt), UserMessage(content='Give me a country name')]

		# EN: Assign value to countries.
		# JP: countries に値を代入する。
		countries = []

		# Generate 10 countries iteratively
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i in range(10):
			# Call the LLM
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await llm.ainvoke(messages)
			# EN: Assign value to country.
			# JP: country に値を代入する。
			country = result.completion.strip()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			countries.append(country)

			# Add the response to messages
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			messages.append(AssistantMessage(content=country))

			# Add the next request (except for the last iteration)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if i < 9:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				messages.append(UserMessage(content='Next country please'))

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'  Country {i + 1}: {country}')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'\n  Generated countries: {", ".join(countries)}')

	# Display cost summary
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('\n💰 Cost Summary')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('=' * 80)

	# EN: Assign value to summary.
	# JP: summary に値を代入する。
	summary = await tc.get_usage_summary()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print(f'Total calls: {summary.entry_count}')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print(f'Total tokens: {summary.total_tokens:,}')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print(f'Total cost: ${summary.total_cost:.6f}')

	# EN: Assign value to expected_cost.
	# JP: expected_cost に値を代入する。
	expected_cost = 0
	# EN: Assign value to expected_invocations.
	# JP: expected_invocations に値を代入する。
	expected_invocations = 0

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('\n📊 Cost breakdown by model:')
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for model, stats in summary.by_model.items():
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		expected_cost += stats.cost
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		expected_invocations += stats.invocations

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'\n{model}:')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'  Calls: {stats.invocations}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'  Prompt tokens: {stats.prompt_tokens:,}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'  Completion tokens: {stats.completion_tokens:,}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'  Total tokens: {stats.total_tokens:,}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'  Cost: ${stats.cost:.6f}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'  Average tokens per call: {stats.average_tokens_per_invocation:.1f}')

	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert summary.entry_count == expected_invocations, f'Expected {expected_invocations} invocations, got {summary.entry_count}'
	# EN: Validate a required condition.
	# JP: 必須条件を検証する。
	assert abs(summary.total_cost - expected_cost) < 1e-6, (
		f'Expected total cost ${expected_cost:.6f}, got ${summary.total_cost:.6f}'
	)


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# Run the test
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(test_iterative_country_generation())

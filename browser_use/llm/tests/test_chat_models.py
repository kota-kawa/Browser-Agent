# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pytest
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm import ChatAnthropic, ChatGoogle, ChatGroq, ChatOpenAI, ChatOpenRouter
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import ContentPartTextParam


# EN: Define class `CapitalResponse`.
# JP: クラス `CapitalResponse` を定義する。
class CapitalResponse(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Structured response for capital question"""

	# EN: Assign annotated value to country.
	# JP: country に型付きの値を代入する。
	country: str
	# EN: Assign annotated value to capital.
	# JP: capital に型付きの値を代入する。
	capital: str


# EN: Define class `TestChatModels`.
# JP: クラス `TestChatModels` を定義する。
class TestChatModels:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.llm.messages import (
		AssistantMessage,
		BaseMessage,
		SystemMessage,
		UserMessage,
	)

	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Test suite for all chat model implementations"""

	# Test Constants
	# EN: Assign value to SYSTEM_MESSAGE.
	# JP: SYSTEM_MESSAGE に値を代入する。
	SYSTEM_MESSAGE = SystemMessage(content=[ContentPartTextParam(text='You are a helpful assistant.', type='text')])
	# EN: Assign value to FRANCE_QUESTION.
	# JP: FRANCE_QUESTION に値を代入する。
	FRANCE_QUESTION = UserMessage(content='What is the capital of France? Answer in one word.')
	# EN: Assign value to FRANCE_ANSWER.
	# JP: FRANCE_ANSWER に値を代入する。
	FRANCE_ANSWER = AssistantMessage(content='Paris')
	# EN: Assign value to GERMANY_QUESTION.
	# JP: GERMANY_QUESTION に値を代入する。
	GERMANY_QUESTION = UserMessage(content='What is the capital of Germany? Answer in one word.')

	# Expected values
	# EN: Assign value to EXPECTED_GERMANY_CAPITAL.
	# JP: EXPECTED_GERMANY_CAPITAL に値を代入する。
	EXPECTED_GERMANY_CAPITAL = 'berlin'
	# EN: Assign value to EXPECTED_FRANCE_COUNTRY.
	# JP: EXPECTED_FRANCE_COUNTRY に値を代入する。
	EXPECTED_FRANCE_COUNTRY = 'france'
	# EN: Assign value to EXPECTED_FRANCE_CAPITAL.
	# JP: EXPECTED_FRANCE_CAPITAL に値を代入する。
	EXPECTED_FRANCE_CAPITAL = 'paris'

	# Test messages for conversation
	# EN: Assign annotated value to CONVERSATION_MESSAGES.
	# JP: CONVERSATION_MESSAGES に型付きの値を代入する。
	CONVERSATION_MESSAGES: list[BaseMessage] = [
		SYSTEM_MESSAGE,
		FRANCE_QUESTION,
		FRANCE_ANSWER,
		GERMANY_QUESTION,
	]

	# Test messages for structured output
	# EN: Assign annotated value to STRUCTURED_MESSAGES.
	# JP: STRUCTURED_MESSAGES に型付きの値を代入する。
	STRUCTURED_MESSAGES: list[BaseMessage] = [UserMessage(content='What is the capital of France?')]

	# OpenAI Tests
	# EN: Define function `openrouter_chat`.
	# JP: 関数 `openrouter_chat` を定義する。
	@pytest.fixture
	def openrouter_chat(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Provides an initialized ChatOpenRouter client for tests."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('OPENROUTER_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('OPENROUTER_API_KEY not set')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatOpenRouter(model='openai/gpt-4o-mini', api_key=os.getenv('OPENROUTER_API_KEY'), temperature=0)

	# EN: Define async function `test_openai_ainvoke_normal`.
	# JP: 非同期関数 `test_openai_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_openai_ainvoke_normal(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from OpenAI"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('OPENAI_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('OPENAI_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatOpenAI(model='gpt-4o-mini', temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)

		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, str)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_openai_ainvoke_structured`.
	# JP: 非同期関数 `test_openai_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_openai_ainvoke_structured(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from OpenAI"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('OPENAI_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('OPENAI_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatOpenAI(model='gpt-4o-mini', temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, CapitalResponse)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# Anthropic Tests
	# EN: Define async function `test_anthropic_ainvoke_normal`.
	# JP: 非同期関数 `test_anthropic_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_anthropic_ainvoke_normal(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from Anthropic"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('ANTHROPIC_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('ANTHROPIC_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatAnthropic(model='claude-3-5-haiku-latest', max_tokens=100, temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, str)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_anthropic_ainvoke_structured`.
	# JP: 非同期関数 `test_anthropic_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_anthropic_ainvoke_structured(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from Anthropic"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('ANTHROPIC_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('ANTHROPIC_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatAnthropic(model='claude-3-5-haiku-latest', max_tokens=100, temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, CapitalResponse)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# Google Gemini Tests
	# EN: Define async function `test_google_ainvoke_normal`.
	# JP: 非同期関数 `test_google_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_google_ainvoke_normal(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from Google Gemini"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('GOOGLE_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('GOOGLE_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGoogle(model='gemini-2.5-flash-lite', api_key=os.getenv('GOOGLE_API_KEY'), temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, str)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_google_ainvoke_structured`.
	# JP: 非同期関数 `test_google_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_google_ainvoke_structured(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from Google Gemini"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('GOOGLE_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('GOOGLE_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGoogle(model='gemini-2.5-flash-lite', api_key=os.getenv('GOOGLE_API_KEY'), temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, CapitalResponse)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# Google Gemini with Vertex AI Tests
	# EN: Define async function `test_google_vertex_ainvoke_normal`.
	# JP: 非同期関数 `test_google_vertex_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_google_vertex_ainvoke_normal(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from Google Gemini via Vertex AI"""
		# Skip if no project ID
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('GOOGLE_CLOUD_PROJECT'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('GOOGLE_CLOUD_PROJECT not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGoogle(
			model='gemini-2.5-flash-lite',
			vertexai=True,
			project=os.getenv('GOOGLE_CLOUD_PROJECT'),
			location='us-central1',
			temperature=0,
		)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, str)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_google_vertex_ainvoke_structured`.
	# JP: 非同期関数 `test_google_vertex_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_google_vertex_ainvoke_structured(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from Google Gemini via Vertex AI"""
		# Skip if no project ID
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('GOOGLE_CLOUD_PROJECT'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('GOOGLE_CLOUD_PROJECT not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGoogle(
			model='gemini-2.5-flash-lite',
			vertexai=True,
			project=os.getenv('GOOGLE_CLOUD_PROJECT'),
			location='us-central1',
			temperature=0,
		)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, CapitalResponse)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# Groq Tests
	# EN: Define async function `test_groq_ainvoke_normal`.
	# JP: 非同期関数 `test_groq_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_groq_ainvoke_normal(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from Groq"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('GROQ_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('GROQ_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGroq(model='llama-3.1-8b-instant', temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, str)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_groq_ainvoke_structured`.
	# JP: 非同期関数 `test_groq_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_groq_ainvoke_structured(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from Groq"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('GROQ_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('GROQ_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGroq(model='llama-3.1-8b-instant', temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)

		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, CapitalResponse)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# OpenRouter Tests
	# EN: Define async function `test_openrouter_ainvoke_normal`.
	# JP: 非同期関数 `test_openrouter_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_openrouter_ainvoke_normal(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from OpenRouter"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('OPENROUTER_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('OPENROUTER_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatOpenRouter(model='openai/gpt-4o-mini', api_key=os.getenv('OPENROUTER_API_KEY'), temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, str)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_openrouter_ainvoke_structured`.
	# JP: 非同期関数 `test_openrouter_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_openrouter_ainvoke_structured(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from OpenRouter"""
		# Skip if no API key
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not os.getenv('OPENROUTER_API_KEY'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pytest.skip('OPENROUTER_API_KEY not set')

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatOpenRouter(model='openai/gpt-4o-mini', api_key=os.getenv('OPENROUTER_API_KEY'), temperature=0)
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(completion, CapitalResponse)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

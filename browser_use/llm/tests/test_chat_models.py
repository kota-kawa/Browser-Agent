import os

import pytest
from pydantic import BaseModel

from browser_use.llm import ChatAnthropic, ChatGoogle, ChatGroq, ChatOpenAI, ChatOpenRouter
from browser_use.llm.messages import ContentPartTextParam


# EN: Define class `CapitalResponse`.
# JP: クラス `CapitalResponse` を定義する。
class CapitalResponse(BaseModel):
	"""Structured response for capital question"""

	country: str
	capital: str


# EN: Define class `TestChatModels`.
# JP: クラス `TestChatModels` を定義する。
class TestChatModels:
	from browser_use.llm.messages import (
		AssistantMessage,
		BaseMessage,
		SystemMessage,
		UserMessage,
	)

	"""Test suite for all chat model implementations"""

	# Test Constants
	SYSTEM_MESSAGE = SystemMessage(content=[ContentPartTextParam(text='You are a helpful assistant.', type='text')])
	FRANCE_QUESTION = UserMessage(content='What is the capital of France? Answer in one word.')
	FRANCE_ANSWER = AssistantMessage(content='Paris')
	GERMANY_QUESTION = UserMessage(content='What is the capital of Germany? Answer in one word.')

	# Expected values
	EXPECTED_GERMANY_CAPITAL = 'berlin'
	EXPECTED_FRANCE_COUNTRY = 'france'
	EXPECTED_FRANCE_CAPITAL = 'paris'

	# Test messages for conversation
	CONVERSATION_MESSAGES: list[BaseMessage] = [
		SYSTEM_MESSAGE,
		FRANCE_QUESTION,
		FRANCE_ANSWER,
		GERMANY_QUESTION,
	]

	# Test messages for structured output
	STRUCTURED_MESSAGES: list[BaseMessage] = [UserMessage(content='What is the capital of France?')]

	# OpenAI Tests
	# EN: Define function `openrouter_chat`.
	# JP: 関数 `openrouter_chat` を定義する。
	@pytest.fixture
	def openrouter_chat(self):
		"""Provides an initialized ChatOpenRouter client for tests."""
		if not os.getenv('OPENROUTER_API_KEY'):
			pytest.skip('OPENROUTER_API_KEY not set')
		return ChatOpenRouter(model='openai/gpt-4o-mini', api_key=os.getenv('OPENROUTER_API_KEY'), temperature=0)

	# EN: Define async function `test_openai_ainvoke_normal`.
	# JP: 非同期関数 `test_openai_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_openai_ainvoke_normal(self):
		"""Test normal text response from OpenAI"""
		# Skip if no API key
		if not os.getenv('OPENAI_API_KEY'):
			pytest.skip('OPENAI_API_KEY not set')

		chat = ChatOpenAI(model='gpt-4o-mini', temperature=0)
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)

		completion = response.completion

		assert isinstance(completion, str)
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_openai_ainvoke_structured`.
	# JP: 非同期関数 `test_openai_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_openai_ainvoke_structured(self):
		"""Test structured output from OpenAI"""
		# Skip if no API key
		if not os.getenv('OPENAI_API_KEY'):
			pytest.skip('OPENAI_API_KEY not set')

		chat = ChatOpenAI(model='gpt-4o-mini', temperature=0)
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		completion = response.completion

		assert isinstance(completion, CapitalResponse)
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# Anthropic Tests
	# EN: Define async function `test_anthropic_ainvoke_normal`.
	# JP: 非同期関数 `test_anthropic_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_anthropic_ainvoke_normal(self):
		"""Test normal text response from Anthropic"""
		# Skip if no API key
		if not os.getenv('ANTHROPIC_API_KEY'):
			pytest.skip('ANTHROPIC_API_KEY not set')

		chat = ChatAnthropic(model='claude-3-5-haiku-latest', max_tokens=100, temperature=0)
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		completion = response.completion

		assert isinstance(completion, str)
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_anthropic_ainvoke_structured`.
	# JP: 非同期関数 `test_anthropic_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_anthropic_ainvoke_structured(self):
		"""Test structured output from Anthropic"""
		# Skip if no API key
		if not os.getenv('ANTHROPIC_API_KEY'):
			pytest.skip('ANTHROPIC_API_KEY not set')

		chat = ChatAnthropic(model='claude-3-5-haiku-latest', max_tokens=100, temperature=0)
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		completion = response.completion

		assert isinstance(completion, CapitalResponse)
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# Google Gemini Tests
	# EN: Define async function `test_google_ainvoke_normal`.
	# JP: 非同期関数 `test_google_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_google_ainvoke_normal(self):
		"""Test normal text response from Google Gemini"""
		# Skip if no API key
		if not os.getenv('GOOGLE_API_KEY'):
			pytest.skip('GOOGLE_API_KEY not set')

		chat = ChatGoogle(model='gemini-2.5-flash-lite', api_key=os.getenv('GOOGLE_API_KEY'), temperature=0)
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		completion = response.completion

		assert isinstance(completion, str)
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_google_ainvoke_structured`.
	# JP: 非同期関数 `test_google_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_google_ainvoke_structured(self):
		"""Test structured output from Google Gemini"""
		# Skip if no API key
		if not os.getenv('GOOGLE_API_KEY'):
			pytest.skip('GOOGLE_API_KEY not set')

		chat = ChatGoogle(model='gemini-2.5-flash-lite', api_key=os.getenv('GOOGLE_API_KEY'), temperature=0)
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		completion = response.completion

		assert isinstance(completion, CapitalResponse)
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# Google Gemini with Vertex AI Tests
	# EN: Define async function `test_google_vertex_ainvoke_normal`.
	# JP: 非同期関数 `test_google_vertex_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_google_vertex_ainvoke_normal(self):
		"""Test normal text response from Google Gemini via Vertex AI"""
		# Skip if no project ID
		if not os.getenv('GOOGLE_CLOUD_PROJECT'):
			pytest.skip('GOOGLE_CLOUD_PROJECT not set')

		chat = ChatGoogle(
			model='gemini-2.5-flash-lite',
			vertexai=True,
			project=os.getenv('GOOGLE_CLOUD_PROJECT'),
			location='us-central1',
			temperature=0,
		)
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		completion = response.completion

		assert isinstance(completion, str)
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_google_vertex_ainvoke_structured`.
	# JP: 非同期関数 `test_google_vertex_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_google_vertex_ainvoke_structured(self):
		"""Test structured output from Google Gemini via Vertex AI"""
		# Skip if no project ID
		if not os.getenv('GOOGLE_CLOUD_PROJECT'):
			pytest.skip('GOOGLE_CLOUD_PROJECT not set')

		chat = ChatGoogle(
			model='gemini-2.5-flash-lite',
			vertexai=True,
			project=os.getenv('GOOGLE_CLOUD_PROJECT'),
			location='us-central1',
			temperature=0,
		)
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		completion = response.completion

		assert isinstance(completion, CapitalResponse)
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# Groq Tests
	# EN: Define async function `test_groq_ainvoke_normal`.
	# JP: 非同期関数 `test_groq_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_groq_ainvoke_normal(self):
		"""Test normal text response from Groq"""
		# Skip if no API key
		if not os.getenv('GROQ_API_KEY'):
			pytest.skip('GROQ_API_KEY not set')

		chat = ChatGroq(model='llama-3.1-8b-instant', temperature=0)
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		completion = response.completion

		assert isinstance(completion, str)
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_groq_ainvoke_structured`.
	# JP: 非同期関数 `test_groq_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_groq_ainvoke_structured(self):
		"""Test structured output from Groq"""
		# Skip if no API key
		if not os.getenv('GROQ_API_KEY'):
			pytest.skip('GROQ_API_KEY not set')

		chat = ChatGroq(model='llama-3.1-8b-instant', temperature=0)
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)

		completion = response.completion

		assert isinstance(completion, CapitalResponse)
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

	# OpenRouter Tests
	# EN: Define async function `test_openrouter_ainvoke_normal`.
	# JP: 非同期関数 `test_openrouter_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	async def test_openrouter_ainvoke_normal(self):
		"""Test normal text response from OpenRouter"""
		# Skip if no API key
		if not os.getenv('OPENROUTER_API_KEY'):
			pytest.skip('OPENROUTER_API_KEY not set')

		chat = ChatOpenRouter(model='openai/gpt-4o-mini', api_key=os.getenv('OPENROUTER_API_KEY'), temperature=0)
		response = await chat.ainvoke(self.CONVERSATION_MESSAGES)
		completion = response.completion

		assert isinstance(completion, str)
		assert self.EXPECTED_GERMANY_CAPITAL in completion.lower()

	# EN: Define async function `test_openrouter_ainvoke_structured`.
	# JP: 非同期関数 `test_openrouter_ainvoke_structured` を定義する。
	@pytest.mark.asyncio
	async def test_openrouter_ainvoke_structured(self):
		"""Test structured output from OpenRouter"""
		# Skip if no API key
		if not os.getenv('OPENROUTER_API_KEY'):
			pytest.skip('OPENROUTER_API_KEY not set')

		chat = ChatOpenRouter(model='openai/gpt-4o-mini', api_key=os.getenv('OPENROUTER_API_KEY'), temperature=0)
		response = await chat.ainvoke(self.STRUCTURED_MESSAGES, output_format=CapitalResponse)
		completion = response.completion

		assert isinstance(completion, CapitalResponse)
		assert completion.country.lower() == self.EXPECTED_FRANCE_COUNTRY
		assert completion.capital.lower() == self.EXPECTED_FRANCE_CAPITAL

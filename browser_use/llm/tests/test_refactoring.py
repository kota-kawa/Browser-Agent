# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from unittest.mock import AsyncMock, MagicMock, patch

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pytest
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from anthropic.types import Message, TextBlock
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from groq import APIStatusError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm import ChatAnthropic, ChatGoogle, ChatGroq, ChatOpenAI
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	AssistantMessage,
	BaseMessage,
	SystemMessage,
	UserMessage,
)


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


# EN: Define class `TestRefactoring`.
# JP: クラス `TestRefactoring` を定義する。
class TestRefactoring:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Test suite for the refactored chat models"""

	# Test Constants
	# EN: Assign value to SYSTEM_MESSAGE.
	# JP: SYSTEM_MESSAGE に値を代入する。
	SYSTEM_MESSAGE = SystemMessage(content='You are a helpful assistant.')
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

	# EN: Define async function `test_openai_ainvoke_normal`.
	# JP: 非同期関数 `test_openai_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	@patch('browser_use.llm.openai.chat.ChatOpenAI.get_client')
	async def test_openai_ainvoke_normal(self, mock_get_client):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from OpenAI"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices = [MagicMock()]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices[0].message.content = self.EXPECTED_GERMANY_CAPITAL
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_get_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatOpenAI(model='gpt-4o-mini', temperature=0, api_key='test')
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
	@patch('browser_use.llm.openai.chat.ChatOpenAI.get_client')
	async def test_openai_ainvoke_structured(self, mock_get_client):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from OpenAI"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices = [MagicMock()]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices[
			0
		].message.content = f'{{"country": "{self.EXPECTED_FRANCE_COUNTRY}", "capital": "{self.EXPECTED_FRANCE_CAPITAL}"}}'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_get_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatOpenAI(model='gpt-4o-mini', temperature=0, api_key='test')
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

	# EN: Define async function `test_groq_ainvoke_structured_fallback`.
	# JP: 非同期関数 `test_groq_ainvoke_structured_fallback` を定義する。
	@pytest.mark.asyncio
	@patch('browser_use.llm.groq.chat.try_parse_groq_failed_generation')
	async def test_groq_ainvoke_structured_fallback(self, mock_parse_failed):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output fallback from Groq"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_parse_failed.return_value = CapitalResponse(
			country=self.EXPECTED_FRANCE_COUNTRY, capital=self.EXPECTED_FRANCE_CAPITAL
		)

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with patch('browser_use.llm.groq.chat.ChatGroq.get_client') as mock_get_client:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			mock_get_client.return_value.chat.completions.create = AsyncMock(
				side_effect=APIStatusError('test', response=MagicMock(), body=None)
			)

			# EN: Assign value to chat.
			# JP: chat に値を代入する。
			chat = ChatGroq(model='meta-llama/llama-4-maverick-17b-128e-instruct', temperature=0, api_key='test')
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
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			mock_parse_failed.assert_called_once()

	# EN: Define async function `test_anthropic_ainvoke_normal`.
	# JP: 非同期関数 `test_anthropic_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	@patch('browser_use.llm.anthropic.chat.ChatAnthropic.get_client')
	async def test_anthropic_ainvoke_normal(self, mock_get_client):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from Anthropic"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock(spec=Message)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.content = [MagicMock(spec=TextBlock)]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.content[0].text = self.EXPECTED_GERMANY_CAPITAL
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage.input_tokens = 0
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage.output_tokens = 0
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage.cache_read_input_tokens = 0
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage.cache_creation_input_tokens = 0
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_get_client.return_value.messages.create = AsyncMock(return_value=mock_response)

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatAnthropic(model='claude-3-5-haiku-latest', max_tokens=100, temperature=0, api_key='test')
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
	@patch('browser_use.llm.anthropic.chat.ChatAnthropic.get_client')
	async def test_anthropic_ainvoke_structured(self, mock_get_client):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from Anthropic"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock(spec=Message)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.content = [MagicMock()]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.content[0].type = 'tool_use'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.content[0].input = {'country': self.EXPECTED_FRANCE_COUNTRY, 'capital': self.EXPECTED_FRANCE_CAPITAL}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage.input_tokens = 0
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage.output_tokens = 0
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage.cache_read_input_tokens = 0
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage.cache_creation_input_tokens = 0
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_get_client.return_value.messages.create = AsyncMock(return_value=mock_response)

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatAnthropic(model='claude-3-5-haiku-latest', max_tokens=100, temperature=0, api_key='test')
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

	# EN: Define async function `test_google_ainvoke_normal`.
	# JP: 非同期関数 `test_google_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	@patch('browser_use.llm.google.chat.ChatGoogle._send_request', new_callable=AsyncMock)
	async def test_google_ainvoke_normal(self, mock_send_request):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from Google Gemini"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.json.return_value = {'candidates': [{'content': {'parts': [{'text': self.EXPECTED_GERMANY_CAPITAL}]}}]}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_send_request.return_value = mock_response

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGoogle(model='gemini-2.0-flash', api_key='test', temperature=0)
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
	@patch('browser_use.llm.google.chat.ChatGoogle._send_request', new_callable=AsyncMock)
	async def test_google_ainvoke_structured(self, mock_send_request):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from Google Gemini"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.json.return_value = {
			'candidates': [
				{
					'content': {
						'parts': [
							{
								'text': f'{{"country": "{self.EXPECTED_FRANCE_COUNTRY}", "capital": "{self.EXPECTED_FRANCE_CAPITAL}"}}'
							}
						]
					}
				}
			]
		}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_send_request.return_value = mock_response

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGoogle(model='gemini-2.0-flash', api_key='test', temperature=0)
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

	# EN: Define async function `test_google_structured_with_wrapped_json`.
	# JP: 非同期関数 `test_google_structured_with_wrapped_json` を定義する。
	@pytest.mark.asyncio
	@patch('browser_use.llm.google.chat.ChatGoogle._send_request', new_callable=AsyncMock)
	async def test_google_structured_with_wrapped_json(self, mock_send_request):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Gemini responses with preamble/code fences should still parse."""
		# EN: Assign value to wrapped_text.
		# JP: wrapped_text に値を代入する。
		wrapped_text = (
			'thinking about the task first...\n'
			'```json\n'
			f'{{"country": "{self.EXPECTED_FRANCE_COUNTRY}", "capital": "{self.EXPECTED_FRANCE_CAPITAL}"}}\n'
			'```\n'
			'回答は上記です。'
		)
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.json.return_value = {'candidates': [{'content': {'parts': [{'text': wrapped_text}]}}]}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_send_request.return_value = mock_response

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGoogle(model='gemini-2.0-flash', api_key='test', temperature=0)
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

	# EN: Define async function `test_google_structured_with_inline_json`.
	# JP: 非同期関数 `test_google_structured_with_inline_json` を定義する。
	@pytest.mark.asyncio
	@patch('browser_use.llm.google.chat.ChatGoogle._send_request', new_callable=AsyncMock)
	async def test_google_structured_with_inline_json(self, mock_send_request):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Gemini responses with trailing text should still parse."""
		# EN: Assign value to inline_text.
		# JP: inline_text に値を代入する。
		inline_text = (
			'Here are the details you asked for:\n'
			f'{{"country": "{self.EXPECTED_FRANCE_COUNTRY}", "capital": "{self.EXPECTED_FRANCE_CAPITAL}"}}\n'
			'Let me know if you need more.'
		)
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.json.return_value = {'candidates': [{'content': {'parts': [{'text': inline_text}]}}]}
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_send_request.return_value = mock_response

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGoogle(model='gemini-2.0-flash', api_key='test', temperature=0)
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

	# EN: Define async function `test_groq_ainvoke_normal`.
	# JP: 非同期関数 `test_groq_ainvoke_normal` を定義する。
	@pytest.mark.asyncio
	@patch('browser_use.llm.groq.chat.ChatGroq.get_client')
	async def test_groq_ainvoke_normal(self, mock_get_client):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test normal text response from Groq"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices = [MagicMock()]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices[0].message.content = self.EXPECTED_GERMANY_CAPITAL
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_get_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGroq(model='meta-llama/llama-4-maverick-17b-128e-instruct', temperature=0, api_key='test')
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
	@patch('browser_use.llm.groq.chat.ChatGroq.get_client')
	async def test_groq_ainvoke_structured(self, mock_get_client):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from Groq"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices = [MagicMock()]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices[
			0
		].message.content = f'{{"country": "{self.EXPECTED_FRANCE_COUNTRY}", "capital": "{self.EXPECTED_FRANCE_CAPITAL}"}}'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_get_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGroq(model='meta-llama/llama-4-maverick-17b-128e-instruct', temperature=0, api_key='test')
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

	# EN: Define async function `test_groq_ainvoke_structured_tool_calling`.
	# JP: 非同期関数 `test_groq_ainvoke_structured_tool_calling` を定義する。
	@pytest.mark.asyncio
	@patch('browser_use.llm.groq.chat.ChatGroq.get_client')
	async def test_groq_ainvoke_structured_tool_calling(self, mock_get_client):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test structured output from Groq with tool calling"""
		# EN: Assign value to mock_response.
		# JP: mock_response に値を代入する。
		mock_response = MagicMock()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices = [MagicMock()]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices[0].message.tool_calls = [MagicMock()]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.choices[0].message.tool_calls[
			0
		].function.arguments = f'{{"country": "{self.EXPECTED_FRANCE_COUNTRY}", "capital": "{self.EXPECTED_FRANCE_CAPITAL}"}}'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_response.usage = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mock_get_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

		# EN: Assign value to chat.
		# JP: chat に値を代入する。
		chat = ChatGroq(model='moonshotai/kimi-k2-instruct', temperature=0, api_key='test')
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

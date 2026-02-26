# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import cast

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.service import Agent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.anthropic.chat import ChatAnthropic
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.anthropic.serializer import AnthropicMessageSerializer, NonSystemMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import (
	AssistantMessage,
	BaseMessage,
	ContentPartImageParam,
	ContentPartTextParam,
	Function,
	ImageURL,
	SystemMessage,
	ToolCall,
	UserMessage,
)

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define class `TestAnthropicCache`.
# JP: クラス `TestAnthropicCache` を定義する。
class TestAnthropicCache:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Comprehensive test for Anthropic cache serialization."""

	# EN: Define function `test_cache_basic_functionality`.
	# JP: 関数 `test_cache_basic_functionality` を定義する。
	def test_cache_basic_functionality(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test basic cache functionality for all message types."""
		# Test cache with different message types
		# EN: Assign annotated value to messages.
		# JP: messages に型付きの値を代入する。
		messages: list[BaseMessage] = [
			SystemMessage(content='System message!', cache=True),
			UserMessage(content='User message!', cache=True),
			AssistantMessage(content='Assistant message!', cache=False),
		]

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		anthropic_messages, system_message = AnthropicMessageSerializer.serialize_messages(messages)

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(anthropic_messages) == 2
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(system_message, list)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(anthropic_messages[0]['content'], list)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(anthropic_messages[1]['content'], str)

		# Test cache with assistant message
		# EN: Assign annotated value to agent_messages.
		# JP: agent_messages に型付きの値を代入する。
		agent_messages: list[BaseMessage] = [
			SystemMessage(content='System message!'),
			UserMessage(content='User message!'),
			AssistantMessage(content='Assistant message!', cache=True),
		]

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		anthropic_messages, system_message = AnthropicMessageSerializer.serialize_messages(agent_messages)

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(system_message, str)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(anthropic_messages[0]['content'], str)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(anthropic_messages[1]['content'], list)

	# EN: Define function `test_cache_with_tool_calls`.
	# JP: 関数 `test_cache_with_tool_calls` を定義する。
	def test_cache_with_tool_calls(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test cache functionality with tool calls."""
		# EN: Assign value to tool_call.
		# JP: tool_call に値を代入する。
		tool_call = ToolCall(id='test_id', function=Function(name='test_function', arguments='{"arg": "value"}'))

		# Assistant with tool calls and cache
		# EN: Assign value to assistant_with_tools.
		# JP: assistant_with_tools に値を代入する。
		assistant_with_tools = AssistantMessage(content='Assistant with tools', tool_calls=[tool_call], cache=True)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([assistant_with_tools])

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(messages) == 1
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], list)
		# Should have both text and tool_use blocks
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(messages[0]['content']) >= 2

	# EN: Define function `test_cache_with_images`.
	# JP: 関数 `test_cache_with_images` を定義する。
	def test_cache_with_images(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test cache functionality with image content."""
		# EN: Assign value to user_with_image.
		# JP: user_with_image に値を代入する。
		user_with_image = UserMessage(
			content=[
				ContentPartTextParam(text='Here is an image:', type='text'),
				ContentPartImageParam(image_url=ImageURL(url='https://example.com/image.jpg'), type='image_url'),
			],
			cache=True,
		)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([user_with_image])

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(messages) == 1
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], list)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(messages[0]['content']) == 2

	# EN: Define function `test_cache_with_base64_images`.
	# JP: 関数 `test_cache_with_base64_images` を定義する。
	def test_cache_with_base64_images(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test cache functionality with base64 images."""
		# EN: Assign value to base64_url.
		# JP: base64_url に値を代入する。
		base64_url = 'data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

		# EN: Assign value to user_with_base64.
		# JP: user_with_base64 に値を代入する。
		user_with_base64 = UserMessage(
			content=[
				ContentPartTextParam(text='Base64 image:', type='text'),
				ContentPartImageParam(image_url=ImageURL(url=base64_url), type='image_url'),
			],
			cache=True,
		)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([user_with_base64])

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(messages) == 1
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], list)

	# EN: Define function `test_cache_content_types`.
	# JP: 関数 `test_cache_content_types` を定義する。
	def test_cache_content_types(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test different content types with cache."""
		# String content with cache should become list
		# EN: Assign value to user_string_cached.
		# JP: user_string_cached に値を代入する。
		user_string_cached = UserMessage(content='String message', cache=True)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([user_string_cached])
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], list)

		# String content without cache should remain string
		# EN: Assign value to user_string_no_cache.
		# JP: user_string_no_cache に値を代入する。
		user_string_no_cache = UserMessage(content='String message', cache=False)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([user_string_no_cache])
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], str)

		# List content maintains list format regardless of cache
		# EN: Assign value to user_list_cached.
		# JP: user_list_cached に値を代入する。
		user_list_cached = UserMessage(content=[ContentPartTextParam(text='List message', type='text')], cache=True)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([user_list_cached])
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], list)

		# EN: Assign value to user_list_no_cache.
		# JP: user_list_no_cache に値を代入する。
		user_list_no_cache = UserMessage(content=[ContentPartTextParam(text='List message', type='text')], cache=False)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([user_list_no_cache])
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], list)

	# EN: Define function `test_assistant_cache_empty_content`.
	# JP: 関数 `test_assistant_cache_empty_content` を定義する。
	def test_assistant_cache_empty_content(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test AssistantMessage with empty content and cache."""
		# With cache
		# EN: Assign value to assistant_empty_cached.
		# JP: assistant_empty_cached に値を代入する。
		assistant_empty_cached = AssistantMessage(content=None, cache=True)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([assistant_empty_cached])

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(messages) == 1
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], list)

		# Without cache
		# EN: Assign value to assistant_empty_no_cache.
		# JP: assistant_empty_no_cache に値を代入する。
		assistant_empty_no_cache = AssistantMessage(content=None, cache=False)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		messages, _ = AnthropicMessageSerializer.serialize_messages([assistant_empty_no_cache])

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(messages) == 1
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(messages[0]['content'], str)

	# EN: Define function `test_mixed_cache_scenarios`.
	# JP: 関数 `test_mixed_cache_scenarios` を定義する。
	def test_mixed_cache_scenarios(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test various combinations of cached and non-cached messages."""
		# EN: Assign annotated value to messages_list.
		# JP: messages_list に型付きの値を代入する。
		messages_list: list[BaseMessage] = [
			SystemMessage(content='System with cache', cache=True),
			UserMessage(content='User with cache', cache=True),
			AssistantMessage(content='Assistant without cache', cache=False),
			UserMessage(content='User without cache', cache=False),
			AssistantMessage(content='Assistant with cache', cache=True),
		]

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		serialized_messages, system_message = AnthropicMessageSerializer.serialize_messages(messages_list)

		# Check system message is cached (becomes list)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(system_message, list)

		# Check serialized messages
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert len(serialized_messages) == 4

		# User with cache should be list
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(serialized_messages[0]['content'], list)

		# Assistant without cache should be string
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(serialized_messages[1]['content'], str)

		# User without cache should be string
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(serialized_messages[2]['content'], str)

		# Assistant with cache should be list
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(serialized_messages[3]['content'], list)

	# EN: Define function `test_system_message_cache_behavior`.
	# JP: 関数 `test_system_message_cache_behavior` を定義する。
	def test_system_message_cache_behavior(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test SystemMessage specific cache behavior."""
		# With cache
		# EN: Assign value to system_cached.
		# JP: system_cached に値を代入する。
		system_cached = SystemMessage(content='System message with cache', cache=True)
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = AnthropicMessageSerializer.serialize(system_cached)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(result, SystemMessage)

		# Test serialization to string format
		# EN: Assign value to serialized_content.
		# JP: serialized_content に値を代入する。
		serialized_content = AnthropicMessageSerializer._serialize_content_to_str(result.content, use_cache=True)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(serialized_content, list)

		# Without cache
		# EN: Assign value to system_no_cache.
		# JP: system_no_cache に値を代入する。
		system_no_cache = SystemMessage(content='System message without cache', cache=False)
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = AnthropicMessageSerializer.serialize(system_no_cache)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(result, SystemMessage)

		# EN: Assign value to serialized_content.
		# JP: serialized_content に値を代入する。
		serialized_content = AnthropicMessageSerializer._serialize_content_to_str(result.content, use_cache=False)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(serialized_content, str)

	# EN: Define function `test_agent_messages_integration`.
	# JP: 関数 `test_agent_messages_integration` を定義する。
	def test_agent_messages_integration(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test integration with actual agent messages."""
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(task='Hello, world!', llm=ChatAnthropic(''))

		# EN: Assign value to messages.
		# JP: messages に値を代入する。
		messages = agent.message_manager.get_messages()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		anthropic_messages, system_message = AnthropicMessageSerializer.serialize_messages(messages)

		# System message should be properly handled
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert system_message is not None

	# EN: Define function `test_cache_cleaning_last_message_only`.
	# JP: 関数 `test_cache_cleaning_last_message_only` を定義する。
	def test_cache_cleaning_last_message_only(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test that only the last cache=True message remains cached."""
		# Create multiple messages with cache=True
		# EN: Assign annotated value to messages_list.
		# JP: messages_list に型付きの値を代入する。
		messages_list: list[BaseMessage] = [
			UserMessage(content='First user message', cache=True),
			AssistantMessage(content='First assistant message', cache=True),
			UserMessage(content='Second user message', cache=True),
			AssistantMessage(content='Second assistant message', cache=False),
			UserMessage(content='Third user message', cache=True),  # This should be the only one cached
		]

		# Test the cleaning method directly (only accepts non-system messages)
		# EN: Assign value to normal_messages.
		# JP: normal_messages に値を代入する。
		normal_messages = cast(list[NonSystemMessage], [msg for msg in messages_list if not isinstance(msg, SystemMessage)])
		# EN: Assign value to cleaned_messages.
		# JP: cleaned_messages に値を代入する。
		cleaned_messages = AnthropicMessageSerializer._clean_cache_messages(normal_messages)

		# Verify only the last cache=True message remains cached
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert not cleaned_messages[0].cache  # First user message should be uncached
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert not cleaned_messages[1].cache  # First assistant message should be uncached
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert not cleaned_messages[2].cache  # Second user message should be uncached
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert not cleaned_messages[3].cache  # Second assistant message was already uncached
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cleaned_messages[4].cache  # Third user message should remain cached

		# Test through serialize_messages
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		serialized_messages, system_message = AnthropicMessageSerializer.serialize_messages(messages_list)

		# Count how many messages have list content (indicating caching)
		# EN: Assign value to cached_content_count.
		# JP: cached_content_count に値を代入する。
		cached_content_count = sum(1 for msg in serialized_messages if isinstance(msg['content'], list))

		# Only one message should have cached content
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cached_content_count == 1

		# The last message should be the cached one
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(serialized_messages[-1]['content'], list)

	# EN: Define function `test_cache_cleaning_with_system_message`.
	# JP: 関数 `test_cache_cleaning_with_system_message` を定義する。
	def test_cache_cleaning_with_system_message(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test that system messages are not affected by cache cleaning logic."""
		# EN: Assign annotated value to messages_list.
		# JP: messages_list に型付きの値を代入する。
		messages_list: list[BaseMessage] = [
			SystemMessage(content='System message', cache=True),  # System messages are handled separately
			UserMessage(content='First user message', cache=True),
			AssistantMessage(content='Assistant message', cache=True),  # This should be the only normal message cached
		]

		# Test through serialize_messages to see the full integration
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		serialized_messages, system_message = AnthropicMessageSerializer.serialize_messages(messages_list)

		# System message should be cached
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(system_message, list)

		# Only one normal message should have cached content (the last one)
		# EN: Assign value to cached_content_count.
		# JP: cached_content_count に値を代入する。
		cached_content_count = sum(1 for msg in serialized_messages if isinstance(msg['content'], list))
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert cached_content_count == 1

		# The last message should be the cached one
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert isinstance(serialized_messages[-1]['content'], list)

	# EN: Define function `test_cache_cleaning_no_cached_messages`.
	# JP: 関数 `test_cache_cleaning_no_cached_messages` を定義する。
	def test_cache_cleaning_no_cached_messages(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test that messages without cache=True are not affected."""
		# EN: Assign value to normal_messages_list.
		# JP: normal_messages_list に値を代入する。
		normal_messages_list = [
			UserMessage(content='User message 1', cache=False),
			AssistantMessage(content='Assistant message 1', cache=False),
			UserMessage(content='User message 2', cache=False),
		]

		# EN: Assign value to cleaned_messages.
		# JP: cleaned_messages に値を代入する。
		cleaned_messages = AnthropicMessageSerializer._clean_cache_messages(normal_messages_list)

		# All messages should remain uncached
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for msg in cleaned_messages:
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert not msg.cache

	# EN: Define function `test_max_4_cache_blocks`.
	# JP: 関数 `test_max_4_cache_blocks` を定義する。
	def test_max_4_cache_blocks(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Test that the max number of cache blocks is 4."""
		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(task='Hello, world!', llm=ChatAnthropic(''))
		# EN: Assign value to messages.
		# JP: messages に値を代入する。
		messages = agent.message_manager.get_messages()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		anthropic_messages, system_message = AnthropicMessageSerializer.serialize_messages(messages)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(anthropic_messages)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(system_message)


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Assign value to test_instance.
	# JP: test_instance に値を代入する。
	test_instance = TestAnthropicCache()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_cache_basic_functionality()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_cache_with_tool_calls()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_cache_with_images()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_cache_with_base64_images()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_cache_content_types()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_assistant_cache_empty_content()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_mixed_cache_scenarios()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_system_message_cache_behavior()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_agent_messages_integration()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_cache_cleaning_last_message_only()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_cache_cleaning_with_system_message()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_cache_cleaning_no_cached_messages()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	test_instance.test_max_4_cache_blocks()
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('All cache tests passed!')

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import tempfile

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pytest

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.prompts import AgentMessagePrompt
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.service import Agent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.views import BrowserStateSummary, TabInfo
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import DOMSelectorMap, EnhancedDOMTreeNode, NodeType, SerializedDOMState, SimplifiedNode
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystem
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.anthropic.chat import ChatAnthropic
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.azure.chat import ChatAzureOpenAI
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.google.chat import ChatGoogle
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.groq.chat import ChatGroq
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.openai.chat import ChatOpenAI

# Set logging level to INFO for this module
# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)
# EN: Evaluate an expression.
# JP: 式を評価する。
logger.setLevel(logging.INFO)


# EN: Define function `create_mock_state_message`.
# JP: 関数 `create_mock_state_message` を定義する。
def create_mock_state_message(temp_dir: str):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Create a mock state message with a single clickable element."""

	# Create a mock DOM element with a single clickable button
	# EN: Assign value to mock_button.
	# JP: mock_button に値を代入する。
	mock_button = EnhancedDOMTreeNode(
		node_id=1,
		backend_node_id=1,
		node_type=NodeType.ELEMENT_NODE,
		node_name='button',
		node_value='Click Me',
		attributes={'id': 'test-button'},
		is_scrollable=False,
		is_visible=True,
		absolute_position=None,
		session_id=None,
		target_id='ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234',
		frame_id=None,
		content_document=None,
		shadow_root_type=None,
		shadow_roots=None,
		parent_node=None,
		children_nodes=None,
		ax_node=None,
		snapshot_node=None,
	)

	# Create selector map
	# EN: Assign annotated value to selector_map.
	# JP: selector_map に型付きの値を代入する。
	selector_map: DOMSelectorMap = {1: mock_button}

	# Create mock tab info with proper target_id
	# EN: Assign value to mock_tab.
	# JP: mock_tab に値を代入する。
	mock_tab = TabInfo(
		target_id='ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234',
		url='https://example.com',
		title='Test Page',
	)

	# EN: Assign value to dom_state.
	# JP: dom_state に値を代入する。
	dom_state = SerializedDOMState(
		_root=SimplifiedNode(
			original_node=mock_button,
			children=[],
			should_display=True,
			interactive_index=1,
		),
		selector_map=selector_map,
	)

	# Create mock browser state with required selector_map
	# EN: Assign value to mock_browser_state.
	# JP: mock_browser_state に値を代入する。
	mock_browser_state = BrowserStateSummary(
		dom_state=dom_state,  # Using the actual DOM element
		url='https://example.com',
		title='Test Page',
		tabs=[mock_tab],
		screenshot='',  # Empty screenshot
		pixels_above=0,
		pixels_below=0,
	)

	# Create file system using the provided temp directory
	# EN: Assign value to mock_file_system.
	# JP: mock_file_system に値を代入する。
	mock_file_system = FileSystem(temp_dir)

	# Create the agent message prompt
	# EN: Assign value to agent_prompt.
	# JP: agent_prompt に値を代入する。
	agent_prompt = AgentMessagePrompt(
		browser_state_summary=mock_browser_state,
		file_system=mock_file_system,  # Now using actual FileSystem instance
		agent_history_description='',  # Empty history
		read_state_description='',  # Empty read state
		task='Click the button on the page',
		include_attributes=['id'],
		step_info=None,
		page_filtered_actions=None,
		max_clickable_elements_length=40000,
		sensitive_data=None,
	)

	# Override the clickable_elements_to_string method to return our simple element
	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	dom_state.llm_representation = lambda include_attributes=None: '[1]<button id="test-button">Click Me</button>'

	# Get the formatted message
	# EN: Assign value to message.
	# JP: message に値を代入する。
	message = agent_prompt.get_user_message(use_vision=False)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return message


# Pytest parameterized version
# EN: Define async function `test_single_step_parametrized`.
# JP: 非同期関数 `test_single_step_parametrized` を定義する。
@pytest.mark.parametrize(
	'llm_class,model_name',
	[
		(ChatGroq, 'meta-llama/llama-4-maverick-17b-128e-instruct'),
		(ChatGoogle, 'gemini-2.0-flash-exp'),
		(ChatOpenAI, 'gpt-4.1-mini'),
		(ChatAnthropic, 'claude-3-5-sonnet-latest'),
		(ChatAzureOpenAI, 'gpt-4.1-mini'),
	],
)
async def test_single_step_parametrized(llm_class, model_name):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Test single step with different LLM providers using pytest parametrize."""
	# EN: Assign value to llm.
	# JP: llm に値を代入する。
	llm = llm_class(model=model_name)

	# EN: Assign value to agent.
	# JP: agent に値を代入する。
	agent = Agent(task='Click the button on the page', llm=llm)

	# Create temporary directory that will stay alive during the test
	# EN: Execute logic with managed resources.
	# JP: リソース管理付きで処理を実行する。
	with tempfile.TemporaryDirectory() as temp_dir:
		# Create mock state message
		# EN: Assign value to mock_message.
		# JP: mock_message に値を代入する。
		mock_message = create_mock_state_message(temp_dir)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		agent.message_manager._set_message_with_type(mock_message, 'state')

		# EN: Assign value to messages.
		# JP: messages に値を代入する。
		messages = agent.message_manager.get_messages()

		# Test with simple question
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await llm.ainvoke(messages, agent.AgentOutput)

		# Basic assertions to ensure response is valid
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert response.completion is not None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert response.usage is not None
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert response.usage.total_tokens > 0


# EN: Define async function `test_single_step`.
# JP: 非同期関数 `test_single_step` を定義する。
async def test_single_step():
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Original test function that tests all models in a loop."""
	# Create a list of models to test
	# EN: Assign annotated value to models.
	# JP: models に型付きの値を代入する。
	models: list[BaseChatModel] = [
		ChatGroq(model='meta-llama/llama-4-maverick-17b-128e-instruct'),
		ChatGoogle(model='gemini-2.0-flash-exp'),
		ChatOpenAI(model='gpt-4.1'),
		ChatAnthropic(model='claude-3-5-sonnet-latest'),  # Using haiku for cost efficiency
		ChatAzureOpenAI(model='gpt-4o-mini'),
	]

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for llm in models:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'\n{"=" * 60}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'Testing with model: {llm.provider} - {llm.model}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'{"=" * 60}\n')

		# EN: Assign value to agent.
		# JP: agent に値を代入する。
		agent = Agent(task='Click the button on the page', llm=llm)

		# Create temporary directory that will stay alive during the test
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with tempfile.TemporaryDirectory() as temp_dir:
			# Create mock state message
			# EN: Assign value to mock_message.
			# JP: mock_message に値を代入する。
			mock_message = create_mock_state_message(temp_dir)

			# Print the mock message content to see what it looks like
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('Mock state message:')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(mock_message.content)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('\n' + '=' * 50 + '\n')

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			agent.message_manager._set_message_with_type(mock_message, 'state')

			# EN: Assign value to messages.
			# JP: messages に値を代入する。
			messages = agent.message_manager.get_messages()

			# Test with simple question
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await llm.ainvoke(messages, agent.AgentOutput)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'Response from {llm.provider}: {response.completion}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'Actions: {str(response.completion.action)}')

			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Error with {llm.provider}: {type(e).__name__}: {str(e)}')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'\n{"=" * 60}\n')


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import asyncio

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(test_single_step())

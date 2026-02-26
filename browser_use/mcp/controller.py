# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""MCP (Model Context Protocol) tool wrapper for browser-use.

This module provides integration between MCP tools and browser-use's action registry system.
MCP tools are dynamically discovered and registered as browser-use actions.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import Field, create_model

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import ActionResult
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.registry.service import Registry

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from mcp import ClientSession, StdioServerParameters
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from mcp.client.stdio import stdio_client
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from mcp.types import TextContent, Tool

	# EN: Assign value to MCP_AVAILABLE.
	# JP: MCP_AVAILABLE に値を代入する。
	MCP_AVAILABLE = True
except ImportError:
	# EN: Assign value to MCP_AVAILABLE.
	# JP: MCP_AVAILABLE に値を代入する。
	MCP_AVAILABLE = False
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.warning('MCP SDK not installed. Install with: pip install mcp')


# EN: Define class `MCPToolWrapper`.
# JP: クラス `MCPToolWrapper` を定義する。
class MCPToolWrapper:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Wrapper to integrate MCP tools as browser-use actions."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, registry: Registry, mcp_command: str, mcp_args: list[str] | None = None):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize MCP tool wrapper.

		Args:
			registry: Browser-use action registry to register MCP tools
			mcp_command: Command to start MCP server (e.g., "npx")
			mcp_args: Arguments for MCP command (e.g., ["@playwright/mcp@latest"])
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not MCP_AVAILABLE:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ImportError('MCP SDK not installed. Install with: pip install mcp')

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.registry = registry
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.mcp_command = mcp_command
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.mcp_args = mcp_args or []
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.session: ClientSession | None = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._tools: dict[str, Tool] = {}
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._registered_actions: set[str] = set()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._shutdown_event = asyncio.Event()

	# EN: Define async function `connect`.
	# JP: 非同期関数 `connect` を定義する。
	async def connect(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Connect to MCP server and discover available tools."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return  # Already connected

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'🔌 Connecting to MCP server: {self.mcp_command} {" ".join(self.mcp_args)}')

		# Create server parameters
		# EN: Assign value to server_params.
		# JP: server_params に値を代入する。
		server_params = StdioServerParameters(command=self.mcp_command, args=self.mcp_args, env=None)

		# Connect to the MCP server
		# EN: Execute async logic with managed resources.
		# JP: リソース管理付きで非同期処理を実行する。
		async with stdio_client(server_params) as (read, write):
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with ClientSession(read, write) as session:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.session = session

				# Initialize the connection
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await session.initialize()

				# Discover available tools
				# EN: Assign value to tools_response.
				# JP: tools_response に値を代入する。
				tools_response = await session.list_tools()
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._tools = {tool.name: tool for tool in tools_response.tools}

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'📦 Discovered {len(self._tools)} MCP tools: {list(self._tools.keys())}')

				# Register all discovered tools as actions
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for tool_name, tool in self._tools.items():
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._register_tool_as_action(tool_name, tool)

				# Keep session alive while tools are being used
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._keep_session_alive()

	# EN: Define async function `_keep_session_alive`.
	# JP: 非同期関数 `_keep_session_alive` を定義する。
	async def _keep_session_alive(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Keep the MCP session alive."""
		# This will block until the session is closed
		# In practice, you'd want to manage this lifecycle better
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._shutdown_event.wait()
		except asyncio.CancelledError:
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass

	# EN: Define function `_register_tool_as_action`.
	# JP: 関数 `_register_tool_as_action` を定義する。
	def _register_tool_as_action(self, tool_name: str, tool: Tool):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Register an MCP tool as a browser-use action.

		Args:
			tool_name: Name of the MCP tool
			tool: MCP Tool object with schema information
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tool_name in self._registered_actions:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return  # Already registered

		# Parse tool parameters to create Pydantic model
		# EN: Assign value to param_fields.
		# JP: param_fields に値を代入する。
		param_fields = {}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if tool.inputSchema:
			# MCP tools use JSON Schema for parameters
			# EN: Assign value to properties.
			# JP: properties に値を代入する。
			properties = tool.inputSchema.get('properties', {})
			# EN: Assign value to required.
			# JP: required に値を代入する。
			required = set(tool.inputSchema.get('required', []))

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for param_name, param_schema in properties.items():
				# Convert JSON Schema type to Python type
				# EN: Assign value to param_type.
				# JP: param_type に値を代入する。
				param_type = self._json_schema_to_python_type(param_schema)

				# Determine if field is required
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if param_name in required:
					# EN: Assign value to default.
					# JP: default に値を代入する。
					default = ...  # Required field
				else:
					# EN: Assign value to default.
					# JP: default に値を代入する。
					default = param_schema.get('default', None)

				# Add field description if available
				# EN: Assign value to field_kwargs.
				# JP: field_kwargs に値を代入する。
				field_kwargs = {}
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'description' in param_schema:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					field_kwargs['description'] = param_schema['description']

				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				param_fields[param_name] = (param_type, Field(default, **field_kwargs))

		# Create Pydantic model for the tool parameters
		# EN: Assign value to param_model.
		# JP: param_model に値を代入する。
		param_model = create_model(f'{tool_name}_Params', **param_fields) if param_fields else None

		# Determine if this is a browser-specific tool
		# EN: Assign value to is_browser_tool.
		# JP: is_browser_tool に値を代入する。
		is_browser_tool = tool_name.startswith('browser_')
		# EN: Assign value to domains.
		# JP: domains に値を代入する。
		domains = None
		# Note: page_filter has been removed since we no longer use Page objects

		# Create wrapper function for the MCP tool
		# EN: Define async function `mcp_action_wrapper`.
		# JP: 非同期関数 `mcp_action_wrapper` を定義する。
		async def mcp_action_wrapper(**kwargs):
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Wrapper function that calls the MCP tool."""
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.session:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError(f'MCP session not connected for tool {tool_name}')

			# Extract parameters (excluding special injected params)
			# EN: Assign value to special_params.
			# JP: special_params に値を代入する。
			special_params = {
				'page',
				'browser_session',
				'context',
				'page_extraction_llm',
				'file_system',
				'available_file_paths',
				'has_sensitive_data',
				'browser',
				'browser_context',
			}

			# EN: Assign value to tool_params.
			# JP: tool_params に値を代入する。
			tool_params = {k: v for k, v in kwargs.items() if k not in special_params}

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'🔧 Calling MCP tool {tool_name} with params: {tool_params}')

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Call the MCP tool
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = await self.session.call_tool(tool_name, tool_params)

				# Convert MCP result to ActionResult
				# MCP tools return results in various formats
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(result, 'content'):
					# Handle structured content responses
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if isinstance(result.content, list):
						# Multiple content items
						# EN: Assign value to content_parts.
						# JP: content_parts に値を代入する。
						content_parts = []
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for item in result.content:
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if isinstance(item, TextContent):
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								content_parts.append(item.text)  # type: ignore[reportAttributeAccessIssue]
							else:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								content_parts.append(str(item))
						# EN: Assign value to extracted_content.
						# JP: extracted_content に値を代入する。
						extracted_content = '\n'.join(content_parts)
					else:
						# EN: Assign value to extracted_content.
						# JP: extracted_content に値を代入する。
						extracted_content = str(result.content)
				else:
					# Direct result
					# EN: Assign value to extracted_content.
					# JP: extracted_content に値を代入する。
					extracted_content = str(result)

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=extracted_content)

			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'❌ MCP tool {tool_name} failed: {e}')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(extracted_content=f'MCP tool {tool_name} failed: {str(e)}', error=str(e))

		# Set function name for better debugging
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mcp_action_wrapper.__name__ = tool_name
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mcp_action_wrapper.__qualname__ = f'mcp.{tool_name}'

		# Register the action with browser-use
		# EN: Assign value to description.
		# JP: description に値を代入する。
		description = tool.description or f'MCP tool: {tool_name}'

		# Use the decorator to register the action
		# EN: Assign value to decorated_wrapper.
		# JP: decorated_wrapper に値を代入する。
		decorated_wrapper = self.registry.action(description=description, param_model=param_model, domains=domains)(
			mcp_action_wrapper
		)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._registered_actions.add(tool_name)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f'✅ Registered MCP tool as action: {tool_name}')

	# EN: Define async function `disconnect`.
	# JP: 非同期関数 `disconnect` を定義する。
	async def disconnect(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Disconnect from the MCP server and clean up resources."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._shutdown_event.set()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.session:
			# Session cleanup will be handled by the context manager
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.session = None

	# EN: Define function `_json_schema_to_python_type`.
	# JP: 関数 `_json_schema_to_python_type` を定義する。
	def _json_schema_to_python_type(self, schema: dict) -> Any:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert JSON Schema type to Python type.

		Args:
			schema: JSON Schema definition

		Returns:
			Python type corresponding to the schema
		"""
		# EN: Assign value to json_type.
		# JP: json_type に値を代入する。
		json_type = schema.get('type', 'string')

		# EN: Assign value to type_mapping.
		# JP: type_mapping に値を代入する。
		type_mapping = {
			'string': str,
			'number': float,
			'integer': int,
			'boolean': bool,
			'array': list,
			'object': dict,
		}

		# EN: Assign value to base_type.
		# JP: base_type に値を代入する。
		base_type = type_mapping.get(json_type, str)

		# Handle nullable types
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if schema.get('nullable', False):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return base_type | None

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return base_type


# Convenience function for easy integration
# EN: Define async function `register_mcp_tools`.
# JP: 非同期関数 `register_mcp_tools` を定義する。
async def register_mcp_tools(registry: Registry, mcp_command: str, mcp_args: list[str] | None = None) -> MCPToolWrapper:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Register MCP tools with a browser-use registry.

	Args:
		registry: Browser-use action registry
		mcp_command: Command to start MCP server
		mcp_args: Arguments for MCP command

	Returns:
		MCPToolWrapper instance (connected)

	Example:
		```python
	        from browser_use import Tools
	        from browser_use.mcp.tools import register_mcp_tools

	        tools = Tools()

	        # Register Playwright MCP tools
	        mcp = await register_mcp_tools(tools.registry, 'npx', ['@playwright/mcp@latest', '--headless'])

	        # Now all MCP tools are available as browser-use actions
		```
	"""
	# EN: Assign value to wrapper.
	# JP: wrapper に値を代入する。
	wrapper = MCPToolWrapper(registry, mcp_command, mcp_args)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	await wrapper.connect()
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return wrapper

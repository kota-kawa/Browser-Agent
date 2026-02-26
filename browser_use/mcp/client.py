# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""MCP (Model Context Protocol) client integration for browser-use.

This module provides integration between external MCP servers and browser-use's action registry.
MCP tools are dynamically discovered and registered as browser-use actions.

Example usage:
    from browser_use import Tools
    from browser_use.mcp.client import MCPClient

    tools = Tools()

    # Connect to an MCP server
    mcp_client = MCPClient(
        server_name="my-server",
        command="npx",
        args=["@mycompany/mcp-server@latest"]
    )

    # Register all MCP tools as browser-use actions
    await mcp_client.register_to_tools(tools)

    # Now use with Agent as normal - MCP tools are available as actions
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, ConfigDict, Field, create_model

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import ActionResult
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.telemetry import MCPClientTelemetryEvent, ProductTelemetry
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.registry.service import Registry
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.service import Tools
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import get_browser_use_version

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)

# Import MCP SDK
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from mcp import ClientSession, StdioServerParameters, types
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from mcp.client.stdio import stdio_client

# EN: Assign value to MCP_AVAILABLE.
# JP: MCP_AVAILABLE に値を代入する。
MCP_AVAILABLE = True


# EN: Define class `MCPClient`.
# JP: クラス `MCPClient` を定義する。
class MCPClient:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Client for connecting to MCP servers and exposing their tools as browser-use actions."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		server_name: str,
		command: str,
		args: list[str] | None = None,
		env: dict[str, str] | None = None,
	):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Initialize MCP client.

		Args:
			server_name: Name of the MCP server (for logging and identification)
			command: Command to start the MCP server (e.g., "npx", "python")
			args: Arguments for the command (e.g., ["@playwright/mcp@latest"])
			env: Environment variables for the server process
		"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.server_name = server_name
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.command = command
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.args = args or []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.env = env

		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.session: ClientSession | None = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._stdio_task = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._read_stream = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._write_stream = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._tools: dict[str, types.Tool] = {}
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._registered_actions: set[str] = set()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._connected = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._disconnect_event = asyncio.Event()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._telemetry = ProductTelemetry()

	# EN: Define async function `connect`.
	# JP: 非同期関数 `connect` を定義する。
	async def connect(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Connect to the MCP server and discover available tools."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._connected:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Already connected to {self.server_name}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to start_time.
		# JP: start_time に値を代入する。
		start_time = time.time()
		# EN: Assign value to error_msg.
		# JP: error_msg に値を代入する。
		error_msg = None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f"🔌 Connecting to MCP server '{self.server_name}': {self.command} {' '.join(self.args)}")

			# Create server parameters
			# EN: Assign value to server_params.
			# JP: server_params に値を代入する。
			server_params = StdioServerParameters(command=self.command, args=self.args, env=self.env)

			# Start stdio client in background task
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._stdio_task = asyncio.create_task(self._run_stdio_client(server_params))

			# Wait for connection to be established
			# EN: Assign value to retries.
			# JP: retries に値を代入する。
			retries = 0
			# EN: Assign value to max_retries.
			# JP: max_retries に値を代入する。
			max_retries = 100  # 10 second timeout (increased for parallel test execution)
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while not self._connected and retries < max_retries:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.1)
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				retries += 1

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self._connected:
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = f"Failed to connect to MCP server '{self.server_name}' after {max_retries * 0.1} seconds"
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError(error_msg)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f"📦 Discovered {len(self._tools)} tools from '{self.server_name}': {list(self._tools.keys())}")

		except Exception as e:
			# EN: Assign value to error_msg.
			# JP: error_msg に値を代入する。
			error_msg = str(e)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise
		finally:
			# Capture telemetry for connect action
			# EN: Assign value to duration.
			# JP: duration に値を代入する。
			duration = time.time() - start_time
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._telemetry.capture(
				MCPClientTelemetryEvent(
					server_name=self.server_name,
					command=self.command,
					tools_discovered=len(self._tools),
					version=get_browser_use_version(),
					action='connect',
					duration_seconds=duration,
					error_message=error_msg,
				)
			)

	# EN: Define async function `_run_stdio_client`.
	# JP: 非同期関数 `_run_stdio_client` を定義する。
	async def _run_stdio_client(self, server_params: StdioServerParameters):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Run the stdio client connection in a background task."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with stdio_client(server_params) as (read_stream, write_stream):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._read_stream = read_stream
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._write_stream = write_stream

				# Create and initialize session
				# EN: Execute async logic with managed resources.
				# JP: リソース管理付きで非同期処理を実行する。
				async with ClientSession(read_stream, write_stream) as session:
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

					# Mark as connected
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._connected = True

					# Keep the connection alive until disconnect is called
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._disconnect_event.wait()

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'MCP server connection error: {e}')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._connected = False
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise
		finally:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._connected = False
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.session = None

	# EN: Define async function `disconnect`.
	# JP: 非同期関数 `disconnect` を定義する。
	async def disconnect(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Disconnect from the MCP server."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._connected:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Assign value to start_time.
		# JP: start_time に値を代入する。
		start_time = time.time()
		# EN: Assign value to error_msg.
		# JP: error_msg に値を代入する。
		error_msg = None

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f"🔌 Disconnecting from MCP server '{self.server_name}'")

			# Signal disconnect
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._connected = False
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._disconnect_event.set()

			# Wait for stdio task to finish
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._stdio_task:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.wait_for(self._stdio_task, timeout=2.0)
				except TimeoutError:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.warning(f"Timeout waiting for MCP server '{self.server_name}' to disconnect")
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._stdio_task.cancel()
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await self._stdio_task
					except asyncio.CancelledError:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._tools.clear()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._registered_actions.clear()

		except Exception as e:
			# EN: Assign value to error_msg.
			# JP: error_msg に値を代入する。
			error_msg = str(e)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Error disconnecting from MCP server: {e}')
		finally:
			# Capture telemetry for disconnect action
			# EN: Assign value to duration.
			# JP: duration に値を代入する。
			duration = time.time() - start_time
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._telemetry.capture(
				MCPClientTelemetryEvent(
					server_name=self.server_name,
					command=self.command,
					tools_discovered=0,  # Tools cleared on disconnect
					version=get_browser_use_version(),
					action='disconnect',
					duration_seconds=duration,
					error_message=error_msg,
				)
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._telemetry.flush()

	# EN: Define async function `register_to_tools`.
	# JP: 非同期関数 `register_to_tools` を定義する。
	async def register_to_tools(
		self,
		tools: Tools,
		tool_filter: list[str] | None = None,
		prefix: str | None = None,
	) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Register MCP tools as actions in the browser-use tools.

		Args:
			tools: Browser-use tools to register actions to
			tool_filter: Optional list of tool names to register (None = all tools)
			prefix: Optional prefix to add to action names (e.g., "playwright_")
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._connected:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.connect()

		# EN: Assign value to registry.
		# JP: registry に値を代入する。
		registry = tools.registry

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for tool_name, tool in self._tools.items():
			# Skip if not in filter
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if tool_filter and tool_name not in tool_filter:
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# Apply prefix if specified
			# EN: Assign value to action_name.
			# JP: action_name に値を代入する。
			action_name = f'{prefix}{tool_name}' if prefix else tool_name

			# Skip if already registered
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if action_name in self._registered_actions:
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# Register the tool as an action
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._register_tool_as_action(registry, action_name, tool)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._registered_actions.add(action_name)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info(f"✅ Registered {len(self._registered_actions)} MCP tools from '{self.server_name}' as browser-use actions")

	# EN: Define function `_register_tool_as_action`.
	# JP: 関数 `_register_tool_as_action` を定義する。
	def _register_tool_as_action(self, registry: Registry, action_name: str, tool: Any) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Register a single MCP tool as a browser-use action.

		Args:
			registry: Browser-use registry to register action to
			action_name: Name for the registered action
			tool: MCP Tool object with schema information
		"""
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
				param_type = self._json_schema_to_python_type(param_schema, f'{action_name}_{param_name}')

				# Determine if field is required and handle defaults
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if param_name in required:
					# EN: Assign value to default.
					# JP: default に値を代入する。
					default = ...  # Required field
				else:
					# Optional field - make type optional and handle default
					# EN: Assign value to param_type.
					# JP: param_type に値を代入する。
					param_type = param_type | None
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'default' in param_schema:
						# EN: Assign value to default.
						# JP: default に値を代入する。
						default = param_schema['default']
					else:
						# EN: Assign value to default.
						# JP: default に値を代入する。
						default = None

				# Add field with description if available
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
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if param_fields:
			# Create a BaseModel class with proper configuration
			# EN: Define class `ConfiguredBaseModel`.
			# JP: クラス `ConfiguredBaseModel` を定義する。
			class ConfiguredBaseModel(BaseModel):
				# EN: Assign value to model_config.
				# JP: model_config に値を代入する。
				model_config = ConfigDict(extra='forbid', validate_by_name=True, validate_by_alias=True)

			# EN: Assign value to param_model.
			# JP: param_model に値を代入する。
			param_model = create_model(f'{action_name}_Params', __base__=ConfiguredBaseModel, **param_fields)
		else:
			# No parameters - create empty model
			# EN: Assign value to param_model.
			# JP: param_model に値を代入する。
			param_model = None

		# Determine if this is a browser-specific tool
		# EN: Assign value to is_browser_tool.
		# JP: is_browser_tool に値を代入する。
		is_browser_tool = tool.name.startswith('browser_') or 'page' in tool.name.lower()

		# Set up action filters
		# EN: Assign value to domains.
		# JP: domains に値を代入する。
		domains = None
		# Note: page_filter has been removed since we no longer use Page objects
		# Browser tools filtering would need to be done via domain filters instead

		# Create async wrapper function for the MCP tool
		# Need to define function with explicit parameters to satisfy registry validation
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if param_model:
			# Type 1: Function takes param model as first parameter
			# EN: Define async function `mcp_action_wrapper`.
			# JP: 非同期関数 `mcp_action_wrapper` を定義する。
			async def mcp_action_wrapper(params: param_model) -> ActionResult:  # type: ignore[no-redef]
				# EN: Describe this block with a docstring.
				# JP: このブロックの説明をドキュメント文字列で記述する。
				"""Wrapper function that calls the MCP tool."""
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not self.session or not self._connected:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=f"MCP server '{self.server_name}' not connected", success=False)

				# Convert pydantic model to dict for MCP call
				# EN: Assign value to tool_params.
				# JP: tool_params に値を代入する。
				tool_params = params.model_dump(exclude_none=True)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f"🔧 Calling MCP tool '{tool.name}' with params: {tool_params}")

				# EN: Assign value to start_time.
				# JP: start_time に値を代入する。
				start_time = time.time()
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = None

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# Call the MCP tool
					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = await self.session.call_tool(tool.name, tool_params)

					# Convert MCP result to ActionResult
					# EN: Assign value to extracted_content.
					# JP: extracted_content に値を代入する。
					extracted_content = self._format_mcp_result(result)

					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(
						extracted_content=extracted_content,
						long_term_memory=f"Used MCP tool '{tool.name}' from {self.server_name}",
					)

				except Exception as e:
					# EN: Assign value to error_msg.
					# JP: error_msg に値を代入する。
					error_msg = f"MCP tool '{tool.name}' failed: {str(e)}"
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(error_msg)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=error_msg, success=False)
				finally:
					# Capture telemetry for tool call
					# EN: Assign value to duration.
					# JP: duration に値を代入する。
					duration = time.time() - start_time
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._telemetry.capture(
						MCPClientTelemetryEvent(
							server_name=self.server_name,
							command=self.command,
							tools_discovered=len(self._tools),
							version=get_browser_use_version(),
							action='tool_call',
							tool_name=tool.name,
							duration_seconds=duration,
							error_message=error_msg,
						)
					)
		else:
			# No parameters - empty function signature
			# EN: Define async function `mcp_action_wrapper`.
			# JP: 非同期関数 `mcp_action_wrapper` を定義する。
			async def mcp_action_wrapper() -> ActionResult:  # type: ignore[no-redef]
				# EN: Describe this block with a docstring.
				# JP: このブロックの説明をドキュメント文字列で記述する。
				"""Wrapper function that calls the MCP tool."""
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not self.session or not self._connected:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=f"MCP server '{self.server_name}' not connected", success=False)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f"🔧 Calling MCP tool '{tool.name}' with no params")

				# EN: Assign value to start_time.
				# JP: start_time に値を代入する。
				start_time = time.time()
				# EN: Assign value to error_msg.
				# JP: error_msg に値を代入する。
				error_msg = None

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# Call the MCP tool with empty params
					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = await self.session.call_tool(tool.name, {})

					# Convert MCP result to ActionResult
					# EN: Assign value to extracted_content.
					# JP: extracted_content に値を代入する。
					extracted_content = self._format_mcp_result(result)

					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(
						extracted_content=extracted_content,
						long_term_memory=f"Used MCP tool '{tool.name}' from {self.server_name}",
					)

				except Exception as e:
					# EN: Assign value to error_msg.
					# JP: error_msg に値を代入する。
					error_msg = f"MCP tool '{tool.name}' failed: {str(e)}"
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(error_msg)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(error=error_msg, success=False)
				finally:
					# Capture telemetry for tool call
					# EN: Assign value to duration.
					# JP: duration に値を代入する。
					duration = time.time() - start_time
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._telemetry.capture(
						MCPClientTelemetryEvent(
							server_name=self.server_name,
							command=self.command,
							tools_discovered=len(self._tools),
							version=get_browser_use_version(),
							action='tool_call',
							tool_name=tool.name,
							duration_seconds=duration,
							error_message=error_msg,
						)
					)

		# Set function metadata for better debugging
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mcp_action_wrapper.__name__ = action_name
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		mcp_action_wrapper.__qualname__ = f'mcp.{self.server_name}.{action_name}'

		# Register the action with browser-use
		# EN: Assign value to description.
		# JP: description に値を代入する。
		description = tool.description or f'MCP tool from {self.server_name}: {tool.name}'

		# Use the registry's action decorator
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		registry.action(description=description, param_model=param_model, domains=domains)(mcp_action_wrapper)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f"✅ Registered MCP tool '{tool.name}' as action '{action_name}'")

	# EN: Define function `_format_mcp_result`.
	# JP: 関数 `_format_mcp_result` を定義する。
	def _format_mcp_result(self, result: Any) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Format MCP tool result into a string for ActionResult.

		Args:
			result: Raw result from MCP tool call

		Returns:
			Formatted string representation of the result
		"""
		# Handle different MCP result formats
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(result, 'content'):
			# Structured content response
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(result.content, list):
				# Multiple content items
				# EN: Assign value to parts.
				# JP: parts に値を代入する。
				parts = []
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for item in result.content:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if hasattr(item, 'text'):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						parts.append(item.text)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif hasattr(item, 'type') and item.type == 'text':
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						parts.append(str(item))
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						parts.append(str(item))
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return '\n'.join(parts)
			else:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return str(result.content)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(result, list):
			# List of content items
			# EN: Assign value to parts.
			# JP: parts に値を代入する。
			parts = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for item in result:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if hasattr(item, 'text'):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					parts.append(item.text)
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					parts.append(str(item))
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '\n'.join(parts)
		else:
			# Direct result or unknown format
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str(result)

	# EN: Define function `_json_schema_to_python_type`.
	# JP: 関数 `_json_schema_to_python_type` を定義する。
	def _json_schema_to_python_type(self, schema: dict, model_name: str = 'NestedModel') -> Any:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Convert JSON Schema type to Python type.

		Args:
			schema: JSON Schema definition
			model_name: Name for nested models

		Returns:
			Python type corresponding to the schema
		"""
		# EN: Assign value to json_type.
		# JP: json_type に値を代入する。
		json_type = schema.get('type', 'string')

		# Basic type mapping
		# EN: Assign value to type_mapping.
		# JP: type_mapping に値を代入する。
		type_mapping = {
			'string': str,
			'number': float,
			'integer': int,
			'boolean': bool,
			'array': list,
			'null': type(None),
		}

		# Handle enums (they're still strings)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'enum' in schema:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str

		# Handle objects with nested properties
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if json_type == 'object':
			# EN: Assign value to properties.
			# JP: properties に値を代入する。
			properties = schema.get('properties', {})
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if properties:
				# Create nested pydantic model for objects with properties
				# EN: Assign value to nested_fields.
				# JP: nested_fields に値を代入する。
				nested_fields = {}
				# EN: Assign value to required_fields.
				# JP: required_fields に値を代入する。
				required_fields = set(schema.get('required', []))

				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for prop_name, prop_schema in properties.items():
					# Recursively process nested properties
					# EN: Assign value to prop_type.
					# JP: prop_type に値を代入する。
					prop_type = self._json_schema_to_python_type(prop_schema, f'{model_name}_{prop_name}')

					# Determine if field is required and handle defaults
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if prop_name in required_fields:
						# EN: Assign value to default.
						# JP: default に値を代入する。
						default = ...  # Required field
					else:
						# Optional field - make type optional and handle default
						# EN: Assign value to prop_type.
						# JP: prop_type に値を代入する。
						prop_type = prop_type | None
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if 'default' in prop_schema:
							# EN: Assign value to default.
							# JP: default に値を代入する。
							default = prop_schema['default']
						else:
							# EN: Assign value to default.
							# JP: default に値を代入する。
							default = None

					# Add field with description if available
					# EN: Assign value to field_kwargs.
					# JP: field_kwargs に値を代入する。
					field_kwargs = {}
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'description' in prop_schema:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						field_kwargs['description'] = prop_schema['description']

					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					nested_fields[prop_name] = (prop_type, Field(default, **field_kwargs))

				# Create a BaseModel class with proper configuration
				# EN: Define class `ConfiguredBaseModel`.
				# JP: クラス `ConfiguredBaseModel` を定義する。
				class ConfiguredBaseModel(BaseModel):
					# EN: Assign value to model_config.
					# JP: model_config に値を代入する。
					model_config = ConfigDict(extra='forbid', validate_by_name=True, validate_by_alias=True)

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# Create and return nested pydantic model
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return create_model(model_name, __base__=ConfiguredBaseModel, **nested_fields)
				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.error(f'Failed to create nested model {model_name}: {e}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug(f'Fields: {nested_fields}')
					# Fallback to basic dict if model creation fails
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return dict
			else:
				# Object without properties - just return dict
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return dict

		# Handle arrays with specific item types
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if json_type == 'array':
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'items' in schema:
				# Get the item type recursively
				# EN: Assign value to item_type.
				# JP: item_type に値を代入する。
				item_type = self._json_schema_to_python_type(schema['items'], f'{model_name}_item')
				# Return properly typed list
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return list[item_type]
			else:
				# Array without item type specification
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return list

		# Get base type for non-object types
		# EN: Assign value to base_type.
		# JP: base_type に値を代入する。
		base_type = type_mapping.get(json_type, str)

		# Handle nullable/optional types
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if schema.get('nullable', False) or json_type == 'null':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return base_type | None

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return base_type

	# EN: Define async function `__aenter__`.
	# JP: 非同期関数 `__aenter__` を定義する。
	async def __aenter__(self):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Async context manager entry."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.connect()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define async function `__aexit__`.
	# JP: 非同期関数 `__aexit__` を定義する。
	async def __aexit__(self, exc_type, exc_val, exc_tb):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Async context manager exit."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.disconnect()

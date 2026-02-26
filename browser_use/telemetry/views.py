# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from abc import ABC, abstractmethod
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Sequence
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import asdict, dataclass
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import is_running_in_docker


# EN: Define class `BaseTelemetryEvent`.
# JP: クラス `BaseTelemetryEvent` を定義する。
@dataclass
class BaseTelemetryEvent(ABC):
	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	@abstractmethod
	def name(self) -> str:
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass

	# EN: Define function `properties`.
	# JP: 関数 `properties` を定義する。
	@property
	def properties(self) -> dict[str, Any]:
		# EN: Assign value to props.
		# JP: props に値を代入する。
		props = {k: v for k, v in asdict(self).items() if k != 'name'}
		# Add Docker context if running in Docker
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		props['is_docker'] = is_running_in_docker()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return props


# EN: Define class `AgentTelemetryEvent`.
# JP: クラス `AgentTelemetryEvent` を定義する。
@dataclass
class AgentTelemetryEvent(BaseTelemetryEvent):
	# start details
	# EN: Assign annotated value to task.
	# JP: task に型付きの値を代入する。
	task: str
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str
	# EN: Assign annotated value to model_provider.
	# JP: model_provider に型付きの値を代入する。
	model_provider: str
	# EN: Assign annotated value to max_steps.
	# JP: max_steps に型付きの値を代入する。
	max_steps: int
	# EN: Assign annotated value to max_actions_per_step.
	# JP: max_actions_per_step に型付きの値を代入する。
	max_actions_per_step: int
	# EN: Assign annotated value to use_vision.
	# JP: use_vision に型付きの値を代入する。
	use_vision: bool
	# EN: Assign annotated value to version.
	# JP: version に型付きの値を代入する。
	version: str
	# EN: Assign annotated value to source.
	# JP: source に型付きの値を代入する。
	source: str
	# EN: Assign annotated value to cdp_url.
	# JP: cdp_url に型付きの値を代入する。
	cdp_url: str | None
	# step details
	# EN: Assign annotated value to action_errors.
	# JP: action_errors に型付きの値を代入する。
	action_errors: Sequence[str | None]
	# EN: Assign annotated value to action_history.
	# JP: action_history に型付きの値を代入する。
	action_history: Sequence[list[dict] | None]
	# EN: Assign annotated value to urls_visited.
	# JP: urls_visited に型付きの値を代入する。
	urls_visited: Sequence[str | None]
	# end details
	# EN: Assign annotated value to steps.
	# JP: steps に型付きの値を代入する。
	steps: int
	# EN: Assign annotated value to total_input_tokens.
	# JP: total_input_tokens に型付きの値を代入する。
	total_input_tokens: int
	# EN: Assign annotated value to total_duration_seconds.
	# JP: total_duration_seconds に型付きの値を代入する。
	total_duration_seconds: float
	# EN: Assign annotated value to success.
	# JP: success に型付きの値を代入する。
	success: bool | None
	# EN: Assign annotated value to final_result_response.
	# JP: final_result_response に型付きの値を代入する。
	final_result_response: str | None
	# EN: Assign annotated value to error_message.
	# JP: error_message に型付きの値を代入する。
	error_message: str | None

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str = 'agent_event'


# EN: Define class `MCPClientTelemetryEvent`.
# JP: クラス `MCPClientTelemetryEvent` を定義する。
@dataclass
class MCPClientTelemetryEvent(BaseTelemetryEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Telemetry event for MCP client usage"""

	# EN: Assign annotated value to server_name.
	# JP: server_name に型付きの値を代入する。
	server_name: str
	# EN: Assign annotated value to command.
	# JP: command に型付きの値を代入する。
	command: str
	# EN: Assign annotated value to tools_discovered.
	# JP: tools_discovered に型付きの値を代入する。
	tools_discovered: int
	# EN: Assign annotated value to version.
	# JP: version に型付きの値を代入する。
	version: str
	# EN: Assign annotated value to action.
	# JP: action に型付きの値を代入する。
	action: str  # 'connect', 'disconnect', 'tool_call'
	# EN: Assign annotated value to tool_name.
	# JP: tool_name に型付きの値を代入する。
	tool_name: str | None = None
	# EN: Assign annotated value to duration_seconds.
	# JP: duration_seconds に型付きの値を代入する。
	duration_seconds: float | None = None
	# EN: Assign annotated value to error_message.
	# JP: error_message に型付きの値を代入する。
	error_message: str | None = None

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str = 'mcp_client_event'


# EN: Define class `MCPServerTelemetryEvent`.
# JP: クラス `MCPServerTelemetryEvent` を定義する。
@dataclass
class MCPServerTelemetryEvent(BaseTelemetryEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Telemetry event for MCP server usage"""

	# EN: Assign annotated value to version.
	# JP: version に型付きの値を代入する。
	version: str
	# EN: Assign annotated value to action.
	# JP: action に型付きの値を代入する。
	action: str  # 'start', 'stop', 'tool_call'
	# EN: Assign annotated value to tool_name.
	# JP: tool_name に型付きの値を代入する。
	tool_name: str | None = None
	# EN: Assign annotated value to duration_seconds.
	# JP: duration_seconds に型付きの値を代入する。
	duration_seconds: float | None = None
	# EN: Assign annotated value to error_message.
	# JP: error_message に型付きの値を代入する。
	error_message: str | None = None
	# EN: Assign annotated value to parent_process_cmdline.
	# JP: parent_process_cmdline に型付きの値を代入する。
	parent_process_cmdline: str | None = None

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str = 'mcp_server_event'


# EN: Define class `CLITelemetryEvent`.
# JP: クラス `CLITelemetryEvent` を定義する。
@dataclass
class CLITelemetryEvent(BaseTelemetryEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Telemetry event for CLI usage"""

	# EN: Assign annotated value to version.
	# JP: version に型付きの値を代入する。
	version: str
	# EN: Assign annotated value to action.
	# JP: action に型付きの値を代入する。
	action: str  # 'start', 'message_sent', 'task_completed', 'error'
	# EN: Assign annotated value to mode.
	# JP: mode に型付きの値を代入する。
	mode: str  # 'interactive', 'oneshot', 'mcp_server'
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str | None = None
	# EN: Assign annotated value to model_provider.
	# JP: model_provider に型付きの値を代入する。
	model_provider: str | None = None
	# EN: Assign annotated value to duration_seconds.
	# JP: duration_seconds に型付きの値を代入する。
	duration_seconds: float | None = None
	# EN: Assign annotated value to error_message.
	# JP: error_message に型付きの値を代入する。
	error_message: str | None = None

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str = 'cli_event'

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

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
		pass

	# EN: Define function `properties`.
	# JP: 関数 `properties` を定義する。
	@property
	def properties(self) -> dict[str, Any]:
		props = {k: v for k, v in asdict(self).items() if k != 'name'}
		# Add Docker context if running in Docker
		props['is_docker'] = is_running_in_docker()
		return props


# EN: Define class `AgentTelemetryEvent`.
# JP: クラス `AgentTelemetryEvent` を定義する。
@dataclass
class AgentTelemetryEvent(BaseTelemetryEvent):
	# start details
	task: str
	model: str
	model_provider: str
	max_steps: int
	max_actions_per_step: int
	use_vision: bool
	version: str
	source: str
	cdp_url: str | None
	# step details
	action_errors: Sequence[str | None]
	action_history: Sequence[list[dict] | None]
	urls_visited: Sequence[str | None]
	# end details
	steps: int
	total_input_tokens: int
	total_duration_seconds: float
	success: bool | None
	final_result_response: str | None
	error_message: str | None

	name: str = 'agent_event'


# EN: Define class `MCPClientTelemetryEvent`.
# JP: クラス `MCPClientTelemetryEvent` を定義する。
@dataclass
class MCPClientTelemetryEvent(BaseTelemetryEvent):
	"""Telemetry event for MCP client usage"""

	server_name: str
	command: str
	tools_discovered: int
	version: str
	action: str  # 'connect', 'disconnect', 'tool_call'
	tool_name: str | None = None
	duration_seconds: float | None = None
	error_message: str | None = None

	name: str = 'mcp_client_event'


# EN: Define class `MCPServerTelemetryEvent`.
# JP: クラス `MCPServerTelemetryEvent` を定義する。
@dataclass
class MCPServerTelemetryEvent(BaseTelemetryEvent):
	"""Telemetry event for MCP server usage"""

	version: str
	action: str  # 'start', 'stop', 'tool_call'
	tool_name: str | None = None
	duration_seconds: float | None = None
	error_message: str | None = None
	parent_process_cmdline: str | None = None

	name: str = 'mcp_server_event'


# EN: Define class `CLITelemetryEvent`.
# JP: クラス `CLITelemetryEvent` を定義する。
@dataclass
class CLITelemetryEvent(BaseTelemetryEvent):
	"""Telemetry event for CLI usage"""

	version: str
	action: str  # 'start', 'message_sent', 'task_completed', 'error'
	mode: str  # 'interactive', 'oneshot', 'mcp_server'
	model: str | None = None
	model_provider: str | None = None
	duration_seconds: float | None = None
	error_message: str | None = None

	name: str = 'cli_event'

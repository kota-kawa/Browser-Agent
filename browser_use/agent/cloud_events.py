# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import base64
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime, timezone
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import anyio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import Field, field_validator
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str

# EN: Assign value to MAX_STRING_LENGTH.
# JP: MAX_STRING_LENGTH に値を代入する。
MAX_STRING_LENGTH = 100000  # 100K chars ~ 25k tokens should be enough
# EN: Assign value to MAX_URL_LENGTH.
# JP: MAX_URL_LENGTH に値を代入する。
MAX_URL_LENGTH = 100000
# EN: Assign value to MAX_TASK_LENGTH.
# JP: MAX_TASK_LENGTH に値を代入する。
MAX_TASK_LENGTH = 100000
# EN: Assign value to MAX_COMMENT_LENGTH.
# JP: MAX_COMMENT_LENGTH に値を代入する。
MAX_COMMENT_LENGTH = 2000
# EN: Assign value to MAX_FILE_CONTENT_SIZE.
# JP: MAX_FILE_CONTENT_SIZE に値を代入する。
MAX_FILE_CONTENT_SIZE = 50 * 1024 * 1024  # 50MB


# EN: Define class `UpdateAgentTaskEvent`.
# JP: クラス `UpdateAgentTaskEvent` を定義する。
class UpdateAgentTaskEvent(BaseEvent):
	# Required fields for identification
	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str  # The task ID to update
	# EN: Assign annotated value to user_id.
	# JP: user_id に型付きの値を代入する。
	user_id: str = Field(max_length=255)  # For authorization
	# EN: Assign annotated value to device_id.
	# JP: device_id に型付きの値を代入する。
	device_id: str | None = Field(None, max_length=255)  # Device ID for auth lookup

	# Optional fields that can be updated
	# EN: Assign annotated value to stopped.
	# JP: stopped に型付きの値を代入する。
	stopped: bool | None = None
	# EN: Assign annotated value to paused.
	# JP: paused に型付きの値を代入する。
	paused: bool | None = None
	# EN: Assign annotated value to done_output.
	# JP: done_output に型付きの値を代入する。
	done_output: str | None = Field(None, max_length=MAX_STRING_LENGTH)
	# EN: Assign annotated value to finished_at.
	# JP: finished_at に型付きの値を代入する。
	finished_at: datetime | None = None
	# EN: Assign annotated value to agent_state.
	# JP: agent_state に型付きの値を代入する。
	agent_state: dict | None = None
	# EN: Assign annotated value to user_feedback_type.
	# JP: user_feedback_type に型付きの値を代入する。
	user_feedback_type: str | None = Field(None, max_length=10)  # UserFeedbackType enum value as string
	# EN: Assign annotated value to user_comment.
	# JP: user_comment に型付きの値を代入する。
	user_comment: str | None = Field(None, max_length=MAX_COMMENT_LENGTH)
	# EN: Assign annotated value to gif_url.
	# JP: gif_url に型付きの値を代入する。
	gif_url: str | None = Field(None, max_length=MAX_URL_LENGTH)

	# EN: Define function `from_agent`.
	# JP: 関数 `from_agent` を定義する。
	@classmethod
	def from_agent(cls, agent) -> 'UpdateAgentTaskEvent':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create an UpdateAgentTaskEvent from an Agent instance"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not hasattr(agent, '_task_start_time'):
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError('Agent must have _task_start_time attribute')

		# EN: Assign value to done_output.
		# JP: done_output に値を代入する。
		done_output = agent.history.final_result() if agent.history else None
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls(
			id=str(agent.task_id),
			user_id='',  # To be filled by cloud handler
			device_id=agent.cloud_sync.auth_client.device_id
			if hasattr(agent, 'cloud_sync') and agent.cloud_sync and agent.cloud_sync.auth_client
			else None,
			stopped=agent.state.stopped if hasattr(agent.state, 'stopped') else False,
			paused=agent.state.paused if hasattr(agent.state, 'paused') else False,
			done_output=done_output,
			finished_at=datetime.now(timezone.utc) if agent.history and agent.history.is_done() else None,
			agent_state=agent.state.model_dump() if hasattr(agent.state, 'model_dump') else {},
			user_feedback_type=None,
			user_comment=None,
			gif_url=None,
			# user_feedback_type and user_comment would be set by the API/frontend
			# gif_url would be set after GIF generation if needed
		)


# EN: Define class `CreateAgentOutputFileEvent`.
# JP: クラス `CreateAgentOutputFileEvent` を定義する。
class CreateAgentOutputFileEvent(BaseEvent):
	# Model fields
	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str = Field(default_factory=uuid7str)
	# EN: Assign annotated value to user_id.
	# JP: user_id に型付きの値を代入する。
	user_id: str = Field(max_length=255)
	# EN: Assign annotated value to device_id.
	# JP: device_id に型付きの値を代入する。
	device_id: str | None = Field(None, max_length=255)  # Device ID for auth lookup
	# EN: Assign annotated value to task_id.
	# JP: task_id に型付きの値を代入する。
	task_id: str
	# EN: Assign annotated value to file_name.
	# JP: file_name に型付きの値を代入する。
	file_name: str = Field(max_length=255)
	# EN: Assign annotated value to file_content.
	# JP: file_content に型付きの値を代入する。
	file_content: str | None = None  # Base64 encoded file content
	# EN: Assign annotated value to content_type.
	# JP: content_type に型付きの値を代入する。
	content_type: str | None = Field(None, max_length=100)  # MIME type for file uploads
	# EN: Assign annotated value to created_at.
	# JP: created_at に型付きの値を代入する。
	created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

	# EN: Define function `validate_file_size`.
	# JP: 関数 `validate_file_size` を定義する。
	@field_validator('file_content')
	@classmethod
	def validate_file_size(cls, v: str | None) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Validate base64 file content size."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if v is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return v
		# Remove data URL prefix if present
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ',' in v:
			# EN: Assign value to v.
			# JP: v に値を代入する。
			v = v.split(',')[1]
		# Estimate decoded size (base64 is ~33% larger)
		# EN: Assign value to estimated_size.
		# JP: estimated_size に値を代入する。
		estimated_size = len(v) * 3 / 4
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if estimated_size > MAX_FILE_CONTENT_SIZE:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'File content exceeds maximum size of {MAX_FILE_CONTENT_SIZE / 1024 / 1024}MB')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return v

	# EN: Define async function `from_agent_and_file`.
	# JP: 非同期関数 `from_agent_and_file` を定義する。
	@classmethod
	async def from_agent_and_file(cls, agent, output_path: str) -> 'CreateAgentOutputFileEvent':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create a CreateAgentOutputFileEvent from a file path"""

		# EN: Assign value to gif_path.
		# JP: gif_path に値を代入する。
		gif_path = Path(output_path)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not gif_path.exists():
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise FileNotFoundError(f'File not found: {output_path}')

		# EN: Assign value to gif_size.
		# JP: gif_size に値を代入する。
		gif_size = os.path.getsize(gif_path)

		# Read GIF content for base64 encoding if needed
		# EN: Assign value to gif_content.
		# JP: gif_content に値を代入する。
		gif_content = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if gif_size < 50 * 1024 * 1024:  # Only read if < 50MB
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with await anyio.open_file(gif_path, 'rb') as f:
				# EN: Assign value to gif_bytes.
				# JP: gif_bytes に値を代入する。
				gif_bytes = await f.read()
				# EN: Assign value to gif_content.
				# JP: gif_content に値を代入する。
				gif_content = base64.b64encode(gif_bytes).decode('utf-8')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls(
			user_id='',  # To be filled by cloud handler
			device_id=agent.cloud_sync.auth_client.device_id
			if hasattr(agent, 'cloud_sync') and agent.cloud_sync and agent.cloud_sync.auth_client
			else None,
			task_id=str(agent.task_id),
			file_name=gif_path.name,
			file_content=gif_content,  # Base64 encoded
			content_type='image/gif',
		)


# EN: Define class `CreateAgentStepEvent`.
# JP: クラス `CreateAgentStepEvent` を定義する。
class CreateAgentStepEvent(BaseEvent):
	# Model fields
	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str = Field(default_factory=uuid7str)
	# EN: Assign annotated value to user_id.
	# JP: user_id に型付きの値を代入する。
	user_id: str = Field(max_length=255)  # Added for authorization checks
	# EN: Assign annotated value to device_id.
	# JP: device_id に型付きの値を代入する。
	device_id: str | None = Field(None, max_length=255)  # Device ID for auth lookup
	# EN: Assign annotated value to created_at.
	# JP: created_at に型付きの値を代入する。
	created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
	# EN: Assign annotated value to agent_task_id.
	# JP: agent_task_id に型付きの値を代入する。
	agent_task_id: str
	# EN: Assign annotated value to step.
	# JP: step に型付きの値を代入する。
	step: int
	# EN: Assign annotated value to evaluation_previous_goal.
	# JP: evaluation_previous_goal に型付きの値を代入する。
	evaluation_previous_goal: str = Field(max_length=MAX_STRING_LENGTH)
	# EN: Assign annotated value to memory.
	# JP: memory に型付きの値を代入する。
	memory: str = Field(max_length=MAX_STRING_LENGTH)
	# EN: Assign annotated value to next_goal.
	# JP: next_goal に型付きの値を代入する。
	next_goal: str = Field(max_length=MAX_STRING_LENGTH)
	# EN: Assign annotated value to actions.
	# JP: actions に型付きの値を代入する。
	actions: list[dict]
	# EN: Assign annotated value to screenshot_url.
	# JP: screenshot_url に型付きの値を代入する。
	screenshot_url: str | None = Field(None, max_length=MAX_FILE_CONTENT_SIZE)  # ~50MB for base64 images
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str = Field(default='', max_length=MAX_URL_LENGTH)

	# EN: Define function `validate_screenshot_size`.
	# JP: 関数 `validate_screenshot_size` を定義する。
	@field_validator('screenshot_url')
	@classmethod
	def validate_screenshot_size(cls, v: str | None) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Validate screenshot URL or base64 content size."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if v is None or not v.startswith('data:'):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return v
		# It's base64 data, check size
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ',' in v:
			# EN: Assign value to base64_part.
			# JP: base64_part に値を代入する。
			base64_part = v.split(',')[1]
			# EN: Assign value to estimated_size.
			# JP: estimated_size に値を代入する。
			estimated_size = len(base64_part) * 3 / 4
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if estimated_size > MAX_FILE_CONTENT_SIZE:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f'Screenshot content exceeds maximum size of {MAX_FILE_CONTENT_SIZE / 1024 / 1024}MB')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return v

	# EN: Define function `from_agent_step`.
	# JP: 関数 `from_agent_step` を定義する。
	@classmethod
	def from_agent_step(
		cls, agent, model_output, result: list, actions_data: list[dict], browser_state_summary
	) -> 'CreateAgentStepEvent':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create a CreateAgentStepEvent from agent step data"""
		# Get first action details if available
		# EN: Assign value to first_action.
		# JP: first_action に値を代入する。
		first_action = model_output.action[0] if model_output.action else None

		# Extract current state from model output
		# EN: Assign value to current_state.
		# JP: current_state に値を代入する。
		current_state = model_output.current_state if hasattr(model_output, 'current_state') else None

		# Capture screenshot as base64 data URL if available
		# EN: Assign value to screenshot_url.
		# JP: screenshot_url に値を代入する。
		screenshot_url = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if browser_state_summary.screenshot:
			# EN: Assign value to screenshot_url.
			# JP: screenshot_url に値を代入する。
			screenshot_url = f'data:image/png;base64,{browser_state_summary.screenshot}'
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import logging

			# EN: Assign value to logger.
			# JP: logger に値を代入する。
			logger = logging.getLogger(__name__)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'📸 Including screenshot in CreateAgentStepEvent, length: {len(browser_state_summary.screenshot)}')
		else:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import logging

			# EN: Assign value to logger.
			# JP: logger に値を代入する。
			logger = logging.getLogger(__name__)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('📸 No screenshot in browser_state_summary for CreateAgentStepEvent')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls(
			user_id='',  # To be filled by cloud handler
			device_id=agent.cloud_sync.auth_client.device_id
			if hasattr(agent, 'cloud_sync') and agent.cloud_sync and agent.cloud_sync.auth_client
			else None,
			agent_task_id=str(agent.task_id),
			step=agent.current_step_number,
			evaluation_previous_goal=current_state.evaluation_previous_goal if current_state else '',
			memory=current_state.memory if current_state else '',
			next_goal=current_state.next_goal if current_state else '',
			actions=actions_data,  # List of action dicts
			url=browser_state_summary.url,
			screenshot_url=screenshot_url,
		)


# EN: Define class `CreateAgentTaskEvent`.
# JP: クラス `CreateAgentTaskEvent` を定義する。
class CreateAgentTaskEvent(BaseEvent):
	# Model fields
	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str = Field(default_factory=uuid7str)
	# EN: Assign annotated value to user_id.
	# JP: user_id に型付きの値を代入する。
	user_id: str = Field(max_length=255)  # Added for authorization checks
	# EN: Assign annotated value to device_id.
	# JP: device_id に型付きの値を代入する。
	device_id: str | None = Field(None, max_length=255)  # Device ID for auth lookup
	# EN: Assign annotated value to agent_session_id.
	# JP: agent_session_id に型付きの値を代入する。
	agent_session_id: str
	# EN: Assign annotated value to llm_model.
	# JP: llm_model に型付きの値を代入する。
	llm_model: str = Field(max_length=100)  # LLMModel enum value as string
	# EN: Assign annotated value to stopped.
	# JP: stopped に型付きの値を代入する。
	stopped: bool = False
	# EN: Assign annotated value to paused.
	# JP: paused に型付きの値を代入する。
	paused: bool = False
	# EN: Assign annotated value to task.
	# JP: task に型付きの値を代入する。
	task: str = Field(max_length=MAX_TASK_LENGTH)
	# EN: Assign annotated value to done_output.
	# JP: done_output に型付きの値を代入する。
	done_output: str | None = Field(None, max_length=MAX_STRING_LENGTH)
	# EN: Assign annotated value to scheduled_task_id.
	# JP: scheduled_task_id に型付きの値を代入する。
	scheduled_task_id: str | None = None
	# EN: Assign annotated value to started_at.
	# JP: started_at に型付きの値を代入する。
	started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
	# EN: Assign annotated value to finished_at.
	# JP: finished_at に型付きの値を代入する。
	finished_at: datetime | None = None
	# EN: Assign annotated value to agent_state.
	# JP: agent_state に型付きの値を代入する。
	agent_state: dict = Field(default_factory=dict)
	# EN: Assign annotated value to user_feedback_type.
	# JP: user_feedback_type に型付きの値を代入する。
	user_feedback_type: str | None = Field(None, max_length=10)  # UserFeedbackType enum value as string
	# EN: Assign annotated value to user_comment.
	# JP: user_comment に型付きの値を代入する。
	user_comment: str | None = Field(None, max_length=MAX_COMMENT_LENGTH)
	# EN: Assign annotated value to gif_url.
	# JP: gif_url に型付きの値を代入する。
	gif_url: str | None = Field(None, max_length=MAX_URL_LENGTH)

	# EN: Define function `from_agent`.
	# JP: 関数 `from_agent` を定義する。
	@classmethod
	def from_agent(cls, agent) -> 'CreateAgentTaskEvent':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create a CreateAgentTaskEvent from an Agent instance"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls(
			id=str(agent.task_id),
			user_id='',  # To be filled by cloud handler
			device_id=agent.cloud_sync.auth_client.device_id
			if hasattr(agent, 'cloud_sync') and agent.cloud_sync and agent.cloud_sync.auth_client
			else None,
			agent_session_id=str(agent.session_id),
			task=agent.task,
			llm_model=agent.llm.model_name,
			agent_state=agent.state.model_dump() if hasattr(agent.state, 'model_dump') else {},
			stopped=False,
			paused=False,
			done_output=None,
			started_at=datetime.fromtimestamp(agent._task_start_time, tz=timezone.utc),
			finished_at=None,
			user_feedback_type=None,
			user_comment=None,
			gif_url=None,
		)


# EN: Define class `CreateAgentSessionEvent`.
# JP: クラス `CreateAgentSessionEvent` を定義する。
class CreateAgentSessionEvent(BaseEvent):
	# Model fields
	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str = Field(default_factory=uuid7str)
	# EN: Assign annotated value to user_id.
	# JP: user_id に型付きの値を代入する。
	user_id: str = Field(max_length=255)
	# EN: Assign annotated value to device_id.
	# JP: device_id に型付きの値を代入する。
	device_id: str | None = Field(None, max_length=255)  # Device ID for auth lookup
	# EN: Assign annotated value to browser_session_id.
	# JP: browser_session_id に型付きの値を代入する。
	browser_session_id: str = Field(max_length=255)
	# EN: Assign annotated value to browser_session_live_url.
	# JP: browser_session_live_url に型付きの値を代入する。
	browser_session_live_url: str = Field(max_length=MAX_URL_LENGTH)
	# EN: Assign annotated value to browser_session_cdp_url.
	# JP: browser_session_cdp_url に型付きの値を代入する。
	browser_session_cdp_url: str = Field(max_length=MAX_URL_LENGTH)
	# EN: Assign annotated value to browser_session_stopped.
	# JP: browser_session_stopped に型付きの値を代入する。
	browser_session_stopped: bool = False
	# EN: Assign annotated value to browser_session_stopped_at.
	# JP: browser_session_stopped_at に型付きの値を代入する。
	browser_session_stopped_at: datetime | None = None
	# EN: Assign annotated value to is_source_api.
	# JP: is_source_api に型付きの値を代入する。
	is_source_api: bool | None = None
	# EN: Assign annotated value to browser_state.
	# JP: browser_state に型付きの値を代入する。
	browser_state: dict = Field(default_factory=dict)
	# EN: Assign annotated value to browser_session_data.
	# JP: browser_session_data に型付きの値を代入する。
	browser_session_data: dict | None = None

	# EN: Define function `from_agent`.
	# JP: 関数 `from_agent` を定義する。
	@classmethod
	def from_agent(cls, agent) -> 'CreateAgentSessionEvent':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create a CreateAgentSessionEvent from an Agent instance"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls(
			id=str(agent.session_id),
			user_id='',  # To be filled by cloud handler
			device_id=agent.cloud_sync.auth_client.device_id
			if hasattr(agent, 'cloud_sync') and agent.cloud_sync and agent.cloud_sync.auth_client
			else None,
			browser_session_id=agent.browser_session.id,
			browser_session_live_url='',  # To be filled by cloud handler
			browser_session_cdp_url='',  # To be filled by cloud handler
			browser_state={
				'viewport': agent.browser_profile.viewport if agent.browser_profile else {'width': 1280, 'height': 720},
				'user_agent': agent.browser_profile.user_agent if agent.browser_profile else None,
				'headless': agent.browser_profile.headless if agent.browser_profile else True,
				'initial_url': None,  # Will be updated during execution
				'final_url': None,  # Will be updated during execution
				'total_pages_visited': 0,  # Will be updated during execution
				'session_duration_seconds': 0,  # Will be updated during execution
			},
			browser_session_data={
				'cookies': [],
				'secrets': {},
				# TODO: send secrets safely so tasks can be replayed on cloud seamlessly
				# 'secrets': dict(agent.sensitive_data) if agent.sensitive_data else {},
				'allowed_domains': agent.browser_profile.allowed_domains if agent.browser_profile else [],
			},
		)


# EN: Define class `UpdateAgentSessionEvent`.
# JP: クラス `UpdateAgentSessionEvent` を定義する。
class UpdateAgentSessionEvent(BaseEvent):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Event to update an existing agent session"""

	# Model fields
	# EN: Assign annotated value to id.
	# JP: id に型付きの値を代入する。
	id: str  # Session ID to update
	# EN: Assign annotated value to user_id.
	# JP: user_id に型付きの値を代入する。
	user_id: str = Field(max_length=255)
	# EN: Assign annotated value to device_id.
	# JP: device_id に型付きの値を代入する。
	device_id: str | None = Field(None, max_length=255)
	# EN: Assign annotated value to browser_session_stopped.
	# JP: browser_session_stopped に型付きの値を代入する。
	browser_session_stopped: bool | None = None
	# EN: Assign annotated value to browser_session_stopped_at.
	# JP: browser_session_stopped_at に型付きの値を代入する。
	browser_session_stopped_at: datetime | None = None
	# EN: Assign annotated value to end_reason.
	# JP: end_reason に型付きの値を代入する。
	end_reason: str | None = Field(None, max_length=100)  # Why the session ended

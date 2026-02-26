# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Cloud sync service for sending events to the Browser Use cloud.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import shutil

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.sync.auth import TEMP_USER_ID, DeviceAuthClient

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define class `CloudSync`.
# JP: クラス `CloudSync` を定義する。
class CloudSync:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Service for syncing events to the Browser Use cloud"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, base_url: str | None = None, allow_session_events_for_auth: bool = False):
		# Backend API URL for all API requests - can be passed directly or defaults to env var
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.base_url = base_url or CONFIG.BROWSER_USE_CLOUD_API_URL
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.auth_client = DeviceAuthClient(base_url=self.base_url)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.auth_task = None
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.session_id: str | None = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.allow_session_events_for_auth = allow_session_events_for_auth
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.auth_flow_active = False  # Flag to indicate auth flow is running
		# Check if cloud sync is actually enabled - if not, we should remain silent
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.enabled = CONFIG.BROWSER_USE_CLOUD_SYNC

	# EN: Define async function `handle_event`.
	# JP: 非同期関数 `handle_event` を定義する。
	async def handle_event(self, event: BaseEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Handle an event by sending it to the cloud"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# If cloud sync is disabled, don't handle any events
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.enabled:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Extract session ID from CreateAgentSessionEvent
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if event.event_type == 'CreateAgentSessionEvent' and hasattr(event, 'id'):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.session_id = str(event.id)  # type: ignore

				# Start authentication immediately when session is created
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not hasattr(self, 'auth_task') or self.auth_task is None:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self.session_id:
						# Start auth in background immediately
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						self.auth_task = asyncio.create_task(self._background_auth(agent_session_id=self.session_id))
					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.warning('Cannot start auth - session_id not set yet')

			# Send events based on authentication status and context
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.auth_client.is_authenticated:
				# User is authenticated - send all events
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._send_event(event)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif self.allow_session_events_for_auth:
				# Special case: allow ALL events during auth flow
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._send_event(event)
				# Mark auth flow as active when we see a session event
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if event.event_type == 'CreateAgentSessionEvent':
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.auth_flow_active = True
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif self.auth_task and not self.auth_task.done():
				# Authentication is in progress - only send session creation events
				# to preserve session context, but don't leak other data
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if event.event_type in ['CreateAgentSessionEvent']:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await self._send_event(event)
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug(f'Skipping event {event.event_type} during auth - not authenticated yet')
			else:
				# User is not authenticated and no auth in progress - don't send anything
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Skipping event {event.event_type} - user not authenticated')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Failed to handle {event.event_type} event: {type(e).__name__}: {e}', exc_info=True)

	# EN: Define async function `_send_event`.
	# JP: 非同期関数 `_send_event` を定義する。
	async def _send_event(self, event: BaseEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Send event to cloud API"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to headers.
			# JP: headers に値を代入する。
			headers = {}

			# Override user_id only if it's not already set to a specific value
			# This allows CLI and other code to explicitly set temp user_id when needed
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.auth_client and self.auth_client.is_authenticated:
				# Only override if we're fully authenticated and event doesn't have temp user_id
				# EN: Assign value to current_user_id.
				# JP: current_user_id に値を代入する。
				current_user_id = getattr(event, 'user_id', None)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if current_user_id != TEMP_USER_ID:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					setattr(event, 'user_id', str(self.auth_client.user_id))
			else:
				# Set temp user_id if not already set
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not hasattr(event, 'user_id') or not getattr(event, 'user_id', None):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					setattr(event, 'user_id', TEMP_USER_ID)

			# Add auth headers if available
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.auth_client:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				headers.update(self.auth_client.get_headers())

			# Send event (batch format with direct BaseEvent serialization)
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with httpx.AsyncClient() as client:
				# Serialize event and add device_id to all events
				# EN: Assign value to event_data.
				# JP: event_data に値を代入する。
				event_data = event.model_dump(mode='json')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.auth_client and self.auth_client.device_id:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					event_data['device_id'] = self.auth_client.device_id

				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await client.post(
					f'{self.base_url.rstrip("/")}/api/v1/events',
					json={'events': [event_data]},
					headers=headers,
					timeout=10.0,
				)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if response.status_code >= 400:
					# Log error but don't raise - we want to fail silently
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug(
						f'Failed to send sync event: POST {response.request.url} {response.status_code} - {response.text}'
					)
		except httpx.TimeoutException:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Event send timed out after 10 seconds: {event}')
		except httpx.ConnectError as e:
			# logger.warning(f'⚠️ Failed to connect to cloud service at {self.base_url}: {e}')
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass
		except httpx.HTTPError as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'HTTP error sending event {event}: {type(e).__name__}: {e}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Unexpected error sending event {event}: {type(e).__name__}: {e}')

	# EN: Define async function `_background_auth`.
	# JP: 非同期関数 `_background_auth` を定義する。
	async def _background_auth(self, agent_session_id: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Run authentication in background or show cloud URL if already authenticated"""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.auth_client, 'auth_client must exist before calling CloudSync._background_auth()'
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.session_id, 'session_id must be set before calling CloudSync._background_auth() can fire'
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Only show cloud URLs if cloud sync is enabled
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.enabled:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# Always show the cloud URL (auth happens immediately when session starts now)
			# EN: Assign value to frontend_url.
			# JP: frontend_url に値を代入する。
			frontend_url = CONFIG.BROWSER_USE_CLOUD_UI_URL or self.base_url.replace('//api.', '//cloud.')
			# EN: Assign value to session_url.
			# JP: session_url に値を代入する。
			session_url = f'{frontend_url.rstrip("/")}/agent/{agent_session_id}'
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			terminal_width, _terminal_height = shutil.get_terminal_size((80, 20))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.auth_client.is_authenticated:
				# User is authenticated - show direct link
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('─' * max(terminal_width - 40, 20))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('🌐  View the details of this run in Browser Use Cloud:')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'    👉  {session_url}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('─' * max(terminal_width - 40, 20) + '\n')
			else:
				# User not authenticated - show auth prompt
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('─' * max(terminal_width - 40, 20))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('🔐 To view this run in Browser Use Cloud, authenticate with:')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('    👉  browser-use auth')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('    or: python -m browser_use.cli auth')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('─' * max(terminal_width - 40, 20) + '\n')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Cloud sync authentication failed: {e}')

	# async def _update_wal_user_ids(self, session_id: str) -> None:
	# 	"""Update user IDs in WAL file after authentication"""
	# 	try:
	# 		assert self.auth_client, 'Cloud sync must be authenticated to update WAL user ID'

	# 		wal_path = CONFIG.BROWSER_USE_CONFIG_DIR / 'events' / f'{session_id}.jsonl'
	# 		if not await anyio.Path(wal_path).exists():
	# 			raise FileNotFoundError(
	# 				f'CloudSync failed to update saved event user_ids after auth: Agent EventBus WAL file not found: {wal_path}'
	# 			)

	# 		# Read all events
	# 		events = []
	# 		content = await anyio.Path(wal_path).read_text()
	# 		for line in content.splitlines():
	# 			if line.strip():
	# 				events.append(json.loads(line))

	# 		# Update user_id and device_id
	# 		user_id = self.auth_client.user_id
	# 		device_id = self.auth_client.device_id
	# 		for event in events:
	# 			if 'user_id' in event:
	# 				event['user_id'] = user_id
	# 			# Add device_id to all events
	# 			event['device_id'] = device_id

	# 		# Write back
	# 		updated_content = '\n'.join(json.dumps(event) for event in events) + '\n'
	# 		await anyio.Path(wal_path).write_text(updated_content)

	# 	except Exception as e:
	# 		logger.warning(f'Failed to update WAL user IDs: {e}')

	# EN: Define async function `wait_for_auth`.
	# JP: 非同期関数 `wait_for_auth` を定義する。
	async def wait_for_auth(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Wait for authentication to complete if in progress"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.auth_task and not self.auth_task.done():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.auth_task

	# EN: Define function `set_auth_flow_active`.
	# JP: 関数 `set_auth_flow_active` を定義する。
	def set_auth_flow_active(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Mark auth flow as active to allow all events"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.auth_flow_active = True

	# EN: Define async function `authenticate`.
	# JP: 非同期関数 `authenticate` を定義する。
	async def authenticate(self, show_instructions: bool = True) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Authenticate with the cloud service"""
		# If cloud sync is disabled, don't authenticate
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.enabled:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Check if already authenticated first
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.auth_client.is_authenticated:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import logging

			# EN: Assign value to logger.
			# JP: logger に値を代入する。
			logger = logging.getLogger(__name__)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if show_instructions:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('✅ Already authenticated! Skipping OAuth flow.')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Not authenticated - run OAuth flow
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await self.auth_client.authenticate(agent_session_id=self.session_id, show_instructions=show_instructions)

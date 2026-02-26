# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
OAuth2 Device Authorization Grant flow client for browser-use.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import shutil
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG

# Temporary user ID for pre-auth events (matches cloud backend)
# EN: Assign value to TEMP_USER_ID.
# JP: TEMP_USER_ID に値を代入する。
TEMP_USER_ID = '99999999-9999-9999-9999-999999999999'


# EN: Define function `get_or_create_device_id`.
# JP: 関数 `get_or_create_device_id` を定義する。
def get_or_create_device_id() -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Get or create a persistent device ID for this installation."""
	# EN: Assign value to device_id_path.
	# JP: device_id_path に値を代入する。
	device_id_path = CONFIG.BROWSER_USE_CONFIG_DIR / 'device_id'

	# Try to read existing device ID
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if device_id_path.exists():
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to device_id.
			# JP: device_id に値を代入する。
			device_id = device_id_path.read_text().strip()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if device_id:  # Make sure it's not empty
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return device_id
		except Exception:
			# If we can't read it, we'll create a new one
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass

	# Create new device ID
	# EN: Assign value to device_id.
	# JP: device_id に値を代入する。
	device_id = uuid7str()

	# Ensure config directory exists
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	CONFIG.BROWSER_USE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

	# Write device ID to file
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	device_id_path.write_text(device_id)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return device_id


# EN: Define class `CloudAuthConfig`.
# JP: クラス `CloudAuthConfig` を定義する。
class CloudAuthConfig(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Configuration for cloud authentication"""

	# EN: Assign annotated value to api_token.
	# JP: api_token に型付きの値を代入する。
	api_token: str | None = None
	# EN: Assign annotated value to user_id.
	# JP: user_id に型付きの値を代入する。
	user_id: str | None = None
	# EN: Assign annotated value to authorized_at.
	# JP: authorized_at に型付きの値を代入する。
	authorized_at: datetime | None = None

	# EN: Define function `load_from_file`.
	# JP: 関数 `load_from_file` を定義する。
	@classmethod
	def load_from_file(cls) -> 'CloudAuthConfig':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load auth config from local file"""

		# EN: Assign value to config_path.
		# JP: config_path に値を代入する。
		config_path = CONFIG.BROWSER_USE_CONFIG_DIR / 'cloud_auth.json'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if config_path.exists():
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with open(config_path) as f:
					# EN: Assign value to data.
					# JP: data に値を代入する。
					data = json.load(f)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return cls.model_validate(data)
			except Exception:
				# Return empty config if file is corrupted
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls()

	# EN: Define function `save_to_file`.
	# JP: 関数 `save_to_file` を定義する。
	def save_to_file(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Save auth config to local file"""

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		CONFIG.BROWSER_USE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

		# EN: Assign value to config_path.
		# JP: config_path に値を代入する。
		config_path = CONFIG.BROWSER_USE_CONFIG_DIR / 'cloud_auth.json'
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with open(config_path, 'w') as f:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			json.dump(self.model_dump(mode='json'), f, indent=2, default=str)

		# Set restrictive permissions (owner read/write only) for security
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			os.chmod(config_path, 0o600)
		except Exception:
			# Some systems may not support chmod, continue anyway
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass


# EN: Define class `DeviceAuthClient`.
# JP: クラス `DeviceAuthClient` を定義する。
class DeviceAuthClient:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Client for OAuth2 device authorization flow"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, base_url: str | None = None, http_client: httpx.AsyncClient | None = None):
		# Backend API URL for OAuth requests - can be passed directly or defaults to env var
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.base_url = base_url or CONFIG.BROWSER_USE_CLOUD_API_URL
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.client_id = 'library'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.scope = 'read write'

		# If no client provided, we'll create one per request
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.http_client = http_client

		# Temporary user ID for pre-auth events
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.temp_user_id = TEMP_USER_ID

		# Get or create persistent device ID
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.device_id = get_or_create_device_id()

		# Load existing auth if available
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.auth_config = CloudAuthConfig.load_from_file()

	# EN: Define function `is_authenticated`.
	# JP: 関数 `is_authenticated` を定義する。
	@property
	def is_authenticated(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if we have valid authentication"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return bool(self.auth_config.api_token and self.auth_config.user_id)

	# EN: Define function `api_token`.
	# JP: 関数 `api_token` を定義する。
	@property
	def api_token(self) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the current API token"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.auth_config.api_token

	# EN: Define function `user_id`.
	# JP: 関数 `user_id` を定義する。
	@property
	def user_id(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the current user ID (temporary or real)"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.auth_config.user_id or self.temp_user_id

	# EN: Define async function `start_device_authorization`.
	# JP: 非同期関数 `start_device_authorization` を定義する。
	async def start_device_authorization(
		self,
		agent_session_id: str | None = None,
	) -> dict:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Start the device authorization flow.
		Returns device authorization details including user code and verification URL.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.http_client:
			# EN: Assign value to response.
			# JP: response に値を代入する。
			response = await self.http_client.post(
				f'{self.base_url.rstrip("/")}/api/v1/oauth/device/authorize',
				data={
					'client_id': self.client_id,
					'scope': self.scope,
					'agent_session_id': agent_session_id or '',
					'device_id': self.device_id,
				},
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			response.raise_for_status()
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return response.json()
		else:
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with httpx.AsyncClient() as client:
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await client.post(
					f'{self.base_url.rstrip("/")}/api/v1/oauth/device/authorize',
					data={
						'client_id': self.client_id,
						'scope': self.scope,
						'agent_session_id': agent_session_id or '',
						'device_id': self.device_id,
					},
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				response.raise_for_status()
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return response.json()

	# EN: Define async function `poll_for_token`.
	# JP: 非同期関数 `poll_for_token` を定義する。
	async def poll_for_token(
		self,
		device_code: str,
		interval: float = 3.0,
		timeout: float = 1800.0,
	) -> dict | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Poll for the access token.
		Returns token info when authorized, None if timeout.
		"""
		# EN: Assign value to start_time.
		# JP: start_time に値を代入する。
		start_time = time.time()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.http_client:
			# Use injected client for all requests
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while time.time() - start_time < timeout:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to response.
					# JP: response に値を代入する。
					response = await self.http_client.post(
						f'{self.base_url.rstrip("/")}/api/v1/oauth/device/token',
						data={
							'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
							'device_code': device_code,
							'client_id': self.client_id,
						},
					)

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if response.status_code == 200:
						# EN: Assign value to data.
						# JP: data に値を代入する。
						data = response.json()

						# Check for pending authorization
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if data.get('error') == 'authorization_pending':
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await asyncio.sleep(interval)
							# EN: Continue to the next loop iteration.
							# JP: ループの次の反復に進む。
							continue

						# Check for slow down
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if data.get('error') == 'slow_down':
							# EN: Assign value to interval.
							# JP: interval に値を代入する。
							interval = data.get('interval', interval * 2)
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await asyncio.sleep(interval)
							# EN: Continue to the next loop iteration.
							# JP: ループの次の反復に進む。
							continue

						# Check for other errors
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if 'error' in data:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							print(f'Error: {data.get("error_description", data["error"])}')
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return None

						# Success! We have a token
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if 'access_token' in data:
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return data

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif response.status_code == 400:
						# Error response
						# EN: Assign value to data.
						# JP: data に値を代入する。
						data = response.json()
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if data.get('error') not in ['authorization_pending', 'slow_down']:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							print(f'Error: {data.get("error_description", "Unknown error")}')
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return None

					else:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						print(f'Unexpected status code: {response.status_code}')
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return None

				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					print(f'Error polling for token: {e}')

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(interval)
		else:
			# Create a new client for polling
			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with httpx.AsyncClient() as client:
				# EN: Repeat logic while a condition is true.
				# JP: 条件が真の間、処理を繰り返す。
				while time.time() - start_time < timeout:
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to response.
						# JP: response に値を代入する。
						response = await client.post(
							f'{self.base_url.rstrip("/")}/api/v1/oauth/device/token',
							data={
								'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
								'device_code': device_code,
								'client_id': self.client_id,
							},
						)

						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if response.status_code == 200:
							# EN: Assign value to data.
							# JP: data に値を代入する。
							data = response.json()

							# Check for pending authorization
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if data.get('error') == 'authorization_pending':
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								await asyncio.sleep(interval)
								# EN: Continue to the next loop iteration.
								# JP: ループの次の反復に進む。
								continue

							# Check for slow down
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if data.get('error') == 'slow_down':
								# EN: Assign value to interval.
								# JP: interval に値を代入する。
								interval = data.get('interval', interval * 2)
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								await asyncio.sleep(interval)
								# EN: Continue to the next loop iteration.
								# JP: ループの次の反復に進む。
								continue

							# Check for other errors
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if 'error' in data:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								print(f'Error: {data.get("error_description", data["error"])}')
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return None

							# Success! We have a token
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if 'access_token' in data:
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return data

						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif response.status_code == 400:
							# Error response
							# EN: Assign value to data.
							# JP: data に値を代入する。
							data = response.json()
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if data.get('error') not in ['authorization_pending', 'slow_down']:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								print(f'Error: {data.get("error_description", "Unknown error")}')
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return None

						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							print(f'Unexpected status code: {response.status_code}')
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return None

					except Exception as e:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						print(f'Error polling for token: {e}')

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await asyncio.sleep(interval)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `authenticate`.
	# JP: 非同期関数 `authenticate` を定義する。
	async def authenticate(
		self,
		agent_session_id: str | None = None,
		show_instructions: bool = True,
	) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Run the full authentication flow.
		Returns True if authentication successful.
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import logging

		# EN: Assign value to logger.
		# JP: logger に値を代入する。
		logger = logging.getLogger(__name__)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Start device authorization
			# EN: Assign value to device_auth.
			# JP: device_auth に値を代入する。
			device_auth = await self.start_device_authorization(agent_session_id)

			# Use frontend URL for user-facing links
			# EN: Assign value to frontend_url.
			# JP: frontend_url に値を代入する。
			frontend_url = CONFIG.BROWSER_USE_CLOUD_UI_URL or self.base_url.replace('//api.', '//cloud.')

			# Replace backend URL with frontend URL in verification URIs
			# EN: Assign value to verification_uri.
			# JP: verification_uri に値を代入する。
			verification_uri = device_auth['verification_uri'].replace(self.base_url, frontend_url)
			# EN: Assign value to verification_uri_complete.
			# JP: verification_uri_complete に値を代入する。
			verification_uri_complete = device_auth['verification_uri_complete'].replace(self.base_url, frontend_url)

			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			terminal_width, _terminal_height = shutil.get_terminal_size((80, 20))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if show_instructions and CONFIG.BROWSER_USE_CLOUD_SYNC:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('─' * max(terminal_width - 40, 20))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('🌐  View the details of this run in Browser Use Cloud:')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'    👉  {verification_uri_complete}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('─' * max(terminal_width - 40, 20) + '\n')

			# Poll for token
			# EN: Assign value to token_data.
			# JP: token_data に値を代入する。
			token_data = await self.poll_for_token(
				device_code=device_auth['device_code'],
				interval=device_auth.get('interval', 5),
			)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if token_data and token_data.get('access_token'):
				# Save authentication
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.auth_config.api_token = token_data['access_token']
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.auth_config.user_id = token_data.get('user_id', self.temp_user_id)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.auth_config.authorized_at = datetime.now()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.auth_config.save_to_file()

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if show_instructions:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug('✅  Authentication successful! Cloud sync is now enabled with your browser-use account.')

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

		except httpx.HTTPStatusError as e:
			# HTTP error with response
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if e.response.status_code == 404:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.warning(
					'Cloud sync authentication endpoint not found (404). Check your BROWSER_USE_CLOUD_API_URL setting.'
				)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.warning(f'Failed to authenticate with cloud service: HTTP {e.response.status_code} - {e.response.text}')
		except httpx.RequestError as e:
			# Connection/network errors
			# logger.warning(f'Failed to connect to cloud service: {type(e).__name__}: {e}')
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass
		except Exception as e:
			# Other unexpected errors
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(f'❌ Unexpected error during cloud sync authentication: {type(e).__name__}: {e}')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if show_instructions:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'❌ Sync authentication failed or timed out with {CONFIG.BROWSER_USE_CLOUD_API_URL}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `get_headers`.
	# JP: 関数 `get_headers` を定義する。
	def get_headers(self) -> dict:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get headers for API requests"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.api_token:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return {'Authorization': f'Bearer {self.api_token}'}
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {}

	# EN: Define function `clear_auth`.
	# JP: 関数 `clear_auth` を定義する。
	def clear_auth(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clear stored authentication"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.auth_config = CloudAuthConfig()

		# Remove the config file entirely instead of saving empty values
		# EN: Assign value to config_path.
		# JP: config_path に値を代入する。
		config_path = CONFIG.BROWSER_USE_CONFIG_DIR / 'cloud_auth.json'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		config_path.unlink(missing_ok=True)

# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Gmail API Service for Browser Use
Handles Gmail API authentication, email reading, and 2FA code extraction.
This service provides a clean interface for agents to interact with Gmail.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import base64
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import aiofiles
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from google.auth.transport.requests import Request
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from google.oauth2.credentials import Credentials
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from google_auth_oauthlib.flow import InstalledAppFlow
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from googleapiclient.discovery import build
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from googleapiclient.errors import HttpError

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define class `GmailService`.
# JP: クラス `GmailService` を定義する。
class GmailService:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Gmail API service for email reading.
	Provides functionality to:
	- Authenticate with Gmail API using OAuth2
	- Read recent emails with filtering
	- Return full email content for agent analysis
	"""

	# Gmail API scopes
	# EN: Assign value to SCOPES.
	# JP: SCOPES に値を代入する。
	SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		credentials_file: str | None = None,
		token_file: str | None = None,
		config_dir: str | None = None,
		access_token: str | None = None,
	):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Initialize Gmail Service
		Args:
		    credentials_file: Path to OAuth credentials JSON from Google Cloud Console
		    token_file: Path to store/load access tokens
		    config_dir: Directory to store config files (defaults to browser-use config directory)
		    access_token: Direct access token (skips file-based auth if provided)
		"""
		# Set up configuration directory using browser-use's config system
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if config_dir is None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.config_dir = CONFIG.BROWSER_USE_CONFIG_DIR
		else:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.config_dir = Path(config_dir).expanduser().resolve()

		# Ensure config directory exists (only if not using direct token)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if access_token is None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.config_dir.mkdir(parents=True, exist_ok=True)

		# Set up credential paths
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.credentials_file = credentials_file or self.config_dir / 'gmail_credentials.json'
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.token_file = token_file or self.config_dir / 'gmail_token.json'

		# Direct access token support
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.access_token = access_token

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.service = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.creds = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._authenticated = False

	# EN: Define function `is_authenticated`.
	# JP: 関数 `is_authenticated` を定義する。
	def is_authenticated(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if Gmail service is authenticated"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._authenticated and self.service is not None

	# EN: Define async function `authenticate`.
	# JP: 非同期関数 `authenticate` を定義する。
	async def authenticate(self) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Handle OAuth authentication and token management
		Returns:
		    bool: True if authentication successful, False otherwise
		"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('🔐 Authenticating with Gmail API...')

			# Check if using direct access token
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.access_token:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('🔑 Using provided access token')
				# Create credentials from access token
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.creds = Credentials(token=self.access_token, scopes=self.SCOPES)
				# Test token validity by building service
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.service = build('gmail', 'v1', credentials=self.creds)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._authenticated = True
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('✅ Gmail API ready with access token!')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True

			# Original file-based authentication flow
			# Try to load existing tokens
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if os.path.exists(self.token_file):
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.creds = Credentials.from_authorized_user_file(str(self.token_file), self.SCOPES)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('📁 Loaded existing tokens')

			# If no valid credentials, run OAuth flow
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.creds or not self.creds.valid:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.creds and self.creds.expired and self.creds.refresh_token:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info('🔄 Refreshing expired tokens...')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.creds.refresh(Request())
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info('🌐 Starting OAuth flow...')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if not os.path.exists(self.credentials_file):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.error(
							f'❌ Gmail credentials file not found: {self.credentials_file}\n'
							'Please download it from Google Cloud Console:\n'
							'1. Go to https://console.cloud.google.com/\n'
							'2. APIs & Services > Credentials\n'
							'3. Download OAuth 2.0 Client JSON\n'
							f"4. Save as 'gmail_credentials.json' in {self.config_dir}/"
						)
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return False

					# EN: Assign value to flow.
					# JP: flow に値を代入する。
					flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), self.SCOPES)
					# Use specific redirect URI to match OAuth credentials
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.creds = flow.run_local_server(port=8080, open_browser=True)

				# Save tokens for next time
				# EN: Execute async logic with managed resources.
				# JP: リソース管理付きで非同期処理を実行する。
				async with aiofiles.open(self.token_file, 'w') as token:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await token.write(self.creds.to_json())
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'💾 Tokens saved to {self.token_file}')

			# Build Gmail service
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.service = build('gmail', 'v1', credentials=self.creds)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._authenticated = True
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('✅ Gmail API ready!')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'❌ Gmail authentication failed: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# EN: Define async function `get_recent_emails`.
	# JP: 非同期関数 `get_recent_emails` を定義する。
	async def get_recent_emails(self, max_results: int = 10, query: str = '', time_filter: str = '1h') -> list[dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Get recent emails with optional query filter
		Args:
		    max_results: Maximum number of emails to fetch
		    query: Gmail search query (e.g., 'from:noreply@example.com')
		    time_filter: Time filter (e.g., '5m', '1h', '1d')
		Returns:
		    List of email dictionaries with parsed content
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.is_authenticated():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error('❌ Gmail service not authenticated. Call authenticate() first.')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Add time filter to query if provided
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if time_filter and 'newer_than:' not in query:
				# EN: Assign value to query.
				# JP: query に値を代入する。
				query = f'newer_than:{time_filter} {query}'.strip()

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'📧 Fetching {max_results} recent emails...')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if query:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'🔍 Query: {query}')

			# Get message list
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.service is not None
			# EN: Assign value to results.
			# JP: results に値を代入する。
			results = self.service.users().messages().list(userId='me', maxResults=max_results, q=query).execute()

			# EN: Assign value to messages.
			# JP: messages に値を代入する。
			messages = results.get('messages', [])
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not messages:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('📭 No messages found')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return []

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'📨 Found {len(messages)} messages, fetching details...')

			# Get full message details
			# EN: Assign value to emails.
			# JP: emails に値を代入する。
			emails = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, message in enumerate(messages, 1):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'📖 Reading email {i}/{len(messages)}...')

				# EN: Assign value to full_message.
				# JP: full_message に値を代入する。
				full_message = self.service.users().messages().get(userId='me', id=message['id'], format='full').execute()

				# EN: Assign value to email_data.
				# JP: email_data に値を代入する。
				email_data = self._parse_email(full_message)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				emails.append(email_data)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return emails

		except HttpError as error:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'❌ Gmail API error: {error}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'❌ Unexpected error fetching emails: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return []

	# EN: Define function `_parse_email`.
	# JP: 関数 `_parse_email` を定義する。
	def _parse_email(self, message: dict[str, Any]) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Parse Gmail message into readable format"""
		# EN: Assign value to headers.
		# JP: headers に値を代入する。
		headers = {h['name']: h['value'] for h in message['payload']['headers']}

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'id': message['id'],
			'thread_id': message['threadId'],
			'subject': headers.get('Subject', ''),
			'from': headers.get('From', ''),
			'to': headers.get('To', ''),
			'date': headers.get('Date', ''),
			'timestamp': int(message['internalDate']),
			'body': self._extract_body(message['payload']),
			'raw_message': message,
		}

	# EN: Define function `_extract_body`.
	# JP: 関数 `_extract_body` を定義する。
	def _extract_body(self, payload: dict[str, Any]) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract email body from payload"""
		# EN: Assign value to body.
		# JP: body に値を代入する。
		body = ''

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if payload.get('body', {}).get('data'):
			# Simple email body
			# EN: Assign value to body.
			# JP: body に値を代入する。
			body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif payload.get('parts'):
			# Multi-part email
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for part in payload['parts']:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if part['mimeType'] == 'text/plain' and part.get('body', {}).get('data'):
					# EN: Assign value to part_body.
					# JP: part_body に値を代入する。
					part_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					body += part_body
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif part['mimeType'] == 'text/html' and not body and part.get('body', {}).get('data'):
					# Fallback to HTML if no plain text
					# EN: Assign value to body.
					# JP: body に値を代入する。
					body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return body

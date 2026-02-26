# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Gmail Actions for Browser Use
Defines agent actions for Gmail integration including 2FA code retrieval,
email reading, and authentication management.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, Field

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.views import ActionResult
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.service import Tools

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .service import GmailService

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)

# Global Gmail service instance - initialized when actions are registered
# EN: Assign annotated value to _gmail_service.
# JP: _gmail_service に型付きの値を代入する。
_gmail_service: GmailService | None = None


# EN: Define class `GetRecentEmailsParams`.
# JP: クラス `GetRecentEmailsParams` を定義する。
class GetRecentEmailsParams(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Parameters for getting recent emails"""

	# EN: Assign annotated value to keyword.
	# JP: keyword に型付きの値を代入する。
	keyword: str = Field(default='', description='A single keyword for search, e.g. github, airbnb, etc.')
	# EN: Assign annotated value to max_results.
	# JP: max_results に型付きの値を代入する。
	max_results: int = Field(default=3, ge=1, le=50, description='Maximum number of emails to retrieve (1-50, default: 3)')


# EN: Define function `register_gmail_actions`.
# JP: 関数 `register_gmail_actions` を定義する。
def register_gmail_actions(tools: Tools, gmail_service: GmailService | None = None, access_token: str | None = None) -> Tools:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Register Gmail actions with the provided tools
	Args:
	    tools: The browser-use tools to register actions with
	    gmail_service: Optional pre-configured Gmail service instance
	    access_token: Optional direct access token (alternative to file-based auth)
	"""
	# EN: Execute this statement.
	# JP: この文を実行する。
	global _gmail_service

	# Use provided service or create a new one with access token if provided
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if gmail_service:
		# EN: Assign value to _gmail_service.
		# JP: _gmail_service に値を代入する。
		_gmail_service = gmail_service
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif access_token:
		# EN: Assign value to _gmail_service.
		# JP: _gmail_service に値を代入する。
		_gmail_service = GmailService(access_token=access_token)
	else:
		# EN: Assign value to _gmail_service.
		# JP: _gmail_service に値を代入する。
		_gmail_service = GmailService()

	# EN: Define async function `get_recent_emails`.
	# JP: 非同期関数 `get_recent_emails` を定義する。
	@tools.registry.action(
		description='Get recent emails from the mailbox with a keyword to retrieve verification codes, OTP, 2FA tokens, magic links, or any recent email content. Keep your query a single keyword.',
		param_model=GetRecentEmailsParams,
	)
	async def get_recent_emails(params: GetRecentEmailsParams) -> ActionResult:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get recent emails from the last 5 minutes with full content"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if _gmail_service is None:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError('Gmail service not initialized')

			# Ensure authentication
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not _gmail_service.is_authenticated():
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info('📧 Gmail not authenticated, attempting authentication...')
				# EN: Assign value to authenticated.
				# JP: authenticated に値を代入する。
				authenticated = await _gmail_service.authenticate()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not authenticated:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ActionResult(
						extracted_content='Failed to authenticate with Gmail. Please ensure Gmail credentials are set up properly.',
						long_term_memory='Gmail authentication failed',
					)

			# Use specified max_results (1-50, default 10), last 5 minutes
			# EN: Assign value to max_results.
			# JP: max_results に値を代入する。
			max_results = params.max_results
			# EN: Assign value to time_filter.
			# JP: time_filter に値を代入する。
			time_filter = '5m'

			# Build query with time filter and optional user query
			# EN: Assign value to query_parts.
			# JP: query_parts に値を代入する。
			query_parts = [f'newer_than:{time_filter}']
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if params.keyword.strip():
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				query_parts.append(params.keyword.strip())

			# EN: Assign value to query.
			# JP: query に値を代入する。
			query = ' '.join(query_parts)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'🔍 Gmail search query: {query}')

			# Get emails
			# EN: Assign value to emails.
			# JP: emails に値を代入する。
			emails = await _gmail_service.get_recent_emails(max_results=max_results, query=query, time_filter=time_filter)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not emails:
				# EN: Assign value to query_info.
				# JP: query_info に値を代入する。
				query_info = f" matching '{params.keyword}'" if params.keyword.strip() else ''
				# EN: Assign value to memory.
				# JP: memory に値を代入する。
				memory = f'No recent emails found from last {time_filter}{query_info}'
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ActionResult(
					extracted_content=memory,
					long_term_memory=memory,
				)

			# Format with full email content for large display
			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = f'Found {len(emails)} recent email{"s" if len(emails) > 1 else ""} from the last {time_filter}:\n\n'

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, email in enumerate(emails, 1):
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				content += f'Email {i}:\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				content += f'From: {email["from"]}\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				content += f'Subject: {email["subject"]}\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				content += f'Date: {email["date"]}\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				content += f'Content:\n{email["body"]}\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				content += '-' * 50 + '\n\n'

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'📧 Retrieved {len(emails)} recent emails')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				extracted_content=content,
				include_extracted_content_only_once=True,
				long_term_memory=f'Retrieved {len(emails)} recent emails from last {time_filter} for query {query}.',
			)

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Error getting recent emails: {e}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ActionResult(
				error=f'Error getting recent emails: {str(e)}',
				long_term_memory='Failed to get recent emails due to error',
			)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return tools

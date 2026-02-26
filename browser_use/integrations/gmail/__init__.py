# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Gmail Integration for Browser Use
Provides Gmail API integration for email reading and verification code extraction.
This integration enables agents to read email content and extract verification codes themselves.
Usage:
    from browser_use.integrations.gmail import GmailService, register_gmail_actions
    # Option 1: Register Gmail actions with file-based authentication
    tools = Tools()
    register_gmail_actions(tools)
    # Option 2: Register Gmail actions with direct access token (recommended for production)
    tools = Tools()
    register_gmail_actions(tools, access_token="your_access_token_here")
    # Option 3: Use the service directly
    gmail = GmailService(access_token="your_access_token_here")
    await gmail.authenticate()
    emails = await gmail.get_recent_emails()
"""

# @file purpose: Gmail integration for 2FA email authentication and email reading

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .actions import register_gmail_actions
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .service import GmailService

# EN: Assign value to __all__.
# JP: __all__ に値を代入する。
__all__ = ['GmailService', 'register_gmail_actions']

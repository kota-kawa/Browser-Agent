# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""MCP (Model Context Protocol) support for browser-use.

This module provides integration with MCP servers and clients for browser automation.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.mcp.client import MCPClient
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.mcp.controller import MCPToolWrapper

# EN: Assign value to __all__.
# JP: __all__ に値を代入する。
__all__ = ['MCPClient', 'MCPToolWrapper', 'BrowserUseServer']  # type: ignore


# EN: Define function `__getattr__`.
# JP: 関数 `__getattr__` を定義する。
def __getattr__(name):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Lazy import to avoid importing server module when only client is needed."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if name == 'BrowserUseServer':
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.mcp.server import BrowserUseServer

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return BrowserUseServer
	# EN: Raise an exception.
	# JP: 例外を送出する。
	raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

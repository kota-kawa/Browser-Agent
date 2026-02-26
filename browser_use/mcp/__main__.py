# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Entry point for running MCP server as a module.

Usage:
    python -m browser_use.mcp
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.mcp.server import main

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(main())

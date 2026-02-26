# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Permissions watchdog for granting browser permissions on connection."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import BrowserConnectedEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `PermissionsWatchdog`.
# JP: クラス `PermissionsWatchdog` を定義する。
class PermissionsWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Grants browser permissions when browser connects."""

	# Event contracts
	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [
		BrowserConnectedEvent,
	]
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent]]] = []

	# EN: Define async function `on_BrowserConnectedEvent`.
	# JP: 非同期関数 `on_BrowserConnectedEvent` を定義する。
	async def on_BrowserConnectedEvent(self, event: BrowserConnectedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Grant permissions when browser connects."""
		# EN: Assign value to permissions.
		# JP: permissions に値を代入する。
		permissions = self.browser_session.browser_profile.permissions

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not permissions:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('No permissions to grant')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🔓 Granting browser permissions: {permissions}')

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Grant permissions using CDP Browser.grantPermissions
			# origin=None means grant to all origins
			# Browser domain commands don't use session_id
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self.browser_session.cdp_client.send.Browser.grantPermissions(
				params={'permissions': permissions}  # type: ignore
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'✅ Successfully granted permissions: {permissions}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'❌ Failed to grant permissions: {str(e)}')
			# Don't raise - permissions are not critical to browser operation

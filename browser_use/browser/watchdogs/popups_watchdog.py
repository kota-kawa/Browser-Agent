# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Watchdog for handling JavaScript dialogs (alert, confirm, prompt) automatically."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import PrivateAttr

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import TabCreatedEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog


# EN: Define class `PopupsWatchdog`.
# JP: クラス `PopupsWatchdog` を定義する。
class PopupsWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Handles JavaScript dialogs (alert, confirm, prompt) by automatically accepting them immediately."""

	# Events this watchdog listens to and emits
	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [TabCreatedEvent]
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent]]] = []

	# Track which targets have dialog handlers registered
	# EN: Assign annotated value to _dialog_listeners_registered.
	# JP: _dialog_listeners_registered に型付きの値を代入する。
	_dialog_listeners_registered: set[str] = PrivateAttr(default_factory=set)

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, **kwargs):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__(**kwargs)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🚀 PopupsWatchdog initialized with browser_session={self.browser_session}, ID={id(self)}')

	# EN: Define async function `on_TabCreatedEvent`.
	# JP: 非同期関数 `on_TabCreatedEvent` を定義する。
	async def on_TabCreatedEvent(self, event: TabCreatedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set up JavaScript dialog handling when a new tab is created."""
		# EN: Assign value to target_id.
		# JP: target_id に値を代入する。
		target_id = event.target_id
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'🎯 PopupsWatchdog received TabCreatedEvent for target {target_id}')

		# Skip if we've already registered for this target
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if target_id in self._dialog_listeners_registered:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Already registered dialog handlers for target {target_id}')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug(f'📌 Starting dialog handler setup for target {target_id}')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Get all CDP sessions for this target and any child frames
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await self.browser_session.get_or_create_cdp_session(
				target_id, focus=False
			)  # don't auto-focus new tabs! sometimes we need to open tabs in background

			# Also register for the root CDP client to catch dialogs from any frame
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.browser_session._cdp_client_root:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug('📌 Also registering handler on root CDP client')

			# Set up async handler for JavaScript dialogs - accept immediately without event dispatch
			# EN: Define async function `handle_dialog`.
			# JP: 非同期関数 `handle_dialog` を定義する。
			async def handle_dialog(event_data, session_id: str | None = None):
				# EN: Describe this block with a docstring.
				# JP: このブロックの説明をドキュメント文字列で記述する。
				"""Handle JavaScript dialog events - accept immediately."""
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to dialog_type.
					# JP: dialog_type に値を代入する。
					dialog_type = event_data.get('type', 'alert')
					# EN: Assign value to message.
					# JP: message に値を代入する。
					message = event_data.get('message', '')

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.info(f"🔔 JavaScript {dialog_type} dialog: '{message[:100]}' - attempting to accept...")

					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('Trying all approaches to accept dialog...')

					# Approach 1: Use the session that detected the dialog
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self.browser_session._cdp_client_root and session_id:
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug(f'🔄 Approach 1: Using session {session_id}')
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await asyncio.wait_for(
								self.browser_session._cdp_client_root.send.Page.handleJavaScriptDialog(
									params={'accept': True},
									session_id=session_id,
								),
								timeout=0.25,
							)
						except (TimeoutError, Exception) as e:
							# EN: Keep a placeholder statement.
							# JP: プレースホルダー文を維持する。
							pass

					# Approach 2: Try with current agent focus session
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if self.browser_session._cdp_client_root and self.browser_session.agent_focus:
						# EN: Handle exceptions around this block.
						# JP: このブロックで例外処理を行う。
						try:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							self.logger.debug(
								f'🔄 Approach 2: Using agent focus session {self.browser_session.agent_focus.session_id}'
							)
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await asyncio.wait_for(
								self.browser_session._cdp_client_root.send.Page.handleJavaScriptDialog(
									params={'accept': True},
									session_id=self.browser_session.agent_focus.session_id,
								),
								timeout=0.25,
							)
						except (TimeoutError, Exception) as e:
							# EN: Keep a placeholder statement.
							# JP: プレースホルダー文を維持する。
							pass

				except Exception as e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.error(f'❌ Critical error in dialog handler: {type(e).__name__}: {e}')

			# Register handler on the specific session
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cdp_session.cdp_client.register.Page.javascriptDialogOpening(handle_dialog)  # type: ignore[arg-type]
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(
				f'Successfully registered Page.javascriptDialogOpening handler for session {cdp_session.session_id}'
			)

			# Also register on root CDP client to catch dialogs from any frame
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if hasattr(self.browser_session._cdp_client_root, 'register'):
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.browser_session._cdp_client_root.register.Page.javascriptDialogOpening(handle_dialog)  # type: ignore[arg-type]
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug('Successfully registered dialog handler on root CDP client for all frames')
				except Exception as root_error:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'Failed to register on root CDP client: {root_error}')

			# Mark this target as having dialog handling set up
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._dialog_listeners_registered.add(target_id)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Set up JavaScript dialog handling for tab {target_id}')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'Failed to set up popup handling for tab {target_id}: {e}')

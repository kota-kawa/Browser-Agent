# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from posthog import Posthog
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.env_loader import load_secrets_env
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.telemetry.views import BaseTelemetryEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import singleton

# EN: Evaluate an expression.
# JP: 式を評価する。
load_secrets_env()

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Assign value to POSTHOG_EVENT_SETTINGS.
# JP: POSTHOG_EVENT_SETTINGS に値を代入する。
POSTHOG_EVENT_SETTINGS = {
	'process_person_profile': True,
}


# EN: Define class `ProductTelemetry`.
# JP: クラス `ProductTelemetry` を定義する。
@singleton
class ProductTelemetry:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Service for capturing anonymized telemetry data.

	If the environment variable `ANONYMIZED_TELEMETRY=False`, anonymized telemetry will be disabled.
	"""

	# EN: Assign value to USER_ID_PATH.
	# JP: USER_ID_PATH に値を代入する。
	USER_ID_PATH = str(CONFIG.BROWSER_USE_CONFIG_DIR / 'device_id')
	# EN: Assign value to PROJECT_API_KEY.
	# JP: PROJECT_API_KEY に値を代入する。
	PROJECT_API_KEY = os.getenv('BROWSER_USE_TELEMETRY_KEY', 'phc_F8JMNjW1i2KbGUTaW1unnDdLSPCoyc52SGRU0JecaUh')
	# EN: Assign value to HOST.
	# JP: HOST に値を代入する。
	HOST = 'https://eu.i.posthog.com'
	# EN: Assign value to UNKNOWN_USER_ID.
	# JP: UNKNOWN_USER_ID に値を代入する。
	UNKNOWN_USER_ID = 'UNKNOWN'

	# EN: Assign value to _curr_user_id.
	# JP: _curr_user_id に値を代入する。
	_curr_user_id = None

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self) -> None:
		# EN: Assign value to telemetry_disabled.
		# JP: telemetry_disabled に値を代入する。
		telemetry_disabled = not CONFIG.ANONYMIZED_TELEMETRY
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.debug_logging = CONFIG.BROWSER_USE_LOGGING_LEVEL == 'debug'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if telemetry_disabled:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._posthog_client = None
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('Using anonymized telemetry, see https://docs.browser-use.com/development/telemetry.')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._posthog_client = Posthog(
				project_api_key=self.PROJECT_API_KEY,
				host=self.HOST,
				disable_geoip=False,
				enable_exception_autocapture=True,
			)

			# Silence posthog's logging
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not self.debug_logging:
				# EN: Assign value to posthog_logger.
				# JP: posthog_logger に値を代入する。
				posthog_logger = logging.getLogger('posthog')
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				posthog_logger.disabled = True

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._posthog_client is None:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('Telemetry disabled')

	# EN: Define function `capture`.
	# JP: 関数 `capture` を定義する。
	def capture(self, event: BaseTelemetryEvent) -> None:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._posthog_client is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._direct_capture(event)

	# EN: Define function `_direct_capture`.
	# JP: 関数 `_direct_capture` を定義する。
	def _direct_capture(self, event: BaseTelemetryEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Should not be thread blocking because posthog magically handles it
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._posthog_client is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._posthog_client.capture(
				distinct_id=self.user_id,
				event=event.name,
				properties={**event.properties, **POSTHOG_EVENT_SETTINGS},
			)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Failed to send telemetry event {event.name}: {e}')

	# EN: Define function `flush`.
	# JP: 関数 `flush` を定義する。
	def flush(self) -> None:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._posthog_client:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._posthog_client.flush()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('PostHog client telemetry queue flushed.')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error(f'Failed to flush PostHog client: {e}')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('PostHog client not available, skipping flush.')

	# EN: Define function `user_id`.
	# JP: 関数 `user_id` を定義する。
	@property
	def user_id(self) -> str:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._curr_user_id:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._curr_user_id

		# File access may fail due to permissions or other reasons. We don't want to
		# crash so we catch all exceptions.
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not os.path.exists(self.USER_ID_PATH):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				os.makedirs(os.path.dirname(self.USER_ID_PATH), exist_ok=True)
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with open(self.USER_ID_PATH, 'w') as f:
					# EN: Assign value to new_user_id.
					# JP: new_user_id に値を代入する。
					new_user_id = uuid7str()
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					f.write(new_user_id)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self._curr_user_id = new_user_id
			else:
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with open(self.USER_ID_PATH) as f:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self._curr_user_id = f.read()
		except Exception:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._curr_user_id = 'UNKNOWN_USER_ID'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._curr_user_id

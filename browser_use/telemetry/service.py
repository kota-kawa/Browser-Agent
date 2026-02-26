import logging
import os

from posthog import Posthog
from uuid_extensions import uuid7str

from browser_use.env_loader import load_secrets_env
from browser_use.telemetry.views import BaseTelemetryEvent
from browser_use.utils import singleton

load_secrets_env()

from browser_use.config import CONFIG

logger = logging.getLogger(__name__)


POSTHOG_EVENT_SETTINGS = {
	'process_person_profile': True,
}


# EN: Define class `ProductTelemetry`.
# JP: クラス `ProductTelemetry` を定義する。
@singleton
class ProductTelemetry:
	"""
	Service for capturing anonymized telemetry data.

	If the environment variable `ANONYMIZED_TELEMETRY=False`, anonymized telemetry will be disabled.
	"""

	USER_ID_PATH = str(CONFIG.BROWSER_USE_CONFIG_DIR / 'device_id')
	PROJECT_API_KEY = os.getenv('BROWSER_USE_TELEMETRY_KEY', 'phc_F8JMNjW1i2KbGUTaW1unnDdLSPCoyc52SGRU0JecaUh')
	HOST = 'https://eu.i.posthog.com'
	UNKNOWN_USER_ID = 'UNKNOWN'

	_curr_user_id = None

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self) -> None:
		telemetry_disabled = not CONFIG.ANONYMIZED_TELEMETRY
		self.debug_logging = CONFIG.BROWSER_USE_LOGGING_LEVEL == 'debug'

		if telemetry_disabled:
			self._posthog_client = None
		else:
			logger.info('Using anonymized telemetry, see https://docs.browser-use.com/development/telemetry.')
			self._posthog_client = Posthog(
				project_api_key=self.PROJECT_API_KEY,
				host=self.HOST,
				disable_geoip=False,
				enable_exception_autocapture=True,
			)

			# Silence posthog's logging
			if not self.debug_logging:
				posthog_logger = logging.getLogger('posthog')
				posthog_logger.disabled = True

		if self._posthog_client is None:
			logger.debug('Telemetry disabled')

	# EN: Define function `capture`.
	# JP: 関数 `capture` を定義する。
	def capture(self, event: BaseTelemetryEvent) -> None:
		if self._posthog_client is None:
			return

		self._direct_capture(event)

	# EN: Define function `_direct_capture`.
	# JP: 関数 `_direct_capture` を定義する。
	def _direct_capture(self, event: BaseTelemetryEvent) -> None:
		"""
		Should not be thread blocking because posthog magically handles it
		"""
		if self._posthog_client is None:
			return

		try:
			self._posthog_client.capture(
				distinct_id=self.user_id,
				event=event.name,
				properties={**event.properties, **POSTHOG_EVENT_SETTINGS},
			)
		except Exception as e:
			logger.error(f'Failed to send telemetry event {event.name}: {e}')

	# EN: Define function `flush`.
	# JP: 関数 `flush` を定義する。
	def flush(self) -> None:
		if self._posthog_client:
			try:
				self._posthog_client.flush()
				logger.debug('PostHog client telemetry queue flushed.')
			except Exception as e:
				logger.error(f'Failed to flush PostHog client: {e}')
		else:
			logger.debug('PostHog client not available, skipping flush.')

	# EN: Define function `user_id`.
	# JP: 関数 `user_id` を定義する。
	@property
	def user_id(self) -> str:
		if self._curr_user_id:
			return self._curr_user_id

		# File access may fail due to permissions or other reasons. We don't want to
		# crash so we catch all exceptions.
		try:
			if not os.path.exists(self.USER_ID_PATH):
				os.makedirs(os.path.dirname(self.USER_ID_PATH), exist_ok=True)
				with open(self.USER_ID_PATH, 'w') as f:
					new_user_id = uuid7str()
					f.write(new_user_id)
				self._curr_user_id = new_user_id
			else:
				with open(self.USER_ID_PATH) as f:
					self._curr_user_id = f.read()
		except Exception:
			self._curr_user_id = 'UNKNOWN_USER_ID'
		return self._curr_user_id

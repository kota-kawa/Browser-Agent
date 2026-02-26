# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Security watchdog for enforcing URL access policies."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	BrowserErrorEvent,
	NavigateToUrlEvent,
	NavigationCompleteEvent,
	TabCreatedEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import is_new_tab_page

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass

# Track if we've shown the glob warning
# EN: Assign value to _GLOB_WARNING_SHOWN.
# JP: _GLOB_WARNING_SHOWN に値を代入する。
_GLOB_WARNING_SHOWN = False


# EN: Define class `SecurityWatchdog`.
# JP: クラス `SecurityWatchdog` を定義する。
class SecurityWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Monitors and enforces security policies for URL access."""

	# Event contracts
	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [
		NavigateToUrlEvent,
		NavigationCompleteEvent,
		TabCreatedEvent,
	]
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent]]] = [
		BrowserErrorEvent,
	]

	# EN: Define async function `on_NavigateToUrlEvent`.
	# JP: 非同期関数 `on_NavigateToUrlEvent` を定義する。
	async def on_NavigateToUrlEvent(self, event: NavigateToUrlEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if navigation URL is allowed before navigation starts."""
		# Security check BEFORE navigation
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_url_allowed(event.url):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'⛔️ Blocking navigation to disallowed URL: {event.url}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='NavigationBlocked',
					message=f'Navigation blocked to disallowed URL: {event.url}',
					details={'url': event.url, 'reason': 'not_in_allowed_domains'},
				)
			)
			# Stop event propagation by raising exception
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Navigation to {event.url} blocked by security policy')

	# EN: Define async function `on_NavigationCompleteEvent`.
	# JP: 非同期関数 `on_NavigationCompleteEvent` を定義する。
	async def on_NavigationCompleteEvent(self, event: NavigationCompleteEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if navigated URL is allowed and close tab if not."""
		# Check if the navigated URL is allowed (in case of redirects)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_url_allowed(event.url):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'⛔️ Navigation to non-allowed URL detected: {event.url}')

			# Dispatch browser error
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='NavigationBlocked',
					message=f'Navigation to non-allowed URL: {event.url}',
					details={'url': event.url, 'target_id': event.target_id},
				)
			)

			# Close the target that navigated to the disallowed URL
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.browser_session._cdp_close_page(event.target_id)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'⛔️ Closed target with non-allowed URL: {event.url}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(f'⛔️ Failed to close target with non-allowed URL: {type(e).__name__} {e}')

	# EN: Define async function `on_TabCreatedEvent`.
	# JP: 非同期関数 `on_TabCreatedEvent` を定義する。
	async def on_TabCreatedEvent(self, event: TabCreatedEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if new tab URL is allowed."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_url_allowed(event.url):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(f'⛔️ New tab created with disallowed URL: {event.url}')

			# Dispatch error and try to close the tab
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='TabCreationBlocked',
					message=f'Tab created with non-allowed URL: {event.url}',
					details={'url': event.url, 'target_id': event.target_id},
				)
			)

			# Try to close the offending tab
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self.browser_session._cdp_close_page(event.target_id)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.info(f'⛔️ Closed new tab with non-allowed URL: {event.url}')
			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.error(f'⛔️ Failed to close new tab with non-allowed URL: {type(e).__name__} {e}')

	# EN: Define function `_is_root_domain`.
	# JP: 関数 `_is_root_domain` を定義する。
	def _is_root_domain(self, domain: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if a domain is a root domain (no subdomain present).

		Simple heuristic: only add www for domains with exactly 1 dot (domain.tld).
		For complex cases like country TLDs or subdomains, users should configure explicitly.

		Args:
			domain: The domain to check

		Returns:
			True if it's a simple root domain, False otherwise
		"""
		# Skip if it contains wildcards or protocol
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if '*' in domain or '://' in domain:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return domain.count('.') == 1

	# EN: Define function `_log_glob_warning`.
	# JP: 関数 `_log_glob_warning` を定義する。
	def _log_glob_warning(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log a warning about glob patterns in allowed_domains."""
		# EN: Execute this statement.
		# JP: この文を実行する。
		global _GLOB_WARNING_SHOWN
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not _GLOB_WARNING_SHOWN:
			# EN: Assign value to _GLOB_WARNING_SHOWN.
			# JP: _GLOB_WARNING_SHOWN に値を代入する。
			_GLOB_WARNING_SHOWN = True
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.warning(
				'⚠️ Using glob patterns in allowed_domains. '
				'Note: Patterns like "*.example.com" will match both subdomains AND the main domain.'
			)

	# EN: Define function `_is_url_allowed`.
	# JP: 関数 `_is_url_allowed` を定義する。
	def _is_url_allowed(self, url: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if a URL is allowed based on the allowed_domains configuration.

		Args:
			url: The URL to check

		Returns:
			True if the URL is allowed, False otherwise
		"""

		# If no allowed_domains specified, allow all URLs
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if (
			not self.browser_session.browser_profile.allowed_domains
			and not self.browser_session.browser_profile.prohibited_domains
		):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Always allow internal browser targets
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if is_new_tab_page(url):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Parse the URL to extract components
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from urllib.parse import urlparse

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to parsed.
			# JP: parsed に値を代入する。
			parsed = urlparse(url)
		except Exception:
			# Invalid URL
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Get the actual host (domain)
		# EN: Assign value to host.
		# JP: host に値を代入する。
		host = parsed.hostname
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not host:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Check each allowed domain pattern
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session.browser_profile.allowed_domains:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for pattern in self.browser_session.browser_profile.allowed_domains:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._is_url_match(url, host, parsed.scheme, pattern):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# Check each prohibited domain pattern
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session.browser_profile.prohibited_domains:
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for pattern in self.browser_session.browser_profile.prohibited_domains:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._is_url_match(url, host, parsed.scheme, pattern):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return False

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True

	# EN: Define function `_is_url_match`.
	# JP: 関数 `_is_url_match` を定義する。
	def _is_url_match(self, url: str, host: str, scheme: str, pattern: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if a URL matches a pattern."""

		# Full URL for matching (scheme + host)
		# EN: Assign value to full_url_pattern.
		# JP: full_url_pattern に値を代入する。
		full_url_pattern = f'{scheme}://{host}'

		# Handle glob patterns
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if '*' in pattern:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._log_glob_warning()
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import fnmatch

			# Check if pattern matches the host
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if pattern.startswith('*.'):
				# Pattern like *.example.com should match subdomains and main domain
				# EN: Assign value to domain_part.
				# JP: domain_part に値を代入する。
				domain_part = pattern[2:]  # Remove *.
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if host == domain_part or host.endswith('.' + domain_part):
					# Only match http/https URLs for domain-only patterns
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if scheme in ['http', 'https']:
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return True
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif pattern.endswith('/*'):
				# Pattern like brave://* should match any brave:// URL
				# EN: Assign value to prefix.
				# JP: prefix に値を代入する。
				prefix = pattern[:-1]  # Remove the * at the end
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if url.startswith(prefix):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True
			else:
				# Use fnmatch for other glob patterns
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if fnmatch.fnmatch(
					full_url_pattern if '://' in pattern else host,
					pattern,
				):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True
		else:
			# Exact match
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if '://' in pattern:
				# Full URL pattern
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if url.startswith(pattern):
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True
			else:
				# Domain-only pattern (case-insensitive comparison)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if host.lower() == pattern.lower():
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True
				# If pattern is a root domain, also check www subdomain
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._is_root_domain(pattern) and host.lower() == f'www.{pattern.lower()}':
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return True

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

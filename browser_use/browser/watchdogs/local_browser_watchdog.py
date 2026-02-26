# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Local browser watchdog for managing browser subprocess lifecycle."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import shutil
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import tempfile
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, Any, ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import psutil
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import BaseEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import PrivateAttr

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import (
	BrowserKillEvent,
	BrowserLaunchEvent,
	BrowserLaunchResult,
	BrowserStopEvent,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.watchdog_base import BaseWatchdog

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `LocalBrowserWatchdog`.
# JP: クラス `LocalBrowserWatchdog` を定義する。
class LocalBrowserWatchdog(BaseWatchdog):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Manages local browser subprocess lifecycle."""

	# Events this watchdog listens to
	# EN: Assign annotated value to LISTENS_TO.
	# JP: LISTENS_TO に型付きの値を代入する。
	LISTENS_TO: ClassVar[list[type[BaseEvent[Any]]]] = [
		BrowserLaunchEvent,
		BrowserKillEvent,
		BrowserStopEvent,
	]

	# Events this watchdog emits
	# EN: Assign annotated value to EMITS.
	# JP: EMITS に型付きの値を代入する。
	EMITS: ClassVar[list[type[BaseEvent[Any]]]] = []

	# Private state for subprocess management
	# EN: Assign annotated value to _subprocess.
	# JP: _subprocess に型付きの値を代入する。
	_subprocess: psutil.Process | None = PrivateAttr(default=None)
	# EN: Assign annotated value to _owns_browser_resources.
	# JP: _owns_browser_resources に型付きの値を代入する。
	_owns_browser_resources: bool = PrivateAttr(default=True)
	# EN: Assign annotated value to _temp_dirs_to_cleanup.
	# JP: _temp_dirs_to_cleanup に型付きの値を代入する。
	_temp_dirs_to_cleanup: list[Path] = PrivateAttr(default_factory=list)
	# EN: Assign annotated value to _original_user_data_dir.
	# JP: _original_user_data_dir に型付きの値を代入する。
	_original_user_data_dir: str | None = PrivateAttr(default=None)

	# EN: Define async function `on_BrowserLaunchEvent`.
	# JP: 非同期関数 `on_BrowserLaunchEvent` を定義する。
	async def on_BrowserLaunchEvent(self, event: BrowserLaunchEvent) -> BrowserLaunchResult:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Launch a local browser process."""

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('[LocalBrowserWatchdog] Received BrowserLaunchEvent, launching local browser...')

			# self.logger.debug('[LocalBrowserWatchdog] Calling _launch_browser...')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			process, cdp_url = await self._launch_browser()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._subprocess = process
			# self.logger.debug(f'[LocalBrowserWatchdog] _launch_browser returned: process={process}, cdp_url={cdp_url}')

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return BrowserLaunchResult(cdp_url=cdp_url)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[LocalBrowserWatchdog] Exception in on_BrowserLaunchEvent: {e}', exc_info=True)
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise

	# EN: Define async function `on_BrowserKillEvent`.
	# JP: 非同期関数 `on_BrowserKillEvent` を定義する。
	async def on_BrowserKillEvent(self, event: BrowserKillEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Kill the local browser subprocess."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('[LocalBrowserWatchdog] Killing local browser process')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._subprocess:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await self._cleanup_process(self._subprocess)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._subprocess = None

		# Clean up temp directories if any were created
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for temp_dir in self._temp_dirs_to_cleanup:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._cleanup_temp_dir(temp_dir)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._temp_dirs_to_cleanup.clear()

		# Restore original user_data_dir if it was modified
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._original_user_data_dir is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.browser_session.browser_profile.user_data_dir = self._original_user_data_dir
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._original_user_data_dir = None

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.logger.debug('[LocalBrowserWatchdog] Browser cleanup completed')

	# EN: Define async function `on_BrowserStopEvent`.
	# JP: 非同期関数 `on_BrowserStopEvent` を定義する。
	async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Listen for BrowserStopEvent and dispatch BrowserKillEvent without awaiting it."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_session.is_local and self._subprocess:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug('[LocalBrowserWatchdog] BrowserStopEvent received, dispatching BrowserKillEvent')
			# Dispatch BrowserKillEvent without awaiting so it gets processed after all BrowserStopEvent handlers
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.event_bus.dispatch(BrowserKillEvent())

	# EN: Define async function `_launch_browser`.
	# JP: 非同期関数 `_launch_browser` を定義する。
	async def _launch_browser(self, max_retries: int = 3) -> tuple[psutil.Process, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Launch browser process and return (process, cdp_url).

		Handles launch errors by falling back to temporary directories if needed.

		Returns:
			Tuple of (psutil.Process, cdp_url)
		"""
		# Keep track of original user_data_dir to restore if needed
		# EN: Assign value to profile.
		# JP: profile に値を代入する。
		profile = self.browser_session.browser_profile
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._original_user_data_dir = str(profile.user_data_dir) if profile.user_data_dir else None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._temp_dirs_to_cleanup = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for attempt in range(max_retries):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Get launch args from profile
				# EN: Assign value to launch_args.
				# JP: launch_args に値を代入する。
				launch_args = profile.get_args()

				# Add debugging port
				# EN: Assign value to debug_port.
				# JP: debug_port に値を代入する。
				debug_port = self._find_free_port()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				launch_args.extend(
					[
						f'--remote-debugging-port={debug_port}',
					]
				)

				# Add homepage URL so browser starts with it already open
				# EN: Import required modules.
				# JP: 必要なモジュールをインポートする。
				from browser_use.browser.constants import DEFAULT_NEW_TAB_URL

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				launch_args.append(DEFAULT_NEW_TAB_URL)
				# EN: Validate a required condition.
				# JP: 必須条件を検証する。
				assert '--user-data-dir' in str(launch_args), (
					'User data dir must be set somewhere in launch args to a non-default path, otherwise Chrome will not let us attach via CDP'
				)

				# Get browser executable
				# Priority: custom executable > fallback paths > playwright subprocess
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if profile.executable_path:
					# EN: Assign value to browser_path.
					# JP: browser_path に値を代入する。
					browser_path = profile.executable_path
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.debug(f'[LocalBrowserWatchdog] 📦 Using custom local browser executable_path= {browser_path}')
				else:
					# self.logger.debug('[LocalBrowserWatchdog] 🔍 Looking for local browser binary path...')
					# Try fallback paths first (system browsers preferred)
					# EN: Assign value to browser_path.
					# JP: browser_path に値を代入する。
					browser_path = self._find_installed_browser_path()
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if not browser_path:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.error(
							'[LocalBrowserWatchdog] ⚠️ No local browser binary found, installing browser using playwright subprocess...'
						)
						# EN: Assign value to browser_path.
						# JP: browser_path に値を代入する。
						browser_path = await self._install_browser_with_playwright()

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[LocalBrowserWatchdog] 📦 Found local browser installed at executable_path= {browser_path}')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not browser_path:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise RuntimeError('No local Chrome/Chromium install found, and failed to install with playwright')

				# Launch browser subprocess directly
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(f'[LocalBrowserWatchdog] 🚀 Launching browser subprocess with {len(launch_args)} args...')
				# EN: Assign value to subprocess.
				# JP: subprocess に値を代入する。
				subprocess = await asyncio.create_subprocess_exec(
					browser_path,
					*launch_args,
					stdout=asyncio.subprocess.PIPE,
					stderr=asyncio.subprocess.PIPE,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.logger.debug(
					f'[LocalBrowserWatchdog] 🎭 Browser running with browser_pid= {subprocess.pid} 🔗 listening on CDP port :{debug_port}'
				)

				# Convert to psutil.Process
				# EN: Assign value to process.
				# JP: process に値を代入する。
				process = psutil.Process(subprocess.pid)

				# Wait for CDP to be ready and get the URL
				# EN: Assign value to cdp_url.
				# JP: cdp_url に値を代入する。
				cdp_url = await self._wait_for_cdp_url(debug_port)

				# Success! Clean up any temp dirs we created but didn't use
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for tmp_dir in self._temp_dirs_to_cleanup:
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						shutil.rmtree(tmp_dir, ignore_errors=True)
					except Exception:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return process, cdp_url

			except Exception as e:
				# EN: Assign value to error_str.
				# JP: error_str に値を代入する。
				error_str = str(e).lower()

				# Check if this is a user_data_dir related error
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if any(err in error_str for err in ['singletonlock', 'user data directory', 'cannot create', 'already in use']):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self.logger.warning(f'Browser launch failed (attempt {attempt + 1}/{max_retries}): {e}')

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if attempt < max_retries - 1:
						# Create a temporary directory for next attempt
						# EN: Assign value to tmp_dir.
						# JP: tmp_dir に値を代入する。
						tmp_dir = Path(tempfile.mkdtemp(prefix='browseruse-tmp-'))
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self._temp_dirs_to_cleanup.append(tmp_dir)

						# Update profile to use temp directory
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						profile.user_data_dir = str(tmp_dir)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.logger.debug(f'Retrying with temporary user_data_dir: {tmp_dir}')

						# Small delay before retry
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await asyncio.sleep(0.5)
						# EN: Continue to the next loop iteration.
						# JP: ループの次の反復に進む。
						continue

				# Not a recoverable error or last attempt failed
				# Restore original user_data_dir before raising
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self._original_user_data_dir is not None:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					profile.user_data_dir = self._original_user_data_dir

				# Clean up any temp dirs we created
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for tmp_dir in self._temp_dirs_to_cleanup:
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						shutil.rmtree(tmp_dir, ignore_errors=True)
					except Exception:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass

				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise

		# Should not reach here, but just in case
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._original_user_data_dir is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			profile.user_data_dir = self._original_user_data_dir
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise RuntimeError(f'Failed to launch browser after {max_retries} attempts')

	# EN: Define function `_find_installed_browser_path`.
	# JP: 関数 `_find_installed_browser_path` を定義する。
	@staticmethod
	def _find_installed_browser_path() -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Try to find browser executable from common fallback locations.

		Prioritizes:
		1. System Chrome Stable
		1. Playwright chromium
		2. Other system native browsers (Chromium -> Chrome Canary/Dev -> Brave)
		3. Playwright headless-shell fallback

		Returns:
			Path to browser executable or None if not found
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import glob
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import platform
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from pathlib import Path

		# EN: Assign value to system.
		# JP: system に値を代入する。
		system = platform.system()
		# EN: Assign value to patterns.
		# JP: patterns に値を代入する。
		patterns = []

		# Get playwright browsers path from environment variable if set
		# EN: Assign value to playwright_path.
		# JP: playwright_path に値を代入する。
		playwright_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if system == 'Darwin':  # macOS
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not playwright_path:
				# EN: Assign value to playwright_path.
				# JP: playwright_path に値を代入する。
				playwright_path = '~/Library/Caches/ms-playwright'
			# EN: Assign value to patterns.
			# JP: patterns に値を代入する。
			patterns = [
				'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
				f'{playwright_path}/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium',
				'/Applications/Chromium.app/Contents/MacOS/Chromium',
				'/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
				'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
				f'{playwright_path}/chromium_headless_shell-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium',
			]
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif system == 'Linux':
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not playwright_path:
				# EN: Assign value to playwright_path.
				# JP: playwright_path に値を代入する。
				playwright_path = '~/.cache/ms-playwright'
			# EN: Assign value to patterns.
			# JP: patterns に値を代入する。
			patterns = [
				'/usr/bin/google-chrome-stable',
				'/usr/bin/google-chrome',
				'/usr/local/bin/google-chrome',
				f'{playwright_path}/chromium-*/chrome-linux/chrome',
				'/usr/bin/chromium',
				'/usr/bin/chromium-browser',
				'/usr/local/bin/chromium',
				'/snap/bin/chromium',
				'/usr/bin/google-chrome-beta',
				'/usr/bin/google-chrome-dev',
				'/usr/bin/brave-browser',
				f'{playwright_path}/chromium_headless_shell-*/chrome-linux/chrome',
			]
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif system == 'Windows':
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not playwright_path:
				# EN: Assign value to playwright_path.
				# JP: playwright_path に値を代入する。
				playwright_path = r'%LOCALAPPDATA%\ms-playwright'
			# EN: Assign value to patterns.
			# JP: patterns に値を代入する。
			patterns = [
				r'C:\Program Files\Google\Chrome\Application\chrome.exe',
				r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
				r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe',
				r'%PROGRAMFILES%\Google\Chrome\Application\chrome.exe',
				r'%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe',
				f'{playwright_path}\\chromium-*\\chrome-win\\chrome.exe',
				r'C:\Program Files\Chromium\Application\chrome.exe',
				r'C:\Program Files (x86)\Chromium\Application\chrome.exe',
				r'%LOCALAPPDATA%\Chromium\Application\chrome.exe',
				r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
				r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe',
				r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
				r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
				r'%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe',
				f'{playwright_path}\\chromium_headless_shell-*\\chrome-win\\chrome.exe',
			]

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for pattern in patterns:
			# Expand user home directory
			# EN: Assign value to expanded_pattern.
			# JP: expanded_pattern に値を代入する。
			expanded_pattern = Path(pattern).expanduser()

			# Handle Windows environment variables
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if system == 'Windows':
				# EN: Assign value to pattern_str.
				# JP: pattern_str に値を代入する。
				pattern_str = str(expanded_pattern)
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for env_var in ['%LOCALAPPDATA%', '%PROGRAMFILES%', '%PROGRAMFILES(X86)%']:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if env_var in pattern_str:
						# EN: Assign value to env_key.
						# JP: env_key に値を代入する。
						env_key = env_var.strip('%').replace('(X86)', ' (x86)')
						# EN: Assign value to env_value.
						# JP: env_value に値を代入する。
						env_value = os.environ.get(env_key, '')
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if env_value:
							# EN: Assign value to pattern_str.
							# JP: pattern_str に値を代入する。
							pattern_str = pattern_str.replace(env_var, env_value)
				# EN: Assign value to expanded_pattern.
				# JP: expanded_pattern に値を代入する。
				expanded_pattern = Path(pattern_str)

			# Convert to string for glob
			# EN: Assign value to pattern_str.
			# JP: pattern_str に値を代入する。
			pattern_str = str(expanded_pattern)

			# Check if pattern contains wildcards
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if '*' in pattern_str:
				# Use glob to expand the pattern
				# EN: Assign value to matches.
				# JP: matches に値を代入する。
				matches = glob.glob(pattern_str)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if matches:
					# Sort matches and take the last one (alphanumerically highest version)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					matches.sort()
					# EN: Assign value to browser_path.
					# JP: browser_path に値を代入する。
					browser_path = matches[-1]
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if Path(browser_path).exists() and Path(browser_path).is_file():
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return browser_path
			else:
				# Direct path check
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if expanded_pattern.exists() and expanded_pattern.is_file():
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return str(expanded_pattern)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `_install_browser_with_playwright`.
	# JP: 非同期関数 `_install_browser_with_playwright` を定義する。
	async def _install_browser_with_playwright(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get browser executable path from playwright in a subprocess to avoid thread issues."""

		# Run in subprocess with timeout
		# EN: Assign value to process.
		# JP: process に値を代入する。
		process = await asyncio.create_subprocess_exec(
			'uvx',
			'playwright',
			'install',
			'chrome',
			'--with-deps',
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE,
		)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'[LocalBrowserWatchdog] 📦 Playwright install output: {stdout}')
			# EN: Assign value to browser_path.
			# JP: browser_path に値を代入する。
			browser_path = self._find_installed_browser_path()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if browser_path:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return browser_path
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.error(f'[LocalBrowserWatchdog] ❌ Playwright local browser installation error: \n{stdout}\n{stderr}')
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError('No local browser path found after: uvx playwright install chrome --with-deps')
		except TimeoutError:
			# Kill the subprocess if it times out
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			process.kill()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await process.wait()
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError('Timeout getting browser path from playwright')
		except Exception as e:
			# Make sure subprocess is terminated
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if process.returncode is None:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				process.kill()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await process.wait()
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError(f'Error getting browser path: {e}')

	# EN: Define function `_find_free_port`.
	# JP: 関数 `_find_free_port` を定義する。
	@staticmethod
	def _find_free_port() -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Find a free port for the debugging interface."""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import socket

		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			s.bind(('127.0.0.1', 0))
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			s.listen(1)
			# EN: Assign value to port.
			# JP: port に値を代入する。
			port = s.getsockname()[1]
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return port

	# EN: Define async function `_wait_for_cdp_url`.
	# JP: 非同期関数 `_wait_for_cdp_url` を定義する。
	@staticmethod
	async def _wait_for_cdp_url(port: int, timeout: float = 30) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Wait for the browser to start and return the CDP URL."""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import httpx

		# EN: Assign value to start_time.
		# JP: start_time に値を代入する。
		start_time = asyncio.get_event_loop().time()
		# EN: Assign value to timeout_config.
		# JP: timeout_config に値を代入する。
		timeout_config = httpx.Timeout(1.0)

		# EN: Execute async logic with managed resources.
		# JP: リソース管理付きで非同期処理を実行する。
		async with httpx.AsyncClient(timeout=timeout_config) as session:
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while asyncio.get_event_loop().time() - start_time < timeout:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to resp.
					# JP: resp に値を代入する。
					resp = await session.get(f'http://localhost:{port}/json/version')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if resp.status_code == 200:
						# Chrome is ready
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return f'http://localhost:{port}/'
				except (httpx.RequestError, httpx.TimeoutException, TimeoutError, OSError):
					# Connection error - Chrome might not be ready yet
					# EN: Keep a placeholder statement.
					# JP: プレースホルダー文を維持する。
					pass
				except Exception:
					# Catch-all to ensure the session context closes cleanly
					# EN: Keep a placeholder statement.
					# JP: プレースホルダー文を維持する。
					pass

				# Chrome is starting up and returning errors or connection failed
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.1)

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise TimeoutError(f'Browser did not start within {timeout} seconds')

	# EN: Define async function `_cleanup_process`.
	# JP: 非同期関数 `_cleanup_process` を定義する。
	@staticmethod
	async def _cleanup_process(process: psutil.Process) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clean up browser process.

		Args:
			process: psutil.Process to terminate
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not process:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Try graceful shutdown first
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			process.terminate()

			# Use async wait instead of blocking wait
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for _ in range(50):  # Wait up to 5 seconds (50 * 0.1)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not process.is_running():
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.1)

			# If still running after 5 seconds, force kill
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if process.is_running():
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				process.kill()
				# Give it a moment to die
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(0.1)

		except psutil.NoSuchProcess:
			# Process already gone
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass
		except Exception:
			# Ignore any other errors during cleanup
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass

	# EN: Define function `_cleanup_temp_dir`.
	# JP: 関数 `_cleanup_temp_dir` を定義する。
	def _cleanup_temp_dir(self, temp_dir: Path | str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Clean up temporary directory.

		Args:
			temp_dir: Path to temporary directory to remove
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not temp_dir:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to temp_path.
			# JP: temp_path に値を代入する。
			temp_path = Path(temp_dir)
			# Only remove if it's actually a temp directory we created
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'browseruse-tmp-' in str(temp_path):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				shutil.rmtree(temp_path, ignore_errors=True)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.logger.debug(f'Failed to cleanup temp dir {temp_dir}: {e}')

	# EN: Define function `browser_pid`.
	# JP: 関数 `browser_pid` を定義する。
	@property
	def browser_pid(self) -> int | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the browser process ID."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self._subprocess:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._subprocess.pid
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `get_browser_pid_via_cdp`.
	# JP: 非同期関数 `get_browser_pid_via_cdp` を定義する。
	@staticmethod
	async def get_browser_pid_via_cdp(browser) -> int | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the browser process ID via CDP SystemInfo.getProcessInfo.

		Args:
			browser: Playwright Browser instance

		Returns:
			Process ID or None if failed
		"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to cdp_session.
			# JP: cdp_session に値を代入する。
			cdp_session = await browser.new_browser_cdp_session()
			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await cdp_session.send('SystemInfo.getProcessInfo')
			# EN: Assign value to process_info.
			# JP: process_info に値を代入する。
			process_info = result.get('processInfo', {})
			# EN: Assign value to pid.
			# JP: pid に値を代入する。
			pid = process_info.get('id')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await cdp_session.detach()
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return pid
		except Exception:
			# If we can't get PID via CDP, it's not critical
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

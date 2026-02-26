# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import sys
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import tempfile
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Iterable
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from enum import Enum
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from functools import cache
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Annotated, Any, Literal, Self
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.parse import urlparse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import (
	AfterValidator,
	AliasChoices,
	BaseModel,
	ConfigDict,
	Field,
	PrivateAttr,
	field_validator,
	model_validator,
)

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.config import CONFIG
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import _log_pretty_path, logger

# EN: Assign value to CHROME_DEBUG_PORT.
# JP: CHROME_DEBUG_PORT に値を代入する。
CHROME_DEBUG_PORT = 9242  # use a non-default port to avoid conflicts with other tools / devs using 9222
# EN: Assign value to CHROME_DISABLED_COMPONENTS.
# JP: CHROME_DISABLED_COMPONENTS に値を代入する。
CHROME_DISABLED_COMPONENTS = [
	# Playwright defaults: https://github.com/microsoft/playwright/blob/41008eeddd020e2dee1c540f7c0cdfa337e99637/packages/playwright-core/src/server/chromium/chromiumSwitches.ts#L76
	# AcceptCHFrame,AutoExpandDetailsElement,AvoidUnnecessaryBeforeUnloadCheckSync,CertificateTransparencyComponentUpdater,DeferRendererTasksAfterInput,DestroyProfileOnBrowserClose,DialMediaRouteProvider,ExtensionManifestV2Disabled,GlobalMediaControls,HttpsUpgrades,ImprovedCookieControls,LazyFrameLoading,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate
	# See https:#github.com/microsoft/playwright/pull/10380
	'AcceptCHFrame',
	# See https:#github.com/microsoft/playwright/pull/10679
	'AutoExpandDetailsElement',
	# See https:#github.com/microsoft/playwright/issues/14047
	'AvoidUnnecessaryBeforeUnloadCheckSync',
	# See https:#github.com/microsoft/playwright/pull/12992
	'CertificateTransparencyComponentUpdater',
	'DestroyProfileOnBrowserClose',
	# See https:#github.com/microsoft/playwright/pull/13854
	'DialMediaRouteProvider',
	# Chromium is disabling manifest version 2. Allow testing it as long as Chromium can actually run it.
	# Disabled in https:#chromium-review.googlesource.com/c/chromium/src/+/6265903.
	'ExtensionManifestV2Disabled',
	'GlobalMediaControls',
	# See https:#github.com/microsoft/playwright/pull/27605
	'HttpsUpgrades',
	'ImprovedCookieControls',
	'LazyFrameLoading',
	# Hides the Lens feature in the URL address bar. Its not working in unofficial builds.
	'LensOverlay',
	# See https:#github.com/microsoft/playwright/pull/8162
	'MediaRouter',
	# See https:#github.com/microsoft/playwright/issues/28023
	'PaintHolding',
	# See https:#github.com/microsoft/playwright/issues/32230
	'ThirdPartyStoragePartitioning',
	# See https://github.com/microsoft/playwright/issues/16126
	'Translate',
	# 3
	# Added by us:
	'AutomationControlled',
	'BackForwardCache',
	'OptimizationHints',
	'ProcessPerSiteUpToMainFrameThreshold',
	'InterestFeedContentSuggestions',
	'CalculateNativeWinOcclusion',  # chrome normally stops rendering tabs if they are not visible (occluded by a foreground window or other app)
	# 'BackForwardCache',  # agent does actually use back/forward navigation, but we can disable if we ever remove that
	'HeavyAdPrivacyMitigations',
	'PrivacySandboxSettings4',
	'AutofillServerCommunication',
	'CrashReporting',
	'OverscrollHistoryNavigation',
	'InfiniteSessionRestore',
	'ExtensionDisableUnsupportedDeveloper',
	'ExtensionManifestV2Unsupported',
]

# EN: Assign value to CHROME_HEADLESS_ARGS.
# JP: CHROME_HEADLESS_ARGS に値を代入する。
CHROME_HEADLESS_ARGS = [
	'--headless=new',
]

# EN: Assign value to CHROME_DOCKER_ARGS.
# JP: CHROME_DOCKER_ARGS に値を代入する。
CHROME_DOCKER_ARGS = [
	# '--disable-gpu',    # GPU is actually supported in headless docker mode now, but sometimes useful to test without it
	'--no-sandbox',
	'--disable-gpu-sandbox',
	'--disable-setuid-sandbox',
	'--disable-dev-shm-usage',
	'--no-xshm',
	'--no-zygote',
	# '--single-process',  # might be the cause of "Target page, context or browser has been closed" errors during CDP page.captureScreenshot https://stackoverflow.com/questions/51629151/puppeteer-protocol-error-page-navigate-target-closed
	'--disable-site-isolation-trials',  # lowers RAM use by 10-16% in docker, but could lead to easier bot blocking if pages can detect it?
]


# EN: Assign value to CHROME_DISABLE_SECURITY_ARGS.
# JP: CHROME_DISABLE_SECURITY_ARGS に値を代入する。
CHROME_DISABLE_SECURITY_ARGS = [
	'--disable-site-isolation-trials',
	'--disable-web-security',
	'--disable-features=IsolateOrigins,site-per-process',
	'--allow-running-insecure-content',
	'--ignore-certificate-errors',
	'--ignore-ssl-errors',
	'--ignore-certificate-errors-spki-list',
]

# EN: Assign value to CHROME_DETERMINISTIC_RENDERING_ARGS.
# JP: CHROME_DETERMINISTIC_RENDERING_ARGS に値を代入する。
CHROME_DETERMINISTIC_RENDERING_ARGS = [
	'--deterministic-mode',
	'--js-flags=--random-seed=1157259159',
	'--force-device-scale-factor=2',
	'--enable-webgl',
	# '--disable-skia-runtime-opts',
	# '--disable-2d-canvas-clip-aa',
	'--font-render-hinting=none',
	'--force-color-profile=srgb',
]

# EN: Assign value to CHROME_DEFAULT_ARGS.
# JP: CHROME_DEFAULT_ARGS に値を代入する。
CHROME_DEFAULT_ARGS = [
	# # provided by playwright by default: https://github.com/microsoft/playwright/blob/41008eeddd020e2dee1c540f7c0cdfa337e99637/packages/playwright-core/src/server/chromium/chromiumSwitches.ts#L76
	'--disable-field-trial-config',  # https://source.chromium.org/chromium/chromium/src/+/main:testing/variations/README.md
	'--disable-background-networking',
	'--disable-background-timer-throttling',  # agents might be working on background pages if the human switches to another tab
	'--disable-backgrounding-occluded-windows',  # same deal, agents are often working on backgrounded browser windows
	'--disable-back-forward-cache',  # Avoids surprises like main request not being intercepted during page.goBack().
	'--disable-breakpad',
	'--disable-client-side-phishing-detection',
	'--disable-component-extensions-with-background-pages',
	'--disable-component-update',  # Avoids unneeded network activity after startup.
	'--no-default-browser-check',
	# '--disable-default-apps',
	'--disable-dev-shm-usage',  # crucial for docker support, harmless in non-docker environments
	# '--disable-extensions',
	# '--disable-features=' + disabledFeatures(assistantMode).join(','),
	# '--allow-pre-commit-input',  # duplicate removed
	'--disable-hang-monitor',
	'--disable-ipc-flooding-protection',  # important to be able to make lots of CDP calls in a tight loop
	'--disable-popup-blocking',
	'--disable-prompt-on-repost',
	'--disable-renderer-backgrounding',
	# '--force-color-profile=srgb',  # moved to CHROME_DETERMINISTIC_RENDERING_ARGS
	'--metrics-recording-only',
	'--no-first-run',
	'--password-store=basic',
	'--use-mock-keychain',
	# // See https://chromium-review.googlesource.com/c/chromium/src/+/2436773
	'--no-service-autorun',
	'--export-tagged-pdf',
	# // https://chromium-review.googlesource.com/c/chromium/src/+/4853540
	'--disable-search-engine-choice-screen',
	# // https://issues.chromium.org/41491762
	'--unsafely-disable-devtools-self-xss-warnings',
	# added by us:
	'--enable-features=NetworkService,NetworkServiceInProcess',
	'--enable-network-information-downlink-max',
	'--test-type=gpu',
	'--disable-sync',
	'--allow-legacy-extension-manifests',
	'--allow-pre-commit-input',
	'--disable-blink-features=AutomationControlled',
	'--install-autogenerated-theme=0,0,0',
	# '--hide-scrollbars',                     # leave them visible! the agent uses them to know when it needs to scroll to see more options
	'--log-level=2',
	# '--enable-logging=stderr',
	'--disable-focus-on-load',
	'--disable-window-activation',
	'--generate-pdf-document-outline',
	'--no-pings',
	'--ash-no-nudges',
	'--disable-infobars',
	'--simulate-outdated-no-au="Tue, 31 Dec 2099 23:59:59 GMT"',
	'--hide-crash-restore-bubble',
	'--suppress-message-center-popups',
	'--disable-domain-reliability',
	'--disable-datasaver-prompt',
	'--disable-speech-synthesis-api',
	'--disable-speech-api',
	'--disable-print-preview',
	'--safebrowsing-disable-auto-update',
	'--disable-external-intent-requests',
	'--disable-desktop-notifications',
	'--noerrdialogs',
	'--silent-debugger-extension-api',
	# Extension welcome tab suppression for automation
	'--disable-extensions-http-throttling',
	'--extensions-on-chrome-urls',
	'--disable-default-apps',
	f'--disable-features={",".join(CHROME_DISABLED_COMPONENTS)}',
]


# EN: Define class `ViewportSize`.
# JP: クラス `ViewportSize` を定義する。
class ViewportSize(BaseModel):
	# EN: Assign annotated value to width.
	# JP: width に型付きの値を代入する。
	width: int = Field(ge=0)
	# EN: Assign annotated value to height.
	# JP: height に型付きの値を代入する。
	height: int = Field(ge=0)

	# EN: Define function `__getitem__`.
	# JP: 関数 `__getitem__` を定義する。
	def __getitem__(self, key: str) -> int:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return dict(self)[key]

	# EN: Define function `__setitem__`.
	# JP: 関数 `__setitem__` を定義する。
	def __setitem__(self, key: str, value: int) -> None:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		setattr(self, key, value)


# EN: Define function `get_display_size`.
# JP: 関数 `get_display_size` を定義する。
@cache
def get_display_size() -> ViewportSize | None:
	# macOS
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from AppKit import NSScreen  # type: ignore[import]

		# EN: Assign value to screen.
		# JP: screen に値を代入する。
		screen = NSScreen.mainScreen().frame()
		# EN: Assign value to size.
		# JP: size に値を代入する。
		size = ViewportSize(width=int(screen.size.width), height=int(screen.size.height))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Display size: {size}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return size
	except Exception:
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass

	# Windows & Linux
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from screeninfo import get_monitors

		# EN: Assign value to monitors.
		# JP: monitors に値を代入する。
		monitors = get_monitors()
		# EN: Assign value to monitor.
		# JP: monitor に値を代入する。
		monitor = monitors[0]
		# EN: Assign value to size.
		# JP: size に値を代入する。
		size = ViewportSize(width=int(monitor.width), height=int(monitor.height))
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Display size: {size}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return size
	except Exception:
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.debug('No display size found')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define function `get_window_adjustments`.
# JP: 関数 `get_window_adjustments` を定義する。
def get_window_adjustments() -> tuple[int, int]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Returns recommended x, y offsets for window positioning"""

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if sys.platform == 'darwin':  # macOS
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return -4, 24  # macOS has a small title bar, no border
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif sys.platform == 'win32':  # Windows
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return -8, 0  # Windows has a border on the left
	else:  # Linux
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 0, 0


# EN: Define function `validate_url`.
# JP: 関数 `validate_url` を定義する。
def validate_url(url: str, schemes: Iterable[str] = ()) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Validate URL format and optionally check for specific schemes."""
	# EN: Assign value to parsed_url.
	# JP: parsed_url に値を代入する。
	parsed_url = urlparse(url)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not parsed_url.netloc:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f'Invalid URL format: {url}')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if schemes and parsed_url.scheme and parsed_url.scheme.lower() not in schemes:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f'URL has invalid scheme: {url} (expected one of {schemes})')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return url


# EN: Define function `validate_float_range`.
# JP: 関数 `validate_float_range` を定義する。
def validate_float_range(value: float, min_val: float, max_val: float) -> float:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Validate that float is within specified range."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not min_val <= value <= max_val:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f'Value {value} outside of range {min_val}-{max_val}')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return value


# EN: Define function `validate_cli_arg`.
# JP: 関数 `validate_cli_arg` を定義する。
def validate_cli_arg(arg: str) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Validate that arg is a valid CLI argument."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not arg.startswith('--'):
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f'Invalid CLI argument: {arg} (should start with --, e.g. --some-key="some value here")')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return arg


# ===== Enum definitions =====


# EN: Define class `RecordHarContent`.
# JP: クラス `RecordHarContent` を定義する。
class RecordHarContent(str, Enum):
	# EN: Assign value to OMIT.
	# JP: OMIT に値を代入する。
	OMIT = 'omit'
	# EN: Assign value to EMBED.
	# JP: EMBED に値を代入する。
	EMBED = 'embed'
	# EN: Assign value to ATTACH.
	# JP: ATTACH に値を代入する。
	ATTACH = 'attach'


# EN: Define class `RecordHarMode`.
# JP: クラス `RecordHarMode` を定義する。
class RecordHarMode(str, Enum):
	# EN: Assign value to FULL.
	# JP: FULL に値を代入する。
	FULL = 'full'
	# EN: Assign value to MINIMAL.
	# JP: MINIMAL に値を代入する。
	MINIMAL = 'minimal'


# EN: Define class `BrowserChannel`.
# JP: クラス `BrowserChannel` を定義する。
class BrowserChannel(str, Enum):
	# EN: Assign value to CHROMIUM.
	# JP: CHROMIUM に値を代入する。
	CHROMIUM = 'chromium'
	# EN: Assign value to CHROME.
	# JP: CHROME に値を代入する。
	CHROME = 'chrome'
	# EN: Assign value to CHROME_BETA.
	# JP: CHROME_BETA に値を代入する。
	CHROME_BETA = 'chrome-beta'
	# EN: Assign value to CHROME_DEV.
	# JP: CHROME_DEV に値を代入する。
	CHROME_DEV = 'chrome-dev'
	# EN: Assign value to CHROME_CANARY.
	# JP: CHROME_CANARY に値を代入する。
	CHROME_CANARY = 'chrome-canary'
	# EN: Assign value to MSEDGE.
	# JP: MSEDGE に値を代入する。
	MSEDGE = 'msedge'
	# EN: Assign value to MSEDGE_BETA.
	# JP: MSEDGE_BETA に値を代入する。
	MSEDGE_BETA = 'msedge-beta'
	# EN: Assign value to MSEDGE_DEV.
	# JP: MSEDGE_DEV に値を代入する。
	MSEDGE_DEV = 'msedge-dev'
	# EN: Assign value to MSEDGE_CANARY.
	# JP: MSEDGE_CANARY に値を代入する。
	MSEDGE_CANARY = 'msedge-canary'


# Using constants from central location in browser_use.config
# EN: Assign value to BROWSERUSE_DEFAULT_CHANNEL.
# JP: BROWSERUSE_DEFAULT_CHANNEL に値を代入する。
BROWSERUSE_DEFAULT_CHANNEL = BrowserChannel.CHROMIUM


# ===== Type definitions with validators =====

# EN: Assign value to UrlStr.
# JP: UrlStr に値を代入する。
UrlStr = Annotated[str, AfterValidator(validate_url)]
# EN: Assign value to NonNegativeFloat.
# JP: NonNegativeFloat に値を代入する。
NonNegativeFloat = Annotated[float, AfterValidator(lambda x: validate_float_range(x, 0, float('inf')))]
# EN: Assign value to CliArgStr.
# JP: CliArgStr に値を代入する。
CliArgStr = Annotated[str, AfterValidator(validate_cli_arg)]


# ===== Base Models =====


# EN: Define class `BrowserContextArgs`.
# JP: クラス `BrowserContextArgs` を定義する。
class BrowserContextArgs(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Base model for common browser context parameters used by
	both BrowserType.new_context() and BrowserType.launch_persistent_context().

	https://playwright.dev/python/docs/api/class-browser#browser-new-context
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(extra='ignore', validate_assignment=False, revalidate_instances='always', populate_by_name=True)

	# Browser context parameters
	# EN: Assign annotated value to accept_downloads.
	# JP: accept_downloads に型付きの値を代入する。
	accept_downloads: bool = True

	# Security options
	# proxy: ProxySettings | None = None
	# EN: Assign annotated value to permissions.
	# JP: permissions に型付きの値を代入する。
	permissions: list[str] = Field(
		default_factory=lambda: ['clipboardReadWrite', 'notifications'],
		description='Browser permissions to grant (CDP Browser.grantPermissions).',
		# clipboardReadWrite is for google sheets and pyperclip automations
		# notifications are to avoid browser fingerprinting
	)
	# client_certificates: list[ClientCertificate] = Field(default_factory=list)
	# http_credentials: HttpCredentials | None = None

	# Viewport options
	# EN: Assign annotated value to user_agent.
	# JP: user_agent に型付きの値を代入する。
	user_agent: str | None = None
	# EN: Assign annotated value to screen.
	# JP: screen に型付きの値を代入する。
	screen: ViewportSize | None = None
	# EN: Assign annotated value to viewport.
	# JP: viewport に型付きの値を代入する。
	viewport: ViewportSize | None = Field(default=None)
	# EN: Assign annotated value to no_viewport.
	# JP: no_viewport に型付きの値を代入する。
	no_viewport: bool | None = None
	# EN: Assign annotated value to device_scale_factor.
	# JP: device_scale_factor に型付きの値を代入する。
	device_scale_factor: NonNegativeFloat | None = None
	# geolocation: Geolocation | None = None

	# Recording Options
	# EN: Assign annotated value to record_har_content.
	# JP: record_har_content に型付きの値を代入する。
	record_har_content: RecordHarContent = RecordHarContent.EMBED
	# EN: Assign annotated value to record_har_mode.
	# JP: record_har_mode に型付きの値を代入する。
	record_har_mode: RecordHarMode = RecordHarMode.FULL
	# EN: Assign annotated value to record_har_path.
	# JP: record_har_path に型付きの値を代入する。
	record_har_path: str | Path | None = Field(default=None, validation_alias=AliasChoices('save_har_path', 'record_har_path'))
	# EN: Assign annotated value to record_video_dir.
	# JP: record_video_dir に型付きの値を代入する。
	record_video_dir: str | Path | None = Field(
		default=None, validation_alias=AliasChoices('save_recording_path', 'record_video_dir')
	)


# EN: Define class `BrowserConnectArgs`.
# JP: クラス `BrowserConnectArgs` を定義する。
class BrowserConnectArgs(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Base model for common browser connect parameters used by
	both connect_over_cdp() and connect_over_ws().

	https://playwright.dev/python/docs/api/class-browsertype#browser-type-connect
	https://playwright.dev/python/docs/api/class-browsertype#browser-type-connect-over-cdp
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(extra='ignore', validate_assignment=True, revalidate_instances='always', populate_by_name=True)

	# EN: Assign annotated value to headers.
	# JP: headers に型付きの値を代入する。
	headers: dict[str, str] | None = Field(default=None, description='Additional HTTP headers to be sent with connect request')


# EN: Define class `BrowserLaunchArgs`.
# JP: クラス `BrowserLaunchArgs` を定義する。
class BrowserLaunchArgs(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Base model for common browser launch parameters used by
	both launch() and launch_persistent_context().

	https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(
		extra='ignore',
		validate_assignment=True,
		revalidate_instances='always',
		from_attributes=True,
		validate_by_name=True,
		validate_by_alias=True,
		populate_by_name=True,
	)

	# EN: Assign annotated value to env.
	# JP: env に型付きの値を代入する。
	env: dict[str, str | float | bool] | None = Field(
		default=None,
		description='Extra environment variables to set when launching the browser. If None, inherits from the current process.',
	)
	# EN: Assign annotated value to executable_path.
	# JP: executable_path に型付きの値を代入する。
	executable_path: str | Path | None = Field(
		default=None,
		validation_alias=AliasChoices('browser_binary_path', 'chrome_binary_path'),
		description='Path to the chromium-based browser executable to use.',
	)
	# EN: Assign annotated value to headless.
	# JP: headless に型付きの値を代入する。
	headless: bool | None = Field(default=None, description='Whether to run the browser in headless or windowed mode.')
	# EN: Assign annotated value to args.
	# JP: args に型付きの値を代入する。
	args: list[CliArgStr] = Field(
		default_factory=list, description='List of *extra* CLI args to pass to the browser when launching.'
	)
	# EN: Assign annotated value to ignore_default_args.
	# JP: ignore_default_args に型付きの値を代入する。
	ignore_default_args: list[CliArgStr] | Literal[True] = Field(
		default_factory=lambda: [
			'--enable-automation',  # we mask the automation fingerprint via JS and other flags
			'--disable-extensions',  # allow browser extensions
			'--hide-scrollbars',  # always show scrollbars in screenshots so agent knows there is more content below it can scroll down to
			'--disable-features=AcceptCHFrame,AutoExpandDetailsElement,AvoidUnnecessaryBeforeUnloadCheckSync,CertificateTransparencyComponentUpdater,DeferRendererTasksAfterInput,DestroyProfileOnBrowserClose,DialMediaRouteProvider,ExtensionManifestV2Disabled,GlobalMediaControls,HttpsUpgrades,ImprovedCookieControls,LazyFrameLoading,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate',
		],
		description='List of default CLI args to stop playwright from applying (see https://github.com/microsoft/playwright/blob/41008eeddd020e2dee1c540f7c0cdfa337e99637/packages/playwright-core/src/server/chromium/chromiumSwitches.ts)',
	)
	# EN: Assign annotated value to channel.
	# JP: channel に型付きの値を代入する。
	channel: BrowserChannel | None = None  # https://playwright.dev/docs/browsers#chromium-headless-shell
	# EN: Assign annotated value to chromium_sandbox.
	# JP: chromium_sandbox に型付きの値を代入する。
	chromium_sandbox: bool = Field(
		default=not CONFIG.IN_DOCKER, description='Whether to enable Chromium sandboxing (recommended unless inside Docker).'
	)
	# EN: Assign annotated value to devtools.
	# JP: devtools に型付きの値を代入する。
	devtools: bool = Field(
		default=False, description='Whether to open DevTools panel automatically for every page, only works when headless=False.'
	)

	# proxy: ProxySettings | None = Field(default=None, description='Proxy settings to use to connect to the browser.')
	# EN: Assign annotated value to downloads_path.
	# JP: downloads_path に型付きの値を代入する。
	downloads_path: str | Path | None = Field(
		default=None,
		description='Directory to save downloads to.',
		validation_alias=AliasChoices('downloads_dir', 'save_downloads_path'),
	)
	# EN: Assign annotated value to traces_dir.
	# JP: traces_dir に型付きの値を代入する。
	traces_dir: str | Path | None = Field(
		default=None,
		description='Directory for saving playwright trace.zip files (playwright actions, screenshots, DOM snapshots, HAR traces).',
		validation_alias=AliasChoices('trace_path', 'traces_dir'),
	)

	# firefox_user_prefs: dict[str, str | float | bool] = Field(default_factory=dict)

	# EN: Define function `validate_devtools_headless`.
	# JP: 関数 `validate_devtools_headless` を定義する。
	@model_validator(mode='after')
	def validate_devtools_headless(self) -> Self:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Cannot open devtools when headless is True"""
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert not (self.headless and self.devtools), 'headless=True and devtools=True cannot both be set at the same time'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define function `set_default_downloads_path`.
	# JP: 関数 `set_default_downloads_path` を定義する。
	@model_validator(mode='after')
	def set_default_downloads_path(self) -> Self:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Set a unique default downloads path if none is provided."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.downloads_path is None:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import uuid

			# Create unique directory in /tmp for downloads
			# EN: Assign value to unique_id.
			# JP: unique_id に値を代入する。
			unique_id = str(uuid.uuid4())[:8]  # 8 characters
			# EN: Assign value to downloads_path.
			# JP: downloads_path に値を代入する。
			downloads_path = Path(f'/tmp/browser-use-downloads-{unique_id}')

			# Ensure path doesn't already exist (extremely unlikely but possible)
			# EN: Repeat logic while a condition is true.
			# JP: 条件が真の間、処理を繰り返す。
			while downloads_path.exists():
				# EN: Assign value to unique_id.
				# JP: unique_id に値を代入する。
				unique_id = str(uuid.uuid4())[:8]
				# EN: Assign value to downloads_path.
				# JP: downloads_path に値を代入する。
				downloads_path = Path(f'/tmp/browser-use-downloads-{unique_id}')

			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.downloads_path = downloads_path
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.downloads_path.mkdir(parents=True, exist_ok=True)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define function `args_as_dict`.
	# JP: 関数 `args_as_dict` を定義する。
	@staticmethod
	def args_as_dict(args: list[str]) -> dict[str, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return the extra launch CLI args as a dictionary."""
		# EN: Assign value to args_dict.
		# JP: args_dict に値を代入する。
		args_dict = {}
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for arg in args:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			key, value, *_ = [*arg.split('=', 1), '', '', '']
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			args_dict[key.strip().lstrip('-')] = value.strip()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return args_dict

	# EN: Define function `args_as_list`.
	# JP: 関数 `args_as_list` を定義する。
	@staticmethod
	def args_as_list(args: dict[str, str]) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return the extra launch CLI args as a list of strings."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [f'--{key.lstrip("-")}={value}' if value else f'--{key.lstrip("-")}' for key, value in args.items()]


# ===== API-specific Models =====


# EN: Define class `BrowserNewContextArgs`.
# JP: クラス `BrowserNewContextArgs` を定義する。
class BrowserNewContextArgs(BrowserContextArgs):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Pydantic model for new_context() arguments.
	Extends BaseContextParams with storage_state parameter.

	https://playwright.dev/python/docs/api/class-browser#browser-new-context
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(extra='ignore', validate_assignment=False, revalidate_instances='always', populate_by_name=True)

	# storage_state is not supported in launch_persistent_context()
	# EN: Assign annotated value to storage_state.
	# JP: storage_state に型付きの値を代入する。
	storage_state: str | Path | dict[str, Any] | None = None
	# TODO: use StorageState type instead of dict[str, Any]

	# to apply this to existing contexts (incl cookies, localStorage, IndexedDB), see:
	# - https://github.com/microsoft/playwright/pull/34591/files
	# - playwright-core/src/server/storageScript.ts restore() function
	# - https://github.com/Skn0tt/playwright/blob/c446bc44bac4fbfdf52439ba434f92192459be4e/packages/playwright-core/src/server/storageScript.ts#L84C1-L123C2

	# @field_validator('storage_state', mode='after')
	# def load_storage_state_from_file(self) -> Self:
	#     """Load storage_state from file if it's a path."""
	#     if isinstance(self.storage_state, (str, Path)):
	#         storage_state_file = Path(self.storage_state)
	#         try:
	#             parsed_storage_state = json.loads(storage_state_file.read_text())
	#             validated_storage_state = StorageState(**parsed_storage_state)
	#             self.storage_state = validated_storage_state
	#         except Exception as e:
	#             raise ValueError(f'Failed to load storage state file {self.storage_state}: {e}') from e
	#     return self
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `BrowserLaunchPersistentContextArgs`.
# JP: クラス `BrowserLaunchPersistentContextArgs` を定義する。
class BrowserLaunchPersistentContextArgs(BrowserLaunchArgs, BrowserContextArgs):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Pydantic model for launch_persistent_context() arguments.
	Combines browser launch parameters and context parameters,
	plus adds the user_data_dir parameter.

	https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(extra='ignore', validate_assignment=False, revalidate_instances='always')

	# Required parameter specific to launch_persistent_context, but can be None to use incognito temp dir
	# EN: Assign annotated value to user_data_dir.
	# JP: user_data_dir に型付きの値を代入する。
	user_data_dir: str | Path | None = None

	# EN: Define function `validate_user_data_dir`.
	# JP: 関数 `validate_user_data_dir` を定義する。
	@field_validator('user_data_dir', mode='after')
	@classmethod
	def validate_user_data_dir(cls, v: str | Path | None) -> str | Path:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Validate user data dir is set to a non-default path."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if v is None:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return tempfile.mkdtemp(prefix='browser-use-user-data-dir-')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return Path(v).expanduser().resolve()


# EN: Define class `ProxySettings`.
# JP: クラス `ProxySettings` を定義する。
class ProxySettings(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Typed proxy settings for Chromium traffic.

	- server: Full proxy URL, e.g. "http://host:8080" or "socks5://host:1080"
	- bypass: Comma-separated hosts to bypass (e.g. "localhost,127.0.0.1,*.internal")
	- username/password: Optional credentials for authenticated proxies
	"""

	# EN: Assign annotated value to server.
	# JP: server に型付きの値を代入する。
	server: str | None = Field(default=None, description='Proxy URL, e.g. http://host:8080 or socks5://host:1080')
	# EN: Assign annotated value to bypass.
	# JP: bypass に型付きの値を代入する。
	bypass: str | None = Field(default=None, description='Comma-separated hosts to bypass, e.g. localhost,127.0.0.1,*.internal')
	# EN: Assign annotated value to username.
	# JP: username に型付きの値を代入する。
	username: str | None = Field(default=None, description='Proxy auth username')
	# EN: Assign annotated value to password.
	# JP: password に型付きの値を代入する。
	password: str | None = Field(default=None, description='Proxy auth password')

	# EN: Define function `__getitem__`.
	# JP: 関数 `__getitem__` を定義する。
	def __getitem__(self, key: str) -> str | None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return getattr(self, key)


# EN: Define class `BrowserProfile`.
# JP: クラス `BrowserProfile` を定義する。
class BrowserProfile(BrowserConnectArgs, BrowserLaunchPersistentContextArgs, BrowserLaunchArgs, BrowserNewContextArgs):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A BrowserProfile is a static template collection of kwargs that can be passed to:
	    - BrowserType.launch(**BrowserLaunchArgs)
	    - BrowserType.connect(**BrowserConnectArgs)
	    - BrowserType.connect_over_cdp(**BrowserConnectArgs)
	    - BrowserType.launch_persistent_context(**BrowserLaunchPersistentContextArgs)
	    - BrowserContext.new_context(**BrowserNewContextArgs)
	    - BrowserSession(**BrowserProfile)
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(
		extra='ignore',
		validate_assignment=True,
		revalidate_instances='always',
		from_attributes=True,
		validate_by_name=True,
		validate_by_alias=True,
	)

	# ... extends options defined in:
	# BrowserLaunchPersistentContextArgs, BrowserLaunchArgs, BrowserNewContextArgs, BrowserConnectArgs

	# Internal tracking (not part of public schema)
	# EN: Assign annotated value to _detected_screen.
	# JP: _detected_screen に型付きの値を代入する。
	_detected_screen: ViewportSize | None = PrivateAttr(default=None)

	# Session/connection configuration
	# EN: Assign annotated value to cdp_url.
	# JP: cdp_url に型付きの値を代入する。
	cdp_url: str | None = Field(default=None, description='CDP URL for connecting to existing browser instance')
	# EN: Assign annotated value to is_local.
	# JP: is_local に型付きの値を代入する。
	is_local: bool = Field(default=False, description='Whether this is a local browser instance')
	# label: str = 'default'

	# custom options we provide that aren't native playwright kwargs
	# EN: Assign annotated value to disable_security.
	# JP: disable_security に型付きの値を代入する。
	disable_security: bool = Field(default=False, description='Disable browser security features.')
	# EN: Assign annotated value to deterministic_rendering.
	# JP: deterministic_rendering に型付きの値を代入する。
	deterministic_rendering: bool = Field(default=False, description='Enable deterministic rendering flags.')
	# EN: Assign annotated value to allowed_domains.
	# JP: allowed_domains に型付きの値を代入する。
	allowed_domains: list[str] | None = Field(
		default=None,
		description='List of allowed domains for navigation e.g. ["*.google.com", "https://example.com", "chrome-extension://*"]',
	)
	# EN: Assign annotated value to prohibited_domains.
	# JP: prohibited_domains に型付きの値を代入する。
	prohibited_domains: list[str] | None = Field(
		default=None,
		description='List of prohibited domains for navigation e.g. ["*.google.com", "https://example.com", "chrome-extension://*"]. Allowed domains take precedence over prohibited domains.',
	)
	# EN: Assign annotated value to keep_alive.
	# JP: keep_alive に型付きの値を代入する。
	keep_alive: bool | None = Field(default=None, description='Keep browser alive after agent run.')

	# --- Proxy settings ---
	# New consolidated proxy config (typed)
	# EN: Assign annotated value to proxy.
	# JP: proxy に型付きの値を代入する。
	proxy: ProxySettings | None = Field(
		default=None,
		description='Proxy settings. Use browser_use.browser.profile.ProxySettings(server, bypass, username, password)',
	)
	# EN: Assign annotated value to enable_default_extensions.
	# JP: enable_default_extensions に型付きの値を代入する。
	enable_default_extensions: bool = Field(
		default=True,
		description="Enable automation-optimized extensions: ad blocking (uBlock Origin), cookie handling (I still don't care about cookies), and URL cleaning (ClearURLs). All extensions work automatically without manual intervention. Extensions are automatically downloaded and loaded when enabled.",
	)
	# EN: Assign annotated value to cookie_whitelist_domains.
	# JP: cookie_whitelist_domains に型付きの値を代入する。
	cookie_whitelist_domains: list[str] = Field(
		default_factory=lambda: ['nature.com', 'qatarairways.com'],
		description='List of domains to whitelist in the "I still don\'t care about cookies" extension, preventing automatic cookie banner handling on these sites.',
	)

	# EN: Assign annotated value to window_size.
	# JP: window_size に型付きの値を代入する。
	window_size: ViewportSize | None = Field(
		default=None,
		description='Browser window size to use when headless=False.',
	)
	# EN: Assign annotated value to request_initial_window_state.
	# JP: request_initial_window_state に型付きの値を代入する。
	request_initial_window_state: bool | None = Field(
		default=None,
		description=(
			'When True, request a fullscreen or maximized window via CDP after the first '
			'session attaches. When False, skip the request. When None, the session will '
			'enable the request automatically when connecting to a remote CDP endpoint.'
		),
	)
	# EN: Assign annotated value to window_height.
	# JP: window_height に型付きの値を代入する。
	window_height: int | None = Field(default=None, description='DEPRECATED, use window_size["height"] instead', exclude=True)
	# EN: Assign annotated value to window_width.
	# JP: window_width に型付きの値を代入する。
	window_width: int | None = Field(default=None, description='DEPRECATED, use window_size["width"] instead', exclude=True)
	# EN: Assign annotated value to window_position.
	# JP: window_position に型付きの値を代入する。
	window_position: ViewportSize | None = Field(
		default=ViewportSize(width=0, height=0),
		description='Window position to use for the browser x,y from the top left when headless=False.',
	)
	# EN: Assign annotated value to cross_origin_iframes.
	# JP: cross_origin_iframes に型付きの値を代入する。
	cross_origin_iframes: bool = Field(
		default=True,
		description='Enable cross-origin iframe support (OOPIF/Out-of-Process iframes). When False, only same-origin frames are processed to avoid complexity and hanging.',
	)
	# EN: Assign annotated value to max_iframes.
	# JP: max_iframes に型付きの値を代入する。
	max_iframes: int = Field(
		default=100,
		description='Maximum number of iframe documents to process to prevent crashes.',
	)
	# EN: Assign annotated value to max_iframe_depth.
	# JP: max_iframe_depth に型付きの値を代入する。
	max_iframe_depth: int = Field(
		ge=0,
		default=5,
		description='Maximum depth for cross-origin iframe recursion (default: 5 levels deep).',
	)

	# --- Page load/wait timings ---

	# EN: Assign annotated value to minimum_wait_page_load_time.
	# JP: minimum_wait_page_load_time に型付きの値を代入する。
	minimum_wait_page_load_time: float = Field(default=0.25, description='Minimum time to wait before capturing page state.')
	# EN: Assign annotated value to wait_for_network_idle_page_load_time.
	# JP: wait_for_network_idle_page_load_time に型付きの値を代入する。
	wait_for_network_idle_page_load_time: float = Field(default=0.5, description='Time to wait for network idle.')

	# EN: Assign annotated value to wait_between_actions.
	# JP: wait_between_actions に型付きの値を代入する。
	wait_between_actions: float = Field(default=0.5, description='Time to wait between actions.')

	# --- UI/viewport/DOM ---

	# EN: Assign annotated value to highlight_elements.
	# JP: highlight_elements に型付きの値を代入する。
	highlight_elements: bool = Field(default=True, description='Highlight interactive elements on the page.')
	# EN: Assign annotated value to filter_highlight_ids.
	# JP: filter_highlight_ids に型付きの値を代入する。
	filter_highlight_ids: bool = Field(
		default=True, description='Only show element IDs in highlights if llm_representation is less than 10 characters.'
	)
	# EN: Assign annotated value to paint_order_filtering.
	# JP: paint_order_filtering に型付きの値を代入する。
	paint_order_filtering: bool = Field(default=True, description='Enable paint order filtering. Slightly experimental.')

	# --- Downloads ---
	# EN: Assign annotated value to auto_download_pdfs.
	# JP: auto_download_pdfs に型付きの値を代入する。
	auto_download_pdfs: bool = Field(default=True, description='Automatically download PDFs when navigating to PDF viewer pages.')

	# EN: Assign annotated value to profile_directory.
	# JP: profile_directory に型付きの値を代入する。
	profile_directory: str = 'Default'  # e.g. 'Profile 1', 'Profile 2', 'Custom Profile', etc.

	# these can be found in BrowserLaunchArgs, BrowserLaunchPersistentContextArgs, BrowserNewContextArgs, BrowserConnectArgs:
	# save_recording_path: alias of record_video_dir
	# save_har_path: alias of record_har_path
	# trace_path: alias of traces_dir

	# these shadow the old playwright args on BrowserContextArgs, but it's ok
	# because we handle them ourselves in a watchdog and we no longer use playwright, so they should live in the scope for our own config in BrowserProfile long-term
	# EN: Assign annotated value to record_video_dir.
	# JP: record_video_dir に型付きの値を代入する。
	record_video_dir: Path | None = Field(
		default=None,
		description='Directory to save video recordings. If set, a video of the session will be recorded.',
		validation_alias=AliasChoices('save_recording_path', 'record_video_dir'),
	)
	# EN: Assign annotated value to record_video_size.
	# JP: record_video_size に型付きの値を代入する。
	record_video_size: ViewportSize | None = Field(
		default=None, description='Video frame size. If not set, it will use the viewport size.'
	)
	# EN: Assign annotated value to record_video_framerate.
	# JP: record_video_framerate に型付きの値を代入する。
	record_video_framerate: int = Field(default=30, description='The framerate to use for the video recording.')

	# TODO: finish implementing extension support in extensions.py
	# extension_ids_to_preinstall: list[str] = Field(
	#     default_factory=list, description='List of Chrome extension IDs to preinstall.'
	# )
	# extensions_dir: Path = Field(
	#     default_factory=lambda: Path('~/.config/browseruse/cache/extensions').expanduser(),
	#     description='Directory containing .crx extension files.',
	# )

	# EN: Define function `__repr__`.
	# JP: 関数 `__repr__` を定義する。
	def __repr__(self) -> str:
		# EN: Assign value to short_dir.
		# JP: short_dir に値を代入する。
		short_dir = _log_pretty_path(self.user_data_dir) if self.user_data_dir else '<incognito>'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'BrowserProfile(user_data_dir= {short_dir}, headless={self.headless})'

	# EN: Define function `__str__`.
	# JP: 関数 `__str__` を定義する。
	def __str__(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'BrowserProfile'

	# EN: Define function `copy_old_config_names_to_new`.
	# JP: 関数 `copy_old_config_names_to_new` を定義する。
	@model_validator(mode='after')
	def copy_old_config_names_to_new(self) -> Self:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Copy old config window_width & window_height to window_size."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.window_width or self.window_height:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(
				f'⚠️ BrowserProfile(window_width=..., window_height=...) are deprecated, use BrowserProfile(window_size={"width": 1920, "height": 1080}) instead.'
			)
			# EN: Assign value to window_size.
			# JP: window_size に値を代入する。
			window_size = self.window_size or ViewportSize(width=0, height=0)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			window_size['width'] = window_size['width'] or self.window_width or 1920
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			window_size['height'] = window_size['height'] or self.window_height or 1080
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.window_size = window_size

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define function `warn_storage_state_user_data_dir_conflict`.
	# JP: 関数 `warn_storage_state_user_data_dir_conflict` を定義する。
	@model_validator(mode='after')
	def warn_storage_state_user_data_dir_conflict(self) -> Self:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Warn when both storage_state and user_data_dir are set, as this can cause conflicts."""
		# EN: Assign value to has_storage_state.
		# JP: has_storage_state に値を代入する。
		has_storage_state = self.storage_state is not None
		# EN: Assign value to has_user_data_dir.
		# JP: has_user_data_dir に値を代入する。
		has_user_data_dir = (self.user_data_dir is not None) and ('tmp' not in str(self.user_data_dir).lower())

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if has_storage_state and has_user_data_dir:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(
				f'⚠️ BrowserSession(...) was passed both storage_state AND user_data_dir. storage_state={self.storage_state} will forcibly overwrite '
				f'cookies/localStorage/sessionStorage in user_data_dir={self.user_data_dir}. '
				f'For multiple browsers in parallel, use only storage_state with user_data_dir=None, '
				f'or use a separate user_data_dir for each browser and set storage_state=None.'
			)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define function `warn_user_data_dir_non_default_version`.
	# JP: 関数 `warn_user_data_dir_non_default_version` を定義する。
	@model_validator(mode='after')
	def warn_user_data_dir_non_default_version(self) -> Self:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		If user is using default profile dir with a non-default channel, force-change it
		to avoid corrupting the default data dir created with a different channel.
		"""

		# EN: Assign value to is_not_using_default_chromium.
		# JP: is_not_using_default_chromium に値を代入する。
		is_not_using_default_chromium = self.executable_path or self.channel not in (BROWSERUSE_DEFAULT_CHANNEL, None)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.user_data_dir == CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR and is_not_using_default_chromium:
			# EN: Assign value to alternate_name.
			# JP: alternate_name に値を代入する。
			alternate_name = (
				Path(self.executable_path).name.lower().replace(' ', '-')
				if self.executable_path
				else self.channel.name.lower()
				if self.channel
				else 'None'
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(
				f'⚠️ {self} Changing user_data_dir= {_log_pretty_path(self.user_data_dir)} ➡️ .../default-{alternate_name} to avoid {alternate_name.upper()} corruping default profile created by {BROWSERUSE_DEFAULT_CHANNEL.name}'
			)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.user_data_dir = CONFIG.BROWSER_USE_DEFAULT_USER_DATA_DIR.parent / f'default-{alternate_name}'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define function `warn_deterministic_rendering_weirdness`.
	# JP: 関数 `warn_deterministic_rendering_weirdness` を定義する。
	@model_validator(mode='after')
	def warn_deterministic_rendering_weirdness(self) -> Self:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.deterministic_rendering:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(
				'⚠️ BrowserSession(deterministic_rendering=True) is NOT RECOMMENDED. It breaks many sites and increases chances of getting blocked by anti-bot systems. '
				'It hardcodes the JS random seed and forces browsers across Linux/Mac/Windows to use the same font rendering engine so that identical screenshots can be generated.'
			)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define function `validate_proxy_settings`.
	# JP: 関数 `validate_proxy_settings` を定義する。
	@model_validator(mode='after')
	def validate_proxy_settings(self) -> Self:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Ensure proxy configuration is consistent."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.proxy and (self.proxy.bypass and not self.proxy.server):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning('BrowserProfile.proxy.bypass provided but proxy has no server; bypass will be ignored.')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self

	# EN: Define function `model_post_init`.
	# JP: 関数 `model_post_init` を定義する。
	def model_post_init(self, __context: Any) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Called after model initialization to set up display configuration."""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.detect_display_configuration()

	# EN: Define function `get_args`.
	# JP: 関数 `get_args` を定義する。
	def get_args(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the list of all Chrome CLI launch args for this profile (compiled from defaults, user-provided, and system-specific)."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(self.ignore_default_args, list):
			# EN: Assign value to default_args.
			# JP: default_args に値を代入する。
			default_args = set(CHROME_DEFAULT_ARGS) - set(self.ignore_default_args)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.ignore_default_args is True:
			# EN: Assign value to default_args.
			# JP: default_args に値を代入する。
			default_args = []
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif not self.ignore_default_args:
			# EN: Assign value to default_args.
			# JP: default_args に値を代入する。
			default_args = CHROME_DEFAULT_ARGS

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.user_data_dir is not None, 'user_data_dir must be set to a non-default path'

		# Capture args before conversion for logging
		# EN: Assign value to pre_conversion_args.
		# JP: pre_conversion_args に値を代入する。
		pre_conversion_args = [
			*default_args,
			*self.args,
			f'--user-data-dir={self.user_data_dir}',
			f'--profile-directory={self.profile_directory}',
			*(CHROME_DOCKER_ARGS if (CONFIG.IN_DOCKER or not self.chromium_sandbox) else []),
			*(CHROME_HEADLESS_ARGS if self.headless else []),
			*(CHROME_DISABLE_SECURITY_ARGS if self.disable_security else []),
			*(CHROME_DETERMINISTIC_RENDERING_ARGS if self.deterministic_rendering else []),
			*(
				[f'--window-size={self.window_size["width"]},{self.window_size["height"]}']
				if self.window_size
				else (['--start-maximized'] if (not self.headless or (self.cdp_url and not self.is_local)) else [])
			),
			*(
				[f'--window-position={self.window_position["width"]},{self.window_position["height"]}']
				if self.window_position
				else []
			),
			*(self._get_extension_args() if self.enable_default_extensions else []),
		]

		# Proxy flags
		# EN: Assign value to proxy_server.
		# JP: proxy_server に値を代入する。
		proxy_server = self.proxy.server if self.proxy else None
		# EN: Assign value to proxy_bypass.
		# JP: proxy_bypass に値を代入する。
		proxy_bypass = self.proxy.bypass if self.proxy else None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if proxy_server:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pre_conversion_args.append(f'--proxy-server={proxy_server}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if proxy_bypass:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				pre_conversion_args.append(f'--proxy-bypass-list={proxy_bypass}')

		# User agent flag
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.user_agent:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			pre_conversion_args.append(f'--user-agent={self.user_agent}')

		# Special handling for --disable-features to merge values instead of overwriting
		# This prevents disable_security=True from breaking extensions by ensuring
		# both default features (including extension-related) and security features are preserved
		# EN: Assign value to disable_features_values.
		# JP: disable_features_values に値を代入する。
		disable_features_values = []
		# EN: Assign value to non_disable_features_args.
		# JP: non_disable_features_args に値を代入する。
		non_disable_features_args = []

		# Extract and merge all --disable-features values
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for arg in pre_conversion_args:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if arg.startswith('--disable-features='):
				# EN: Assign value to features.
				# JP: features に値を代入する。
				features = arg.split('=', 1)[1]
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				disable_features_values.extend(features.split(','))
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				non_disable_features_args.append(arg)

		# Remove duplicates while preserving order
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if disable_features_values:
			# EN: Assign value to unique_features.
			# JP: unique_features に値を代入する。
			unique_features = []
			# EN: Assign value to seen.
			# JP: seen に値を代入する。
			seen = set()
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for feature in disable_features_values:
				# EN: Assign value to feature.
				# JP: feature に値を代入する。
				feature = feature.strip()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if feature and feature not in seen:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					unique_features.append(feature)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					seen.add(feature)

			# Add merged disable-features back
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			non_disable_features_args.append(f'--disable-features={",".join(unique_features)}')

		# convert to dict and back to dedupe and merge other duplicate args
		# EN: Assign value to final_args_list.
		# JP: final_args_list に値を代入する。
		final_args_list = BrowserLaunchArgs.args_as_list(BrowserLaunchArgs.args_as_dict(non_disable_features_args))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return final_args_list

	# EN: Define function `_get_extension_args`.
	# JP: 関数 `_get_extension_args` を定義する。
	def _get_extension_args(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get Chrome args for enabling default extensions (ad blocker and cookie handler)."""
		# EN: Assign value to extension_paths.
		# JP: extension_paths に値を代入する。
		extension_paths = self._ensure_default_extensions_downloaded()

		# EN: Assign value to args.
		# JP: args に値を代入する。
		args = [
			'--enable-extensions',
			'--disable-extensions-file-access-check',
			'--disable-extensions-http-throttling',
			'--enable-extension-activity-logging',
		]

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if extension_paths:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			args.append(f'--load-extension={",".join(extension_paths)}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return args

	# EN: Define function `_ensure_default_extensions_downloaded`.
	# JP: 関数 `_ensure_default_extensions_downloaded` を定義する。
	def _ensure_default_extensions_downloaded(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Ensure default extensions are downloaded and cached locally.
		Returns list of paths to extension directories.
		"""

		# Extension definitions - optimized for automation and content extraction
		# Combines uBlock Origin (ad blocking) + "I still don't care about cookies" (cookie banner handling)
		# EN: Assign value to extensions.
		# JP: extensions に値を代入する。
		extensions = [
			{
				'name': 'uBlock Origin',
				'id': 'cjpalhdlnbpafiamejdnhcphjbkeiagm',
				'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=133&acceptformat=crx3&x=id%3Dcjpalhdlnbpafiamejdnhcphjbkeiagm%26uc',
			},
			{
				'name': "I still don't care about cookies",
				'id': 'edibdbjcniadpccecjdfdjjppcpchdlm',
				'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=133&acceptformat=crx3&x=id%3Dedibdbjcniadpccecjdfdjjppcpchdlm%26uc',
			},
			{
				'name': 'ClearURLs',
				'id': 'lckanjgmijmafbedllaakclkaicjfmnk',
				'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=133&acceptformat=crx3&x=id%3Dlckanjgmijmafbedllaakclkaicjfmnk%26uc',
			},
			# {
			#     'name': 'Captcha Solver: Auto captcha solving service',
			#     'id': 'pgojnojmmhpofjgdmaebadhbocahppod',
			#     'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=130&acceptformat=crx3&x=id%3Dpgojnojmmhpofjgdmaebadhbocahppod%26uc',
			# },
			# Consent-O-Matic disabled - using uBlock Origin's cookie lists instead for simplicity
			# {
			#     'name': 'Consent-O-Matic',
			#     'id': 'mdjildafknihdffpkfmmpnpoiajfjnjd',
			#     'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=130&acceptformat=crx3&x=id%3Dmdjildafknihdffpkfmmpnpoiajfjnjd%26uc',
			# },
			# {
			#     'name': 'Privacy | Protect Your Payments',
			#     'id': 'hmgpakheknboplhmlicfkkgjipfabmhp',
			#     'url': 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=130&acceptformat=crx3&x=id%3Dhmgpakheknboplhmlicfkkgjipfabmhp%26uc',
			# },
		]

		# Create extensions cache directory
		# EN: Assign value to cache_dir.
		# JP: cache_dir に値を代入する。
		cache_dir = CONFIG.BROWSER_USE_EXTENSIONS_DIR
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		cache_dir.mkdir(parents=True, exist_ok=True)
		# logger.debug(f'📁 Extensions cache directory: {_log_pretty_path(cache_dir)}')

		# EN: Assign value to extension_paths.
		# JP: extension_paths に値を代入する。
		extension_paths = []
		# EN: Assign value to loaded_extension_names.
		# JP: loaded_extension_names に値を代入する。
		loaded_extension_names = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for ext in extensions:
			# EN: Assign value to ext_dir.
			# JP: ext_dir に値を代入する。
			ext_dir = cache_dir / ext['id']
			# EN: Assign value to crx_file.
			# JP: crx_file に値を代入する。
			crx_file = cache_dir / f'{ext["id"]}.crx'

			# Check if extension is already extracted
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if ext_dir.exists() and (ext_dir / 'manifest.json').exists():
				# logger.debug(f'✅ Using cached {ext["name"]} extension from {_log_pretty_path(ext_dir)}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				extension_paths.append(str(ext_dir))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				loaded_extension_names.append(ext['name'])
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Download extension if not cached
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not crx_file.exists():
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.info(f'📦 Downloading {ext["name"]} extension...')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					self._download_extension(ext['url'], crx_file)
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug(f'📦 Found cached {ext["name"]} .crx file')

				# Extract extension
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'📂 Extracting {ext["name"]} extension...')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._extract_extension(crx_file, ext_dir)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				extension_paths.append(str(ext_dir))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				loaded_extension_names.append(ext['name'])

			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.warning(f'⚠️ Failed to setup {ext["name"]} extension: {e}')
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

		# Apply minimal patch to cookie extension with configurable whitelist
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, path in enumerate(extension_paths):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if loaded_extension_names[i] == "I still don't care about cookies":
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._apply_minimal_extension_patch(Path(path), self.cookie_whitelist_domains)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if extension_paths:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'[BrowserProfile] 🧩 Extensions loaded ({len(extension_paths)}): [{", ".join(loaded_extension_names)}]')
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning('[BrowserProfile] ⚠️ No default extensions could be loaded')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return extension_paths

	# EN: Define function `_apply_minimal_extension_patch`.
	# JP: 関数 `_apply_minimal_extension_patch` を定義する。
	def _apply_minimal_extension_patch(self, ext_dir: Path, whitelist_domains: list[str]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Minimal patch: pre-populate chrome.storage.local with configurable domain whitelist."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to bg_path.
			# JP: bg_path に値を代入する。
			bg_path = ext_dir / 'data' / 'background.js'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not bg_path.exists():
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with open(bg_path, encoding='utf-8') as f:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = f.read()

			# Create the whitelisted domains object for JavaScript with proper indentation
			# EN: Assign value to whitelist_entries.
			# JP: whitelist_entries に値を代入する。
			whitelist_entries = [f'        "{domain}": true' for domain in whitelist_domains]
			# EN: Assign value to whitelist_js.
			# JP: whitelist_js に値を代入する。
			whitelist_js = '{\n' + ',\n'.join(whitelist_entries) + '\n      }'

			# Find the initialize() function and inject storage setup before updateSettings()
			# The actual function uses 2-space indentation, not tabs
			# EN: Assign value to old_init.
			# JP: old_init に値を代入する。
			old_init = """async function initialize(checkInitialized, magic) {
  if (checkInitialized && initialized) {
    return;
  }
  loadCachedRules();
  await updateSettings();
  await recreateTabList(magic);
  initialized = true;
}"""

			# New function with configurable whitelist initialization
			# EN: Assign value to new_init.
			# JP: new_init に値を代入する。
			new_init = f"""// Pre-populate storage with configurable domain whitelist if empty
async function ensureWhitelistStorage() {{
  const result = await chrome.storage.local.get({{ settings: null }});
  if (!result.settings) {{
    const defaultSettings = {{
      statusIndicators: true,
      whitelistedDomains: {whitelist_js}
    }};
    await chrome.storage.local.set({{ settings: defaultSettings }});
  }}
}}

async function initialize(checkInitialized, magic) {{
  if (checkInitialized && initialized) {{
    return;
  }}
  loadCachedRules();
  await ensureWhitelistStorage(); // Add storage initialization
  await updateSettings();
  await recreateTabList(magic);
  initialized = true;
}}"""

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if old_init in content:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = content.replace(old_init, new_init)

				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with open(bg_path, 'w', encoding='utf-8') as f:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					f.write(content)

				# EN: Assign value to domain_list.
				# JP: domain_list に値を代入する。
				domain_list = ', '.join(whitelist_domains)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.info(f'[BrowserProfile] ✅ Cookie extension: {domain_list} pre-populated in storage')
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('[BrowserProfile] Initialize function not found for patching')

		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'[BrowserProfile] Could not patch extension storage: {e}')

	# EN: Define function `_download_extension`.
	# JP: 関数 `_download_extension` を定義する。
	def _download_extension(self, url: str, output_path: Path) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Download extension .crx file."""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import urllib.request

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with urllib.request.urlopen(url) as response:
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with open(output_path, 'wb') as f:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					f.write(response.read())
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise Exception(f'Failed to download extension: {e}')

	# EN: Define function `_extract_extension`.
	# JP: 関数 `_extract_extension` を定義する。
	def _extract_extension(self, crx_path: Path, extract_dir: Path) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract .crx file to directory."""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import os
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		import zipfile

		# Remove existing directory
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if extract_dir.exists():
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import shutil

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			shutil.rmtree(extract_dir)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		extract_dir.mkdir(parents=True, exist_ok=True)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# CRX files are ZIP files with a header, try to extract as ZIP
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with zipfile.ZipFile(crx_path, 'r') as zip_ref:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				zip_ref.extractall(extract_dir)

			# Verify manifest exists
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not (extract_dir / 'manifest.json').exists():
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise Exception('No manifest.json found in extension')

		except zipfile.BadZipFile:
			# CRX files have a header before the ZIP data
			# Skip the CRX header and extract the ZIP part
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with open(crx_path, 'rb') as f:
				# Read CRX header to find ZIP start
				# EN: Assign value to magic.
				# JP: magic に値を代入する。
				magic = f.read(4)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if magic != b'Cr24':
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise Exception('Invalid CRX file format')

				# EN: Assign value to version.
				# JP: version に値を代入する。
				version = int.from_bytes(f.read(4), 'little')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if version == 2:
					# EN: Assign value to pubkey_len.
					# JP: pubkey_len に値を代入する。
					pubkey_len = int.from_bytes(f.read(4), 'little')
					# EN: Assign value to sig_len.
					# JP: sig_len に値を代入する。
					sig_len = int.from_bytes(f.read(4), 'little')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					f.seek(16 + pubkey_len + sig_len)  # Skip to ZIP data
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif version == 3:
					# EN: Assign value to header_len.
					# JP: header_len に値を代入する。
					header_len = int.from_bytes(f.read(4), 'little')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					f.seek(12 + header_len)  # Skip to ZIP data

				# Extract ZIP data
				# EN: Assign value to zip_data.
				# JP: zip_data に値を代入する。
				zip_data = f.read()

			# Write ZIP data to temp file and extract
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			import tempfile

			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				temp_zip.write(zip_data)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				temp_zip.flush()

				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					zip_ref.extractall(extract_dir)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				os.unlink(temp_zip.name)

	# EN: Define function `detect_display_configuration`.
	# JP: 関数 `detect_display_configuration` を定義する。
	def detect_display_configuration(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Detect the system display size and initialize the display-related config defaults:
		        screen, window_size, window_position, viewport, no_viewport, device_scale_factor
		"""

		# EN: Assign value to display_size.
		# JP: display_size に値を代入する。
		display_size = get_display_size()
		# EN: Assign value to force_remote_headful.
		# JP: force_remote_headful に値を代入する。
		force_remote_headful = bool(self.cdp_url and not self.is_local)
		# Remote CDP sessions (e.g. selenium/standalone-chrome) expose a headful display
		# even when local display detection fails, so treat them as screen-available.
		# EN: Assign value to has_screen_available.
		# JP: has_screen_available に値を代入する。
		has_screen_available = bool(display_size) or force_remote_headful
		# EN: Assign value to detected_screen.
		# JP: detected_screen に値を代入する。
		detected_screen = self.screen or display_size or ViewportSize(width=1920, height=1080)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.screen = detected_screen
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._detected_screen = detected_screen

		# Prefer headful mode for remote sessions and when a display is available by default
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if force_remote_headful:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.headless = False
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif self.headless is None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.headless = not has_screen_available

		# Determine viewport behavior based on mode and user preferences
		# EN: Assign value to user_provided_viewport.
		# JP: user_provided_viewport に値を代入する。
		user_provided_viewport = self.viewport is not None
		# EN: Assign value to user_provided_window_size.
		# JP: user_provided_window_size に値を代入する。
		user_provided_window_size = self.window_size is not None

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.headless:
			# Headless mode: always use viewport for content size control
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.viewport = self.viewport or self.window_size or self.screen
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.window_position = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.window_size = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.no_viewport = False
		else:
			# Headful mode: respect user's viewport preference
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not user_provided_window_size:
				# Default behaviour should maximise the window to fill the display.
				# When Chrome receives an explicit --window-size argument it will
				# use that resolution even if it is smaller than the available
				# display, which caused the visible gap on wide screens. By leaving
				# window_size unset we allow the default --start-maximized flag to
				# take effect so the browser fills all available space. Only keep
				# window_size when a user explicitly configured it or when no
				# display is detected (e.g. virtual display fallback).
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if has_screen_available:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.window_size = None
				else:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					self.window_size = ViewportSize(width=1920, height=1080)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if user_provided_viewport:
				# User explicitly set viewport - enable viewport mode
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.no_viewport = False
			else:
				# Default headful: content fits to window (no viewport)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.no_viewport = True if self.no_viewport is None else self.no_viewport

		# Handle special requirements (device_scale_factor forces viewport mode)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.device_scale_factor and self.no_viewport is None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.no_viewport = False

		# Finalize configuration
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.no_viewport:
			# No viewport mode: content adapts to window
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.viewport = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.device_scale_factor = None
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.screen = None
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.viewport is None
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.no_viewport is True
		else:
			# Viewport mode: ensure viewport is set
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.viewport = self.viewport or self.screen
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.device_scale_factor = self.device_scale_factor or 1.0
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.viewport is not None
			# EN: Validate a required condition.
			# JP: 必須条件を検証する。
			assert self.no_viewport is False

		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert not (self.headless and self.no_viewport), 'headless=True and no_viewport=True cannot both be set at the same time'

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from contextlib import suppress
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# JP: CDP (Chrome DevTools Protocol) の検出/解決ロジック
# EN: CDP (Chrome DevTools Protocol) detection and resolution utilities
from .config import logger
from .env import _env_int

# JP: CDP URL 自動検出のチューニング値
# EN: Tunables for CDP auto-detection
_CDP_PROBE_TIMEOUT = float(os.environ.get('BROWSER_USE_CDP_TIMEOUT', '2.0'))
_CDP_DETECTION_RETRIES = _env_int('BROWSER_USE_CDP_RETRIES', 5)
_CDP_DETECTION_RETRY_DELAY = float(os.environ.get('BROWSER_USE_CDP_RETRY_DELAY', '1.5'))

# JP: 一時的に作成した WebDriver セッションの後片付け用
# EN: Cleanup hook for temporary WebDriver sessions
_CDP_SESSION_CLEANUP: Callable[[], None] | None = None


# EN: Define function `_replace_cdp_session_cleanup`.
# JP: 関数 `_replace_cdp_session_cleanup` を定義する。
def _replace_cdp_session_cleanup(cleanup: Callable[[], None] | None) -> None:
	"""Store a cleanup callback, closing any previously registered session."""

	# JP: 既存のクリーンアップ関数を差し替える
	# EN: Swap the current cleanup callback safely
	global _CDP_SESSION_CLEANUP

	previous = _CDP_SESSION_CLEANUP
	_CDP_SESSION_CLEANUP = cleanup
	if previous and previous is not cleanup:
		with suppress(Exception):
			previous()


# EN: Define function `_consume_cdp_session_cleanup`.
# JP: 関数 `_consume_cdp_session_cleanup` を定義する。
def _consume_cdp_session_cleanup() -> Callable[[], None] | None:
	"""Return and clear the currently registered CDP cleanup callback."""

	# JP: 現在のクリーンアップ関数を取り出してクリアする
	# EN: Pop the cleanup callback and clear it
	global _CDP_SESSION_CLEANUP

	cleanup = _CDP_SESSION_CLEANUP
	_CDP_SESSION_CLEANUP = None
	return cleanup


# EN: Define function `_probe_cdp_candidate`.
# JP: 関数 `_probe_cdp_candidate` を定義する。
def _probe_cdp_candidate(base_url: str) -> str | None:
	# JP: /json/version などの既知パスを巡回して WebSocket URL を取得
	# EN: Probe known endpoints to extract a WebSocket debugger URL
	base = base_url.rstrip('/')
	paths = ('/json/version', '/devtools/version', '/json')
	for path in paths:
		target = f'{base}{path}'
		try:
			with urlopen(target, timeout=_CDP_PROBE_TIMEOUT) as response:
				if response.status != 200:
					continue
				try:
					payload: Any = json.load(response)
				except json.JSONDecodeError:
					continue
		except (URLError, HTTPError, TimeoutError, OSError):
			continue

		if isinstance(payload, dict):
			ws_url = payload.get('webSocketDebuggerUrl') or payload.get('webSocketUrl') or payload.get('websocketUrl')
			if ws_url:
				candidate_url = ws_url.strip()
				if candidate_url:
					_replace_cdp_session_cleanup(None)
					return candidate_url
		elif isinstance(payload, list):
			for item in payload:
				if isinstance(item, dict):
					ws_url = item.get('webSocketDebuggerUrl')
					if ws_url:
						candidate_url = ws_url.strip()
						if candidate_url:
							_replace_cdp_session_cleanup(None)
							return candidate_url
	return None


# EN: Define function `_extract_cdp_url`.
# JP: 関数 `_extract_cdp_url` を定義する。
def _extract_cdp_url(capabilities: dict[str, Any]) -> str | None:
	# JP: WebDriver capabilities から CDP URL を抽出
	# EN: Extract CDP URL from WebDriver capabilities
	for key in ('se:cdp', 'se:cdpUrl', 'se:cdpURL'):
		raw_value = capabilities.get(key)
		if isinstance(raw_value, str):
			trimmed = raw_value.strip()
			if trimmed:
				return trimmed
	return None


# EN: Define function `_cleanup_webdriver_session`.
# JP: 関数 `_cleanup_webdriver_session` を定義する。
def _cleanup_webdriver_session(base_endpoint: str, session_id: str) -> None:
	# JP: 作成した WebDriver セッションを終了してリソースを解放
	# EN: Terminate the temporary WebDriver session to free resources
	delete_url = f'{base_endpoint}/session/{session_id}'
	request = Request(delete_url, method='DELETE')
	try:
		with urlopen(request, timeout=_CDP_PROBE_TIMEOUT):
			pass
	except (URLError, HTTPError, TimeoutError, OSError):
		logger.debug('Failed to clean up temporary WebDriver session %s', session_id, exc_info=True)


# EN: Define function `_probe_webdriver_endpoint`.
# JP: 関数 `_probe_webdriver_endpoint` を定義する。
def _probe_webdriver_endpoint(base_endpoint: str) -> str | None:
	# JP: WebDriver にセッション作成を試み、返却 capabilities から CDP URL を取得
	# EN: Try a WebDriver session and read the CDP URL from returned capabilities
	session_url = f'{base_endpoint}/session'
	payload = json.dumps(
		{
			'capabilities': {
				'alwaysMatch': {
					'browserName': 'chrome',
				}
			}
		}
	).encode('utf-8')
	request = Request(
		session_url,
		data=payload,
		headers={'Content-Type': 'application/json'},
	)

	session_id: str | None = None
	capabilities: dict[str, Any] | None = None

	try:
		with urlopen(request, timeout=_CDP_PROBE_TIMEOUT) as response:
			if response.status not in (200, 201):
				return None
			try:
				data: Any = json.load(response)
			except json.JSONDecodeError:
				return None
	except (URLError, HTTPError, TimeoutError, OSError):
		return None

	if isinstance(data, dict):
		value = data.get('value')
		if isinstance(value, dict):
			maybe_caps = value.get('capabilities')
			if isinstance(maybe_caps, dict):
				capabilities = maybe_caps
			raw_session = value.get('sessionId')
			if isinstance(raw_session, str) and raw_session.strip():
				session_id = raw_session.strip()
		if capabilities is None:
			maybe_caps = data.get('capabilities')
			if isinstance(maybe_caps, dict):
				capabilities = maybe_caps
		if not session_id:
			raw_session = data.get('sessionId')
			if isinstance(raw_session, str) and raw_session.strip():
				session_id = raw_session.strip()

	cdp_url = _extract_cdp_url(capabilities) if capabilities else None
	if cdp_url:
		cdp_url = cdp_url.strip()

	if not cdp_url:
		if session_id:
			_cleanup_webdriver_session(base_endpoint, session_id)
		return None

	if session_id:
		cleaned = False

		# EN: Define function `cleanup_session`.
		# JP: 関数 `cleanup_session` を定義する。
		def cleanup_session() -> None:
			# JP: DELETE が多重実行されないよう一度だけ実行する
			# EN: Ensure session DELETE is executed at most once
			nonlocal cleaned
			if cleaned:
				return
			cleaned = True
			_cleanup_webdriver_session(base_endpoint, session_id)

		_replace_cdp_session_cleanup(cleanup_session)
	else:
		_replace_cdp_session_cleanup(None)

	return cdp_url


# EN: Define function `_probe_cdp_via_webdriver`.
# JP: 関数 `_probe_cdp_via_webdriver` を定義する。
def _probe_cdp_via_webdriver(base_url: str) -> str | None:
	# JP: WebDriver 経由で CDP URL を取得できるか試す
	# EN: Attempt to obtain CDP URL via WebDriver endpoints
	normalized = base_url.strip()
	if not normalized or not normalized.lower().startswith(('http://', 'https://')):
		return None

	normalized = normalized.rstrip('/')
	endpoints = []
	if normalized:
		endpoints.append(normalized)
		if not normalized.endswith('/wd/hub'):
			endpoints.append(f'{normalized}/wd/hub')

	seen: set[str] = set()
	for endpoint in endpoints:
		endpoint = endpoint.rstrip('/')
		if not endpoint or endpoint in seen:
			continue
		seen.add(endpoint)
		ws_url = _probe_webdriver_endpoint(endpoint)
		if ws_url:
			return ws_url
	return None


# EN: Define function `_detect_cdp_from_candidates`.
# JP: 関数 `_detect_cdp_from_candidates` を定義する。
def _detect_cdp_from_candidates(candidates: list[str]) -> str | None:
	# JP: 候補 URL から CDP の WebSocket を順に検出
	# EN: Scan candidates for a valid CDP WebSocket URL
	for candidate in candidates:
		ws_url = _probe_cdp_candidate(candidate)
		if ws_url:
			logger.info('Detected Chrome DevTools endpoint at %s', candidate)
			return ws_url

	for candidate in candidates:
		ws_url = _probe_cdp_via_webdriver(candidate)
		if ws_url:
			logger.info('Detected Chrome DevTools endpoint via WebDriver at %s', candidate)
			return ws_url

	return None


# EN: Define function `_resolve_cdp_url`.
# JP: 関数 `_resolve_cdp_url` を定義する。
def _resolve_cdp_url() -> str | None:
	# JP: 環境変数の明示指定を優先し、無ければ候補探索を行う
	# EN: Prefer explicit env vars, otherwise probe candidate endpoints
	explicit_keys = ('BROWSER_USE_CDP_URL', 'CDP_URL', 'REMOTE_CDP_URL')
	for key in explicit_keys:
		value = os.environ.get(key)
		if value:
			logger.info('Using CDP URL from %s', key)
			_replace_cdp_session_cleanup(None)
			return value.strip()

	candidate_env = os.environ.get('BROWSER_USE_CDP_CANDIDATES')
	if candidate_env:
		# JP: 逗号区切りの候補URLを優先的に利用する
		# EN: Prefer explicitly supplied comma-separated candidate URLs
		candidates = [entry.strip() for entry in candidate_env.split(',') if entry.strip()]
	else:
		# JP: 典型的な Docker/ローカル構成向けの既定候補
		# EN: Default candidate endpoints for common Docker/local layouts
		candidates = [
			'http://browser:9222',
			'http://browser:4444',
			'http://browser:4444/wd/hub',
			'http://localhost:9222',
			'http://localhost:4444',
			'http://localhost:4444/wd/hub',
			'http://127.0.0.1:9222',
			'http://127.0.0.1:4444',
			'http://127.0.0.1:4444/wd/hub',
		]

	retries = max(1, _CDP_DETECTION_RETRIES)
	delay = _CDP_DETECTION_RETRY_DELAY if _CDP_DETECTION_RETRY_DELAY > 0 else 0.0

	for attempt in range(1, retries + 1):
		# JP: 既定回数まで検出をリトライする
		# EN: Retry detection up to the configured limit
		ws_url = _detect_cdp_from_candidates(candidates)
		if ws_url:
			return ws_url

		cleanup = _consume_cdp_session_cleanup()
		if cleanup:
			with suppress(Exception):
				cleanup()

		if attempt < retries:
			logger.info(
				'Chrome DevToolsのCDP URLの検出に失敗しました。リトライします (%s/%s)...',
				attempt + 1,
				retries,
			)
			if delay:
				# JP: 起動直後の CDP 待ちに備えてリトライ間隔を空ける
				# EN: Sleep between retries to allow CDP endpoint startup
				time.sleep(delay)

	logger.warning('Chrome DevToolsのCDP URLを自動検出できませんでした。環境変数BROWSER_USE_CDP_URLを設定してください。')
	return None

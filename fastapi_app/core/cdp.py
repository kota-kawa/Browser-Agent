# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Callable
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from contextlib import suppress
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.error import HTTPError, URLError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.request import Request, urlopen

# JP: CDP (Chrome DevTools Protocol) の検出/解決ロジック
# EN: CDP (Chrome DevTools Protocol) detection and resolution utilities
from .config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .env import _env_int

# JP: CDP URL 自動検出のチューニング値
# EN: Tunables for CDP auto-detection
_CDP_PROBE_TIMEOUT = float(os.environ.get('BROWSER_USE_CDP_TIMEOUT', '2.0'))
# EN: Assign value to _CDP_DETECTION_RETRIES.
# JP: _CDP_DETECTION_RETRIES に値を代入する。
_CDP_DETECTION_RETRIES = _env_int('BROWSER_USE_CDP_RETRIES', 5)
# EN: Assign value to _CDP_DETECTION_RETRY_DELAY.
# JP: _CDP_DETECTION_RETRY_DELAY に値を代入する。
_CDP_DETECTION_RETRY_DELAY = float(os.environ.get('BROWSER_USE_CDP_RETRY_DELAY', '1.5'))

# JP: 一時的に作成した WebDriver セッションの後片付け用
# EN: Cleanup hook for temporary WebDriver sessions
_CDP_SESSION_CLEANUP: Callable[[], None] | None = None


# EN: Define function `_replace_cdp_session_cleanup`.
# JP: 関数 `_replace_cdp_session_cleanup` を定義する。
def _replace_cdp_session_cleanup(cleanup: Callable[[], None] | None) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Store a cleanup callback, closing any previously registered session."""

	# JP: 既存のクリーンアップ関数を差し替える
	# EN: Swap the current cleanup callback safely
	global _CDP_SESSION_CLEANUP

	# EN: Assign value to previous.
	# JP: previous に値を代入する。
	previous = _CDP_SESSION_CLEANUP
	# EN: Assign value to _CDP_SESSION_CLEANUP.
	# JP: _CDP_SESSION_CLEANUP に値を代入する。
	_CDP_SESSION_CLEANUP = cleanup
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if previous and previous is not cleanup:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with suppress(Exception):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			previous()


# EN: Define function `_consume_cdp_session_cleanup`.
# JP: 関数 `_consume_cdp_session_cleanup` を定義する。
def _consume_cdp_session_cleanup() -> Callable[[], None] | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return and clear the currently registered CDP cleanup callback."""

	# JP: 現在のクリーンアップ関数を取り出してクリアする
	# EN: Pop the cleanup callback and clear it
	global _CDP_SESSION_CLEANUP

	# EN: Assign value to cleanup.
	# JP: cleanup に値を代入する。
	cleanup = _CDP_SESSION_CLEANUP
	# EN: Assign value to _CDP_SESSION_CLEANUP.
	# JP: _CDP_SESSION_CLEANUP に値を代入する。
	_CDP_SESSION_CLEANUP = None
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return cleanup


# EN: Define function `_probe_cdp_candidate`.
# JP: 関数 `_probe_cdp_candidate` を定義する。
def _probe_cdp_candidate(base_url: str) -> str | None:
	# JP: /json/version などの既知パスを巡回して WebSocket URL を取得
	# EN: Probe known endpoints to extract a WebSocket debugger URL
	base = base_url.rstrip('/')
	# EN: Assign value to paths.
	# JP: paths に値を代入する。
	paths = ('/json/version', '/devtools/version', '/json')
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for path in paths:
		# EN: Assign value to target.
		# JP: target に値を代入する。
		target = f'{base}{path}'
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with urlopen(target, timeout=_CDP_PROBE_TIMEOUT) as response:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if response.status != 200:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign annotated value to payload.
					# JP: payload に型付きの値を代入する。
					payload: Any = json.load(response)
				except json.JSONDecodeError:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
		except (URLError, HTTPError, TimeoutError, OSError):
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(payload, dict):
			# EN: Assign value to ws_url.
			# JP: ws_url に値を代入する。
			ws_url = payload.get('webSocketDebuggerUrl') or payload.get('webSocketUrl') or payload.get('websocketUrl')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if ws_url:
				# EN: Assign value to candidate_url.
				# JP: candidate_url に値を代入する。
				candidate_url = ws_url.strip()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if candidate_url:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					_replace_cdp_session_cleanup(None)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return candidate_url
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(payload, list):
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for item in payload:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(item, dict):
					# EN: Assign value to ws_url.
					# JP: ws_url に値を代入する。
					ws_url = item.get('webSocketDebuggerUrl')
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if ws_url:
						# EN: Assign value to candidate_url.
						# JP: candidate_url に値を代入する。
						candidate_url = ws_url.strip()
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if candidate_url:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							_replace_cdp_session_cleanup(None)
							# EN: Return a value from the function.
							# JP: 関数から値を返す。
							return candidate_url
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define function `_extract_cdp_url`.
# JP: 関数 `_extract_cdp_url` を定義する。
def _extract_cdp_url(capabilities: dict[str, Any]) -> str | None:
	# JP: WebDriver capabilities から CDP URL を抽出
	# EN: Extract CDP URL from WebDriver capabilities
	for key in ('se:cdp', 'se:cdpUrl', 'se:cdpURL'):
		# EN: Assign value to raw_value.
		# JP: raw_value に値を代入する。
		raw_value = capabilities.get(key)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(raw_value, str):
			# EN: Assign value to trimmed.
			# JP: trimmed に値を代入する。
			trimmed = raw_value.strip()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if trimmed:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return trimmed
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define function `_cleanup_webdriver_session`.
# JP: 関数 `_cleanup_webdriver_session` を定義する。
def _cleanup_webdriver_session(base_endpoint: str, session_id: str) -> None:
	# JP: 作成した WebDriver セッションを終了してリソースを解放
	# EN: Terminate the temporary WebDriver session to free resources
	delete_url = f'{base_endpoint}/session/{session_id}'
	# EN: Assign value to request.
	# JP: request に値を代入する。
	request = Request(delete_url, method='DELETE')
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with urlopen(request, timeout=_CDP_PROBE_TIMEOUT):
			# EN: Keep a placeholder statement.
			# JP: プレースホルダー文を維持する。
			pass
	except (URLError, HTTPError, TimeoutError, OSError):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Failed to clean up temporary WebDriver session %s', session_id, exc_info=True)


# EN: Define function `_probe_webdriver_endpoint`.
# JP: 関数 `_probe_webdriver_endpoint` を定義する。
def _probe_webdriver_endpoint(base_endpoint: str) -> str | None:
	# JP: WebDriver にセッション作成を試み、返却 capabilities から CDP URL を取得
	# EN: Try a WebDriver session and read the CDP URL from returned capabilities
	session_url = f'{base_endpoint}/session'
	# EN: Assign value to payload.
	# JP: payload に値を代入する。
	payload = json.dumps(
		{
			'capabilities': {
				'alwaysMatch': {
					'browserName': 'chrome',
				}
			}
		}
	).encode('utf-8')
	# EN: Assign value to request.
	# JP: request に値を代入する。
	request = Request(
		session_url,
		data=payload,
		headers={'Content-Type': 'application/json'},
	)

	# EN: Assign annotated value to session_id.
	# JP: session_id に型付きの値を代入する。
	session_id: str | None = None
	# EN: Assign annotated value to capabilities.
	# JP: capabilities に型付きの値を代入する。
	capabilities: dict[str, Any] | None = None

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with urlopen(request, timeout=_CDP_PROBE_TIMEOUT) as response:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if response.status not in (200, 201):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign annotated value to data.
				# JP: data に型付きの値を代入する。
				data: Any = json.load(response)
			except json.JSONDecodeError:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None
	except (URLError, HTTPError, TimeoutError, OSError):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if isinstance(data, dict):
		# EN: Assign value to value.
		# JP: value に値を代入する。
		value = data.get('value')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(value, dict):
			# EN: Assign value to maybe_caps.
			# JP: maybe_caps に値を代入する。
			maybe_caps = value.get('capabilities')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(maybe_caps, dict):
				# EN: Assign value to capabilities.
				# JP: capabilities に値を代入する。
				capabilities = maybe_caps
			# EN: Assign value to raw_session.
			# JP: raw_session に値を代入する。
			raw_session = value.get('sessionId')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(raw_session, str) and raw_session.strip():
				# EN: Assign value to session_id.
				# JP: session_id に値を代入する。
				session_id = raw_session.strip()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if capabilities is None:
			# EN: Assign value to maybe_caps.
			# JP: maybe_caps に値を代入する。
			maybe_caps = data.get('capabilities')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(maybe_caps, dict):
				# EN: Assign value to capabilities.
				# JP: capabilities に値を代入する。
				capabilities = maybe_caps
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not session_id:
			# EN: Assign value to raw_session.
			# JP: raw_session に値を代入する。
			raw_session = data.get('sessionId')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(raw_session, str) and raw_session.strip():
				# EN: Assign value to session_id.
				# JP: session_id に値を代入する。
				session_id = raw_session.strip()

	# EN: Assign value to cdp_url.
	# JP: cdp_url に値を代入する。
	cdp_url = _extract_cdp_url(capabilities) if capabilities else None
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if cdp_url:
		# EN: Assign value to cdp_url.
		# JP: cdp_url に値を代入する。
		cdp_url = cdp_url.strip()

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not cdp_url:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if session_id:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_cleanup_webdriver_session(base_endpoint, session_id)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if session_id:
		# EN: Assign value to cleaned.
		# JP: cleaned に値を代入する。
		cleaned = False

		# EN: Define function `cleanup_session`.
		# JP: 関数 `cleanup_session` を定義する。
		def cleanup_session() -> None:
			# EN: Execute this statement.
			# JP: この文を実行する。
			nonlocal cleaned
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cleaned:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return
			# EN: Assign value to cleaned.
			# JP: cleaned に値を代入する。
			cleaned = True
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_cleanup_webdriver_session(base_endpoint, session_id)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_replace_cdp_session_cleanup(cleanup_session)
	else:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_replace_cdp_session_cleanup(None)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return cdp_url


# EN: Define function `_probe_cdp_via_webdriver`.
# JP: 関数 `_probe_cdp_via_webdriver` を定義する。
def _probe_cdp_via_webdriver(base_url: str) -> str | None:
	# JP: WebDriver 経由で CDP URL を取得できるか試す
	# EN: Attempt to obtain CDP URL via WebDriver endpoints
	normalized = base_url.strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not normalized or not normalized.lower().startswith(('http://', 'https://')):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Assign value to normalized.
	# JP: normalized に値を代入する。
	normalized = normalized.rstrip('/')
	# EN: Assign value to endpoints.
	# JP: endpoints に値を代入する。
	endpoints = []
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if normalized:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		endpoints.append(normalized)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not normalized.endswith('/wd/hub'):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			endpoints.append(f'{normalized}/wd/hub')

	# EN: Assign annotated value to seen.
	# JP: seen に型付きの値を代入する。
	seen: set[str] = set()
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for endpoint in endpoints:
		# EN: Assign value to endpoint.
		# JP: endpoint に値を代入する。
		endpoint = endpoint.rstrip('/')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not endpoint or endpoint in seen:
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		seen.add(endpoint)
		# EN: Assign value to ws_url.
		# JP: ws_url に値を代入する。
		ws_url = _probe_webdriver_endpoint(endpoint)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ws_url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ws_url
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define function `_detect_cdp_from_candidates`.
# JP: 関数 `_detect_cdp_from_candidates` を定義する。
def _detect_cdp_from_candidates(candidates: list[str]) -> str | None:
	# JP: 候補 URL から CDP の WebSocket を順に検出
	# EN: Scan candidates for a valid CDP WebSocket URL
	for candidate in candidates:
		# EN: Assign value to ws_url.
		# JP: ws_url に値を代入する。
		ws_url = _probe_cdp_candidate(candidate)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ws_url:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('Detected Chrome DevTools endpoint at %s', candidate)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ws_url

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for candidate in candidates:
		# EN: Assign value to ws_url.
		# JP: ws_url に値を代入する。
		ws_url = _probe_cdp_via_webdriver(candidate)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ws_url:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('Detected Chrome DevTools endpoint via WebDriver at %s', candidate)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ws_url

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define function `_resolve_cdp_url`.
# JP: 関数 `_resolve_cdp_url` を定義する。
def _resolve_cdp_url() -> str | None:
	# JP: 環境変数の明示指定を優先し、無ければ候補探索を行う
	# EN: Prefer explicit env vars, otherwise probe candidate endpoints
	explicit_keys = ('BROWSER_USE_CDP_URL', 'CDP_URL', 'REMOTE_CDP_URL')
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for key in explicit_keys:
		# EN: Assign value to value.
		# JP: value に値を代入する。
		value = os.environ.get(key)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if value:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('Using CDP URL from %s', key)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_replace_cdp_session_cleanup(None)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return value.strip()

	# EN: Assign value to candidate_env.
	# JP: candidate_env に値を代入する。
	candidate_env = os.environ.get('BROWSER_USE_CDP_CANDIDATES')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if candidate_env:
		# EN: Assign value to candidates.
		# JP: candidates に値を代入する。
		candidates = [entry.strip() for entry in candidate_env.split(',') if entry.strip()]
	else:
		# EN: Assign value to candidates.
		# JP: candidates に値を代入する。
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

	# EN: Assign value to retries.
	# JP: retries に値を代入する。
	retries = max(1, _CDP_DETECTION_RETRIES)
	# EN: Assign value to delay.
	# JP: delay に値を代入する。
	delay = _CDP_DETECTION_RETRY_DELAY if _CDP_DETECTION_RETRY_DELAY > 0 else 0.0

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for attempt in range(1, retries + 1):
		# JP: 既定回数まで検出をリトライする
		# EN: Retry detection up to the configured limit
		ws_url = _detect_cdp_from_candidates(candidates)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if ws_url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ws_url

		# EN: Assign value to cleanup.
		# JP: cleanup に値を代入する。
		cleanup = _consume_cdp_session_cleanup()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if cleanup:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with suppress(Exception):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				cleanup()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if attempt < retries:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(
				'Chrome DevToolsのCDP URLの検出に失敗しました。リトライします (%s/%s)...',
				attempt + 1,
				retries,
			)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if delay:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				time.sleep(delay)

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	logger.warning('Chrome DevToolsのCDP URLを自動検出できませんでした。環境変数BROWSER_USE_CDP_URLを設定してください。')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None

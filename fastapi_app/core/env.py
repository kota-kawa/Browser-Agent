# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

# JP: 環境変数・URLの正規化を扱うユーティリティ
# EN: Utilities for environment variables and URL normalization
from .config import logger

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser.constants import DEFAULT_NEW_TAB_URL
except ModuleNotFoundError:
	# EN: Assign value to DEFAULT_NEW_TAB_URL.
	# JP: DEFAULT_NEW_TAB_URL に値を代入する。
	DEFAULT_NEW_TAB_URL = 'https://www.yahoo.co.jp'


# EN: Define function `_env_int`.
# JP: 関数 `_env_int` を定義する。
def _env_int(name: str, default: int) -> int:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return an integer environment variable with a fallback."""

	# JP: 未設定または不正値の場合は既定値にフォールバック
	# EN: Fall back to default on missing/invalid values
	raw_value = os.environ.get(name)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if raw_value is None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return default
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to parsed.
		# JP: parsed に値を代入する。
		parsed = int(raw_value)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return parsed if parsed > 0 else default
	except ValueError:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('環境変数%sの値が無効のため既定値を使用します: %s', name, raw_value)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return default


# EN: Assign value to _DEFAULT_EMBED_BROWSER_URL.
# JP: _DEFAULT_EMBED_BROWSER_URL に値を代入する。
_DEFAULT_EMBED_BROWSER_URL = 'http://127.0.0.1:7900/vnc_lite.html?autoconnect=1&resize=scale&scale=auto&view_clip=false'
# EN: Assign value to _ALLOWED_RESIZE_VALUES.
# JP: _ALLOWED_RESIZE_VALUES に値を代入する。
_ALLOWED_RESIZE_VALUES = {'scale', 'remote', 'off'}


# EN: Define function `_normalize_embed_browser_url`.
# JP: 関数 `_normalize_embed_browser_url` を定義する。
def _normalize_embed_browser_url(value: str) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Ensure the embedded noVNC URL fills the container on first load."""

	# JP: noVNC の表示が崩れないよう resize/scale パラメータを補完する
	# EN: Patch resize/scale parameters so noVNC fits the container
	if not value:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return value

	# EN: Assign value to parsed.
	# JP: parsed に値を代入する。
	parsed = urlparse(value)
	# EN: Assign value to query_items.
	# JP: query_items に値を代入する。
	query_items = parse_qsl(parsed.query, keep_blank_values=True)

	# EN: Assign value to has_scale.
	# JP: has_scale に値を代入する。
	has_scale = any(key == 'scale' for key, _ in query_items)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not has_scale:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		query_items.append(('scale', 'auto'))

	# EN: Assign annotated value to normalized_items.
	# JP: normalized_items に型付きの値を代入する。
	normalized_items: list[tuple[str, str]] = []
	# EN: Assign value to resize_present.
	# JP: resize_present に値を代入する。
	resize_present = False
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for key, value in query_items:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if key == 'resize':
			# EN: Assign value to resize_present.
			# JP: resize_present に値を代入する。
			resize_present = True
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if value not in _ALLOWED_RESIZE_VALUES:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				normalized_items.append(('resize', 'scale'))
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				normalized_items.append((key, value))
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			normalized_items.append((key, value))

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not resize_present:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		normalized_items.append(('resize', 'scale'))

	# EN: Assign value to normalized_query.
	# JP: normalized_query に値を代入する。
	normalized_query = urlencode(normalized_items)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return urlunparse(parsed._replace(query=normalized_query))


# EN: Define function `_get_env_trimmed`.
# JP: 関数 `_get_env_trimmed` を定義する。
def _get_env_trimmed(name: str) -> str | None:
	# JP: 前後空白を除去し、空文字は None にする
	# EN: Trim whitespace and convert empty strings to None
	value = os.environ.get(name)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if value is None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None
	# EN: Assign value to trimmed.
	# JP: trimmed に値を代入する。
	trimmed = value.strip()
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return trimmed or None


# EN: Define function `_normalize_start_url`.
# JP: 関数 `_normalize_start_url` を定義する。
def _normalize_start_url(value: str | None) -> str | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Normalize a configured start URL for the embedded browser."""

	# JP: 入力の無効値を除外し、必要なら https:// を補う
	# EN: Drop invalid values and add https:// when missing
	if not value:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Assign value to normalized.
	# JP: normalized に値を代入する。
	normalized = value.strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not normalized:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Assign value to lowered.
	# JP: lowered に値を代入する。
	lowered = normalized.lower()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if lowered in {'none', 'off', 'false'}:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if normalized.startswith('//'):
		# EN: Assign value to normalized.
		# JP: normalized に値を代入する。
		normalized = normalized[2:]

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if '://' not in normalized and not normalized.startswith(('about:', 'chrome:', 'file:')):
		# EN: Assign value to normalized.
		# JP: normalized に値を代入する。
		normalized = f'https://{normalized}'

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return normalized


# JP: 開始ページは環境変数を優先し、無ければブラウザ既定の新規タブURL
# EN: Prefer env-configured start URL; otherwise use the browser default new-tab URL
_DEFAULT_START_URL = (
	_normalize_start_url(
		_get_env_trimmed('BROWSER_DEFAULT_START_URL'),
	)
	or DEFAULT_NEW_TAB_URL
)

# JP: 埋め込みブラウザ（noVNC）のURLを正規化
# EN: Normalize the embedded browser (noVNC) URL
_BROWSER_URL = _normalize_embed_browser_url(os.environ.get('EMBED_BROWSER_URL', _DEFAULT_EMBED_BROWSER_URL))

# JP: 主要な環境変数を数値として読み込む
# EN: Load key numeric environment settings
_AGENT_MAX_STEPS = _env_int('AGENT_MAX_STEPS', 20)
# EN: Assign value to _WEBARENA_MAX_STEPS.
# JP: _WEBARENA_MAX_STEPS に値を代入する。
_WEBARENA_MAX_STEPS = _env_int('WEBARENA_AGENT_MAX_STEPS', 20)
# EN: Assign value to _CONVERSATION_CONTEXT_WINDOW.
# JP: _CONVERSATION_CONTEXT_WINDOW に値を代入する。
_CONVERSATION_CONTEXT_WINDOW = _env_int('CONVERSATION_CONTEXT_WINDOW', 10)
# EN: Assign value to _LLM_DAILY_API_LIMIT.
# JP: _LLM_DAILY_API_LIMIT に値を代入する。
_LLM_DAILY_API_LIMIT = _env_int('LLM_DAILY_API_LIMIT', 0)

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

# JP: IPベースのリクエスト制限ロジック
# EN: IP-based request rate-limiting logic
from fastapi import Request

from ..core.config import logger
from ..core.env import _IP_RATE_LIMIT_REQUESTS, _IP_RATE_LIMIT_TRUST_PROXY_HEADERS, _IP_RATE_LIMIT_WINDOW_SECONDS


# EN: Define class `_IpBucket`.
# JP: クラス `_IpBucket` を定義する。
@dataclass
class _IpBucket:
	timestamps: deque[float]
	lock: threading.Lock


# EN: Define class `RequestRateLimiter`.
# JP: クラス `RequestRateLimiter` を定義する。
class RequestRateLimiter:
	"""Thread-safe IP-based sliding-window request limiter."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, *, max_requests: int, window_seconds: int, now_fn: Callable[[], float] | None = None) -> None:
		self._max_requests = max_requests
		self._window_seconds = window_seconds
		self._now = now_fn or time.monotonic
		self._buckets: dict[str, _IpBucket] = {}
		self._index_lock = threading.Lock()

	# EN: Define function `allow`.
	# JP: 関数 `allow` を定義する。
	def allow(self, key: str) -> bool:
		# JP: 制限無効設定（<=0）の場合は常に許可
		# EN: Always allow when limiter is disabled via non-positive settings
		if self._max_requests <= 0 or self._window_seconds <= 0:
			return True

		now = self._now()
		cutoff = now - float(self._window_seconds)

		# JP: キーごとのバケットを遅延生成（初回アクセス時のみ）
		# EN: Lazily create a per-key bucket on first access
		with self._index_lock:
			bucket = self._buckets.get(key)
			if bucket is None:
				bucket = _IpBucket(timestamps=deque(), lock=threading.Lock())
				self._buckets[key] = bucket

		with bucket.lock:
			timestamps = bucket.timestamps
			# JP: スライディングウィンドウ外の古い記録を除外
			# EN: Drop timestamps that are outside the sliding window
			while timestamps and timestamps[0] <= cutoff:
				timestamps.popleft()

			if len(timestamps) >= self._max_requests:
				return False

			timestamps.append(now)
			return True


_RATE_LIMITER = RequestRateLimiter(
	max_requests=_IP_RATE_LIMIT_REQUESTS,
	window_seconds=_IP_RATE_LIMIT_WINDOW_SECONDS,
)


# EN: Define function `_extract_forwarded_ip`.
# JP: 関数 `_extract_forwarded_ip` を定義する。
def _extract_forwarded_ip(value: str) -> str | None:
	# JP: X-Forwarded-For の先頭IP（元クライアント想定）を取り出す
	# EN: Parse the first IP from X-Forwarded-For as the client candidate
	parts = [segment.strip() for segment in value.split(',') if segment.strip()]
	return parts[0] if parts else None


# EN: Define function `get_client_ip`.
# JP: 関数 `get_client_ip` を定義する。
def get_client_ip(request: Request, *, trust_proxy_headers: bool | None = None) -> str:
	"""Return best-effort client IP from request headers or connection info."""
	use_proxy_headers = _IP_RATE_LIMIT_TRUST_PROXY_HEADERS if trust_proxy_headers is None else trust_proxy_headers

	# JP: プロキシヘッダーを信頼する設定時のみヘッダー起点で判定
	# EN: Use proxy headers only when explicitly trusted
	if use_proxy_headers:
		x_forwarded_for = request.headers.get('X-Forwarded-For')
		if x_forwarded_for:
			forwarded_ip = _extract_forwarded_ip(x_forwarded_for)
			if forwarded_ip:
				return forwarded_ip

		x_real_ip = (request.headers.get('X-Real-IP') or '').strip()
		if x_real_ip:
			return x_real_ip

	client = request.client
	if client and client.host:
		return client.host

	return 'unknown'


# EN: Define function `is_ip_rate_limited`.
# JP: 関数 `is_ip_rate_limited` を定義する。
def is_ip_rate_limited(request: Request) -> tuple[bool, str]:
	"""Return whether request should be blocked by IP rate limiter."""
	# JP: 判定結果と識別に使ったIPをセットで返す
	# EN: Return both decision and resolved client IP for callers/logging
	client_ip = get_client_ip(request)
	allowed = _RATE_LIMITER.allow(client_ip)
	if not allowed:
		logger.info(
			'IP rate limit exceeded: ip=%s requests=%s window_seconds=%s',
			client_ip,
			_IP_RATE_LIMIT_REQUESTS,
			_IP_RATE_LIMIT_WINDOW_SECONDS,
		)
	return (not allowed, client_ip)

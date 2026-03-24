from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

from fastapi import Request

from ..core.config import logger
from ..core.env import _IP_RATE_LIMIT_REQUESTS, _IP_RATE_LIMIT_TRUST_PROXY_HEADERS, _IP_RATE_LIMIT_WINDOW_SECONDS


@dataclass
class _IpBucket:
	timestamps: deque[float]
	lock: threading.Lock


class RequestRateLimiter:
	"""Thread-safe IP-based sliding-window request limiter."""

	def __init__(self, *, max_requests: int, window_seconds: int, now_fn: Callable[[], float] | None = None) -> None:
		self._max_requests = max_requests
		self._window_seconds = window_seconds
		self._now = now_fn or time.monotonic
		self._buckets: dict[str, _IpBucket] = {}
		self._index_lock = threading.Lock()

	def allow(self, key: str) -> bool:
		if self._max_requests <= 0 or self._window_seconds <= 0:
			return True

		now = self._now()
		cutoff = now - float(self._window_seconds)

		with self._index_lock:
			bucket = self._buckets.get(key)
			if bucket is None:
				bucket = _IpBucket(timestamps=deque(), lock=threading.Lock())
				self._buckets[key] = bucket

		with bucket.lock:
			timestamps = bucket.timestamps
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


def _extract_forwarded_ip(value: str) -> str | None:
	parts = [segment.strip() for segment in value.split(',') if segment.strip()]
	return parts[0] if parts else None


def get_client_ip(request: Request, *, trust_proxy_headers: bool | None = None) -> str:
	"""Return best-effort client IP from request headers or connection info."""
	use_proxy_headers = _IP_RATE_LIMIT_TRUST_PROXY_HEADERS if trust_proxy_headers is None else trust_proxy_headers

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


def is_ip_rate_limited(request: Request) -> tuple[bool, str]:
	"""Return whether request should be blocked by IP rate limiter."""
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

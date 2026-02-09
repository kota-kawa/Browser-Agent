from __future__ import annotations

import os
import re
from dataclasses import dataclass

from httpx import URL

from ..core.config import logger

try:
	from groq import AsyncGroq
except ModuleNotFoundError as exc:  # pragma: no cover - handled by InputGuardError
	AsyncGroq = None  # type: ignore[assignment,misc]
	_GROQ_IMPORT_ERROR = exc
else:
	_GROQ_IMPORT_ERROR = None


_DEFAULT_LLAMA_GUARD_MODEL = 'meta-llama/llama-guard-4-12b'
_SAFETY_TAG_RE = re.compile(r'S\d+')


class InputGuardError(RuntimeError):
	"""Raised when the Groq Llama Guard check cannot be completed."""


@dataclass(frozen=True)
class InputGuardResult:
	"""Result of a Llama Guard safety check."""

	is_safe: bool
	raw_output: str
	categories: tuple[str, ...]


_guard_client: AsyncGroq | None = None


def _normalize_groq_base_url(value: str | None) -> str | URL | None:
	if not value:
		return None
	if isinstance(value, str) and value.endswith('/openai/v1'):
		return value.removesuffix('/openai/v1')
	if isinstance(value, URL) and value.path.endswith('/openai/v1'):
		return value.copy_with(path=value.path.removesuffix('/openai/v1'))
	return value


def _get_guard_client() -> AsyncGroq:
	global _guard_client

	if _guard_client is not None:
		return _guard_client

	if _GROQ_IMPORT_ERROR is not None or AsyncGroq is None:
		raise InputGuardError('Groq 用の依存関係が見つかりません。') from _GROQ_IMPORT_ERROR

	api_key = (os.getenv('GROQ_API_KEY') or '').strip()
	if not api_key:
		raise InputGuardError('GROQ_API_KEY が設定されていません。')

	base_url = _normalize_groq_base_url(os.getenv('GROQ_API_BASE'))
	_guard_client = AsyncGroq(api_key=api_key, base_url=base_url)
	return _guard_client


def _parse_guard_output(output: str | None) -> InputGuardResult:
	text = (output or '').strip()
	if not text:
		return InputGuardResult(is_safe=False, raw_output='', categories=())

	lines = [line.strip() for line in text.splitlines() if line.strip()]
	first_line = lines[0].lower() if lines else ''
	first_token = first_line.split(maxsplit=1)[0]
	if first_token == 'safe':
		return InputGuardResult(is_safe=True, raw_output=text, categories=())

	categories = tuple(dict.fromkeys(_SAFETY_TAG_RE.findall(text)))
	return InputGuardResult(is_safe=False, raw_output=text, categories=categories)


async def check_prompt_safety(prompt: str) -> InputGuardResult:
	"""Check prompt safety using Groq Llama Guard.

	Returns an InputGuardResult indicating whether the prompt is safe.
	"""
	model = (os.getenv('LLAMA_GUARD_MODEL') or '').strip() or _DEFAULT_LLAMA_GUARD_MODEL
	client = _get_guard_client()

	try:
		response = await client.chat.completions.create(
			model=model,
			messages=[{'role': 'user', 'content': prompt}],
			temperature=0,
		)
	except Exception as exc:
		logger.warning('Llama Guard call failed: %s', exc)
		raise InputGuardError('入力の安全性チェックに失敗しました。') from exc

	content = None
	if response and response.choices:
		message = response.choices[0].message
		content = getattr(message, 'content', None)

	return _parse_guard_output(content)

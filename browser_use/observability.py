# @file purpose: Observability module for browser-use that handles optional lmnr integration with debug mode support
"""
Observability module for browser-use

This module provides observability decorators that optionally integrate with lmnr (Laminar) for tracing.
If lmnr is not installed, it provides no-op wrappers that accept the same parameters.

Features:
- Optional lmnr integration - works with or without lmnr installed
- Debug mode support - observe_debug only traces when in debug mode
- Full parameter compatibility with lmnr observe decorator
- No-op fallbacks when lmnr is unavailable
"""

import logging
import os
from collections.abc import Callable
from functools import wraps
from typing import Any, Literal, TypeVar, cast

from browser_use.env_loader import load_secrets_env

logger = logging.getLogger(__name__)
load_secrets_env()

# Type definitions
F = TypeVar('F', bound=Callable[..., Any])


# Check if we're in debug mode
# EN: Define function `_is_debug_mode`.
# JP: 関数 `_is_debug_mode` を定義する。
def _is_debug_mode() -> bool:
	"""Check if we're in debug mode based on environment variables or logging level."""

	lmnr_debug_mode = os.getenv('LMNR_LOGGING_LEVEL', '').lower()
	if lmnr_debug_mode == 'debug':
		# logger.info('Debug mode is enabled for observability')
		return True
	# logger.info('Debug mode is disabled for observability')
	return False


# Try to import lmnr observe
_LMNR_AVAILABLE = False
_lmnr_observe = None

try:
	from lmnr import observe as _lmnr_observe  # type: ignore

	if os.environ.get('BROWSER_USE_VERBOSE_OBSERVABILITY', 'false').lower() == 'true':
		logger.debug('Lmnr is available for observability')
	_LMNR_AVAILABLE = True
except ImportError:
	if os.environ.get('BROWSER_USE_VERBOSE_OBSERVABILITY', 'false').lower() == 'true':
		logger.debug('Lmnr is not available for observability')
	_LMNR_AVAILABLE = False


# EN: Define function `_create_no_op_decorator`.
# JP: 関数 `_create_no_op_decorator` を定義する。
def _create_no_op_decorator(
	name: str | None = None,
	ignore_input: bool = False,
	ignore_output: bool = False,
	metadata: dict[str, Any] | None = None,
	**kwargs: Any,
) -> Callable[[F], F]:
	"""Create a no-op decorator that accepts all lmnr observe parameters but does nothing."""

	# EN: Define function `decorator`.
	# JP: 関数 `decorator` を定義する。
	def decorator(func: F) -> F:
		# EN: Define function `wrapper`.
		# JP: 関数 `wrapper` を定義する。
		@wraps(func)
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)

		return cast(F, wrapper)

	return decorator


# EN: Define function `observe`.
# JP: 関数 `observe` を定義する。
def observe(
	name: str | None = None,
	ignore_input: bool = False,
	ignore_output: bool = False,
	metadata: dict[str, Any] | None = None,
	span_type: Literal['DEFAULT', 'LLM', 'TOOL'] = 'DEFAULT',
	**kwargs: Any,
) -> Callable[[F], F]:
	"""
	Observability decorator that traces function execution when lmnr is available.

	This decorator will use lmnr's observe decorator if lmnr is installed,
	otherwise it will be a no-op that accepts the same parameters.

	Args:
	    name: Name of the span/trace
	    ignore_input: Whether to ignore function input parameters in tracing
	    ignore_output: Whether to ignore function output in tracing
	    metadata: Additional metadata to attach to the span
	    **kwargs: Additional parameters passed to lmnr observe

	Returns:
	    Decorated function that may be traced depending on lmnr availability

	Example:
	    @observe(name="my_function", metadata={"version": "1.0"})
	    def my_function(param1, param2):
	        return param1 + param2
	"""
	kwargs = {
		'name': name,
		'ignore_input': ignore_input,
		'ignore_output': ignore_output,
		'metadata': metadata,
		'span_type': span_type,
		**kwargs,
	}

	if _LMNR_AVAILABLE and _lmnr_observe:
		# Use the real lmnr observe decorator
		return cast(Callable[[F], F], _lmnr_observe(**kwargs))
	else:
		# Use no-op decorator
		return _create_no_op_decorator(**kwargs)


# EN: Define function `observe_debug`.
# JP: 関数 `observe_debug` を定義する。
def observe_debug(
	name: str | None = None,
	ignore_input: bool = False,
	ignore_output: bool = False,
	metadata: dict[str, Any] | None = None,
	span_type: Literal['DEFAULT', 'LLM', 'TOOL'] = 'DEFAULT',
	**kwargs: Any,
) -> Callable[[F], F]:
	"""
	Debug-only observability decorator that only traces when in debug mode.

	This decorator will use lmnr's observe decorator if both lmnr is installed
	AND we're in debug mode, otherwise it will be a no-op.

	Debug mode is determined by:
	- DEBUG environment variable set to 1/true/yes/on
	- BROWSER_USE_DEBUG environment variable set to 1/true/yes/on
	- Root logging level set to DEBUG or lower

	Args:
	    name: Name of the span/trace
	    ignore_input: Whether to ignore function input parameters in tracing
	    ignore_output: Whether to ignore function output in tracing
	    metadata: Additional metadata to attach to the span
	    **kwargs: Additional parameters passed to lmnr observe

	Returns:
	    Decorated function that may be traced only in debug mode

	Example:
	    @observe_debug(ignore_input=True, ignore_output=True,name="debug_function", metadata={"debug": True})
	    def debug_function(param1, param2):
	        return param1 + param2
	"""
	kwargs = {
		'name': name,
		'ignore_input': ignore_input,
		'ignore_output': ignore_output,
		'metadata': metadata,
		'span_type': span_type,
		**kwargs,
	}

	if _LMNR_AVAILABLE and _lmnr_observe and _is_debug_mode():
		# Use the real lmnr observe decorator only in debug mode
		return cast(Callable[[F], F], _lmnr_observe(**kwargs))
	else:
		# Use no-op decorator (either not in debug mode or lmnr not available)
		return _create_no_op_decorator(**kwargs)


# Convenience functions for checking availability and debug status
# EN: Define function `is_lmnr_available`.
# JP: 関数 `is_lmnr_available` を定義する。
def is_lmnr_available() -> bool:
	"""Check if lmnr is available for tracing."""
	return _LMNR_AVAILABLE


# EN: Define function `is_debug_mode`.
# JP: 関数 `is_debug_mode` を定義する。
def is_debug_mode() -> bool:
	"""Check if we're currently in debug mode."""
	return _is_debug_mode()


# EN: Define function `get_observability_status`.
# JP: 関数 `get_observability_status` を定義する。
def get_observability_status() -> dict[str, bool]:
	"""Get the current status of observability features."""
	return {
		'lmnr_available': _LMNR_AVAILABLE,
		'debug_mode': _is_debug_mode(),
		'observe_active': _LMNR_AVAILABLE,
		'observe_debug_active': _LMNR_AVAILABLE and _is_debug_mode(),
	}

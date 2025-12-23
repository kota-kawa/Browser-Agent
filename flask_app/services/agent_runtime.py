from __future__ import annotations

import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any

import requests
from browser_use.model_selection import apply_model_selection

from ..core.cdp import _consume_cdp_session_cleanup, _resolve_cdp_url
from ..core.config import logger
from ..core.env import _AGENT_MAX_STEPS
from ..core.exceptions import AgentControllerError
from ..core.models import SUPPORTED_MODELS
from ..prompts.system_prompt import _should_disable_vision
from .agent_controller import BrowserAgentController
from .formatting import _append_final_response_notice

_PLATFORM_BASE = os.getenv('MULTI_AGENT_PLATFORM_BASE', 'http://web:5050').rstrip('/')
_VISION_SETTINGS_PATH = Path('local_vision_settings.json')

_AGENT_CONTROLLER: BrowserAgentController | None = None


def _load_vision_pref() -> bool:
	try:
		if _VISION_SETTINGS_PATH.exists():
			data = json.loads(_VISION_SETTINGS_PATH.read_text(encoding='utf-8'))
			if isinstance(data, dict) and 'enabled' in data:
				return bool(data['enabled'])
	except Exception:
		logger.debug('Failed to load vision preference; defaulting to True', exc_info=True)
	return True


def _save_vision_pref(enabled: bool) -> None:
	try:
		_VISION_SETTINGS_PATH.write_text(
			json.dumps({'enabled': bool(enabled)}, ensure_ascii=False, indent=2),
			encoding='utf-8',
		)
	except Exception:
		logger.debug('Failed to persist vision preference', exc_info=True)


_VISION_PREF = _load_vision_pref()


def finalize_summary(text: str) -> str:
	"""Ensure run summaries include the final-response marker for downstream consumers."""

	return _append_final_response_notice(text or '')


def get_agent_controller() -> BrowserAgentController:
	global _AGENT_CONTROLLER
	if _AGENT_CONTROLLER is None:
		cdp_url = _resolve_cdp_url()
		cleanup = _consume_cdp_session_cleanup()
		if not cdp_url:
			if cleanup:
				with suppress(Exception):
					cleanup()
			raise AgentControllerError('Chrome DevToolsのCDP URLが検出できませんでした。BROWSER_USE_CDP_URL を設定してください。')
		try:
			_AGENT_CONTROLLER = BrowserAgentController(
				cdp_url=cdp_url,
				max_steps=_AGENT_MAX_STEPS,
				cdp_cleanup=cleanup,
			)
			try:
				_AGENT_CONTROLLER.set_vision_enabled(_VISION_PREF)
			except Exception:
				logger.debug('Failed to apply saved vision preference to controller', exc_info=True)
		except Exception:
			if cleanup:
				with suppress(Exception):
					cleanup()
			raise
	return _AGENT_CONTROLLER


def reset_agent_controller() -> None:
	"""Shutdown existing controller so the next request uses refreshed LLM settings."""

	global _AGENT_CONTROLLER
	if _AGENT_CONTROLLER is not None:
		try:
			_AGENT_CONTROLLER.shutdown()
		except Exception:
			logger.debug('Failed to shutdown controller during model refresh', exc_info=True)
	_AGENT_CONTROLLER = None


def get_existing_controller() -> BrowserAgentController:
	if _AGENT_CONTROLLER is None:
		raise AgentControllerError('エージェントはまだ初期化されていません。')
	return _AGENT_CONTROLLER


def get_controller_if_initialized() -> BrowserAgentController | None:
	return _AGENT_CONTROLLER


def find_model_label(provider: str, model: str) -> str:
	"""Return the display label for a provider/model pair if known."""

	for entry in SUPPORTED_MODELS:
		if entry.get('provider') == provider and entry.get('model') == model:
			return entry.get('label', '')
	return ''


def notify_platform(selection: dict[str, Any]) -> None:
	"""Best-effort push of the latest Browser model selection back to the platform."""

	if not _PLATFORM_BASE or not selection or not isinstance(selection, dict):
		return

	try:
		url = f'{_PLATFORM_BASE}/api/model_settings'
		payload = {'selection': {'browser': selection}}
		headers = {'X-Agent-Origin': 'browser'}
		resp = requests.post(url, json=payload, headers=headers, timeout=2.0)
		if not resp.ok:
			logger.info('Platform model sync skipped (%s %s)', resp.status_code, resp.text)
	except requests.exceptions.RequestException as exc:
		logger.info('Platform model sync skipped (%s)', exc)


def current_model_selection() -> dict[str, Any]:
	"""Return current browser model selection with provider/model."""

	try:
		return apply_model_selection('browser')
	except Exception:
		logger.debug('Failed to load current model selection', exc_info=True)
		return {'provider': '', 'model': ''}


def vision_state() -> dict[str, Any]:
	"""Compute vision toggle state considering model capability."""

	selection = current_model_selection()
	provider = (selection.get('provider') or '').strip().lower()
	model = (selection.get('model') or '').strip().lower()

	supported = not _should_disable_vision(provider, model)
	effective = bool(_VISION_PREF and supported)

	return {
		'user_enabled': bool(_VISION_PREF),
		'model_supported': supported,
		'effective': effective,
		'provider': provider,
		'model': model,
	}


def set_vision_pref(enabled: bool) -> dict[str, Any]:
	global _VISION_PREF
	_VISION_PREF = bool(enabled)
	_save_vision_pref(_VISION_PREF)

	# Apply to running controller if present
	if _AGENT_CONTROLLER is not None:
		try:
			_AGENT_CONTROLLER.set_vision_enabled(_VISION_PREF)
		except Exception as exc:
			logger.debug('Failed to apply vision toggle to controller: %s', exc)

	return vision_state()

from __future__ import annotations

import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any

import httpx
# JP: コントローラー初期化やモデル設定を扱うランタイム層
# EN: Runtime layer that manages controller initialization and model settings
from browser_use.model_selection import apply_model_selection

from ..core.cdp import _consume_cdp_session_cleanup, _resolve_cdp_url
from ..core.config import logger
from ..core.env import _AGENT_MAX_STEPS
from ..core.exceptions import AgentControllerError
from ..core.models import SUPPORTED_MODELS
from ..prompts.system_prompt import _should_disable_vision
from .agent_controller import BrowserAgentController
from .formatting import _append_final_response_notice

# JP: 外部プラットフォーム同期先と Vision 設定ファイルのパス
# EN: Platform sync endpoint and vision settings file path
_PLATFORM_BASE = os.getenv('MULTI_AGENT_PLATFORM_BASE', 'http://web:5050').rstrip('/')
_VISION_SETTINGS_PATH = Path('local_vision_settings.json')

_AGENT_CONTROLLER: BrowserAgentController | None = None


# EN: Define function `_load_vision_pref`.
# JP: 関数 `_load_vision_pref` を定義する。
def _load_vision_pref() -> bool:
	# JP: Vision の有効/無効をローカル設定から読み込む
	# EN: Load the vision toggle from local settings
	try:
		if _VISION_SETTINGS_PATH.exists():
			data = json.loads(_VISION_SETTINGS_PATH.read_text(encoding='utf-8'))
			if isinstance(data, dict) and 'enabled' in data:
				return bool(data['enabled'])
	except Exception:
		logger.debug('Failed to load vision preference; defaulting to True', exc_info=True)
	return True


# EN: Define function `_save_vision_pref`.
# JP: 関数 `_save_vision_pref` を定義する。
def _save_vision_pref(enabled: bool) -> None:
	# JP: Vision 設定をローカルファイルに保存
	# EN: Persist the vision toggle to local settings
	try:
		_VISION_SETTINGS_PATH.write_text(
			json.dumps({'enabled': bool(enabled)}, ensure_ascii=False, indent=2),
			encoding='utf-8',
		)
	except Exception:
		logger.debug('Failed to persist vision preference', exc_info=True)


_VISION_PREF = _load_vision_pref()


# EN: Define function `finalize_summary`.
# JP: 関数 `finalize_summary` を定義する。
def finalize_summary(text: str) -> str:
	"""Ensure run summaries include the final-response marker for downstream consumers."""

	# JP: downstream が識別できるよう、完了マーカーを必ず付与
	# EN: Always append a final-response marker for downstream consumers
	return _append_final_response_notice(text or '')


# EN: Define function `get_agent_controller`.
# JP: 関数 `get_agent_controller` を定義する。
def get_agent_controller() -> BrowserAgentController:
	# JP: シングルトンのコントローラーを遅延初期化で生成
	# EN: Lazily initialize the singleton controller
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
			# JP: 保存済みの Vision 設定を反映
			# EN: Apply persisted vision preference
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


# EN: Define function `reset_agent_controller`.
# JP: 関数 `reset_agent_controller` を定義する。
def reset_agent_controller() -> None:
	"""Shutdown existing controller so the next request uses refreshed LLM settings."""

	# JP: モデル更新時にコントローラーを明示的に再作成させる
	# EN: Force controller recreation after model updates
	global _AGENT_CONTROLLER
	if _AGENT_CONTROLLER is not None:
		try:
			_AGENT_CONTROLLER.shutdown()
		except Exception:
			logger.debug('Failed to shutdown controller during model refresh', exc_info=True)
	_AGENT_CONTROLLER = None


# EN: Define function `get_existing_controller`.
# JP: 関数 `get_existing_controller` を定義する。
def get_existing_controller() -> BrowserAgentController:
	# JP: 既に初期化済みのコントローラーのみ返す
	# EN: Return the controller only if already initialized
	if _AGENT_CONTROLLER is None:
		raise AgentControllerError('エージェントはまだ初期化されていません。')
	return _AGENT_CONTROLLER


# EN: Define function `get_controller_if_initialized`.
# JP: 関数 `get_controller_if_initialized` を定義する。
def get_controller_if_initialized() -> BrowserAgentController | None:
	# JP: 初期化済みなら返し、未初期化なら None
	# EN: Return controller if initialized, otherwise None
	return _AGENT_CONTROLLER


# EN: Define function `find_model_label`.
# JP: 関数 `find_model_label` を定義する。
def find_model_label(provider: str, model: str) -> str:
	"""Return the display label for a provider/model pair if known."""

	# JP: UI 表示用のラベルを探索
	# EN: Look up the UI label for the provider/model pair
	for entry in SUPPORTED_MODELS:
		if entry.get('provider') == provider and entry.get('model') == model:
			return entry.get('label', '')
	return ''


# EN: Define function `notify_platform`.
# JP: 関数 `notify_platform` を定義する。
def notify_platform(selection: dict[str, Any]) -> None:
	"""Best-effort push of the latest Browser model selection back to the platform."""

	# JP: 失敗しても処理を止めないベストエフォート通知
	# EN: Best-effort push; errors are logged and ignored
	if not _PLATFORM_BASE or not selection or not isinstance(selection, dict):
		return

	try:
		url = f'{_PLATFORM_BASE}/api/model_settings'
		payload = {'selection': {'browser': selection}}
		headers = {'X-Agent-Origin': 'browser'}
		resp = httpx.post(url, json=payload, headers=headers, timeout=2.0)
		if resp.is_error:
			logger.info('Platform model sync skipped (%s %s)', resp.status_code, resp.text)
	except httpx.RequestError as exc:
		logger.info('Platform model sync skipped (%s)', exc)


# EN: Define function `current_model_selection`.
# JP: 関数 `current_model_selection` を定義する。
def current_model_selection() -> dict[str, Any]:
	"""Return current browser model selection with provider/model."""

	# JP: モデル選択の最新状態を返す
	# EN: Return the latest model selection
	try:
		return apply_model_selection('browser')
	except Exception:
		logger.debug('Failed to load current model selection', exc_info=True)
		return {'provider': '', 'model': ''}


# EN: Define function `vision_state`.
# JP: 関数 `vision_state` を定義する。
def vision_state() -> dict[str, Any]:
	"""Compute vision toggle state considering model capability."""

	# JP: モデルの対応可否を考慮して実効状態を計算
	# EN: Compute effective vision state with model capability in mind
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


# EN: Define function `set_vision_pref`.
# JP: 関数 `set_vision_pref` を定義する。
def set_vision_pref(enabled: bool) -> dict[str, Any]:
	# JP: Vision の希望値を更新して実行中コントローラーへ反映
	# EN: Update vision preference and apply to the running controller
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

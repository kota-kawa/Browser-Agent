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
from contextlib import suppress
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# JP: コントローラー初期化やモデル設定を扱うランタイム層
# EN: Runtime layer that manages controller initialization and model settings
from browser_use.model_selection import apply_model_selection

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.cdp import _consume_cdp_session_cleanup, _resolve_cdp_url
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.env import _AGENT_MAX_STEPS
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.exceptions import AgentControllerError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.models import SUPPORTED_MODELS
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..prompts.system_prompt import _should_disable_vision
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .agent_controller import BrowserAgentController
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .formatting import _append_final_response_notice

# JP: 外部プラットフォーム同期先と Vision 設定ファイルのパス
# EN: Platform sync endpoint and vision settings file path
_PLATFORM_BASE = os.getenv('MULTI_AGENT_PLATFORM_BASE', 'http://web:5050').rstrip('/')
# EN: Assign value to _VISION_SETTINGS_PATH.
# JP: _VISION_SETTINGS_PATH に値を代入する。
_VISION_SETTINGS_PATH = Path('local_vision_settings.json')

# EN: Assign annotated value to _AGENT_CONTROLLER.
# JP: _AGENT_CONTROLLER に型付きの値を代入する。
_AGENT_CONTROLLER: BrowserAgentController | None = None


# EN: Define function `_load_vision_pref`.
# JP: 関数 `_load_vision_pref` を定義する。
def _load_vision_pref() -> bool:
	# JP: Vision の有効/無効をローカル設定から読み込む
	# EN: Load the vision toggle from local settings
	try:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if _VISION_SETTINGS_PATH.exists():
			# EN: Assign value to data.
			# JP: data に値を代入する。
			data = json.loads(_VISION_SETTINGS_PATH.read_text(encoding='utf-8'))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(data, dict) and 'enabled' in data:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return bool(data['enabled'])
	except Exception:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Failed to load vision preference; defaulting to True', exc_info=True)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return True


# EN: Define function `_save_vision_pref`.
# JP: 関数 `_save_vision_pref` を定義する。
def _save_vision_pref(enabled: bool) -> None:
	# JP: Vision 設定をローカルファイルに保存
	# EN: Persist the vision toggle to local settings
	try:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_VISION_SETTINGS_PATH.write_text(
			json.dumps({'enabled': bool(enabled)}, ensure_ascii=False, indent=2),
			encoding='utf-8',
		)
	except Exception:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Failed to persist vision preference', exc_info=True)


# EN: Assign value to _VISION_PREF.
# JP: _VISION_PREF に値を代入する。
_VISION_PREF = _load_vision_pref()


# EN: Define function `finalize_summary`.
# JP: 関数 `finalize_summary` を定義する。
def finalize_summary(text: str) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
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
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _AGENT_CONTROLLER is None:
		# EN: Assign value to cdp_url.
		# JP: cdp_url に値を代入する。
		cdp_url = _resolve_cdp_url()
		# EN: Assign value to cleanup.
		# JP: cleanup に値を代入する。
		cleanup = _consume_cdp_session_cleanup()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not cdp_url:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cleanup:
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with suppress(Exception):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					cleanup()
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise AgentControllerError('Chrome DevToolsのCDP URLが検出できませんでした。BROWSER_USE_CDP_URL を設定してください。')
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to _AGENT_CONTROLLER.
			# JP: _AGENT_CONTROLLER に値を代入する。
			_AGENT_CONTROLLER = BrowserAgentController(
				cdp_url=cdp_url,
				max_steps=_AGENT_MAX_STEPS,
				cdp_cleanup=cleanup,
			)
			# JP: 保存済みの Vision 設定を反映
			# EN: Apply persisted vision preference
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_AGENT_CONTROLLER.set_vision_enabled(_VISION_PREF)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug('Failed to apply saved vision preference to controller', exc_info=True)
		except Exception:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if cleanup:
				# EN: Execute logic with managed resources.
				# JP: リソース管理付きで処理を実行する。
				with suppress(Exception):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					cleanup()
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return _AGENT_CONTROLLER


# EN: Define function `reset_agent_controller`.
# JP: 関数 `reset_agent_controller` を定義する。
def reset_agent_controller() -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Shutdown existing controller so the next request uses refreshed LLM settings."""

	# JP: モデル更新時にコントローラーを明示的に再作成させる
	# EN: Force controller recreation after model updates
	global _AGENT_CONTROLLER
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _AGENT_CONTROLLER is not None:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_AGENT_CONTROLLER.shutdown()
		except Exception:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('Failed to shutdown controller during model refresh', exc_info=True)
	# EN: Assign value to _AGENT_CONTROLLER.
	# JP: _AGENT_CONTROLLER に値を代入する。
	_AGENT_CONTROLLER = None


# EN: Define function `get_existing_controller`.
# JP: 関数 `get_existing_controller` を定義する。
def get_existing_controller() -> BrowserAgentController:
	# JP: 既に初期化済みのコントローラーのみ返す
	# EN: Return the controller only if already initialized
	if _AGENT_CONTROLLER is None:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise AgentControllerError('エージェントはまだ初期化されていません。')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
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
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return the display label for a provider/model pair if known."""

	# JP: UI 表示用のラベルを探索
	# EN: Look up the UI label for the provider/model pair
	for entry in SUPPORTED_MODELS:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if entry.get('provider') == provider and entry.get('model') == model:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return entry.get('label', '')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return ''


# EN: Define function `notify_platform`.
# JP: 関数 `notify_platform` を定義する。
def notify_platform(selection: dict[str, Any]) -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Best-effort push of the latest Browser model selection back to the platform."""

	# JP: 失敗しても処理を止めないベストエフォート通知
	# EN: Best-effort push; errors are logged and ignored
	if not _PLATFORM_BASE or not selection or not isinstance(selection, dict):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = f'{_PLATFORM_BASE}/api/model_settings'
		# EN: Assign value to payload.
		# JP: payload に値を代入する。
		payload = {'selection': {'browser': selection}}
		# EN: Assign value to headers.
		# JP: headers に値を代入する。
		headers = {'X-Agent-Origin': 'browser'}
		# EN: Assign value to resp.
		# JP: resp に値を代入する。
		resp = httpx.post(url, json=payload, headers=headers, timeout=2.0)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if resp.is_error:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info('Platform model sync skipped (%s %s)', resp.status_code, resp.text)
	except httpx.RequestError as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info('Platform model sync skipped (%s)', exc)


# EN: Define function `current_model_selection`.
# JP: 関数 `current_model_selection` を定義する。
def current_model_selection() -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return current browser model selection with provider/model."""

	# JP: モデル選択の最新状態を返す
	# EN: Return the latest model selection
	try:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return apply_model_selection('browser')
	except Exception:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Failed to load current model selection', exc_info=True)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {'provider': '', 'model': ''}


# EN: Define function `vision_state`.
# JP: 関数 `vision_state` を定義する。
def vision_state() -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Compute vision toggle state considering model capability."""

	# JP: モデルの対応可否を考慮して実効状態を計算
	# EN: Compute effective vision state with model capability in mind
	selection = current_model_selection()
	# EN: Assign value to provider.
	# JP: provider に値を代入する。
	provider = (selection.get('provider') or '').strip().lower()
	# EN: Assign value to model.
	# JP: model に値を代入する。
	model = (selection.get('model') or '').strip().lower()

	# EN: Assign value to supported.
	# JP: supported に値を代入する。
	supported = not _should_disable_vision(provider, model)
	# EN: Assign value to effective.
	# JP: effective に値を代入する。
	effective = bool(_VISION_PREF and supported)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
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
	# EN: Assign value to _VISION_PREF.
	# JP: _VISION_PREF に値を代入する。
	_VISION_PREF = bool(enabled)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	_save_vision_pref(_VISION_PREF)

	# Apply to running controller if present
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _AGENT_CONTROLLER is not None:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_AGENT_CONTROLLER.set_vision_enabled(_VISION_PREF)
		except Exception as exc:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('Failed to apply vision toggle to controller: %s', exc)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return vision_state()

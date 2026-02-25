from __future__ import annotations

import json
# JP: 履歴・ステップ表示を整形するユーティリティ
# EN: Utilities for formatting history and step outputs
from pathlib import Path
from typing import Any

try:
	from browser_use.agent.views import ActionResult, AgentHistoryList, AgentOutput
	from browser_use.browser.views import BrowserStateSummary
	from browser_use.tools.registry.views import ActionModel
except ModuleNotFoundError:
	# JP: 開発環境で browser_use を直接参照するためパスを調整
	# EN: Adjust sys.path to import browser_use in local dev
	import sys

	ROOT_DIR = Path(__file__).resolve().parents[2]
	if str(ROOT_DIR) not in sys.path:
		sys.path.insert(0, str(ROOT_DIR))
	from browser_use.agent.views import ActionResult, AgentHistoryList, AgentOutput
	from browser_use.browser.views import BrowserStateSummary
	from browser_use.tools.registry.views import ActionModel

# JP: UI/下流処理が検知する終了マーカー
# EN: Final-response marker for UI and downstream consumers
_FINAL_RESPONSE_NOTICE = '※ ブラウザエージェントの応答はここで終了です。'
_FINAL_RESPONSE_MARKER = '[browser-agent-final]'


def _append_final_response_notice(message: str) -> str:
	"""Append a human/machine readable marker signalling that output is final."""

	# JP: 既に付与済みなら重複させない
	# EN: Avoid duplicating the marker if already present
	base = (message or '').strip()
	if _FINAL_RESPONSE_MARKER in base:
		return base
	notice = f'{_FINAL_RESPONSE_NOTICE} {_FINAL_RESPONSE_MARKER}'.strip()
	if base:
		return f'{base}\n\n{notice}'
	return notice


def _compact_text(text: str) -> str:
	# JP: 余計な前後空白を削除
	# EN: Trim leading/trailing whitespace
	return text.strip()


def _stringify_value(value: Any) -> str:
	"""Format a value as string without truncation."""
	# JP: dict/list は JSON にして読みやすくする
	# EN: Pretty-print dict/list as JSON when possible
	if isinstance(value, str):
		return value.strip()
	elif isinstance(value, (dict, list)):
		try:
			return json.dumps(value, ensure_ascii=False, indent=2)
		except TypeError:
			return str(value)
	else:
		return str(value)


def _format_action(action: ActionModel) -> str:
	# JP: アクション名とパラメータを人間向けに整形
	# EN: Render action name and params for readability
	action_dump = action.model_dump(exclude_none=True)
	if not action_dump:
		return '不明なアクション'

	name, params = next(iter(action_dump.items()))
	if not isinstance(params, dict) or not params:
		return name

	param_parts = []
	for key, value in params.items():
		if value is None:
			continue
		param_parts.append(f'{key}={_stringify_value(value)}')

	joined = ', '.join(param_parts)
	return f'{name}({joined})' if joined else name


def _format_result(result: ActionResult) -> str:
	"""Format action result without truncation."""
	# JP: エラー優先で表示し、無ければ要素を連結
	# EN: Prefer error text; otherwise join available segments
	if result.error:
		return _compact_text(result.error)

	segments: list[str] = []
	if result.is_done:
		status = '成功' if result.success else '失敗'
		segments.append(f'完了[{status}]')
	if result.extracted_content:
		segments.append(_compact_text(result.extracted_content))
	if result.long_term_memory:
		segments.append(_compact_text(result.long_term_memory))
	if not segments and result.metadata:
		try:
			metadata_text = json.dumps(result.metadata, ensure_ascii=False)
		except TypeError:
			metadata_text = str(result.metadata)
		segments.append(_compact_text(metadata_text))

	return ' / '.join(segments) if segments else ''


def _format_step_entry(index: int, step: Any) -> str:
	# JP: ステップ1件分をチャット表示向けに整形
	# EN: Format a single step entry for chat display
	lines: list[str] = [f'ステップ{index}']
	state = getattr(step, 'state', None)
	if state:
		page_parts: list[str] = []
		if getattr(state, 'title', None):
			page_parts.append(_compact_text(state.title))
		if getattr(state, 'url', None):
			page_parts.append(state.url)
		# if page_parts:
		# 	lines.append('ページ: ' + ' / '.join(page_parts))

	model_output = getattr(step, 'model_output', None)
	if model_output:
		action_lines = [_format_action(action) for action in model_output.action]
		if action_lines:
			lines.append('アクション: ' + ' / '.join(action_lines))
		if model_output.evaluation_previous_goal:
			lines.append('評価: ' + _compact_text(model_output.evaluation_previous_goal))
		if model_output.next_goal:
			lines.append('次の目標: ' + _compact_text(model_output.next_goal))
		if model_output.current_status:
			lines.append('現在の状況: ' + _compact_text(model_output.current_status))

	result_lines = [text for text in (_format_result(r) for r in getattr(step, 'result', [])) if text]
	if result_lines:
		lines.append('結果: ' + ' / '.join(result_lines))

	return '\n'.join(lines)


def _iter_history_steps(history: AgentHistoryList) -> list[tuple[int, Any]]:
	# JP: step_number を正規化しつつ順序付きリストへ変換
	# EN: Normalize step numbers and return an ordered list
	steps: list[tuple[int, Any]] = []
	next_index = 1
	for step in history.history:
		metadata = getattr(step, 'metadata', None)
		step_number = getattr(metadata, 'step_number', None) if metadata else None
		if not isinstance(step_number, int) or step_number < 1:
			step_number = next_index
		steps.append((step_number, step))
		next_index = step_number + 1
	return steps


def _format_history_messages(history: AgentHistoryList) -> list[tuple[int, str]]:
	# JP: 履歴をステップ番号と表示文のペアに変換
	# EN: Convert history into (step_number, message) pairs
	return [(step_number, _format_step_entry(step_number, step)) for step_number, step in _iter_history_steps(history)]


def _format_step_plan(
	step_number: int,
	state: BrowserStateSummary,
	model_output: AgentOutput,
) -> str:
	"""Format a step plan without truncation."""
	# JP: 実行前の計画をステップ単位で整形
	# EN: Format pre-execution step plans
	lines: list[str] = [f'ステップ{step_number}']

	if model_output.evaluation_previous_goal:
		lines.append('評価: ' + _compact_text(model_output.evaluation_previous_goal))
	if model_output.memory:
		lines.append('メモリ: ' + _compact_text(model_output.memory))
	if model_output.next_goal:
		lines.append('次の目標: ' + _compact_text(model_output.next_goal))
	if model_output.current_status:
		lines.append('現在の状況: ' + _compact_text(model_output.current_status))
	if model_output.persistent_notes:
		lines.append('永続メモ: ' + _compact_text(model_output.persistent_notes))

	return '\n'.join(lines)


def _summarize_history(history: AgentHistoryList) -> str:
	# JP: 実行結果の要約を生成して最終応答にする
	# EN: Build a summary of the run as the final response
	steps = _iter_history_steps(history)
	total_steps = max((step_number for step_number, _ in steps), default=0)
	success = history.is_successful()
	if success is True:
		prefix, status = '✅', '成功'
	elif success is False:
		prefix, status = '⚠️', '失敗'
	else:
		prefix, status = 'ℹ️', '未確定'

	lines = [f'{prefix} {total_steps}ステップでエージェントが実行されました（結果: {status}）。']

	final_text = history.final_result()
	if final_text:
		lines.append('最終報告: ' + _compact_text(final_text))
	elif success is True:
		lines.append('最終報告: (詳細な結果テキストはありません)')

	if history.history:
		last_state = history.history[-1].state
		if last_state and last_state.url:
			lines.append(f'最終URL: {last_state.url}')

	return _append_final_response_notice('\n'.join(lines))

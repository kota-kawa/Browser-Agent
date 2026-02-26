# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# JP: 履歴・ステップ表示を整形するユーティリティ
# EN: Utilities for formatting history and step outputs
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.agent.views import ActionResult, AgentHistoryList, AgentOutput
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser.views import BrowserStateSummary
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.tools.registry.views import ActionModel
except ModuleNotFoundError:
	# JP: 開発環境で browser_use を直接参照するためパスを調整
	# EN: Adjust sys.path to import browser_use in local dev
	import sys

	# EN: Assign value to ROOT_DIR.
	# JP: ROOT_DIR に値を代入する。
	ROOT_DIR = Path(__file__).resolve().parents[2]
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if str(ROOT_DIR) not in sys.path:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		sys.path.insert(0, str(ROOT_DIR))
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.agent.views import ActionResult, AgentHistoryList, AgentOutput
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser.views import BrowserStateSummary
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.tools.registry.views import ActionModel

# JP: UI/下流処理が検知する終了マーカー
# EN: Final-response marker for UI and downstream consumers
_FINAL_RESPONSE_NOTICE = '※ ブラウザエージェントの応答はここで終了です。'
# EN: Assign value to _FINAL_RESPONSE_MARKER.
# JP: _FINAL_RESPONSE_MARKER に値を代入する。
_FINAL_RESPONSE_MARKER = '[browser-agent-final]'


# EN: Define function `_append_final_response_notice`.
# JP: 関数 `_append_final_response_notice` を定義する。
def _append_final_response_notice(message: str) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Append a human/machine readable marker signalling that output is final."""

	# JP: 既に付与済みなら重複させない
	# EN: Avoid duplicating the marker if already present
	base = (message or '').strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if _FINAL_RESPONSE_MARKER in base:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return base
	# EN: Assign value to notice.
	# JP: notice に値を代入する。
	notice = f'{_FINAL_RESPONSE_NOTICE} {_FINAL_RESPONSE_MARKER}'.strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if base:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'{base}\n\n{notice}'
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return notice


# EN: Define function `_compact_text`.
# JP: 関数 `_compact_text` を定義する。
def _compact_text(text: str) -> str:
	# JP: 余計な前後空白を削除
	# EN: Trim leading/trailing whitespace
	return text.strip()


# EN: Define function `_stringify_value`.
# JP: 関数 `_stringify_value` を定義する。
def _stringify_value(value: Any) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Format a value as string without truncation."""
	# JP: dict/list は JSON にして読みやすくする
	# EN: Pretty-print dict/list as JSON when possible
	if isinstance(value, str):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return value.strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif isinstance(value, (dict, list)):
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return json.dumps(value, ensure_ascii=False, indent=2)
		except TypeError:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str(value)
	else:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(value)


# EN: Define function `_format_action`.
# JP: 関数 `_format_action` を定義する。
def _format_action(action: ActionModel) -> str:
	# JP: アクション名とパラメータを人間向けに整形
	# EN: Render action name and params for readability
	action_dump = action.model_dump(exclude_none=True)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not action_dump:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '不明なアクション'

	# EN: Assign value to target variable.
	# JP: target variable に値を代入する。
	name, params = next(iter(action_dump.items()))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not isinstance(params, dict) or not params:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return name

	# EN: Assign value to param_parts.
	# JP: param_parts に値を代入する。
	param_parts = []
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for key, value in params.items():
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if value is None:
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		param_parts.append(f'{key}={_stringify_value(value)}')

	# EN: Assign value to joined.
	# JP: joined に値を代入する。
	joined = ', '.join(param_parts)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return f'{name}({joined})' if joined else name


# EN: Define function `_format_result`.
# JP: 関数 `_format_result` を定義する。
def _format_result(result: ActionResult) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Format action result without truncation."""
	# JP: エラー優先で表示し、無ければ要素を連結
	# EN: Prefer error text; otherwise join available segments
	if result.error:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _compact_text(result.error)

	# EN: Assign annotated value to segments.
	# JP: segments に型付きの値を代入する。
	segments: list[str] = []
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if result.is_done:
		# EN: Assign value to status.
		# JP: status に値を代入する。
		status = '成功' if result.success else '失敗'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		segments.append(f'完了[{status}]')
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if result.extracted_content:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		segments.append(_compact_text(result.extracted_content))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if result.long_term_memory:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		segments.append(_compact_text(result.long_term_memory))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not segments and result.metadata:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to metadata_text.
			# JP: metadata_text に値を代入する。
			metadata_text = json.dumps(result.metadata, ensure_ascii=False)
		except TypeError:
			# EN: Assign value to metadata_text.
			# JP: metadata_text に値を代入する。
			metadata_text = str(result.metadata)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		segments.append(_compact_text(metadata_text))

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return ' / '.join(segments) if segments else ''


# EN: Define function `_format_step_entry`.
# JP: 関数 `_format_step_entry` を定義する。
def _format_step_entry(index: int, step: Any) -> str:
	# JP: ステップ1件分をチャット表示向けに整形
	# EN: Format a single step entry for chat display
	lines: list[str] = [f'ステップ{index}']
	# EN: Assign value to state.
	# JP: state に値を代入する。
	state = getattr(step, 'state', None)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if state:
		# EN: Assign annotated value to page_parts.
		# JP: page_parts に型付きの値を代入する。
		page_parts: list[str] = []
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if getattr(state, 'title', None):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			page_parts.append(_compact_text(state.title))
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if getattr(state, 'url', None):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			page_parts.append(state.url)
		# if page_parts:
		# 	lines.append('ページ: ' + ' / '.join(page_parts))

	# EN: Assign value to model_output.
	# JP: model_output に値を代入する。
	model_output = getattr(step, 'model_output', None)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if model_output:
		# EN: Assign value to action_lines.
		# JP: action_lines に値を代入する。
		action_lines = [_format_action(action) for action in model_output.action]
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if action_lines:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('アクション: ' + ' / '.join(action_lines))
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if model_output.evaluation_previous_goal:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('評価: ' + _compact_text(model_output.evaluation_previous_goal))
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if model_output.next_goal:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('次の目標: ' + _compact_text(model_output.next_goal))
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if model_output.current_status:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('現在の状況: ' + _compact_text(model_output.current_status))

	# EN: Assign value to result_lines.
	# JP: result_lines に値を代入する。
	result_lines = [text for text in (_format_result(r) for r in getattr(step, 'result', [])) if text]
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if result_lines:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('結果: ' + ' / '.join(result_lines))

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return '\n'.join(lines)


# EN: Define function `_iter_history_steps`.
# JP: 関数 `_iter_history_steps` を定義する。
def _iter_history_steps(history: AgentHistoryList) -> list[tuple[int, Any]]:
	# JP: step_number を正規化しつつ順序付きリストへ変換
	# EN: Normalize step numbers and return an ordered list
	steps: list[tuple[int, Any]] = []
	# EN: Assign value to next_index.
	# JP: next_index に値を代入する。
	next_index = 1
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for step in history.history:
		# EN: Assign value to metadata.
		# JP: metadata に値を代入する。
		metadata = getattr(step, 'metadata', None)
		# EN: Assign value to step_number.
		# JP: step_number に値を代入する。
		step_number = getattr(metadata, 'step_number', None) if metadata else None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not isinstance(step_number, int) or step_number < 1:
			# EN: Assign value to step_number.
			# JP: step_number に値を代入する。
			step_number = next_index
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		steps.append((step_number, step))
		# EN: Assign value to next_index.
		# JP: next_index に値を代入する。
		next_index = step_number + 1
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return steps


# EN: Define function `_format_history_messages`.
# JP: 関数 `_format_history_messages` を定義する。
def _format_history_messages(history: AgentHistoryList) -> list[tuple[int, str]]:
	# JP: 履歴をステップ番号と表示文のペアに変換
	# EN: Convert history into (step_number, message) pairs
	return [(step_number, _format_step_entry(step_number, step)) for step_number, step in _iter_history_steps(history)]


# EN: Define function `_format_step_plan`.
# JP: 関数 `_format_step_plan` を定義する。
def _format_step_plan(
	step_number: int,
	state: BrowserStateSummary,
	model_output: AgentOutput,
) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Format a step plan without truncation."""
	# JP: 実行前の計画をステップ単位で整形
	# EN: Format pre-execution step plans
	lines: list[str] = [f'ステップ{step_number}']

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if model_output.evaluation_previous_goal:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('評価: ' + _compact_text(model_output.evaluation_previous_goal))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if model_output.memory:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('メモリ: ' + _compact_text(model_output.memory))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if model_output.next_goal:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('次の目標: ' + _compact_text(model_output.next_goal))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if model_output.current_status:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('現在の状況: ' + _compact_text(model_output.current_status))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if model_output.persistent_notes:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('永続メモ: ' + _compact_text(model_output.persistent_notes))

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return '\n'.join(lines)


# EN: Define function `_summarize_history`.
# JP: 関数 `_summarize_history` を定義する。
def _summarize_history(history: AgentHistoryList) -> str:
	# JP: 実行結果の要約を生成して最終応答にする
	# EN: Build a summary of the run as the final response
	steps = _iter_history_steps(history)
	# EN: Assign value to total_steps.
	# JP: total_steps に値を代入する。
	total_steps = max((step_number for step_number, _ in steps), default=0)
	# EN: Assign value to success.
	# JP: success に値を代入する。
	success = history.is_successful()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if success is True:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		prefix, status = '✅', '成功'
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif success is False:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		prefix, status = '⚠️', '失敗'
	else:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		prefix, status = 'ℹ️', '未確定'

	# EN: Assign value to lines.
	# JP: lines に値を代入する。
	lines = [f'{prefix} {total_steps}ステップでエージェントが実行されました（結果: {status}）。']

	# EN: Assign value to final_text.
	# JP: final_text に値を代入する。
	final_text = history.final_result()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if final_text:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('最終報告: ' + _compact_text(final_text))
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	elif success is True:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('最終報告: (詳細な結果テキストはありません)')

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if history.history:
		# EN: Assign value to last_state.
		# JP: last_state に値を代入する。
		last_state = history.history[-1].state
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if last_state and last_state.url:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(f'最終URL: {last_state.url}')

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return _append_final_response_notice('\n'.join(lines))

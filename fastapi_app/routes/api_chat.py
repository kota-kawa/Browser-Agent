# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# JP: チャット/フォローアップの API
# EN: Chat and follow-up API endpoints
from fastapi import APIRouter, Request
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from fastapi.responses import JSONResponse

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.env import _CONVERSATION_CONTEXT_WINDOW
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.exceptions import AgentControllerError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.agent_runtime import finalize_summary, get_agent_controller
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.conversation_review import _analyze_conversation_history
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.formatting import _format_history_messages, _summarize_history
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.history_store import (
	_append_history_message,
	_broadcaster,
	_copy_history,
	_update_history_message,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..services.input_guard import InputGuardError, check_prompt_safety
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .utils import read_json_payload

# EN: Assign value to router.
# JP: router に値を代入する。
router = APIRouter()

# EN: Assign value to _STEP_MESSAGE_RE.
# JP: _STEP_MESSAGE_RE に値を代入する。
_STEP_MESSAGE_RE = re.compile(r'^ステップ\d+')


# EN: Define function `_build_recent_conversation_context`.
# JP: 関数 `_build_recent_conversation_context` を定義する。
def _build_recent_conversation_context(
	messages: list[dict[str, Any]],
	limit: int,
) -> str | None:
	# JP: 直近の会話だけを抽出し、ステップログは除外して短いコンテキストを作る
	# EN: Build a short recent-context block while excluding step-log messages
	if limit <= 0 or not messages:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Assign annotated value to filtered.
	# JP: filtered に型付きの値を代入する。
	filtered: list[dict[str, str]] = []
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for msg in messages:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not isinstance(msg, dict):
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue
		# EN: Assign value to role.
		# JP: role に値を代入する。
		role = msg.get('role')
		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = (msg.get('content') or '').strip()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not content:
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if role == 'assistant' and _STEP_MESSAGE_RE.match(content):
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		filtered.append({'role': role, 'content': content})

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not filtered:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Assign value to tail.
	# JP: tail に値を代入する。
	tail = filtered[-limit:]
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not tail:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# JP: LLM に渡すための人間可読な履歴文に整形
	# EN: Format a human-readable history snippet for the LLM
	lines = ['以下は直近の会話履歴です。必要に応じて参照してください。']
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for entry in tail:
		# EN: Assign value to role_label.
		# JP: role_label に値を代入する。
		role_label = 'ユーザー' if entry['role'] == 'user' else 'アシスタント'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append(f'{role_label}: {entry["content"]}')
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return '\n'.join(lines)


# EN: Define async function `chat`.
# JP: 非同期関数 `chat` を定義する。
@router.post('/api/chat')
async def chat(request: Request) -> JSONResponse:
	# EN: Assign value to payload.
	# JP: payload に値を代入する。
	payload = await read_json_payload(request)
	# EN: Assign value to prompt.
	# JP: prompt に値を代入する。
	prompt = (payload.get('prompt') or '').strip()
	# EN: Assign value to start_new_task.
	# JP: start_new_task に値を代入する。
	start_new_task = bool(payload.get('new_task'))
	# JP: 信頼された呼び出し元のみ、初回の会話レビューをスキップ可能
	# EN: Trusted callers may skip the initial conversation review
	skip_conversation_review = bool(payload.get('skip_conversation_review'))

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not prompt:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': 'プロンプトを入力してください。'}, status_code=400)

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# JP: 入力の安全性を事前にチェックしてブロックを防ぐ
		# EN: Pre-check prompt safety and block unsafe input early
		guard_result = await check_prompt_safety(prompt)
	except InputGuardError as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Safety guard check failed: %s', exc)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': f'入力の安全性チェックに失敗しました: {exc}'}, status_code=503)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not guard_result.is_safe:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.info('Blocked prompt by safety guard. Categories: %s', ','.join(guard_result.categories))
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse(
			{'error': '入力内容が安全性チェックによりブロックされました。別の表現でお試しください。'},
			status_code=400,
		)

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# JP: 実行中のコントローラーを取得（初期化も含む）
		# EN: Get or initialize the agent controller
		controller = get_agent_controller()
	except AgentControllerError as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_append_history_message('user', prompt)
		# EN: Assign value to message.
		# JP: message に値を代入する。
		message = finalize_summary(f'エージェントの実行に失敗しました: {exc}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning(message)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_append_history_message('assistant', message)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_broadcaster.publish(
			{
				'type': 'status',
				'payload': {
					'agent_running': False,
					'run_summary': message,
				},
			}
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'messages': _copy_history(), 'run_summary': message})
	except Exception as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_append_history_message('user', prompt)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Unexpected error while running browser agent')
		# EN: Assign value to error_message.
		# JP: error_message に値を代入する。
		error_message = finalize_summary(f'エージェントの実行中に予期しないエラーが発生しました: {exc}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_append_history_message('assistant', error_message)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_broadcaster.publish(
			{
				'type': 'status',
				'payload': {
					'agent_running': False,
					'run_summary': error_message,
				},
			}
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'messages': _copy_history(), 'run_summary': error_message})

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if start_new_task:
		# JP: 新規タスク開始は実行中でない時のみ許可
		# EN: Allow starting a new task only when the agent is idle
		if controller.is_running():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_append_history_message('user', prompt)
			# EN: Assign value to message.
			# JP: message に値を代入する。
			message = 'エージェント実行中は新しいタスクを開始できません。現在の実行が完了するまでお待ちください。'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_append_history_message('assistant', message)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse(
				{
					'messages': _copy_history(),
					'run_summary': message,
					'agent_running': True,
				},
				status_code=409,
			)
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.prepare_for_new_task()
		except AgentControllerError as exc:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_append_history_message('user', prompt)
			# EN: Assign value to message.
			# JP: message に値を代入する。
			message = finalize_summary(f'新しいタスクを開始できませんでした: {exc}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_append_history_message('assistant', message)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'messages': _copy_history(), 'run_summary': message}, status_code=400)

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	_append_history_message('user', prompt)

	# JP: 初回プロンプトはブラウザ操作の要否をAIレビューで判定する
	# EN: For the first prompt, decide whether browser actions are needed
	if not skip_conversation_review and not controller.is_running() and not controller.has_handled_initial_prompt():
		# EN: Assign value to analysis.
		# JP: analysis に値を代入する。
		analysis = _analyze_conversation_history(_copy_history(), loop=controller.loop)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not analysis.get('needs_action'):
			# EN: Assign value to reply.
			# JP: reply に値を代入する。
			reply = finalize_summary(analysis.get('reply') or analysis.get('reason') or 'ブラウザ操作は不要と判断しました。')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_append_history_message('assistant', reply)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.mark_initial_prompt_handled()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_broadcaster.publish(
				{
					'type': 'status',
					'payload': {
						'agent_running': False,
						'run_summary': reply,
					},
				}
			)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'messages': _copy_history(), 'run_summary': reply})

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if controller.is_running():
		# JP: 実行中はフォローアップとして指示をキューに積む
		# EN: If running, enqueue as a follow-up instruction
		was_paused = controller.is_paused()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.enqueue_follow_up(prompt)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if was_paused:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				controller.resume()
		except AgentControllerError as exc:
			# EN: Assign value to message.
			# JP: message に値を代入する。
			message = f'フォローアップの指示の適用に失敗しました: {exc}'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(message)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_append_history_message('assistant', message)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'messages': _copy_history(), 'run_summary': message, 'queued': False})

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if was_paused:
			# EN: Assign value to ack_message.
			# JP: ack_message に値を代入する。
			ack_message = 'エージェントは一時停止中でした。新しい指示で実行を再開します。'
		else:
			# EN: Assign value to ack_message.
			# JP: ack_message に値を代入する。
			ack_message = 'フォローアップの指示を受け付けました。現在の実行に反映します。'
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_append_history_message('assistant', ack_message)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse(
			{
				'messages': _copy_history(),
				'run_summary': ack_message,
				'queued': True,
				'agent_running': True,
			},
			status_code=202,
		)

	# EN: Define function `on_complete`.
	# JP: 関数 `on_complete` を定義する。
	def on_complete(result_or_error: Any) -> None:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(result_or_error, Exception):
				# JP: 例外時は要約メッセージを返してステータス更新
				# EN: On error, report a summarized message and update status
				exc = result_or_error
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(exc, AgentControllerError):
					# EN: Assign value to message.
					# JP: message に値を代入する。
					message = finalize_summary(f'エージェントの実行に失敗しました: {exc}')
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.warning(message)
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.exception('Unexpected error while running browser agent')
					# EN: Assign value to message.
					# JP: message に値を代入する。
					message = finalize_summary(f'エージェントの実行中に予期しないエラーが発生しました: {exc}')

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_append_history_message('assistant', message)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_broadcaster.publish(
					{
						'type': 'status',
						'payload': {
							'agent_running': False,
							'run_summary': message,
						},
					}
				)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Assign value to run_result.
			# JP: run_result に値を代入する。
			run_result = result_or_error
			# Ensure we have the result object
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not hasattr(run_result, 'history'):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.error('AgentRunResult missing history attribute: %r', run_result)
				# EN: Assign value to message.
				# JP: message に値を代入する。
				message = finalize_summary('エージェントの実行結果が不正です。')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_append_history_message('assistant', message)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_broadcaster.publish(
					{
						'type': 'status',
						'payload': {
							'agent_running': False,
							'run_summary': message,
						},
					}
				)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Assign value to agent_history.
			# JP: agent_history に値を代入する。
			agent_history = run_result.filtered_history or run_result.history
			# JP: ステップ履歴をチャット履歴へ反映する
			# EN: Project step history into the chat history
			step_messages = _format_history_messages(agent_history)
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for step_number, content in step_messages:
				# EN: Assign value to message_id.
				# JP: message_id に値を代入する。
				message_id = run_result.step_message_ids.get(step_number)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if message_id is None:
					# EN: Assign value to message_id.
					# JP: message_id に値を代入する。
					message_id = controller.get_step_message_id(step_number)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if message_id is not None:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					_update_history_message(message_id, content)
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					controller.remember_step_message_id(step_number, message_id)
				else:
					# EN: Assign value to appended.
					# JP: appended に値を代入する。
					appended = _append_history_message('assistant', content)
					# EN: Assign value to new_id.
					# JP: new_id に値を代入する。
					new_id = int(appended['id'])
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					controller.remember_step_message_id(step_number, new_id)
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					run_result.step_message_ids[step_number] = new_id

			# JP: 最終的な要約を作成してUIへ通知
			# EN: Create a final summary and notify the UI
			summary_message = _summarize_history(agent_history)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_append_history_message('assistant', summary_message)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			_broadcaster.publish(
				{
					'type': 'status',
					'payload': {
						'agent_running': False,
						'run_summary': summary_message,
					},
				}
			)
		except Exception as exc:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.exception('Unexpected error in on_complete callback')
			# EN: Assign value to error_message.
			# JP: error_message に値を代入する。
			error_message = finalize_summary(f'結果の処理中にエラーが発生しました: {exc}')
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_append_history_message('assistant', error_message)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				_broadcaster.publish(
					{
						'type': 'status',
						'payload': {
							'agent_running': False,
							'run_summary': error_message,
						},
					}
				)
			except Exception:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.exception('Failed to report error in on_complete')

	# EN: Assign value to context_message.
	# JP: context_message に値を代入する。
	context_message = _build_recent_conversation_context(
		_copy_history(),
		_CONVERSATION_CONTEXT_WINDOW,
	)

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# JP: 非同期で実行し、即座に 202 を返す
		# EN: Run asynchronously and return 202 immediately
		controller.run(
			prompt,
			background=True,
			completion_callback=on_complete,
			additional_system_message=context_message,
		)
	except AgentControllerError as exc:
		# EN: Assign value to message.
		# JP: message に値を代入する。
		message = finalize_summary(f'エージェントの実行に失敗しました: {exc}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning(message)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_append_history_message('assistant', message)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_broadcaster.publish(
			{
				'type': 'status',
				'payload': {
					'agent_running': False,
					'run_summary': message,
				},
			}
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'messages': _copy_history(), 'run_summary': message})
	except Exception as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Unexpected error while running browser agent')
		# EN: Assign value to error_message.
		# JP: error_message に値を代入する。
		error_message = finalize_summary(f'エージェントの実行中に予期しないエラーが発生しました: {exc}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_append_history_message('assistant', error_message)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_broadcaster.publish(
			{
				'type': 'status',
				'payload': {
					'agent_running': False,
					'run_summary': error_message,
				},
			}
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'messages': _copy_history(), 'run_summary': error_message})

	# Return immediately with 202 Accepted
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse({'messages': _copy_history(), 'run_summary': '', 'agent_running': True}, status_code=202)


# EN: Define async function `agent_relay`.
# JP: 非同期関数 `agent_relay` を定義する。
@router.post('/api/agent-relay')
async def agent_relay(request: Request) -> JSONResponse:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Endpoint for receiving requests from external agents without updating the main chat history.
	Expected JSON payload:
	- prompt: instruction for the browser agent
	"""
	# EN: Assign value to payload.
	# JP: payload に値を代入する。
	payload = await read_json_payload(request)
	# EN: Assign value to prompt.
	# JP: prompt に値を代入する。
	prompt = (payload.get('prompt') or '').strip()

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not prompt:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': 'プロンプトを入力してください。'}, status_code=400)

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# JP: メインチャット履歴に影響せず、コントローラーのみ利用する
		# EN: Use the controller without touching main chat history
		controller = get_agent_controller()
	except AgentControllerError as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Failed to initialize agent controller for agent relay: %s', exc)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': f'エージェントの初期化に失敗しました: {exc}'}, status_code=503)
	except Exception as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Unexpected error while preparing agent controller for agent relay')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': f'エージェントの初期化中に予期しないエラーが発生しました: {exc}'}, status_code=500)

	# JP: 外部エージェントにも初回レビューを適用
	# EN: Apply the initial review for external agent requests as well
	if not controller.is_running() and not controller.has_handled_initial_prompt():
		# EN: Assign value to analysis.
		# JP: analysis に値を代入する。
		analysis = _analyze_conversation_history([{'role': 'user', 'content': prompt}], loop=controller.loop)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not analysis.get('needs_action'):
			# EN: Assign value to reply.
			# JP: reply に値を代入する。
			reply = analysis.get('reply') or analysis.get('reason') or 'ブラウザ操作は不要と判断しました。'
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.mark_initial_prompt_handled()
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return (
				JSONResponse(
					{
						'summary': reply,
						'steps': [],
						'success': True,
						'final_result': reply,
						'analysis': analysis,
						'action_taken': False,
					}
				),
			)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if controller.is_running():
		# JP: 実行中はフォローアップとして扱う
		# EN: Treat as follow-up when already running
		was_paused = controller.is_paused()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			controller.enqueue_follow_up(prompt)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if was_paused:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				controller.resume()
		except AgentControllerError as exc:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning('Failed to enqueue follow-up instruction via agent relay: %s', exc)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'error': f'フォローアップの指示の適用に失敗しました: {exc}'}, status_code=400)
		except Exception as exc:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.exception('Unexpected error while enqueueing follow-up instruction via agent relay')
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return JSONResponse({'error': f'フォローアップ指示の処理中に予期しないエラーが発生しました: {exc}'}, status_code=500)

		# EN: Assign value to ack_message.
		# JP: ack_message に値を代入する。
		ack_message = 'フォローアップの指示を受け付けました。現在の実行に反映します。'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse(
			{
				'status': 'follow_up_enqueued',
				'message': ack_message,
				'agent_running': True,
				'queued': True,
			},
			status_code=202,
		)

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# JP: 履歴に残さない同期実行（外部利用向け）
		# EN: Run synchronously without recording history (external use)
		run_result = controller.run(prompt, record_history=False)
	except AgentControllerError as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Failed to execute agent relay request: %s', exc)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': f'エージェントの実行に失敗しました: {exc}'}, status_code=500)
	except Exception as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Unexpected error while executing agent relay request')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return JSONResponse({'error': f'予期しないエラーが発生しました: {exc}'}, status_code=500)

	# EN: Assign value to agent_history.
	# JP: agent_history に値を代入する。
	agent_history = run_result.filtered_history or run_result.history
	# EN: Assign value to summary_message.
	# JP: summary_message に値を代入する。
	summary_message = _summarize_history(agent_history)
	# EN: Assign value to step_messages.
	# JP: step_messages に値を代入する。
	step_messages = [{'step_number': number, 'content': content} for number, content in _format_history_messages(agent_history)]

	# EN: Assign annotated value to response_data.
	# JP: response_data に型付きの値を代入する。
	response_data: dict[str, Any] = {
		'summary': summary_message,
		'steps': step_messages,
		'success': agent_history.is_successful(),
		'final_result': agent_history.final_result(),
	}

	# EN: Assign value to usage.
	# JP: usage に値を代入する。
	usage = getattr(agent_history, 'usage', None)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if usage is not None:
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			response_data['usage'] = usage.model_dump()
		except AttributeError:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			response_data['usage'] = usage

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return JSONResponse(response_data)

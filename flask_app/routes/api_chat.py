from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..core.config import logger
from ..core.env import _CONVERSATION_CONTEXT_WINDOW
from ..core.exceptions import AgentControllerError
from ..services.agent_runtime import finalize_summary, get_agent_controller
from ..services.conversation_review import _analyze_conversation_history
from ..services.formatting import _format_history_messages, _summarize_history
from ..services.history_store import (
	_append_history_message,
	_broadcaster,
	_copy_history,
	_update_history_message,
)
from ..services.input_guard import InputGuardError, check_prompt_safety
from .utils import read_json_payload

router = APIRouter()

_STEP_MESSAGE_RE = re.compile(r'^ステップ\\d+')


def _build_recent_conversation_context(
	messages: list[dict[str, Any]],
	limit: int,
) -> str | None:
	if limit <= 0 or not messages:
		return None

	filtered: list[dict[str, str]] = []
	for msg in messages:
		if not isinstance(msg, dict):
			continue
		role = msg.get('role')
		content = (msg.get('content') or '').strip()
		if not content:
			continue
		if role == 'assistant' and _STEP_MESSAGE_RE.match(content):
			continue
		filtered.append({'role': role, 'content': content})

	if not filtered:
		return None

	tail = filtered[-limit:]
	if not tail:
		return None

	lines = ['以下は直近の会話履歴です。必要に応じて参照してください。']
	for entry in tail:
		role_label = 'ユーザー' if entry['role'] == 'user' else 'アシスタント'
		lines.append(f'{role_label}: {entry["content"]}')
	return '\n'.join(lines)


@router.post('/api/chat')
async def chat(request: Request) -> JSONResponse:
	payload = await read_json_payload(request)
	prompt = (payload.get('prompt') or '').strip()
	start_new_task = bool(payload.get('new_task'))
	# Trusted callers can bypass the initial AI review when they already planned concrete steps.
	skip_conversation_review = bool(payload.get('skip_conversation_review'))

	if not prompt:
		return JSONResponse({'error': 'プロンプトを入力してください。'}, status_code=400)

	try:
		guard_result = await check_prompt_safety(prompt)
	except InputGuardError as exc:
		logger.warning('Llama Guard check failed: %s', exc)
		return JSONResponse({'error': f'入力の安全性チェックに失敗しました: {exc}'}, status_code=503)

	if not guard_result.is_safe:
		logger.info('Blocked prompt by Llama Guard. Categories: %s', ','.join(guard_result.categories))
		return JSONResponse(
			{'error': '入力内容が安全性チェックによりブロックされました。別の表現でお試しください。'},
			status_code=400,
		)

	try:
		controller = get_agent_controller()
	except AgentControllerError as exc:
		_append_history_message('user', prompt)
		message = finalize_summary(f'エージェントの実行に失敗しました: {exc}')
		logger.warning(message)
		_append_history_message('assistant', message)
		_broadcaster.publish(
			{
				'type': 'status',
				'payload': {
					'agent_running': False,
					'run_summary': message,
				},
			}
		)
		return JSONResponse({'messages': _copy_history(), 'run_summary': message})
	except Exception as exc:
		_append_history_message('user', prompt)
		logger.exception('Unexpected error while running browser agent')
		error_message = finalize_summary(f'エージェントの実行中に予期しないエラーが発生しました: {exc}')
		_append_history_message('assistant', error_message)
		_broadcaster.publish(
			{
				'type': 'status',
				'payload': {
					'agent_running': False,
					'run_summary': error_message,
				},
			}
		)
		return JSONResponse({'messages': _copy_history(), 'run_summary': error_message})

	if start_new_task:
		if controller.is_running():
			_append_history_message('user', prompt)
			message = 'エージェント実行中は新しいタスクを開始できません。現在の実行が完了するまでお待ちください。'
			_append_history_message('assistant', message)
			return JSONResponse(
				{
					'messages': _copy_history(),
					'run_summary': message,
					'agent_running': True,
				},
				status_code=409,
			)
		try:
			controller.prepare_for_new_task()
		except AgentControllerError as exc:
			_append_history_message('user', prompt)
			message = finalize_summary(f'新しいタスクを開始できませんでした: {exc}')
			_append_history_message('assistant', message)
			return JSONResponse({'messages': _copy_history(), 'run_summary': message}, status_code=400)

	_append_history_message('user', prompt)

	# First prompt of a task: decide if browser actions are needed
	if not skip_conversation_review and not controller.is_running() and not controller.has_handled_initial_prompt():
		analysis = _analyze_conversation_history(_copy_history(), loop=controller.loop)
		if not analysis.get('needs_action'):
			reply = finalize_summary(analysis.get('reply') or analysis.get('reason') or 'ブラウザ操作は不要と判断しました。')
			_append_history_message('assistant', reply)
			controller.mark_initial_prompt_handled()
			_broadcaster.publish(
				{
					'type': 'status',
					'payload': {
						'agent_running': False,
						'run_summary': reply,
					},
				}
			)
			return JSONResponse({'messages': _copy_history(), 'run_summary': reply})

	if controller.is_running():
		was_paused = controller.is_paused()
		try:
			controller.enqueue_follow_up(prompt)
			if was_paused:
				controller.resume()
		except AgentControllerError as exc:
			message = f'フォローアップの指示の適用に失敗しました: {exc}'
			logger.warning(message)
			_append_history_message('assistant', message)
			return JSONResponse({'messages': _copy_history(), 'run_summary': message, 'queued': False})

		if was_paused:
			ack_message = 'エージェントは一時停止中でした。新しい指示で実行を再開します。'
		else:
			ack_message = 'フォローアップの指示を受け付けました。現在の実行に反映します。'
		_append_history_message('assistant', ack_message)
		return JSONResponse(
			{
				'messages': _copy_history(),
				'run_summary': ack_message,
				'queued': True,
				'agent_running': True,
			},
			status_code=202,
		)

	def on_complete(result_or_error: Any) -> None:
		try:
			if isinstance(result_or_error, Exception):
				exc = result_or_error
				if isinstance(exc, AgentControllerError):
					message = finalize_summary(f'エージェントの実行に失敗しました: {exc}')
					logger.warning(message)
				else:
					logger.exception('Unexpected error while running browser agent')
					message = finalize_summary(f'エージェントの実行中に予期しないエラーが発生しました: {exc}')

				_append_history_message('assistant', message)
				_broadcaster.publish(
					{
						'type': 'status',
						'payload': {
							'agent_running': False,
							'run_summary': message,
						},
					}
				)
				return

			run_result = result_or_error
			# Ensure we have the result object
			if not hasattr(run_result, 'history'):
				logger.error('AgentRunResult missing history attribute: %r', run_result)
				message = finalize_summary('エージェントの実行結果が不正です。')
				_append_history_message('assistant', message)
				_broadcaster.publish(
					{
						'type': 'status',
						'payload': {
							'agent_running': False,
							'run_summary': message,
						},
					}
				)
				return

			agent_history = run_result.filtered_history or run_result.history
			step_messages = _format_history_messages(agent_history)
			for step_number, content in step_messages:
				message_id = run_result.step_message_ids.get(step_number)
				if message_id is None:
					message_id = controller.get_step_message_id(step_number)
				if message_id is not None:
					_update_history_message(message_id, content)
					controller.remember_step_message_id(step_number, message_id)
				else:
					appended = _append_history_message('assistant', content)
					new_id = int(appended['id'])
					controller.remember_step_message_id(step_number, new_id)
					run_result.step_message_ids[step_number] = new_id

			summary_message = _summarize_history(agent_history)
			_append_history_message('assistant', summary_message)
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
			logger.exception('Unexpected error in on_complete callback')
			error_message = finalize_summary(f'結果の処理中にエラーが発生しました: {exc}')
			try:
				_append_history_message('assistant', error_message)
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
				logger.exception('Failed to report error in on_complete')

	context_message = _build_recent_conversation_context(
		_copy_history(),
		_CONVERSATION_CONTEXT_WINDOW,
	)

	try:
		controller.run(
			prompt,
			background=True,
			completion_callback=on_complete,
			additional_system_message=context_message,
		)
	except AgentControllerError as exc:
		message = finalize_summary(f'エージェントの実行に失敗しました: {exc}')
		logger.warning(message)
		_append_history_message('assistant', message)
		_broadcaster.publish(
			{
				'type': 'status',
				'payload': {
					'agent_running': False,
					'run_summary': message,
				},
			}
		)
		return JSONResponse({'messages': _copy_history(), 'run_summary': message})
	except Exception as exc:
		logger.exception('Unexpected error while running browser agent')
		error_message = finalize_summary(f'エージェントの実行中に予期しないエラーが発生しました: {exc}')
		_append_history_message('assistant', error_message)
		_broadcaster.publish(
			{
				'type': 'status',
				'payload': {
					'agent_running': False,
					'run_summary': error_message,
				},
			}
		)
		return JSONResponse({'messages': _copy_history(), 'run_summary': error_message})

	# Return immediately with 202 Accepted
	return JSONResponse({'messages': _copy_history(), 'run_summary': '', 'agent_running': True}, status_code=202)


@router.post('/api/agent-relay')
async def agent_relay(request: Request) -> JSONResponse:
	"""
	Endpoint for receiving requests from external agents without updating the main chat history.
	Expected JSON payload:
	- prompt: instruction for the browser agent
	"""
	payload = await read_json_payload(request)
	prompt = (payload.get('prompt') or '').strip()

	if not prompt:
		return JSONResponse({'error': 'プロンプトを入力してください。'}, status_code=400)

	try:
		controller = get_agent_controller()
	except AgentControllerError as exc:
		logger.warning('Failed to initialize agent controller for agent relay: %s', exc)
		return JSONResponse({'error': f'エージェントの初期化に失敗しました: {exc}'}, status_code=503)
	except Exception as exc:
		logger.exception('Unexpected error while preparing agent controller for agent relay')
		return JSONResponse({'error': f'エージェントの初期化中に予期しないエラーが発生しました: {exc}'}, status_code=500)

	# First prompt of a task: decide if browser actions are needed
	if not controller.is_running() and not controller.has_handled_initial_prompt():
		analysis = _analyze_conversation_history([{'role': 'user', 'content': prompt}], loop=controller.loop)
		if not analysis.get('needs_action'):
			reply = analysis.get('reply') or analysis.get('reason') or 'ブラウザ操作は不要と判断しました。'
			controller.mark_initial_prompt_handled()
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

	if controller.is_running():
		was_paused = controller.is_paused()
		try:
			controller.enqueue_follow_up(prompt)
			if was_paused:
				controller.resume()
		except AgentControllerError as exc:
			logger.warning('Failed to enqueue follow-up instruction via agent relay: %s', exc)
			return JSONResponse({'error': f'フォローアップの指示の適用に失敗しました: {exc}'}, status_code=400)
		except Exception as exc:
			logger.exception('Unexpected error while enqueueing follow-up instruction via agent relay')
			return JSONResponse({'error': f'フォローアップ指示の処理中に予期しないエラーが発生しました: {exc}'}, status_code=500)

		ack_message = 'フォローアップの指示を受け付けました。現在の実行に反映します。'
		return JSONResponse(
			{
				'status': 'follow_up_enqueued',
				'message': ack_message,
				'agent_running': True,
				'queued': True,
			},
			status_code=202,
		)

	try:
		run_result = controller.run(prompt, record_history=False)
	except AgentControllerError as exc:
		logger.warning('Failed to execute agent relay request: %s', exc)
		return JSONResponse({'error': f'エージェントの実行に失敗しました: {exc}'}, status_code=500)
	except Exception as exc:
		logger.exception('Unexpected error while executing agent relay request')
		return JSONResponse({'error': f'予期しないエラーが発生しました: {exc}'}, status_code=500)

	agent_history = run_result.filtered_history or run_result.history
	summary_message = _summarize_history(agent_history)
	step_messages = [{'step_number': number, 'content': content} for number, content in _format_history_messages(agent_history)]

	response_data: dict[str, Any] = {
		'summary': summary_message,
		'steps': step_messages,
		'success': agent_history.is_successful(),
		'final_result': agent_history.final_result(),
	}

	usage = getattr(agent_history, 'usage', None)
	if usage is not None:
		try:
			response_data['usage'] = usage.model_dump()
		except AttributeError:
			response_data['usage'] = usage

	return JSONResponse(response_data)

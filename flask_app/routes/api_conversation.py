from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..services.agent_runtime import get_controller_if_initialized
from ..services.conversation_review import _analyze_conversation_history
from .utils import read_json_payload

router = APIRouter()


@router.post('/api/conversations/review')
@router.post('/api/check-conversation-history')  # backward compatibility
async def check_conversation_history(request: Request) -> JSONResponse:
	"""
	Endpoint to receive and analyze conversation history from other agents.

	Expects JSON payload with:
	- history (preferred) or conversation_history: list of message objects with 'role' and 'content' fields

	Returns:
	- analysis: the LLM analysis result
	- action_taken: whether any browser action was initiated
	- run_summary: summary of the action taken (if any)
	"""
	payload = await read_json_payload(request)
	conversation_history = payload.get('history') or payload.get('conversation_history') or payload.get('messages') or []

	if not conversation_history:
		return JSONResponse({'error': '会話履歴が提供されていません。'}, status_code=400)

	if not isinstance(conversation_history, list):
		return JSONResponse({'error': '会話履歴はリスト形式である必要があります。'}, status_code=400)

	# Try to use existing controller loop to avoid creating short-lived loops
	controller = get_controller_if_initialized()
	loop = controller.loop if controller else None

	# Analyze the conversation history
	analysis = _analyze_conversation_history(conversation_history, loop=loop)

	response_data = {
		'analysis': analysis,
		'should_reply': bool(analysis.get('should_reply')),
		'reply': analysis.get('reply') or '',
		'addressed_agents': analysis.get('addressed_agents') or [],
		'action_taken': False,
		'run_summary': None,
	}

	# If action is needed, we currently DO NOT trigger the browser agent automatically.
	# We just inform the platform that an action is possible.
	if analysis.get('needs_action') and analysis.get('task_description'):
		task_description = analysis['task_description']
		# Update reply to include the proposed task if not already present
		if not response_data.get('reply'):
			response_data['reply'] = f'ブラウザ操作が可能です: {task_description}'
			response_data['should_reply'] = True

		# We do NOT execute the task here.
		response_data['action_taken'] = False
		response_data['run_summary'] = f'ブラウザ操作が提案されましたが、自動実行は無効化されています: {task_description}'

	return JSONResponse(response_data)

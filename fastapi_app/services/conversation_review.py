# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, Literal

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, Field, ValidationError

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.exceptions import ModelProviderError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import SystemMessage, UserMessage

# JP: 会話履歴からブラウザ操作の要否を判定するレビュー機能
# EN: Conversation review that decides whether browser actions are needed
from ..core.config import logger
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.env import _CONVERSATION_CONTEXT_WINDOW
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from ..core.exceptions import AgentControllerError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from .llm_factory import _create_selected_llm


# EN: Define class `ConversationAnalysis`.
# JP: クラス `ConversationAnalysis` を定義する。
class ConversationAnalysis(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Data model for the result of conversation analysis."""

	# JP: ブラウザ操作の要否と返答内容を含む構造化結果
	# EN: Structured output including action need and reply content
	should_reply: bool = Field(
		..., description='True if the assistant should provide a helpful reply even when no browser action is required.'
	)
	# EN: Assign annotated value to reply.
	# JP: reply に型付きの値を代入する。
	reply: str = Field(
		default='',
		description='A concise but complete answer for the user. Must be empty if should_reply is False.',
	)
	# EN: Assign annotated value to addressed_agents.
	# JP: addressed_agents に型付きの値を代入する。
	addressed_agents: list[str] = Field(
		default_factory=list,
		description='A list of agent names that are addressed in the conversation (e.g., "Browser Agent").',
	)
	# EN: Assign annotated value to needs_action.
	# JP: needs_action に型付きの値を代入する。
	needs_action: bool = Field(..., description='True if the conversation requires a browser action.')
	# EN: Assign annotated value to action_type.
	# JP: action_type に型付きの値を代入する。
	action_type: Literal['search', 'navigate', 'form_fill', 'data_extract'] | None = Field(
		None, description='The type of browser action required.'
	)
	# EN: Assign annotated value to task_description.
	# JP: task_description に型付きの値を代入する。
	task_description: str | None = Field(None, description='A specific and concrete task description for the browser agent.')
	# EN: Assign annotated value to reason.
	# JP: reason に型付きの値を代入する。
	reason: str = Field('', description='The reasoning behind the analysis and decision.')


# EN: Define function `_build_error_response`.
# JP: 関数 `_build_error_response` を定義する。
def _build_error_response(reason: str) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return a consistently shaped failure payload for the endpoint."""

	# JP: 失敗時も同一フォーマットで返して呼び出し側の処理を簡潔にする
	# EN: Keep a stable payload shape to simplify callers
	return {
		'should_reply': False,
		'reply': '',
		'addressed_agents': [],
		'needs_action': False,
		'action_type': None,
		'task_description': None,
		'reason': reason,
	}


# EN: Define function `_normalize_analysis_payload`.
# JP: 関数 `_normalize_analysis_payload` を定義する。
def _normalize_analysis_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Fill missing or malformed fields with safe defaults before validation."""

	# JP: 欠落フィールドを補完し、異常値を安全側へ補正
	# EN: Fill missing fields and coerce invalid values to safe defaults
	if payload is None:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {}

	# EN: Assign annotated value to normalized.
	# JP: normalized に型付きの値を代入する。
	normalized: dict[str, Any] = dict(payload)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	normalized.setdefault('should_reply', False)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	normalized.setdefault('reply', '')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	normalized.setdefault('addressed_agents', [])
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	normalized.setdefault('needs_action', False)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	normalized.setdefault('action_type', None)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	normalized.setdefault('task_description', None)

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not normalized.get('reason'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		normalized['reason'] = 'LLM output did not include a reason.'

	# Guard action_type against unexpected values
	# EN: Assign value to valid_action_types.
	# JP: valid_action_types に値を代入する。
	valid_action_types = {'search', 'navigate', 'form_fill', 'data_extract', None}
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if normalized.get('action_type') not in valid_action_types:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		normalized['action_type'] = None

	# If a reply is present, ensure should_reply is true.
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if normalized.get('reply'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		normalized['should_reply'] = True

	# Ensure reply is empty if should_reply is False
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not normalized.get('should_reply'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		normalized['reply'] = normalized.get('reply', '') or ''

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return normalized


# EN: Define function `_sanitize_json_string`.
# JP: 関数 `_sanitize_json_string` を定義する。
def _sanitize_json_string(text: str) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Sanitize a string for JSON parsing by fixing common LLM output issues."""
	# JP: LLM出力の改行/タブ等を簡易的にエスケープ補正
	# EN: Lightly sanitize common newline/tab issues in LLM JSON output
	# Fix unescaped newlines in string values
	# This is a simplified approach - replace literal newlines with escaped ones
	# within what appears to be JSON string content
	try:
		# EN: Assign value to result.
		# JP: result に値を代入する。
		result = re.sub(
			r'"((?:[^"\\]|\\.)*)(?:\n|\r|\t)((?:[^"\\]|\\.)*)"',
			lambda m: f'"{m.group(1)}\\n{m.group(2)}"',
			text,
		)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result
	except Exception:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return text


# EN: Define function `_extract_json_from_text`.
# JP: 関数 `_extract_json_from_text` を定義する。
def _extract_json_from_text(text: str) -> dict | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Extracts JSON from text, tolerating markdown code blocks and sanitizing."""
	# JP: ```json``` 形式と生の JSON の両方に対応
	# EN: Handle both ```json``` blocks and raw JSON blobs
	# Try to sanitize the text first
	sanitized_text = _sanitize_json_string(text)

	# EN: Assign value to candidates.
	# JP: candidates に値を代入する。
	candidates = [text]
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if sanitized_text != text:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		candidates.append(sanitized_text)

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for candidate in candidates:
		# Look for a JSON block ```json ... ```
		# EN: Assign value to json_match.
		# JP: json_match に値を代入する。
		json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', candidate)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if json_match:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return json.loads(json_match.group(1))
			except json.JSONDecodeError:
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass  # Fallback to the next method

		# Look for any JSON-like structure
		# EN: Assign value to json_match.
		# JP: json_match に値を代入する。
		json_match = re.search(r'\{[\s\S]*\}', candidate)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if json_match:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return json.loads(json_match.group())
			except json.JSONDecodeError:
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define function `_get_completion_payload`.
# JP: 関数 `_get_completion_payload` を定義する。
def _get_completion_payload(response: Any) -> Any:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Extract the completion payload from an LLM response.

	Supports both the current `.completion` attribute and the legacy `.result`
	field to stay compatible with older `browser-use` builds or third-party
	clients.
	"""
	# JP: 新旧インターフェース両対応のため複数属性を確認
	# EN: Support both new and legacy response shapes
	if hasattr(response, 'completion'):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return response.completion
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if hasattr(response, 'result'):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return response.result
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if isinstance(response, dict):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return response.get('completion') or response.get('result')
	# EN: Raise an exception.
	# JP: 例外を送出する。
	raise AttributeError('LLM response did not include a completion/result payload')


# EN: Define async function `_retry_with_json_correction`.
# JP: 非同期関数 `_retry_with_json_correction` を定義する。
async def _retry_with_json_correction(
	llm: Any, messages: list[Any], failed_output: str, error: Exception, max_retries: int = 2
) -> dict[str, Any] | None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Retry LLM call with JSON correction prompt after parse failure."""
	# JP: 失敗した JSON を短く抜粋し、修正指示を追加して再試行
	# EN: Retry with a correction prompt including a truncated bad output
	truncated_output = failed_output[:1500] + '...' if len(failed_output) > 1500 else failed_output

	# EN: Assign value to correction_message.
	# JP: correction_message に値を代入する。
	correction_message = UserMessage(
		role='user',
		content=f"""あなたの出力はJSONとして不正でした。エラー: {str(error)[:300]}

前回の出力（一部）:
{truncated_output}

以下の点に注意して、正しいJSONのみを再出力してください：
1. 文字列内の改行は \\n でエスケープする
2. 文字列内のダブルクォートは \\" でエスケープする
3. 制御文字（タブ等）は適切にエスケープする
4. JSONの構文（カンマ、括弧の対応）を確認する
5. 説明やマークダウンは含めず、純粋なJSONのみを出力する""",
	)

	# EN: Assign value to retry_messages.
	# JP: retry_messages に値を代入する。
	retry_messages = messages + [correction_message]

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for attempt in range(max_retries):
		# JP: 最大回数までリトライし、成功したら即返す
		# EN: Retry up to max_retries and return immediately on success
		try:
			# EN: Assign value to response.
			# JP: response に値を代入する。
			response = await llm.ainvoke(retry_messages)
			# EN: Assign value to response_text.
			# JP: response_text に値を代入する。
			response_text = _get_completion_payload(response)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(response_text, str):
				# EN: Assign value to extracted_json.
				# JP: extracted_json に値を代入する。
				extracted_json = _extract_json_from_text(response_text)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if extracted_json:
					# EN: Assign value to normalized.
					# JP: normalized に値を代入する。
					normalized = _normalize_analysis_payload(extracted_json)
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ConversationAnalysis.model_validate(normalized).model_dump()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(response_text, dict):
				# EN: Assign value to normalized.
				# JP: normalized に値を代入する。
				normalized = _normalize_analysis_payload(response_text)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ConversationAnalysis.model_validate(normalized).model_dump()

		except Exception as retry_error:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'JSON correction retry {attempt + 1}/{max_retries} failed: {retry_error}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if attempt == max_retries - 1:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return None


# EN: Define async function `_fallback_to_text_parsing`.
# JP: 非同期関数 `_fallback_to_text_parsing` を定義する。
async def _fallback_to_text_parsing(llm: Any, messages: list[Any]) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Fallback path when structured output is unavailable."""
	# JP: Structured output が使えない場合に JSON 抽出で対応
	# EN: Fallback to JSON extraction when structured output fails
	try:
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await llm.ainvoke(messages)
		# EN: Assign value to response_text.
		# JP: response_text に値を代入する。
		response_text = _get_completion_payload(response)
		# EN: Assign value to extracted_json.
		# JP: extracted_json に値を代入する。
		extracted_json = None
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(response_text, str):
			# EN: Assign value to extracted_json.
			# JP: extracted_json に値を代入する。
			extracted_json = _extract_json_from_text(response_text)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(response_text, dict):
			# EN: Assign value to extracted_json.
			# JP: extracted_json に値を代入する。
			extracted_json = response_text

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if extracted_json:
			# EN: Assign value to normalized.
			# JP: normalized に値を代入する。
			normalized = _normalize_analysis_payload(extracted_json)
			# EN: Assign value to analysis_result.
			# JP: analysis_result に値を代入する。
			analysis_result = ConversationAnalysis.model_validate(normalized)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return analysis_result.model_dump()

		# If JSON extraction failed, try retry with correction prompt
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(response_text, str):
			# EN: Assign value to retry_result.
			# JP: retry_result に値を代入する。
			retry_result = await _retry_with_json_correction(llm, messages, response_text, ValueError('JSON extraction failed'))
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if retry_result:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return retry_result

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError('Fallback parsing failed to produce a valid model.')

	except ModelProviderError as fallback_exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Provider error during conversation history analysis fallback: %s', fallback_exc)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _build_error_response(f'会話履歴の分析用LLM呼び出しに失敗しました: {fallback_exc}')
	except (ValidationError, ValueError) as fallback_exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Error during conversation history analysis fallback: %s', fallback_exc)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _build_error_response(f'会話履歴の分析中にエラーが発生しました: {fallback_exc}')


# EN: Define function `_looks_like_refusal`.
# JP: 関数 `_looks_like_refusal` を定義する。
def _looks_like_refusal(text: str) -> bool:
	# JP: 「拒否」に見える文言を簡易的に検出
	# EN: Heuristically detect refusal-like replies
	if not text:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True
	# EN: Assign value to lowered.
	# JP: lowered に値を代入する。
	lowered = text.lower()
	# EN: Assign value to refusal_phrases.
	# JP: refusal_phrases に値を代入する。
	refusal_phrases = (
		'ブラウザ操作',
		'文脈外',
		'回答しない',
		'回答でき',
		'対応でき',
		'できません',
		'outside the scope',
		'cannot answer',
		'not provide an answer',
		'not able to',
		'guidelines',
	)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return any(phrase in lowered for phrase in refusal_phrases)


# EN: Define function `_stringify_reply`.
# JP: 関数 `_stringify_reply` を定義する。
def _stringify_reply(payload: Any) -> str:
	# JP: 返答候補を文字列に正規化
	# EN: Normalize reply payload into a string
	if isinstance(payload, str):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return payload.strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if isinstance(payload, dict):
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for key in ('reply', 'content', 'text', 'message'):
			# EN: Assign value to value.
			# JP: value に値を代入する。
			value = payload.get(key)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(value, str) and value.strip():
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return value.strip()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return json.dumps(payload, ensure_ascii=False)
		except TypeError:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str(payload)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return str(payload).strip()


# EN: Define async function `_generate_direct_reply_async`.
# JP: 非同期関数 `_generate_direct_reply_async` を定義する。
async def _generate_direct_reply_async(llm: Any, conversation_history: list[dict[str, Any]]) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Generate a direct answer when no browser action is required."""
	# JP: ブラウザ不要時に直接回答を生成
	# EN: Generate a direct reply when no browser action is needed
	if not conversation_history:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ''

	# EN: Assign value to conversation_history.
	# JP: conversation_history に値を代入する。
	conversation_history = _trim_conversation_history(conversation_history)
	# EN: Assign value to conversation_text.
	# JP: conversation_text に値を代入する。
	conversation_text = ''
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for msg in conversation_history:
		# EN: Assign value to role.
		# JP: role に値を代入する。
		role = msg.get('role', 'unknown')
		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = msg.get('content', '')
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		conversation_text += f'{role}: {content}\n'

	# EN: Assign value to prompt.
	# JP: prompt に値を代入する。
	prompt = f"""以下は会話履歴です。最新のユーザーの質問に日本語で答えてください。

条件:
- ブラウザ操作やエージェントの都合には触れない
- 可能な範囲で直接回答する（不足があれば合理的な前提を短く述べる）
- 不要な質問はしない
- 簡潔だが質問には十分に答える

会話履歴:
{conversation_text}
"""

	# EN: Assign value to messages.
	# JP: messages に値を代入する。
	messages = [
		SystemMessage(content='You are a helpful assistant who answers user questions directly in Japanese.'),
		UserMessage(role='user', content=prompt),
	]
	# EN: Assign value to response.
	# JP: response に値を代入する。
	response = await llm.ainvoke(messages)
	# EN: Assign value to reply_text.
	# JP: reply_text に値を代入する。
	reply_text = _stringify_reply(_get_completion_payload(response))
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return reply_text


# EN: Define async function `_ensure_direct_reply_async`.
# JP: 非同期関数 `_ensure_direct_reply_async` を定義する。
async def _ensure_direct_reply_async(
	analysis_payload: dict[str, Any],
	llm: Any,
	conversation_history: list[dict[str, Any]],
) -> dict[str, Any]:
	# JP: needs_action が False の場合は直接回答を補強する
	# EN: Ensure a direct reply when no action is required
	if not analysis_payload or analysis_payload.get('needs_action'):
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return analysis_payload

	# EN: Assign value to reply_text.
	# JP: reply_text に値を代入する。
	reply_text = (analysis_payload.get('reply') or '').strip()
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not reply_text or _looks_like_refusal(reply_text) or not analysis_payload.get('should_reply'):
		# EN: Assign value to direct_reply.
		# JP: direct_reply に値を代入する。
		direct_reply = await _generate_direct_reply_async(llm, conversation_history)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if direct_reply:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			analysis_payload['reply'] = direct_reply
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			analysis_payload['should_reply'] = True

	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if analysis_payload.get('reply'):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		analysis_payload['should_reply'] = True

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return analysis_payload


# EN: Define function `_trim_conversation_history`.
# JP: 関数 `_trim_conversation_history` を定義する。
def _trim_conversation_history(
	conversation_history: list[dict[str, Any]],
	window_size: int | None = None,
) -> list[dict[str, Any]]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Keep the first user input and the most recent messages up to ``window_size``.

	The first user message anchors context, and the tail keeps the latest turns
	for the LLM. Duplicates are removed using message ids when present.
	"""
	# JP: 最初のユーザー発話をアンカーにし、最新の会話を優先
	# EN: Anchor on the first user message and keep the latest turns
	if window_size is None:
		# EN: Assign value to window_size.
		# JP: window_size に値を代入する。
		window_size = _CONVERSATION_CONTEXT_WINDOW
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not conversation_history or window_size <= 0:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return conversation_history

	# EN: Assign value to first_user_message.
	# JP: first_user_message に値を代入する。
	first_user_message = next((msg for msg in conversation_history if msg.get('role') == 'user'), None)
	# EN: Assign value to anchor.
	# JP: anchor に値を代入する。
	anchor = first_user_message or conversation_history[0]
	# EN: Assign value to tail.
	# JP: tail に値を代入する。
	tail = conversation_history[-window_size:]

	# EN: Define function `_normalize`.
	# JP: 関数 `_normalize` を定義する。
	def _normalize(value: Any) -> Any:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(value, (str, int, float, type(None))):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return value
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return repr(value)

	# EN: Define function `_key`.
	# JP: 関数 `_key` を定義する。
	def _key(msg: dict[str, Any]) -> tuple[str, Any, Any, Any]:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(msg, dict) and 'id' in msg:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ('id', msg.get('id'), None, None)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (
			'content',
			_normalize(msg.get('role')),
			_normalize(msg.get('content')),
			_normalize(msg.get('timestamp')),
		)

	# EN: Assign annotated value to seen.
	# JP: seen に型付きの値を代入する。
	seen: set[tuple[str, Any, Any, Any]] = set()
	# EN: Assign annotated value to selected.
	# JP: selected に型付きの値を代入する。
	selected: list[dict[str, Any]] = []
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for msg in [anchor, *tail]:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not isinstance(msg, dict):
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue
		# EN: Assign value to msg_key.
		# JP: msg_key に値を代入する。
		msg_key = _key(msg)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if msg_key in seen:
			# EN: Continue to the next loop iteration.
			# JP: ループの次の反復に進む。
			continue
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		seen.add(msg_key)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		selected.append(msg)

	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return selected


# EN: Define async function `_analyze_conversation_history_async`.
# JP: 非同期関数 `_analyze_conversation_history_async` を定義する。
async def _analyze_conversation_history_async(conversation_history: list[dict[str, Any]]) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Analyze conversation history using LLM to determine if browser operations are needed
	and whether the browser agent should proactively speak up.
	"""
	# JP: LLM を使ってブラウザ操作の必要性を解析
	# EN: Use LLM to analyze whether browser actions are required
	llm = None
	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Assign value to llm.
		# JP: llm に値を代入する。
		llm = _create_selected_llm()
	except AgentControllerError as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Failed to create LLM for conversation analysis: %s', exc)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _build_error_response(f'LLMの初期化に失敗しました: {exc}')

	# Format conversation history for analysis
	# JP: LLM に渡すための会話テキストを整形
	# EN: Format conversation history into a text block for the LLM
	conversation_history = _trim_conversation_history(conversation_history)
	# EN: Assign value to conversation_text.
	# JP: conversation_text に値を代入する。
	conversation_text = ''
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for msg in conversation_history:
		# EN: Assign value to role.
		# JP: role に値を代入する。
		role = msg.get('role', 'unknown')
		# EN: Assign value to content.
		# JP: content に値を代入する。
		content = msg.get('content', '')
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		conversation_text += f'{role}: {content}\n'

	# Create a prompt to analyze the conversation
	# JP: ブラウザ操作に特化した判定プロンプト
	# EN: Prompt specialized for browser-action decisioning
	analysis_prompt = f"""あなたは「ブラウザ操作に強い」アシスタントです。

【役割】
- Web検索: 情報検索、調査、ニュース確認
- Webページ操作: ナビゲーション、フォーム入力、データ抽出
- オンラインサービス: 予約、購入、申し込み手続き
- Webサイトの閲覧支援: 特定ページへのアクセス
- ブラウザ操作が不要な質問でも、可能な範囲で直接回答する

【対応方針】
- ブラウザ操作が不要で、一般知識や推論で答えられる質問は **必ず回答** する
- 最新情報や正確な確認が必要な質問は `needs_action: true` とする
- 物理的な操作（IoT等）は実行できないが、一般的な手順や注意点は説明できる

【判断ルール】
1. `needs_action: true` は、Webブラウザでの操作が「必須」な場合のみ
2. `should_reply: true` は、ユーザーの質問に回答できる場合は常に `true`
3. ブラウザ操作が不要な場合は `needs_action: false` のまま `reply` に回答を書く
4. 他エージェントへの呼びかけ・任せる判断は禁止

【出力言語】
- `reply` と `reason` は必ず日本語で書く

【発言する例】
- 「東京の天気を調べて」→ needs_action: true, action_type: "search"
- 「Amazonで商品を検索して」→ needs_action: true
- 「Pythonのリスト内包表記を教えて」→ needs_action: false, should_reply: true
- 「夕食のレシピを教えて」→ needs_action: false, should_reply: true

【発言できない操作の例（回答は可能）】
- 「エアコンをつけて」→ 操作はできないが、一般的な手順説明は可

会話履歴:
{conversation_text}

JSONのみで出力:
{{
  "should_reply": true/false,
  "reply": "ユーザーへの直接回答（簡潔だが質問に答える）",
  "addressed_agents": [],
  "needs_action": true/false,
  "action_type": "search" | "navigate" | "form_fill" | "data_extract" | null,
  "task_description": "ブラウザに依頼する具体的タスク",
  "reason": "判断の理由"
}}
"""

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# Use LLM to generate structured analysis
		# JP: 可能なら構造化出力（Pydantic）で取得
		# EN: Prefer structured output (Pydantic) when supported
		messages = [
			SystemMessage(content='You are an expert in analyzing conversations.'),
			UserMessage(role='user', content=analysis_prompt),
		]
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await llm.ainvoke(messages, output_format=ConversationAnalysis)

		# The response result should now be a Pydantic model instance
		# EN: Assign value to analysis_result.
		# JP: analysis_result に値を代入する。
		analysis_result = _get_completion_payload(response)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(analysis_result, ConversationAnalysis):
			# EN: Assign value to analysis_payload.
			# JP: analysis_payload に値を代入する。
			analysis_payload = analysis_result.model_dump()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(analysis_result, dict):
			# EN: Assign value to normalized.
			# JP: normalized に値を代入する。
			normalized = _normalize_analysis_payload(analysis_result)
			# EN: Assign value to analysis_payload.
			# JP: analysis_payload に値を代入する。
			analysis_payload = ConversationAnalysis.model_validate(normalized).model_dump()
		else:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise TypeError(f'Expected ConversationAnalysis, but got {type(analysis_result).__name__}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await _ensure_direct_reply_async(analysis_payload, llm, conversation_history)

	except ModelProviderError as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Structured output failed due to provider error, retrying without schema: %s', exc)
		# EN: Assign value to analysis_payload.
		# JP: analysis_payload に値を代入する。
		analysis_payload = await _fallback_to_text_parsing(llm, messages)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await _ensure_direct_reply_async(analysis_payload, llm, conversation_history)
	except (ValidationError, TypeError, AttributeError) as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.warning('Structured output failed, falling back to text parsing: %s', exc)
		# EN: Assign value to analysis_payload.
		# JP: analysis_payload に値を代入する。
		analysis_payload = await _fallback_to_text_parsing(llm, messages)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return await _ensure_direct_reply_async(analysis_payload, llm, conversation_history)
	except Exception as exc:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.exception('Unexpected error during conversation history analysis')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _build_error_response(f'予期しないエラーが発生しました: {exc}')
	finally:
		# JP: LLM クライアントを安全にクローズ
		# EN: Close the LLM client safely
		if llm:
			# EN: Assign value to aclose.
			# JP: aclose に値を代入する。
			aclose = getattr(llm, 'aclose', None)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if callable(aclose):
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await aclose()
				except RuntimeError as close_exc:
					# Suppress "Event loop is closed" errors from httpx/anyio during cleanup
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if 'Event loop is closed' not in str(close_exc):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						logger.debug('Failed to close LLM client during conversation analysis', exc_info=True)
				except Exception:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug('Failed to close LLM client during conversation analysis', exc_info=True)


# EN: Define function `_analyze_conversation_history`.
# JP: 関数 `_analyze_conversation_history` を定義する。
def _analyze_conversation_history(
	conversation_history: list[dict[str, Any]],
	loop: asyncio.AbstractEventLoop | None = None,
) -> dict[str, Any]:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Synchronous wrapper for async conversation history analysis.

	Note: Uses asyncio.run() to create a new event loop since this can be called
	from a synchronous request context. Falls back to manual loop creation if an
	event loop is already running (e.g., in tests).
	"""
	# JP: 同期コンテキスト向けにイベントループを調整
	# EN: Adapt async analysis for synchronous callers
	if loop and loop.is_running():
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to future.
			# JP: future に値を代入する。
			future = asyncio.run_coroutine_threadsafe(_analyze_conversation_history_async(conversation_history), loop)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return future.result()
		except RuntimeError:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug('Failed to run on provided loop, falling back to new loop.')

	# EN: Handle exceptions around this block.
	# JP: このブロックで例外処理を行う。
	try:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return asyncio.run(_analyze_conversation_history_async(conversation_history))
	except RuntimeError as exc:
		# Handle case where event loop is already running
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Event loop already running, creating new loop: %s', exc)
		# EN: Assign value to loop.
		# JP: loop に値を代入する。
		loop = asyncio.new_event_loop()
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return loop.run_until_complete(_analyze_conversation_history_async(conversation_history))
		finally:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			loop.close()

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from browser_use.llm.exceptions import ModelProviderError
from browser_use.llm.messages import SystemMessage, UserMessage

# JP: 会話履歴からブラウザ操作の要否を判定するレビュー機能
# EN: Conversation review that decides whether browser actions are needed
from ..core.config import logger
from ..core.env import _CONVERSATION_CONTEXT_WINDOW
from ..core.exceptions import AgentControllerError
from .llm_factory import _create_selected_llm


# EN: Define class `ConversationAnalysis`.
# JP: クラス `ConversationAnalysis` を定義する。
class ConversationAnalysis(BaseModel):
	"""Data model for the result of conversation analysis."""

	# JP: ブラウザ操作の要否と返答内容を含む構造化結果
	# EN: Structured output including action need and reply content
	should_reply: bool = Field(
		..., description='True if the assistant should provide a helpful reply even when no browser action is required.'
	)
	reply: str = Field(
		default='',
		description='A concise but complete answer for the user. Must be empty if should_reply is False.',
	)
	addressed_agents: list[str] = Field(
		default_factory=list,
		description='A list of agent names that are addressed in the conversation (e.g., "Browser Agent").',
	)
	needs_action: bool = Field(..., description='True if the conversation requires a browser action.')
	action_type: Literal['search', 'navigate', 'form_fill', 'data_extract'] | None = Field(
		None, description='The type of browser action required.'
	)
	task_description: str | None = Field(None, description='A specific and concrete task description for the browser agent.')
	reason: str = Field('', description='The reasoning behind the analysis and decision.')


# EN: Define function `_build_error_response`.
# JP: 関数 `_build_error_response` を定義する。
def _build_error_response(reason: str) -> dict[str, Any]:
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
	"""Fill missing or malformed fields with safe defaults before validation."""

	# JP: 欠落フィールドを補完し、異常値を安全側へ補正
	# EN: Fill missing fields and coerce invalid values to safe defaults
	if payload is None:
		return {}

	normalized: dict[str, Any] = dict(payload)
	normalized.setdefault('should_reply', False)
	normalized.setdefault('reply', '')
	normalized.setdefault('addressed_agents', [])
	normalized.setdefault('needs_action', False)
	normalized.setdefault('action_type', None)
	normalized.setdefault('task_description', None)

	if not normalized.get('reason'):
		normalized['reason'] = 'LLM output did not include a reason.'

	# JP: 想定外の action_type は無効値としてクリアする
	# EN: Guard action_type against unexpected values
	valid_action_types = {'search', 'navigate', 'form_fill', 'data_extract', None}
	if normalized.get('action_type') not in valid_action_types:
		normalized['action_type'] = None

	# JP: reply が入っている場合は should_reply を強制的に true に揃える
	# EN: If a reply is present, ensure should_reply is true
	if normalized.get('reply'):
		normalized['should_reply'] = True

	# JP: should_reply=false のときは reply を空文字へ正規化する
	# EN: Ensure reply is normalized when should_reply is false
	if not normalized.get('should_reply'):
		normalized['reply'] = normalized.get('reply', '') or ''

	return normalized


# EN: Define function `_sanitize_json_string`.
# JP: 関数 `_sanitize_json_string` を定義する。
def _sanitize_json_string(text: str) -> str:
	"""Sanitize a string for JSON parsing by fixing common LLM output issues."""
	# JP: LLM出力の改行/タブ等を簡易的にエスケープ補正
	# EN: Lightly sanitize common newline/tab issues in LLM JSON output
	# JP: 文字列値内の未エスケープ改行を簡易的に `\\n` へ置換する
	# EN: Replace likely unescaped newlines in JSON string literals with `\\n`
	try:
		result = re.sub(
			r'"((?:[^"\\]|\\.)*)(?:\n|\r|\t)((?:[^"\\]|\\.)*)"',
			lambda m: f'"{m.group(1)}\\n{m.group(2)}"',
			text,
		)
		return result
	except Exception:
		return text


# EN: Define function `_extract_json_from_text`.
# JP: 関数 `_extract_json_from_text` を定義する。
def _extract_json_from_text(text: str) -> dict | None:
	"""Extracts JSON from text, tolerating markdown code blocks and sanitizing."""
	# JP: ```json``` 形式と生の JSON の両方に対応
	# EN: Handle both ```json``` blocks and raw JSON blobs
	# JP: まず補正済みテキストも候補として評価する
	# EN: Include a sanitized variant as an additional parse candidate
	sanitized_text = _sanitize_json_string(text)

	candidates = [text]
	if sanitized_text != text:
		candidates.append(sanitized_text)

	for candidate in candidates:
		# JP: Markdown の ```json ... ``` ブロックを優先して抽出
		# EN: First try parsing a Markdown ```json ... ``` block
		json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', candidate)
		if json_match:
			try:
				return json.loads(json_match.group(1))
			except json.JSONDecodeError:
				pass  # Fallback to the next method

		# JP: 失敗時はテキスト全体から JSON らしい塊を抽出して再試行
		# EN: On failure, try any JSON-like object found in the text
		json_match = re.search(r'\{[\s\S]*\}', candidate)
		if json_match:
			try:
				return json.loads(json_match.group())
			except json.JSONDecodeError:
				continue

	return None


# EN: Define function `_get_completion_payload`.
# JP: 関数 `_get_completion_payload` を定義する。
def _get_completion_payload(response: Any) -> Any:
	"""Extract the completion payload from an LLM response.

	Supports both the current `.completion` attribute and the legacy `.result`
	field to stay compatible with older `browser-use` builds or third-party
	clients.
	"""
	# JP: 新旧インターフェース両対応のため複数属性を確認
	# EN: Support both new and legacy response shapes
	if hasattr(response, 'completion'):
		return response.completion
	if hasattr(response, 'result'):
		return response.result
	if isinstance(response, dict):
		return response.get('completion') or response.get('result')
	raise AttributeError('LLM response did not include a completion/result payload')


# EN: Define async function `_retry_with_json_correction`.
# JP: 非同期関数 `_retry_with_json_correction` を定義する。
async def _retry_with_json_correction(
	llm: Any, messages: list[Any], failed_output: str, error: Exception, max_retries: int = 2
) -> dict[str, Any] | None:
	"""Retry LLM call with JSON correction prompt after parse failure."""
	# JP: 失敗した JSON を短く抜粋し、修正指示を追加して再試行
	# EN: Retry with a correction prompt including a truncated bad output
	truncated_output = failed_output[:1500] + '...' if len(failed_output) > 1500 else failed_output

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

	retry_messages = messages + [correction_message]

	for attempt in range(max_retries):
		# JP: 最大回数までリトライし、成功したら即返す
		# EN: Retry up to max_retries and return immediately on success
		try:
			response = await llm.ainvoke(retry_messages)
			response_text = _get_completion_payload(response)

			if isinstance(response_text, str):
				extracted_json = _extract_json_from_text(response_text)
				if extracted_json:
					normalized = _normalize_analysis_payload(extracted_json)
					return ConversationAnalysis.model_validate(normalized).model_dump()
			elif isinstance(response_text, dict):
				normalized = _normalize_analysis_payload(response_text)
				return ConversationAnalysis.model_validate(normalized).model_dump()

		except Exception as retry_error:
			logger.debug(f'JSON correction retry {attempt + 1}/{max_retries} failed: {retry_error}')
			if attempt == max_retries - 1:
				return None
			continue

	return None


# EN: Define async function `_fallback_to_text_parsing`.
# JP: 非同期関数 `_fallback_to_text_parsing` を定義する。
async def _fallback_to_text_parsing(llm: Any, messages: list[Any]) -> dict[str, Any]:
	"""Fallback path when structured output is unavailable."""
	# JP: Structured output が使えない場合に JSON 抽出で対応
	# EN: Fallback to JSON extraction when structured output fails
	try:
		response = await llm.ainvoke(messages)
		response_text = _get_completion_payload(response)
		extracted_json = None
		if isinstance(response_text, str):
			extracted_json = _extract_json_from_text(response_text)
		elif isinstance(response_text, dict):
			extracted_json = response_text

		if extracted_json:
			normalized = _normalize_analysis_payload(extracted_json)
			analysis_result = ConversationAnalysis.model_validate(normalized)
			return analysis_result.model_dump()

		# JP: 抽出失敗時は補正用プロンプトを追加して再試行する
		# EN: If extraction fails, retry once with a JSON-correction prompt
		if isinstance(response_text, str):
			retry_result = await _retry_with_json_correction(llm, messages, response_text, ValueError('JSON extraction failed'))
			if retry_result:
				return retry_result

		raise ValueError('Fallback parsing failed to produce a valid model.')

	except ModelProviderError as fallback_exc:
		logger.warning('Provider error during conversation history analysis fallback: %s', fallback_exc)
		return _build_error_response(f'会話履歴の分析用LLM呼び出しに失敗しました: {fallback_exc}')
	except (ValidationError, ValueError) as fallback_exc:
		logger.warning('Error during conversation history analysis fallback: %s', fallback_exc)
		return _build_error_response(f'会話履歴の分析中にエラーが発生しました: {fallback_exc}')


# EN: Define function `_looks_like_refusal`.
# JP: 関数 `_looks_like_refusal` を定義する。
def _looks_like_refusal(text: str) -> bool:
	# JP: 「拒否」に見える文言を簡易的に検出
	# EN: Heuristically detect refusal-like replies
	if not text:
		return True
	lowered = text.lower()
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
	return any(phrase in lowered for phrase in refusal_phrases)


# EN: Define function `_stringify_reply`.
# JP: 関数 `_stringify_reply` を定義する。
def _stringify_reply(payload: Any) -> str:
	# JP: 返答候補を文字列に正規化
	# EN: Normalize reply payload into a string
	if isinstance(payload, str):
		return payload.strip()
	if isinstance(payload, dict):
		for key in ('reply', 'content', 'text', 'message'):
			value = payload.get(key)
			if isinstance(value, str) and value.strip():
				return value.strip()
		try:
			return json.dumps(payload, ensure_ascii=False)
		except TypeError:
			return str(payload)
	return str(payload).strip()


# EN: Define async function `_generate_direct_reply_async`.
# JP: 非同期関数 `_generate_direct_reply_async` を定義する。
async def _generate_direct_reply_async(llm: Any, conversation_history: list[dict[str, Any]]) -> str:
	"""Generate a direct answer when no browser action is required."""
	# JP: ブラウザ不要時に直接回答を生成
	# EN: Generate a direct reply when no browser action is needed
	if not conversation_history:
		return ''

	conversation_history = _trim_conversation_history(conversation_history)
	conversation_text = ''
	for msg in conversation_history:
		role = msg.get('role', 'unknown')
		content = msg.get('content', '')
		conversation_text += f'{role}: {content}\n'

	prompt = f"""以下は会話履歴です。最新のユーザーの質問に日本語で答えてください。

条件:
- ブラウザ操作やエージェントの都合には触れない
- 可能な範囲で直接回答する（不足があれば合理的な前提を短く述べる）
- 不要な質問はしない
- 簡潔だが質問には十分に答える

会話履歴:
{conversation_text}
"""

	messages = [
		SystemMessage(content='You are a helpful assistant who answers user questions directly in Japanese.'),
		UserMessage(role='user', content=prompt),
	]
	response = await llm.ainvoke(messages)
	reply_text = _stringify_reply(_get_completion_payload(response))
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
		return analysis_payload

	reply_text = (analysis_payload.get('reply') or '').strip()
	if not reply_text or _looks_like_refusal(reply_text) or not analysis_payload.get('should_reply'):
		direct_reply = await _generate_direct_reply_async(llm, conversation_history)
		if direct_reply:
			analysis_payload['reply'] = direct_reply
			analysis_payload['should_reply'] = True

	if analysis_payload.get('reply'):
		analysis_payload['should_reply'] = True

	return analysis_payload


# EN: Define function `_trim_conversation_history`.
# JP: 関数 `_trim_conversation_history` を定義する。
def _trim_conversation_history(
	conversation_history: list[dict[str, Any]],
	window_size: int | None = None,
) -> list[dict[str, Any]]:
	"""Keep the first user input and the most recent messages up to ``window_size``.

	The first user message anchors context, and the tail keeps the latest turns
	for the LLM. Duplicates are removed using message ids when present.
	"""
	# JP: 最初のユーザー発話をアンカーにし、最新の会話を優先
	# EN: Anchor on the first user message and keep the latest turns
	if window_size is None:
		window_size = _CONVERSATION_CONTEXT_WINDOW
	if not conversation_history or window_size <= 0:
		return conversation_history

	first_user_message = next((msg for msg in conversation_history if msg.get('role') == 'user'), None)
	anchor = first_user_message or conversation_history[0]
	tail = conversation_history[-window_size:]

	# EN: Define function `_normalize`.
	# JP: 関数 `_normalize` を定義する。
	def _normalize(value: Any) -> Any:
		if isinstance(value, (str, int, float, type(None))):
			return value
		return repr(value)

	# EN: Define function `_key`.
	# JP: 関数 `_key` を定義する。
	def _key(msg: dict[str, Any]) -> tuple[str, Any, Any, Any]:
		if isinstance(msg, dict) and 'id' in msg:
			return ('id', msg.get('id'), None, None)
		return (
			'content',
			_normalize(msg.get('role')),
			_normalize(msg.get('content')),
			_normalize(msg.get('timestamp')),
		)

	seen: set[tuple[str, Any, Any, Any]] = set()
	selected: list[dict[str, Any]] = []
	for msg in [anchor, *tail]:
		if not isinstance(msg, dict):
			continue
		msg_key = _key(msg)
		if msg_key in seen:
			continue
		seen.add(msg_key)
		selected.append(msg)

	return selected


# EN: Define async function `_analyze_conversation_history_async`.
# JP: 非同期関数 `_analyze_conversation_history_async` を定義する。
async def _analyze_conversation_history_async(conversation_history: list[dict[str, Any]]) -> dict[str, Any]:
	"""
	Analyze conversation history using LLM to determine if browser operations are needed
	and whether the browser agent should proactively speak up.
	"""
	# JP: LLM を使ってブラウザ操作の必要性を解析
	# EN: Use LLM to analyze whether browser actions are required
	llm = None
	try:
		llm = _create_selected_llm()
	except AgentControllerError as exc:
		logger.warning('Failed to create LLM for conversation analysis: %s', exc)
		return _build_error_response(f'LLMの初期化に失敗しました: {exc}')

	# Format conversation history for analysis
	# JP: LLM に渡すための会話テキストを整形
	# EN: Format conversation history into a text block for the LLM
	conversation_history = _trim_conversation_history(conversation_history)
	conversation_text = ''
	for msg in conversation_history:
		role = msg.get('role', 'unknown')
		content = msg.get('content', '')
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

	try:
		# Use LLM to generate structured analysis
		# JP: 可能なら構造化出力（Pydantic）で取得
		# EN: Prefer structured output (Pydantic) when supported
		messages = [
			SystemMessage(content='You are an expert in analyzing conversations.'),
			UserMessage(role='user', content=analysis_prompt),
		]
		response = await llm.ainvoke(messages, output_format=ConversationAnalysis)

		# JP: 新旧レスポンス形式を吸収して ConversationAnalysis へ正規化する
		# EN: Normalize response payload into ConversationAnalysis across response shapes
		analysis_result = _get_completion_payload(response)

		if isinstance(analysis_result, ConversationAnalysis):
			analysis_payload = analysis_result.model_dump()
		elif isinstance(analysis_result, dict):
			normalized = _normalize_analysis_payload(analysis_result)
			analysis_payload = ConversationAnalysis.model_validate(normalized).model_dump()
		else:
			raise TypeError(f'Expected ConversationAnalysis, but got {type(analysis_result).__name__}')

		return await _ensure_direct_reply_async(analysis_payload, llm, conversation_history)

	except ModelProviderError as exc:
		logger.warning('Structured output failed due to provider error, retrying without schema: %s', exc)
		analysis_payload = await _fallback_to_text_parsing(llm, messages)
		return await _ensure_direct_reply_async(analysis_payload, llm, conversation_history)
	except (ValidationError, TypeError, AttributeError) as exc:
		logger.warning('Structured output failed, falling back to text parsing: %s', exc)
		analysis_payload = await _fallback_to_text_parsing(llm, messages)
		return await _ensure_direct_reply_async(analysis_payload, llm, conversation_history)
	except Exception as exc:
		logger.exception('Unexpected error during conversation history analysis')
		return _build_error_response(f'予期しないエラーが発生しました: {exc}')
	finally:
		# JP: LLM クライアントを安全にクローズ
		# EN: Close the LLM client safely
		if llm:
			aclose = getattr(llm, 'aclose', None)
			if callable(aclose):
				try:
					await aclose()
				except RuntimeError as close_exc:
					# Suppress "Event loop is closed" errors from httpx/anyio during cleanup
					if 'Event loop is closed' not in str(close_exc):
						logger.debug('Failed to close LLM client during conversation analysis', exc_info=True)
				except Exception:
					logger.debug('Failed to close LLM client during conversation analysis', exc_info=True)


# EN: Define function `_analyze_conversation_history`.
# JP: 関数 `_analyze_conversation_history` を定義する。
def _analyze_conversation_history(
	conversation_history: list[dict[str, Any]],
	loop: asyncio.AbstractEventLoop | None = None,
) -> dict[str, Any]:
	"""
	Synchronous wrapper for async conversation history analysis.

	Note: Uses asyncio.run() to create a new event loop since this can be called
	from a synchronous request context. Falls back to manual loop creation if an
	event loop is already running (e.g., in tests).
	"""
	# JP: 同期コンテキスト向けにイベントループを調整
	# EN: Adapt async analysis for synchronous callers
	if loop and loop.is_running():
		try:
			future = asyncio.run_coroutine_threadsafe(_analyze_conversation_history_async(conversation_history), loop)
			return future.result()
		except RuntimeError:
			logger.debug('Failed to run on provided loop, falling back to new loop.')

	try:
		return asyncio.run(_analyze_conversation_history_async(conversation_history))
	except RuntimeError as exc:
		# JP: 既存ループが占有されている場合は新規ループで実行する
		# EN: If a loop is already running, execute on a dedicated new loop
		logger.debug('Event loop already running, creating new loop: %s', exc)
		loop = asyncio.new_event_loop()
		try:
			return loop.run_until_complete(_analyze_conversation_history_async(conversation_history))
		finally:
			loop.close()

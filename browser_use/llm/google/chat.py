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
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass, field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, Literal, TypeVar, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, ValidationError

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.exceptions import ModelProviderError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import AssistantMessage, BaseMessage, SystemMessage, UserMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)

# EN: Assign value to VerifiedGeminiModels.
# JP: VerifiedGeminiModels に値を代入する。
VerifiedGeminiModels = Literal[
	'gemini-2.5-flash-lite',
	'gemini-3-pro-preview',
]


# EN: Define class `ChatGoogle`.
# JP: クラス `ChatGoogle` を定義する。
@dataclass
class ChatGoogle(BaseChatModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Google Gemini chat wrapper."""

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: VerifiedGeminiModels | str
	# EN: Assign annotated value to temperature.
	# JP: temperature に型付きの値を代入する。
	temperature: float | None = 0.2
	# EN: Assign annotated value to top_p.
	# JP: top_p に型付きの値を代入する。
	top_p: float | None = None
	# EN: Assign annotated value to max_output_tokens.
	# JP: max_output_tokens に型付きの値を代入する。
	max_output_tokens: int | None = 4096
	# EN: Assign annotated value to api_key.
	# JP: api_key に型付きの値を代入する。
	api_key: str | None = None
	# EN: Assign annotated value to base_url.
	# JP: base_url に型付きの値を代入する。
	base_url: str = 'https://generativelanguage.googleapis.com/v1beta'
	# EN: Assign annotated value to timeout.
	# JP: timeout に型付きの値を代入する。
	timeout: float | httpx.Timeout | None = None
	# EN: Assign annotated value to max_retries.
	# JP: max_retries に型付きの値を代入する。
	max_retries: int = 5
	# EN: Assign annotated value to http_client.
	# JP: http_client に型付きの値を代入する。
	http_client: httpx.AsyncClient | None = None

	# EN: Assign annotated value to _async_client.
	# JP: _async_client に型付きの値を代入する。
	_async_client: httpx.AsyncClient = field(init=False, repr=False)

	# EN: Define function `__post_init__`.
	# JP: 関数 `__post_init__` を定義する。
	def __post_init__(self) -> None:
		# EN: Assign value to google_api_key.
		# JP: google_api_key に値を代入する。
		google_api_key = self.api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not google_api_key:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(
				message='Google API key not provided',
				status_code=401,
				model=str(self.model),
			)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.api_key = google_api_key
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._async_client = self.http_client or httpx.AsyncClient(timeout=self.timeout)

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'google'

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(self.model)

	# EN: Define function `_prepare_messages`.
	# JP: 関数 `_prepare_messages` を定義する。
	def _prepare_messages(self, messages: list[BaseMessage]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
		# EN: Assign value to gemini_messages.
		# JP: gemini_messages に値を代入する。
		gemini_messages = []
		# EN: Assign value to system_instruction.
		# JP: system_instruction に値を代入する。
		system_instruction = None

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for msg in messages:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(msg, SystemMessage):
				# Gemini API handles system instructions separately
				# Usually there is only one system message, but if multiple, we concatenate?
				# The snippet shows {"systemInstruction": {"parts": [...]}}
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if system_instruction is None:
					# EN: Assign value to system_instruction.
					# JP: system_instruction に値を代入する。
					system_instruction = {'role': 'system', 'parts': [{'text': msg.content}]}
				else:
					# Append to existing parts
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					system_instruction['parts'].append({'text': msg.content})
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(msg, UserMessage):
				# EN: Assign value to role.
				# JP: role に値を代入する。
				role = 'user'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(msg, AssistantMessage):
				# EN: Assign value to role.
				# JP: role に値を代入する。
				role = 'model'
			else:
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = []
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(msg.content, str):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content.append({'text': msg.content})
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(msg.content, list):
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for item in msg.content:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if isinstance(item, str):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						content.append({'text': item})
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif isinstance(item, dict):
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if item.get('type') == 'text':
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							content.append({'text': item.get('text', '')})
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif item.get('type') == 'image_url':
							# Assuming image_url is a dict with 'url' key
							# and url is a base64 encoded image
							# EN: Assign value to image_data.
							# JP: image_data に値を代入する。
							image_data = item.get('image_url', {}).get('url', '')
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if 'base64,' in image_data:
								# EN: Assign value to mime_type.
								# JP: mime_type に値を代入する。
								mime_type = image_data.split(';')[0].split(':')[1]
								# EN: Assign value to data.
								# JP: data に値を代入する。
								data = image_data.split('base64,')[1]
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								content.append({'inline_data': {'mime_type': mime_type, 'data': data}})

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			gemini_messages.append({'role': role, 'parts': content})

		# If we have a system_instruction, it should be returned separately
		# Note: The API expects system_instruction to be a dict like {role: "system", parts: [...]} not inside contents
		# Wait, the official REST API doc says: "systemInstruction": { "parts": [...] } (role is optional or ignored? Snippet said "role": "string" in request body param list but "system" is not a standard role in contents).
		# Let's trust the snippet: "systemInstruction": { "role": string, "parts": [...] }

		# If system_instruction role is needed, 'system' seems appropriate or 'user' if forcing it?
		# Docs usually imply it's separate. We'll leave 'role': 'system' inside the object if we constructed it that way,
		# but strictly speaking it might just need 'parts'.
		# However, `systemInstruction` is a top-level field.

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return gemini_messages, system_instruction

	# EN: Define async function `_send_request`.
	# JP: 非同期関数 `_send_request` を定義する。
	async def _send_request(
		self,
		gemini_messages: list[dict[str, Any]],
		generation_config: dict[str, Any],
		system_instruction: dict[str, Any] | None = None,
	) -> httpx.Response:
		# EN: Assign value to url.
		# JP: url に値を代入する。
		url = f'{self.base_url}/models/{self.model}:generateContent'
		# EN: Assign value to headers.
		# JP: headers に値を代入する。
		headers = {
			'Content-Type': 'application/json',
		}
		# EN: Assign value to json_payload.
		# JP: json_payload に値を代入する。
		json_payload = {
			'contents': gemini_messages,
			'generationConfig': generation_config,
		}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if system_instruction:
			# Ensure role is not user/model if strictly systemInstruction?
			# Actually, the snippet showed: "systemInstruction": { "role": string, ... }
			# We'll include it as is.
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			json_payload['systemInstruction'] = system_instruction

		# EN: Assign value to params.
		# JP: params に値を代入する。
		params = {'key': self.api_key}

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for attempt in range(self.max_retries):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self._async_client.post(url, headers=headers, json=json_payload, params=params)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				response.raise_for_status()
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return response
			except httpx.HTTPStatusError as e:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if e.response.status_code >= 500 and attempt < self.max_retries - 1:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(
					message=e.response.text,
					status_code=e.response.status_code,
					model=self.name,
				) from e

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ModelProviderError(f'Failed to get response after {self.max_retries} retries', model=self.name)

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	async def ainvoke(self, messages: list[BaseMessage], output_format: None = None) -> ChatInvokeCompletion[str]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	async def ainvoke(self, messages: list[BaseMessage], output_format: type[T]) -> ChatInvokeCompletion[T]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		gemini_messages, system_instruction = self._prepare_messages(messages)

		# EN: Assign value to generation_config.
		# JP: generation_config に値を代入する。
		generation_config = {
			'temperature': self.temperature,
			'topP': self.top_p,
			'maxOutputTokens': self.max_output_tokens,
		}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if output_format:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			generation_config['response_mime_type'] = 'application/json'

		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await self._send_request(gemini_messages, generation_config, system_instruction)

		# EN: Assign value to response_data.
		# JP: response_data に値を代入する。
		response_data = response.json()

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to content_text.
			# JP: content_text に値を代入する。
			content_text = response_data['candidates'][0]['content']['parts'][0]['text']
		except (KeyError, IndexError):
			# Better error handling for blocked content
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if response_data.get('promptFeedback', {}).get('blockReason'):
				# EN: Assign value to block_reason.
				# JP: block_reason に値を代入する。
				block_reason = response_data['promptFeedback']['blockReason']
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(f'Response blocked: {block_reason}', model=self.name)

			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError('Invalid response structure from Gemini API', model=self.name)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if output_format:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to parsed_content.
				# JP: parsed_content に値を代入する。
				parsed_content = self._parse_json_output(content_text, output_format)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(completion=parsed_content, usage=None)
			except (json.JSONDecodeError, ValueError, ValidationError) as e:
				# JSON parse error - attempt retry with corrective prompt
				# EN: Assign value to retry_result.
				# JP: retry_result に値を代入する。
				retry_result = await self._retry_json_parse(
					gemini_messages, generation_config, system_instruction, content_text, output_format, e
				)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if retry_result is not None:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ChatInvokeCompletion(completion=retry_result, usage=None)
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(f'Failed to parse model output as JSON: {e}', model=self.name) from e
		else:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return ChatInvokeCompletion(completion=content_text, usage=None)

	# EN: Define async function `_retry_json_parse`.
	# JP: 非同期関数 `_retry_json_parse` を定義する。
	async def _retry_json_parse(
		self,
		original_messages: list[dict[str, Any]],
		generation_config: dict[str, Any],
		system_instruction: dict[str, Any] | None,
		failed_output: str,
		output_format: type[T],
		original_error: Exception,
		max_retries: int = 2,
	) -> T | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Retry JSON parsing with corrective prompts when initial parse fails."""
		# Truncate long outputs for the correction prompt
		# EN: Assign value to truncated_output.
		# JP: truncated_output に値を代入する。
		truncated_output = failed_output[:2000] + '...' if len(failed_output) > 2000 else failed_output

		# EN: Assign value to correction_prompt.
		# JP: correction_prompt に値を代入する。
		correction_prompt = f"""あなたの前回の出力はJSONとして不正でした。以下のエラーが発生しました:
{str(original_error)[:500]}

前回の出力（一部）:
{truncated_output}

以下の点に注意して、正しいJSONを再出力してください：
1. 文字列内の改行は \\n でエスケープする
2. 文字列内のダブルクォートは \\" でエスケープする
3. 制御文字（タブ等）は適切にエスケープする
4. JSONの構文（カンマ、括弧の対応）を確認する

正しいJSON形式のみを出力してください。説明や追加のテキストは不要です。"""

		# EN: Assign value to retry_messages.
		# JP: retry_messages に値を代入する。
		retry_messages = original_messages + [{'role': 'user', 'parts': [{'text': correction_prompt}]}]

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for attempt in range(max_retries):
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to response.
				# JP: response に値を代入する。
				response = await self._send_request(retry_messages, generation_config, system_instruction)
				# EN: Assign value to response_data.
				# JP: response_data に値を代入する。
				response_data = response.json()
				# EN: Assign value to content_text.
				# JP: content_text に値を代入する。
				content_text = response_data['candidates'][0]['content']['parts'][0]['text']
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return self._parse_json_output(content_text, output_format)
			except (json.JSONDecodeError, ValueError, KeyError, IndexError):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if attempt == max_retries - 1:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue
			except Exception:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return None

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define async function `aclose`.
	# JP: 非同期関数 `aclose` を定義する。
	async def aclose(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Close the underlying HTTP client."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(self, '_async_client') and not self._async_client.is_closed:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await self._async_client.aclose()
			except RuntimeError as e:
				# Ignore "Event loop is closed" error during cleanup
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'Event loop is closed' not in str(e):
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise

	# EN: Define function `_parse_json_output`.
	# JP: 関数 `_parse_json_output` を定義する。
	def _parse_json_output(self, text: str, output_format: type[T]) -> T:
		# EN: Assign value to raw_text.
		# JP: raw_text に値を代入する。
		raw_text = text.strip()

		# EN: Define function `_sanitize_json_string`.
		# JP: 関数 `_sanitize_json_string` を定義する。
		def _sanitize_json_string(s: str) -> str:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Sanitize JSON string by escaping problematic characters."""
			# Fix common JSON issues in LLM output
			# 1. Replace unescaped newlines within string values
			# 2. Replace unescaped tabs
			# 3. Fix unescaped quotes in string values

			# First, try to fix control characters within JSON string values
			# This regex finds string values and escapes control chars within them
			# EN: Define function `escape_control_chars`.
			# JP: 関数 `escape_control_chars` を定義する。
			def escape_control_chars(match: re.Match) -> str:
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = match.group(1)
				# Escape unescaped control characters
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = content.replace('\n', '\\n')
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = content.replace('\r', '\\r')
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = content.replace('\t', '\\t')
				# Handle unescaped backslashes that aren't part of escape sequences
				# Be careful not to double-escape already escaped sequences
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return f'"{content}"'

			# Try to fix strings with unescaped control characters
			# Match JSON strings (simplified pattern)
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# Pattern to find string values in JSON
				# EN: Assign value to result.
				# JP: result に値を代入する。
				result = re.sub(
					r'"((?:[^"\\]|\\.)*)(?:\n|\r|\t)((?:[^"\\]|\\.)*)"',
					lambda m: f'"{m.group(1)}\\n{m.group(2)}"',
					s,
				)
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return result
			except Exception:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return s

		# EN: Define function `_extract_json_candidate`.
		# JP: 関数 `_extract_json_candidate` を定義する。
		def _extract_json_candidate(blob: str) -> str | None:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Pull a JSON object out of a mixed Gemini response."""
			# Prefer fenced code blocks if present
			# EN: Assign value to fence_match.
			# JP: fence_match に値を代入する。
			fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', blob)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if fence_match:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return fence_match.group(1).strip()

			# Otherwise grab the first JSON-looking object
			# EN: Assign value to brace_match.
			# JP: brace_match に値を代入する。
			brace_match = re.search(r'\{[\s\S]*\}', blob)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if brace_match:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return brace_match.group(0).strip()

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Build list of candidates to try
		# EN: Assign annotated value to candidates.
		# JP: candidates に型付きの値を代入する。
		candidates: list[str] = [raw_text]
		# EN: Assign value to extracted.
		# JP: extracted に値を代入する。
		extracted = _extract_json_candidate(raw_text)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if extracted and extracted not in candidates:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			candidates.append(extracted)

		# Also try sanitized versions
		# EN: Assign value to sanitized_raw.
		# JP: sanitized_raw に値を代入する。
		sanitized_raw = _sanitize_json_string(raw_text)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if sanitized_raw != raw_text and sanitized_raw not in candidates:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			candidates.append(sanitized_raw)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if extracted:
			# EN: Assign value to sanitized_extracted.
			# JP: sanitized_extracted に値を代入する。
			sanitized_extracted = _sanitize_json_string(extracted)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if sanitized_extracted != extracted and sanitized_extracted not in candidates:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				candidates.append(sanitized_extracted)

		# EN: Assign annotated value to last_error.
		# JP: last_error に型付きの値を代入する。
		last_error: Exception | None = None
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for candidate in candidates:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# If the candidate is JSON and missing required keys (e.g., LLM returned {"error": {...}}),
				# coerce it into a minimal AgentOutput shape with a safe done action so the agent can continue.
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to obj.
					# JP: obj に値を代入する。
					obj = json.loads(candidate)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if isinstance(obj, dict) and 'action' not in obj:
						# EN: Assign value to error_msg.
						# JP: error_msg に値を代入する。
						error_msg = None
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if 'error' in obj:
							# EN: Assign value to err_val.
							# JP: err_val に値を代入する。
							err_val = obj['error']
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if isinstance(err_val, dict):
								# EN: Assign value to error_msg.
								# JP: error_msg に値を代入する。
								error_msg = err_val.get('message') or err_val.get('detail') or str(err_val)
							else:
								# EN: Assign value to error_msg.
								# JP: error_msg に値を代入する。
								error_msg = str(err_val)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif 'message' in obj:
							# EN: Assign value to error_msg.
							# JP: error_msg に値を代入する。
							error_msg = str(obj.get('message'))

						# EN: Assign value to coerced.
						# JP: coerced に値を代入する。
						coerced = {
							'evaluation_previous_goal': obj.get('evaluation_previous_goal') or '',
							'memory': obj.get('memory') or '',
							'next_goal': obj.get('next_goal') or '',
							'current_status': obj.get('current_status') or '',
							'action': [
								{
									'done': {
										'text': error_msg or 'LLM returned an error payload; converted to done action',
										'success': False,
										'files_to_display': [],
									}
								}
							],
						}
						# EN: Assign value to candidate.
						# JP: candidate に値を代入する。
						candidate = json.dumps(coerced)
				except Exception:
					# EN: Keep a placeholder statement.
					# JP: プレースホルダー文を維持する。
					pass

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return output_format.model_validate_json(candidate)
			except (ValueError, json.JSONDecodeError, ValidationError) as e:
				# EN: Assign value to last_error.
				# JP: last_error に値を代入する。
				last_error = e
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return output_format.model_validate(json.loads(candidate))
				except Exception as e2:
					# EN: Assign value to last_error.
					# JP: last_error に値を代入する。
					last_error = e2
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError(f'Failed to decode JSON from model output: {text[:500]}... Error: {last_error}')

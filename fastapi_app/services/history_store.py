# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# JP: SSE 向けの履歴メッセージストア
# EN: In-memory history store for SSE updates
import queue
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import threading
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from contextlib import suppress
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from itertools import count
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Assign value to _message_sequence.
# JP: _message_sequence に値を代入する。
_message_sequence = count()


# EN: Define function `_utc_timestamp`.
# JP: 関数 `_utc_timestamp` を定義する。
def _utc_timestamp() -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Return a simple ISO 8601 timestamp in UTC."""

	# JP: クライアント表示に使う簡易UTCタイムスタンプ
	# EN: Simple UTC timestamp for client display
	return datetime.utcnow().isoformat(timespec='seconds') + 'Z'


# EN: Define function `_make_message`.
# JP: 関数 `_make_message` を定義する。
def _make_message(role: str, content: str) -> dict[str, str | int]:
	# JP: 一貫したメッセージ形式を生成
	# EN: Create a message in the consistent shape
	return {
		'id': next(_message_sequence),
		'role': role,
		'content': content,
		'timestamp': _utc_timestamp(),
	}


# EN: Define function `_initial_history`.
# JP: 関数 `_initial_history` を定義する。
def _initial_history() -> list[dict[str, str | int]]:
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return []


# EN: Define class `MessageBroadcaster`.
# JP: クラス `MessageBroadcaster` を定義する。
class MessageBroadcaster:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Simple pub/sub helper for Server-Sent Events."""

	# JP: SSE リスナー管理とブロードキャストを担う
	# EN: Manages SSE listeners and broadcasts events
	def __init__(self) -> None:
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._listeners: list[queue.SimpleQueue[dict[str, Any]]] = []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._lock = threading.Lock()

	# EN: Define function `subscribe`.
	# JP: 関数 `subscribe` を定義する。
	def subscribe(self) -> queue.SimpleQueue[dict[str, Any]]:
		# JP: リスナーを登録し専用キューを返す
		# EN: Register a listener and return its queue
		listener: queue.SimpleQueue[dict[str, Any]] = queue.SimpleQueue()
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with self._lock:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._listeners.append(listener)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return listener

	# EN: Define function `unsubscribe`.
	# JP: 関数 `unsubscribe` を定義する。
	def unsubscribe(self, listener: queue.SimpleQueue[dict[str, Any]]) -> None:
		# JP: リスナー解除（存在しない場合は無視）
		# EN: Remove listener (ignore if missing)
		with self._lock:
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with suppress(ValueError):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self._listeners.remove(listener)

	# EN: Define function `publish`.
	# JP: 関数 `publish` を定義する。
	def publish(self, event: dict[str, Any]) -> None:
		# JP: 登録済みリスナーへイベントを一斉送信
		# EN: Fan out events to all listeners
		with self._lock:
			# EN: Assign value to listeners.
			# JP: listeners に値を代入する。
			listeners = list(self._listeners)
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for listener in listeners:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			listener.put(event)

	# EN: Define function `publish_message`.
	# JP: 関数 `publish_message` を定義する。
	def publish_message(self, message: dict[str, Any]) -> None:
		# JP: 新規メッセージ通知
		# EN: Publish a new message event
		self.publish({'type': 'message', 'payload': message})

	# EN: Define function `publish_update`.
	# JP: 関数 `publish_update` を定義する。
	def publish_update(self, message: dict[str, Any]) -> None:
		# JP: 既存メッセージの更新通知
		# EN: Publish an update event for a message
		self.publish({'type': 'update', 'payload': message})

	# EN: Define function `publish_reset`.
	# JP: 関数 `publish_reset` を定義する。
	def publish_reset(self) -> None:
		# JP: 履歴リセット通知
		# EN: Publish a reset event
		self.publish({'type': 'reset'})


# EN: Assign value to _history_lock.
# JP: _history_lock に値を代入する。
_history_lock = threading.Lock()
# EN: Assign annotated value to _history.
# JP: _history に型付きの値を代入する。
_history: list[dict[str, str | int]] = _initial_history()
# EN: Assign value to _broadcaster.
# JP: _broadcaster に値を代入する。
_broadcaster = MessageBroadcaster()


# EN: Define function `_copy_history`.
# JP: 関数 `_copy_history` を定義する。
def _copy_history() -> list[dict[str, str | int]]:
	# JP: 外部公開用にコピーを返す
	# EN: Return a copy for external consumers
	with _history_lock:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [dict(message) for message in _history]


# EN: Define function `_append_history_message`.
# JP: 関数 `_append_history_message` を定義する。
def _append_history_message(role: str, content: str) -> dict[str, str | int]:
	# JP: 履歴へ追加し SSE で配信
	# EN: Append to history and broadcast via SSE
	message = _make_message(role, content)
	# EN: Execute logic with managed resources.
	# JP: リソース管理付きで処理を実行する。
	with _history_lock:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_history.append(message)
		# EN: Assign value to stored.
		# JP: stored に値を代入する。
		stored = dict(message)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	_broadcaster.publish_message(stored)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return stored


# EN: Define function `_update_history_message`.
# JP: 関数 `_update_history_message` を定義する。
def _update_history_message(message_id: int, new_content: str) -> dict[str, str | int] | None:
	# JP: 既存メッセージを更新して通知
	# EN: Update an existing message and broadcast
	with _history_lock:
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for entry in _history:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry['id'] == message_id:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				entry['content'] = new_content
				# EN: Assign value to updated.
				# JP: updated に値を代入する。
				updated = dict(entry)
				# EN: Exit the current loop.
				# JP: 現在のループを終了する。
				break
		else:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	_broadcaster.publish_update(updated)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return updated


# EN: Define function `_reset_history`.
# JP: 関数 `_reset_history` を定義する。
def _reset_history() -> list[dict[str, str | int]]:
	# JP: 履歴を初期状態に戻す
	# EN: Reset history to the initial state
	global _history, _message_sequence
	# EN: Execute logic with managed resources.
	# JP: リソース管理付きで処理を実行する。
	with _history_lock:
		# EN: Assign value to _message_sequence.
		# JP: _message_sequence に値を代入する。
		_message_sequence = count()
		# EN: Assign value to _history.
		# JP: _history に値を代入する。
		_history = _initial_history()
		# EN: Assign value to snapshot.
		# JP: snapshot に値を代入する。
		snapshot = [dict(message) for message in _history]
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	_broadcaster.publish_reset()
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return snapshot

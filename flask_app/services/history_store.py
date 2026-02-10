from __future__ import annotations

# JP: SSE 向けの履歴メッセージストア
# EN: In-memory history store for SSE updates
import queue
import threading
from contextlib import suppress
from datetime import datetime
from itertools import count
from typing import Any

_message_sequence = count()


def _utc_timestamp() -> str:
	"""Return a simple ISO 8601 timestamp in UTC."""

	# JP: クライアント表示に使う簡易UTCタイムスタンプ
	# EN: Simple UTC timestamp for client display
	return datetime.utcnow().isoformat(timespec='seconds') + 'Z'


def _make_message(role: str, content: str) -> dict[str, str | int]:
	# JP: 一貫したメッセージ形式を生成
	# EN: Create a message in the consistent shape
	return {
		'id': next(_message_sequence),
		'role': role,
		'content': content,
		'timestamp': _utc_timestamp(),
	}


def _initial_history() -> list[dict[str, str | int]]:
	return []


class MessageBroadcaster:
	"""Simple pub/sub helper for Server-Sent Events."""

	# JP: SSE リスナー管理とブロードキャストを担う
	# EN: Manages SSE listeners and broadcasts events
	def __init__(self) -> None:
		self._listeners: list[queue.SimpleQueue[dict[str, Any]]] = []
		self._lock = threading.Lock()

	def subscribe(self) -> queue.SimpleQueue[dict[str, Any]]:
		# JP: リスナーを登録し専用キューを返す
		# EN: Register a listener and return its queue
		listener: queue.SimpleQueue[dict[str, Any]] = queue.SimpleQueue()
		with self._lock:
			self._listeners.append(listener)
		return listener

	def unsubscribe(self, listener: queue.SimpleQueue[dict[str, Any]]) -> None:
		# JP: リスナー解除（存在しない場合は無視）
		# EN: Remove listener (ignore if missing)
		with self._lock:
			with suppress(ValueError):
				self._listeners.remove(listener)

	def publish(self, event: dict[str, Any]) -> None:
		# JP: 登録済みリスナーへイベントを一斉送信
		# EN: Fan out events to all listeners
		with self._lock:
			listeners = list(self._listeners)
		for listener in listeners:
			listener.put(event)

	def publish_message(self, message: dict[str, Any]) -> None:
		# JP: 新規メッセージ通知
		# EN: Publish a new message event
		self.publish({'type': 'message', 'payload': message})

	def publish_update(self, message: dict[str, Any]) -> None:
		# JP: 既存メッセージの更新通知
		# EN: Publish an update event for a message
		self.publish({'type': 'update', 'payload': message})

	def publish_reset(self) -> None:
		# JP: 履歴リセット通知
		# EN: Publish a reset event
		self.publish({'type': 'reset'})


_history_lock = threading.Lock()
_history: list[dict[str, str | int]] = _initial_history()
_broadcaster = MessageBroadcaster()


def _copy_history() -> list[dict[str, str | int]]:
	# JP: 外部公開用にコピーを返す
	# EN: Return a copy for external consumers
	with _history_lock:
		return [dict(message) for message in _history]


def _append_history_message(role: str, content: str) -> dict[str, str | int]:
	# JP: 履歴へ追加し SSE で配信
	# EN: Append to history and broadcast via SSE
	message = _make_message(role, content)
	with _history_lock:
		_history.append(message)
		stored = dict(message)
	_broadcaster.publish_message(stored)
	return stored


def _update_history_message(message_id: int, new_content: str) -> dict[str, str | int] | None:
	# JP: 既存メッセージを更新して通知
	# EN: Update an existing message and broadcast
	with _history_lock:
		for entry in _history:
			if entry['id'] == message_id:
				entry['content'] = new_content
				updated = dict(entry)
				break
		else:
			return None
	_broadcaster.publish_update(updated)
	return updated


def _reset_history() -> list[dict[str, str | int]]:
	# JP: 履歴を初期状態に戻す
	# EN: Reset history to the initial state
	global _history, _message_sequence
	with _history_lock:
		_message_sequence = count()
		_history = _initial_history()
		snapshot = [dict(message) for message in _history]
	_broadcaster.publish_reset()
	return snapshot

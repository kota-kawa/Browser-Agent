# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Scratchpad - 外部メモ機能

エージェントの記憶（Context Window）だけに頼らず、収集した情報を一時保存する「メモ帳」領域。
構造化データを外部に保存し、タスク終了時にそこからまとめて回答を生成できる。
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, Field

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define class `ScratchpadEntry`.
# JP: クラス `ScratchpadEntry` を定義する。
class ScratchpadEntry(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Scratchpad の個別エントリ"""

	# EN: Assign annotated value to key.
	# JP: key に型付きの値を代入する。
	key: str = Field(..., description='エントリのキー（例: 店名、項目名）')
	# EN: Assign annotated value to data.
	# JP: data に型付きの値を代入する。
	data: dict[str, Any] = Field(default_factory=dict, description='構造化データ')
	# EN: Assign annotated value to source_url.
	# JP: source_url に型付きの値を代入する。
	source_url: str | None = Field(default=None, description='情報取得元のURL')
	# EN: Assign annotated value to timestamp.
	# JP: timestamp に型付きの値を代入する。
	timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description='記録時刻')
	# EN: Assign annotated value to notes.
	# JP: notes に型付きの値を代入する。
	notes: str | None = Field(default=None, description='追加メモ')

	# EN: Define function `to_summary`.
	# JP: 関数 `to_summary` を定義する。
	def to_summary(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""エントリの要約を生成"""
		# EN: Assign value to parts.
		# JP: parts に値を代入する。
		parts = [f'【{self.key}】']
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for k, v in self.data.items():
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(f'  {k}: {v}')
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.notes:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(f'  メモ: {self.notes}')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(parts)


# EN: Define class `Scratchpad`.
# JP: クラス `Scratchpad` を定義する。
class Scratchpad(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	外部メモ（Scratchpad）

	エージェントが収集した情報を一時保存し、タスク終了時にまとめて回答を生成するためのシステム。

	使用例:
	- 店舗情報の収集: 店名、座敷有無、評価、価格帯など
	- 検索結果の比較: 複数の製品やサービスの比較情報
	- マルチステップタスク: 各ステップで収集した情報の蓄積
	"""

	# EN: Assign annotated value to entries.
	# JP: entries に型付きの値を代入する。
	entries: list[ScratchpadEntry] = Field(default_factory=list, description='保存されたエントリのリスト')
	# EN: Assign annotated value to task_context.
	# JP: task_context に型付きの値を代入する。
	task_context: str | None = Field(default=None, description='タスクのコンテキスト情報')
	# EN: Assign annotated value to summary_template.
	# JP: summary_template に型付きの値を代入する。
	summary_template: str | None = Field(default=None, description='まとめ生成時のテンプレート')

	# EN: Define function `add_entry`.
	# JP: 関数 `add_entry` を定義する。
	def add_entry(
		self,
		key: str,
		data: dict[str, Any],
		source_url: str | None = None,
		notes: str | None = None,
	) -> ScratchpadEntry:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		新しいエントリを追加

		Args:
		    key: エントリのキー（例: 店名）
		    data: 構造化データ（例: {'座敷': 'あり', '評価': 4.5}）
		    source_url: 情報取得元のURL
		    notes: 追加メモ

		Returns:
		    追加されたエントリ
		"""
		# EN: Assign value to entry.
		# JP: entry に値を代入する。
		entry = ScratchpadEntry(
			key=key,
			data=data,
			source_url=source_url,
			notes=notes,
		)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.entries.append(entry)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug(f'Scratchpad: Added entry "{key}" with {len(data)} data fields')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return entry

	# EN: Define function `update_entry`.
	# JP: 関数 `update_entry` を定義する。
	def update_entry(
		self,
		key: str,
		data: dict[str, Any] | None = None,
		notes: str | None = None,
		merge: bool = True,
	) -> ScratchpadEntry | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		既存のエントリを更新

		Args:
		    key: 更新するエントリのキー
		    data: 更新するデータ
		    notes: 更新するメモ
		    merge: Trueの場合、既存データとマージ。Falseの場合、置換。

		Returns:
		    更新されたエントリ、見つからない場合はNone
		"""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for entry in self.entries:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry.key == key:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if data is not None:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if merge:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						entry.data.update(data)
					else:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						entry.data = data
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if notes is not None:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					entry.notes = notes
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				entry.timestamp = datetime.now().isoformat()
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Scratchpad: Updated entry "{key}"')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return entry
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `get_entry`.
	# JP: 関数 `get_entry` を定義する。
	def get_entry(self, key: str) -> ScratchpadEntry | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""キーでエントリを取得"""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for entry in self.entries:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry.key == key:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return entry
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `remove_entry`.
	# JP: 関数 `remove_entry` を定義する。
	def remove_entry(self, key: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""エントリを削除"""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, entry in enumerate(self.entries):
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry.key == key:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				self.entries.pop(i)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				logger.debug(f'Scratchpad: Removed entry "{key}"')
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `clear`.
	# JP: 関数 `clear` を定義する。
	def clear(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""すべてのエントリをクリア"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.entries.clear()
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		logger.debug('Scratchpad: Cleared all entries')

	# EN: Define function `get_all_keys`.
	# JP: 関数 `get_all_keys` を定義する。
	def get_all_keys(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""すべてのエントリキーを取得"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [entry.key for entry in self.entries]

	# EN: Define function `count`.
	# JP: 関数 `count` を定義する。
	def count(self) -> int:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""エントリ数を取得"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return len(self.entries)

	# EN: Define function `to_summary`.
	# JP: 関数 `to_summary` を定義する。
	def to_summary(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		すべてのエントリの要約を生成

		タスク終了時にまとめて回答を生成する際に使用。
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.entries:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '（Scratchpadにデータがありません）'

		# EN: Assign value to parts.
		# JP: parts に値を代入する。
		parts = []
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.task_context:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(f'【タスク】{self.task_context}\n')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		parts.append(f'【収集データ】（{len(self.entries)}件）\n')

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, entry in enumerate(self.entries, 1):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(f'{i}. {entry.to_summary()}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append('')  # 空行

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(parts).strip()

	# EN: Define function `to_structured_data`.
	# JP: 関数 `to_structured_data` を定義する。
	def to_structured_data(self) -> list[dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""すべてのエントリを構造化データとして取得"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [
			{
				'key': entry.key,
				'data': entry.data,
				'source_url': entry.source_url,
				'timestamp': entry.timestamp,
				'notes': entry.notes,
			}
			for entry in self.entries
		]

	# EN: Define function `to_json`.
	# JP: 関数 `to_json` を定義する。
	def to_json(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""JSON形式でエクスポート"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return json.dumps(self.to_structured_data(), ensure_ascii=False, indent=2)

	# EN: Define function `from_json`.
	# JP: 関数 `from_json` を定義する。
	@classmethod
	def from_json(cls, json_str: str) -> Scratchpad:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""JSONからインポート"""
		# EN: Assign value to data.
		# JP: data に値を代入する。
		data = json.loads(json_str)
		# EN: Assign value to scratchpad.
		# JP: scratchpad に値を代入する。
		scratchpad = cls()
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for item in data:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			scratchpad.add_entry(
				key=item['key'],
				data=item.get('data', {}),
				source_url=item.get('source_url'),
				notes=item.get('notes'),
			)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return scratchpad

	# EN: Define function `generate_report`.
	# JP: 関数 `generate_report` を定義する。
	def generate_report(self, format_type: str = 'text') -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		収集データからレポートを生成

		Args:
		    format_type: 'text', 'markdown', 'json'のいずれか

		Returns:
		    生成されたレポート
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if format_type == 'json':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.to_json()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.entries:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '収集されたデータはありません。'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if format_type == 'markdown':
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self._generate_markdown_report()

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._generate_text_report()

	# EN: Define function `_generate_text_report`.
	# JP: 関数 `_generate_text_report` を定義する。
	def _generate_text_report(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""テキスト形式のレポートを生成"""
		# EN: Assign value to lines.
		# JP: lines に値を代入する。
		lines = []

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.task_context:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(f'■ タスク: {self.task_context}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append(f'■ 収集結果 ({len(self.entries)}件)')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('=' * 40)

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, entry in enumerate(self.entries, 1):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(f'\n{i}. {entry.key}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('-' * 30)
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for k, v in entry.data.items():
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(f'   {k}: {v}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry.notes:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(f'   メモ: {entry.notes}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry.source_url:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(f'   出典: {entry.source_url}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(lines)

	# EN: Define function `_generate_markdown_report`.
	# JP: 関数 `_generate_markdown_report` を定義する。
	def _generate_markdown_report(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Markdown形式のレポートを生成"""
		# EN: Assign value to lines.
		# JP: lines に値を代入する。
		lines = []

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.task_context:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(f'# {self.task_context}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('')

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append(f'## 収集結果 ({len(self.entries)}件)')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('')

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, entry in enumerate(self.entries, 1):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(f'### {i}. {entry.key}')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('| 項目 | 内容 |')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('|------|------|')
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for k, v in entry.data.items():
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(f'| {k} | {v} |')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry.notes:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append('')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(f'> {entry.notes}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if entry.source_url:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append('')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				lines.append(f'*出典: {entry.source_url}*')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append('')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(lines)

	# EN: Define function `get_state`.
	# JP: 関数 `get_state` を定義する。
	def get_state(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""状態をシリアライズ可能な形式で取得"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'entries': [entry.model_dump() for entry in self.entries],
			'task_context': self.task_context,
			'summary_template': self.summary_template,
		}

	# EN: Define function `from_state`.
	# JP: 関数 `from_state` を定義する。
	@classmethod
	def from_state(cls, state: dict[str, Any]) -> Scratchpad:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""状態から復元"""
		# EN: Assign value to scratchpad.
		# JP: scratchpad に値を代入する。
		scratchpad = cls(
			task_context=state.get('task_context'),
			summary_template=state.get('summary_template'),
		)
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for entry_data in state.get('entries', []):
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			scratchpad.entries.append(ScratchpadEntry(**entry_data))
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return scratchpad

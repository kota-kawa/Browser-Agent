# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import shutil
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from abc import ABC, abstractmethod
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from concurrent.futures import ThreadPoolExecutor
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, Field
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from reportlab.lib.pagesizes import letter
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from reportlab.lib.styles import getSampleStyleSheet
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# EN: Assign value to INVALID_FILENAME_ERROR_MESSAGE.
# JP: INVALID_FILENAME_ERROR_MESSAGE に値を代入する。
INVALID_FILENAME_ERROR_MESSAGE = 'Error: Invalid filename format. Must be alphanumeric with supported extension.'
# EN: Assign value to DEFAULT_FILE_SYSTEM_PATH.
# JP: DEFAULT_FILE_SYSTEM_PATH に値を代入する。
DEFAULT_FILE_SYSTEM_PATH = 'browseruse_agent_data'


# EN: Define class `FileSystemError`.
# JP: クラス `FileSystemError` を定義する。
class FileSystemError(Exception):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Custom exception for file system operations that should be shown to LLM"""

	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `BaseFile`.
# JP: クラス `BaseFile` を定義する。
class BaseFile(BaseModel, ABC):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Base class for all file types"""

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str
	# EN: Assign annotated value to content.
	# JP: content に型付きの値を代入する。
	content: str = ''

	# --- Subclass must define this ---
	# EN: Define function `extension`.
	# JP: 関数 `extension` を定義する。
	@property
	@abstractmethod
	def extension(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""File extension (e.g. 'txt', 'md')"""
		# EN: Keep a placeholder statement.
		# JP: プレースホルダー文を維持する。
		pass

	# EN: Define function `write_file_content`.
	# JP: 関数 `write_file_content` を定義する。
	def write_file_content(self, content: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Update internal content (formatted)"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.update_content(content)

	# EN: Define function `append_file_content`.
	# JP: 関数 `append_file_content` を定義する。
	def append_file_content(self, content: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Append content to internal content"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.update_content(self.content + content)

	# --- These are shared and implemented here ---

	# EN: Define function `update_content`.
	# JP: 関数 `update_content` を定義する。
	def update_content(self, content: str) -> None:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.content = content

	# EN: Define function `sync_to_disk_sync`.
	# JP: 関数 `sync_to_disk_sync` を定義する。
	def sync_to_disk_sync(self, path: Path) -> None:
		# EN: Assign value to file_path.
		# JP: file_path に値を代入する。
		file_path = path / self.full_name
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		file_path.write_text(self.content)

	# EN: Define async function `sync_to_disk`.
	# JP: 非同期関数 `sync_to_disk` を定義する。
	async def sync_to_disk(self, path: Path) -> None:
		# EN: Assign value to file_path.
		# JP: file_path に値を代入する。
		file_path = path / self.full_name
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with ThreadPoolExecutor() as executor:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.get_event_loop().run_in_executor(executor, lambda: file_path.write_text(self.content))

	# EN: Define async function `write`.
	# JP: 非同期関数 `write` を定義する。
	async def write(self, content: str, path: Path) -> None:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.write_file_content(content)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.sync_to_disk(path)

	# EN: Define async function `append`.
	# JP: 非同期関数 `append` を定義する。
	async def append(self, content: str, path: Path) -> None:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.append_file_content(content)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await self.sync_to_disk(path)

	# EN: Define function `read`.
	# JP: 関数 `read` を定義する。
	def read(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.content

	# EN: Define function `full_name`.
	# JP: 関数 `full_name` を定義する。
	@property
	def full_name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'{self.name}.{self.extension}'

	# EN: Define function `get_size`.
	# JP: 関数 `get_size` を定義する。
	@property
	def get_size(self) -> int:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return len(self.content)

	# EN: Define function `get_line_count`.
	# JP: 関数 `get_line_count` を定義する。
	@property
	def get_line_count(self) -> int:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return len(self.content.splitlines())


# EN: Define class `MarkdownFile`.
# JP: クラス `MarkdownFile` を定義する。
class MarkdownFile(BaseFile):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Markdown file implementation"""

	# EN: Define function `extension`.
	# JP: 関数 `extension` を定義する。
	@property
	def extension(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'md'


# EN: Define class `TxtFile`.
# JP: クラス `TxtFile` を定義する。
class TxtFile(BaseFile):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Plain text file implementation"""

	# EN: Define function `extension`.
	# JP: 関数 `extension` を定義する。
	@property
	def extension(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'txt'


# EN: Define class `JsonFile`.
# JP: クラス `JsonFile` を定義する。
class JsonFile(BaseFile):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""JSON file implementation"""

	# EN: Define function `extension`.
	# JP: 関数 `extension` を定義する。
	@property
	def extension(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'json'


# EN: Define class `CsvFile`.
# JP: クラス `CsvFile` を定義する。
class CsvFile(BaseFile):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""CSV file implementation"""

	# EN: Define function `extension`.
	# JP: 関数 `extension` を定義する。
	@property
	def extension(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'csv'


# EN: Define class `PdfFile`.
# JP: クラス `PdfFile` を定義する。
class PdfFile(BaseFile):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""PDF file implementation"""

	# EN: Define function `extension`.
	# JP: 関数 `extension` を定義する。
	@property
	def extension(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'pdf'

	# EN: Define function `sync_to_disk_sync`.
	# JP: 関数 `sync_to_disk_sync` を定義する。
	def sync_to_disk_sync(self, path: Path) -> None:
		# EN: Assign value to file_path.
		# JP: file_path に値を代入する。
		file_path = path / self.full_name
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Create PDF document
			# EN: Assign value to doc.
			# JP: doc に値を代入する。
			doc = SimpleDocTemplate(str(file_path), pagesize=letter)
			# EN: Assign value to styles.
			# JP: styles に値を代入する。
			styles = getSampleStyleSheet()
			# EN: Assign value to story.
			# JP: story に値を代入する。
			story = []

			# Convert markdown content to simple text and add to PDF
			# For basic implementation, we'll treat content as plain text
			# This avoids the AGPL license issue while maintaining functionality
			# EN: Assign value to content_lines.
			# JP: content_lines に値を代入する。
			content_lines = self.content.split('\n')

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for line in content_lines:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if line.strip():
					# Handle basic markdown headers
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if line.startswith('# '):
						# EN: Assign value to para.
						# JP: para に値を代入する。
						para = Paragraph(line[2:], styles['Title'])
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif line.startswith('## '):
						# EN: Assign value to para.
						# JP: para に値を代入する。
						para = Paragraph(line[3:], styles['Heading1'])
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif line.startswith('### '):
						# EN: Assign value to para.
						# JP: para に値を代入する。
						para = Paragraph(line[4:], styles['Heading2'])
					else:
						# EN: Assign value to para.
						# JP: para に値を代入する。
						para = Paragraph(line, styles['Normal'])
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					story.append(para)
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					story.append(Spacer(1, 6))

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			doc.build(story)
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise FileSystemError(f"Error: Could not write to file '{self.full_name}'. {str(e)}")

	# EN: Define async function `sync_to_disk`.
	# JP: 非同期関数 `sync_to_disk` を定義する。
	async def sync_to_disk(self, path: Path) -> None:
		# EN: Execute logic with managed resources.
		# JP: リソース管理付きで処理を実行する。
		with ThreadPoolExecutor() as executor:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await asyncio.get_event_loop().run_in_executor(executor, lambda: self.sync_to_disk_sync(path))


# EN: Define class `FileSystemState`.
# JP: クラス `FileSystemState` を定義する。
class FileSystemState(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Serializable state of the file system"""

	# EN: Assign annotated value to files.
	# JP: files に型付きの値を代入する。
	files: dict[str, dict[str, Any]] = Field(default_factory=dict)  # full filename -> file data
	# EN: Assign annotated value to base_dir.
	# JP: base_dir に型付きの値を代入する。
	base_dir: str
	# EN: Assign annotated value to extracted_content_count.
	# JP: extracted_content_count に型付きの値を代入する。
	extracted_content_count: int = 0


# EN: Define class `FileSystem`.
# JP: クラス `FileSystem` を定義する。
class FileSystem:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Enhanced file system with in-memory storage and multiple file type support"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, base_dir: str | Path, create_default_files: bool = True):
		# Handle the Path conversion before calling super().__init__
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.base_dir.mkdir(parents=True, exist_ok=True)

		# Create and use a dedicated subfolder for all operations
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.data_dir = self.base_dir / DEFAULT_FILE_SYSTEM_PATH
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.data_dir.exists():
			# clean the data directory
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			shutil.rmtree(self.data_dir)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self.data_dir.mkdir(exist_ok=True)

		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._file_types: dict[str, type[BaseFile]] = {
			'md': MarkdownFile,
			'txt': TxtFile,
			'json': JsonFile,
			'csv': CsvFile,
			'pdf': PdfFile,
		}

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.files = {}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if create_default_files:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.default_files = ['todo.md']
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._create_default_files()

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.extracted_content_count = 0

	# EN: Define function `get_allowed_extensions`.
	# JP: 関数 `get_allowed_extensions` を定義する。
	def get_allowed_extensions(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get allowed extensions"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return list(self._file_types.keys())

	# EN: Define function `_get_file_type_class`.
	# JP: 関数 `_get_file_type_class` を定義する。
	def _get_file_type_class(self, extension: str) -> type[BaseFile] | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the appropriate file class for an extension."""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self._file_types.get(extension.lower(), None)

	# EN: Define function `_create_default_files`.
	# JP: 関数 `_create_default_files` を定義する。
	def _create_default_files(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Create default results and todo files"""
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for full_filename in self.default_files:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			name_without_ext, extension = self._parse_filename(full_filename)
			# EN: Assign value to file_class.
			# JP: file_class に値を代入する。
			file_class = self._get_file_type_class(extension)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not file_class:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f"Error: Invalid file extension '{extension}' for file '{full_filename}'.")

			# EN: Assign value to file_obj.
			# JP: file_obj に値を代入する。
			file_obj = file_class(name=name_without_ext)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.files[full_filename] = file_obj  # Use full filename as key
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			file_obj.sync_to_disk_sync(self.data_dir)

	# EN: Define function `_is_valid_filename`.
	# JP: 関数 `_is_valid_filename` を定義する。
	def _is_valid_filename(self, file_name: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Check if filename matches the required pattern: name.extension"""
		# Build extensions pattern from _file_types
		# EN: Assign value to extensions.
		# JP: extensions に値を代入する。
		extensions = '|'.join(self._file_types.keys())
		# EN: Assign value to pattern.
		# JP: pattern に値を代入する。
		pattern = rf'^[a-zA-Z0-9_\-]+\.({extensions})$'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return bool(re.match(pattern, file_name))

	# EN: Define function `_parse_filename`.
	# JP: 関数 `_parse_filename` を定義する。
	def _parse_filename(self, filename: str) -> tuple[str, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Parse filename into name and extension. Always check _is_valid_filename first."""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		name, extension = filename.rsplit('.', 1)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return name, extension.lower()

	# EN: Define function `get_dir`.
	# JP: 関数 `get_dir` を定義する。
	def get_dir(self) -> Path:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the file system directory"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.data_dir

	# EN: Define function `get_file`.
	# JP: 関数 `get_file` を定義する。
	def get_file(self, full_filename: str) -> BaseFile | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get a file object by full filename"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_valid_filename(full_filename):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# Use full filename as key
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.files.get(full_filename)

	# EN: Define function `list_files`.
	# JP: 関数 `list_files` を定義する。
	def list_files(self) -> list[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""List all files in the system"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [file_obj.full_name for file_obj in self.files.values()]

	# EN: Define function `display_file`.
	# JP: 関数 `display_file` を定義する。
	def display_file(self, full_filename: str) -> str | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Display file content using file-specific display method"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_valid_filename(full_filename):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to file_obj.
		# JP: file_obj に値を代入する。
		file_obj = self.get_file(full_filename)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not file_obj:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return file_obj.read()

	# EN: Define async function `read_file`.
	# JP: 非同期関数 `read_file` を定義する。
	async def read_file(self, full_filename: str, external_file: bool = False) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Read file content using file-specific read method and return appropriate message to LLM"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if external_file:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					_, extension = self._parse_filename(full_filename)
				except Exception:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return f'Error: Invalid filename format {full_filename}. Must be alphanumeric with a supported extension.'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if extension in ['md', 'txt', 'json', 'csv']:
					# EN: Import required modules.
					# JP: 必要なモジュールをインポートする。
					import anyio

					# EN: Execute async logic with managed resources.
					# JP: リソース管理付きで非同期処理を実行する。
					async with await anyio.open_file(full_filename, 'r') as f:
						# EN: Assign value to content.
						# JP: content に値を代入する。
						content = await f.read()
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return f'Read from file {full_filename}.\n<content>\n{content}\n</content>'
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif extension == 'pdf':
					# EN: Import required modules.
					# JP: 必要なモジュールをインポートする。
					import pypdf

					# EN: Assign value to reader.
					# JP: reader に値を代入する。
					reader = pypdf.PdfReader(full_filename)
					# EN: Assign value to num_pages.
					# JP: num_pages に値を代入する。
					num_pages = len(reader.pages)
					# EN: Assign value to MAX_PDF_PAGES.
					# JP: MAX_PDF_PAGES に値を代入する。
					MAX_PDF_PAGES = 10
					# EN: Assign value to extra_pages.
					# JP: extra_pages に値を代入する。
					extra_pages = num_pages - MAX_PDF_PAGES
					# EN: Assign value to extracted_text.
					# JP: extracted_text に値を代入する。
					extracted_text = ''
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for page in reader.pages[:MAX_PDF_PAGES]:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						extracted_text += page.extract_text()
					# EN: Assign value to extra_pages_text.
					# JP: extra_pages_text に値を代入する。
					extra_pages_text = f'{extra_pages} more pages...' if extra_pages > 0 else ''
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return f'Read from file {full_filename}.\n<content>\n{extracted_text}\n{extra_pages_text}</content>'
				else:
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return f'Error: Cannot read file {full_filename} as {extension} extension is not supported.'
			except FileNotFoundError:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return f"Error: File '{full_filename}' not found."
			except PermissionError:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return f"Error: Permission denied to read file '{full_filename}'."
			except Exception as e:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return f"Error: Could not read file '{full_filename}'."

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_valid_filename(full_filename):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return INVALID_FILENAME_ERROR_MESSAGE

		# EN: Assign value to file_obj.
		# JP: file_obj に値を代入する。
		file_obj = self.get_file(full_filename)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not file_obj:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"File '{full_filename}' not found."

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = file_obj.read()
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Read from file {full_filename}.\n<content>\n{content}\n</content>'
		except FileSystemError as e:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str(e)
		except Exception:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"Error: Could not read file '{full_filename}'."

	# EN: Define async function `write_file`.
	# JP: 非同期関数 `write_file` を定義する。
	async def write_file(self, full_filename: str, content: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Write content to file using file-specific write method"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_valid_filename(full_filename):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return INVALID_FILENAME_ERROR_MESSAGE

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			name_without_ext, extension = self._parse_filename(full_filename)
			# EN: Assign value to file_class.
			# JP: file_class に値を代入する。
			file_class = self._get_file_type_class(extension)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not file_class:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f"Error: Invalid file extension '{extension}' for file '{full_filename}'.")

			# Create or get existing file using full filename as key
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if full_filename in self.files:
				# EN: Assign value to file_obj.
				# JP: file_obj に値を代入する。
				file_obj = self.files[full_filename]
			else:
				# EN: Assign value to file_obj.
				# JP: file_obj に値を代入する。
				file_obj = file_class(name=name_without_ext)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.files[full_filename] = file_obj  # Use full filename as key

			# Use file-specific write method
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await file_obj.write(content, self.data_dir)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Data written to file {full_filename} successfully.'
		except FileSystemError as e:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str(e)
		except Exception as e:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"Error: Could not write to file '{full_filename}'. {str(e)}"

	# EN: Define async function `append_file`.
	# JP: 非同期関数 `append_file` を定義する。
	async def append_file(self, full_filename: str, content: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Append content to file using file-specific append method"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_valid_filename(full_filename):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return INVALID_FILENAME_ERROR_MESSAGE

		# EN: Assign value to file_obj.
		# JP: file_obj に値を代入する。
		file_obj = self.get_file(full_filename)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not file_obj:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"File '{full_filename}' not found."

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await file_obj.append(content, self.data_dir)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Data appended to file {full_filename} successfully.'
		except FileSystemError as e:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str(e)
		except Exception as e:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"Error: Could not append to file '{full_filename}'. {str(e)}"

	# EN: Define async function `replace_file_str`.
	# JP: 非同期関数 `replace_file_str` を定義する。
	async def replace_file_str(self, full_filename: str, old_str: str, new_str: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Replace old_str with new_str in file_name"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_valid_filename(full_filename):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return INVALID_FILENAME_ERROR_MESSAGE

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not old_str:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return 'Error: Cannot replace empty string. Please provide a non-empty string to replace.'

		# EN: Assign value to file_obj.
		# JP: file_obj に値を代入する。
		file_obj = self.get_file(full_filename)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not file_obj:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"File '{full_filename}' not found."

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = file_obj.read()
			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = content.replace(old_str, new_str)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			await file_obj.write(content, self.data_dir)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f'Successfully replaced all occurrences of "{old_str}" with "{new_str}" in file {full_filename}'
		except FileSystemError as e:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return str(e)
		except Exception as e:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return f"Error: Could not replace string in file '{full_filename}'. {str(e)}"

	# EN: Define async function `save_extracted_content`.
	# JP: 非同期関数 `save_extracted_content` を定義する。
	async def save_extracted_content(self, content: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Save extracted content to a numbered file"""
		# EN: Assign value to initial_filename.
		# JP: initial_filename に値を代入する。
		initial_filename = f'extracted_content_{self.extracted_content_count}'
		# EN: Assign value to extracted_filename.
		# JP: extracted_filename に値を代入する。
		extracted_filename = f'{initial_filename}.md'
		# EN: Assign value to file_obj.
		# JP: file_obj に値を代入する。
		file_obj = MarkdownFile(name=initial_filename)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await file_obj.write(content, self.data_dir)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.files[extracted_filename] = file_obj
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		self.extracted_content_count += 1
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'Extracted content saved to file {extracted_filename} successfully.'

	# EN: Define function `describe`.
	# JP: 関数 `describe` を定義する。
	def describe(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""List all files with their content information using file-specific display methods"""
		# EN: Assign value to DISPLAY_CHARS.
		# JP: DISPLAY_CHARS に値を代入する。
		DISPLAY_CHARS = 400
		# EN: Assign value to description.
		# JP: description に値を代入する。
		description = ''

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for file_obj in self.files.values():
			# Skip todo.md from description
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if file_obj.full_name == 'todo.md':
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Assign value to content.
			# JP: content に値を代入する。
			content = file_obj.read()

			# Handle empty files
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not content:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				description += f'<file>\n{file_obj.full_name} - [empty file]\n</file>\n'
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Assign value to lines.
			# JP: lines に値を代入する。
			lines = content.splitlines()
			# EN: Assign value to line_count.
			# JP: line_count に値を代入する。
			line_count = len(lines)

			# For small files, display the entire content
			# EN: Assign value to whole_file_description.
			# JP: whole_file_description に値を代入する。
			whole_file_description = (
				f'<file>\n{file_obj.full_name} - {line_count} lines\n<content>\n{content}\n</content>\n</file>\n'
			)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if len(content) < int(1.5 * DISPLAY_CHARS):
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				description += whole_file_description
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# For larger files, display start and end previews
			# EN: Assign value to half_display_chars.
			# JP: half_display_chars に値を代入する。
			half_display_chars = DISPLAY_CHARS // 2

			# Get start preview
			# EN: Assign value to start_preview.
			# JP: start_preview に値を代入する。
			start_preview = ''
			# EN: Assign value to start_line_count.
			# JP: start_line_count に値を代入する。
			start_line_count = 0
			# EN: Assign value to chars_count.
			# JP: chars_count に値を代入する。
			chars_count = 0
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for line in lines:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if chars_count + len(line) + 1 > half_display_chars:
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				start_preview += line + '\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				chars_count += len(line) + 1
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				start_line_count += 1

			# Get end preview
			# EN: Assign value to end_preview.
			# JP: end_preview に値を代入する。
			end_preview = ''
			# EN: Assign value to end_line_count.
			# JP: end_line_count に値を代入する。
			end_line_count = 0
			# EN: Assign value to chars_count.
			# JP: chars_count に値を代入する。
			chars_count = 0
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for line in reversed(lines):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if chars_count + len(line) + 1 > half_display_chars:
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break
				# EN: Assign value to end_preview.
				# JP: end_preview に値を代入する。
				end_preview = line + '\n' + end_preview
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				chars_count += len(line) + 1
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				end_line_count += 1

			# Calculate lines in between
			# EN: Assign value to middle_line_count.
			# JP: middle_line_count に値を代入する。
			middle_line_count = line_count - start_line_count - end_line_count
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if middle_line_count <= 0:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				description += whole_file_description
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Assign value to start_preview.
			# JP: start_preview に値を代入する。
			start_preview = start_preview.strip('\n').rstrip()
			# EN: Assign value to end_preview.
			# JP: end_preview に値を代入する。
			end_preview = end_preview.strip('\n').rstrip()

			# Format output
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not (start_preview or end_preview):
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				description += f'<file>\n{file_obj.full_name} - {line_count} lines\n<content>\n{middle_line_count} lines...\n</content>\n</file>\n'
			else:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				description += f'<file>\n{file_obj.full_name} - {line_count} lines\n<content>\n{start_preview}\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				description += f'... {middle_line_count} more lines ...\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				description += f'{end_preview}\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				description += '</content>\n</file>\n'

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return description.strip('\n')

	# EN: Define function `get_todo_contents`.
	# JP: 関数 `get_todo_contents` を定義する。
	def get_todo_contents(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get todo file contents"""
		# EN: Assign value to todo_file.
		# JP: todo_file に値を代入する。
		todo_file = self.get_file('todo.md')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return todo_file.read() if todo_file else ''

	# EN: Define function `get_state`.
	# JP: 関数 `get_state` を定義する。
	def get_state(self) -> FileSystemState:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get serializable state of the file system"""
		# EN: Assign value to files_data.
		# JP: files_data に値を代入する。
		files_data = {}
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for full_filename, file_obj in self.files.items():
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			files_data[full_filename] = {'type': file_obj.__class__.__name__, 'data': file_obj.model_dump()}

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return FileSystemState(
			files=files_data, base_dir=str(self.base_dir), extracted_content_count=self.extracted_content_count
		)

	# EN: Define function `nuke`.
	# JP: 関数 `nuke` を定義する。
	def nuke(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Delete the file system directory"""
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		shutil.rmtree(self.data_dir)

	# EN: Define function `from_state`.
	# JP: 関数 `from_state` を定義する。
	@classmethod
	def from_state(cls, state: FileSystemState) -> 'FileSystem':
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Restore file system from serializable state at the exact same location"""
		# Create file system without default files
		# EN: Assign value to fs.
		# JP: fs に値を代入する。
		fs = cls(base_dir=Path(state.base_dir), create_default_files=False)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		fs.extracted_content_count = state.extracted_content_count

		# Restore all files
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for full_filename, file_data in state.files.items():
			# EN: Assign value to file_type.
			# JP: file_type に値を代入する。
			file_type = file_data['type']
			# EN: Assign value to file_info.
			# JP: file_info に値を代入する。
			file_info = file_data['data']

			# Create the appropriate file object based on type
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if file_type == 'MarkdownFile':
				# EN: Assign value to file_obj.
				# JP: file_obj に値を代入する。
				file_obj = MarkdownFile(**file_info)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif file_type == 'TxtFile':
				# EN: Assign value to file_obj.
				# JP: file_obj に値を代入する。
				file_obj = TxtFile(**file_info)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif file_type == 'JsonFile':
				# EN: Assign value to file_obj.
				# JP: file_obj に値を代入する。
				file_obj = JsonFile(**file_info)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif file_type == 'CsvFile':
				# EN: Assign value to file_obj.
				# JP: file_obj に値を代入する。
				file_obj = CsvFile(**file_info)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif file_type == 'PdfFile':
				# EN: Assign value to file_obj.
				# JP: file_obj に値を代入する。
				file_obj = PdfFile(**file_info)
			else:
				# Skip unknown file types
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# Add to files dict and sync to disk
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			fs.files[full_filename] = file_obj
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			file_obj.sync_to_disk_sync(fs.data_dir)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return fs

from typing import Generic, TypeVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


# Action Input Models
# EN: Define class `SearchGoogleAction`.
# JP: クラス `SearchGoogleAction` を定義する。
class SearchGoogleAction(BaseModel):
	query: str


# EN: Define class `GoToUrlAction`.
# JP: クラス `GoToUrlAction` を定義する。
class GoToUrlAction(BaseModel):
	url: str
	new_tab: bool = False  # True to open in new tab, False to navigate in current tab


# EN: Define class `ClickElementAction`.
# JP: クラス `ClickElementAction` を定義する。
class ClickElementAction(BaseModel):
	index: int = Field(ge=1, description='index of the element to click')
	while_holding_ctrl: bool | None = Field(
		default=None,
		description='Set to True to open the navigation in a new background tab (Ctrl+Click behavior). Optional.',
	)
	# expect_download: bool = Field(default=False, description='set True if expecting a download, False otherwise')  # moved to downloads_watchdog.py
	# click_count: int = 1  # TODO


# EN: Define class `InputTextAction`.
# JP: クラス `InputTextAction` を定義する。
class InputTextAction(BaseModel):
	index: int = Field(
		ge=0,
		description='index of the element to input text into, 0 is the page',
		validation_alias=AliasChoices('index', 'element_index'),
	)
	text: str
	clear_existing: bool = Field(default=True, description='set True to clear existing text, False to append to existing text')


# EN: Define class `DoneAction`.
# JP: クラス `DoneAction` を定義する。
class DoneAction(BaseModel):
	text: str
	success: bool
	files_to_display: list[str] | None = []


T = TypeVar('T', bound=BaseModel)


# EN: Define class `StructuredOutputAction`.
# JP: クラス `StructuredOutputAction` を定義する。
class StructuredOutputAction(BaseModel, Generic[T]):
	success: bool = True
	data: T


# EN: Define class `SwitchTabAction`.
# JP: クラス `SwitchTabAction` を定義する。
class SwitchTabAction(BaseModel):
	tab_id: str = Field(
		min_length=4,
		max_length=4,
		description='Last 4 chars of TargetID',
	)  # last 4 chars of TargetID


# EN: Define class `CloseTabAction`.
# JP: クラス `CloseTabAction` を定義する。
class CloseTabAction(BaseModel):
	tab_id: str = Field(min_length=4, max_length=4, description='4 character Tab ID')  # last 4 chars of TargetID


# EN: Define class `ScrollAction`.
# JP: クラス `ScrollAction` を定義する。
class ScrollAction(BaseModel):
	down: bool  # True to scroll down, False to scroll up
	num_pages: float  # Number of pages to scroll (0.5 = half page, 1.0 = one page, etc.)
	frame_element_index: int | None = None  # Optional element index to find scroll container for


# EN: Define class `SendKeysAction`.
# JP: クラス `SendKeysAction` を定義する。
class SendKeysAction(BaseModel):
	keys: str


# EN: Define class `UploadFileAction`.
# JP: クラス `UploadFileAction` を定義する。
class UploadFileAction(BaseModel):
	index: int
	path: str


# EN: Define class `ExtractPageContentAction`.
# JP: クラス `ExtractPageContentAction` を定義する。
class ExtractPageContentAction(BaseModel):
	value: str


# EN: Define class `NoParamsAction`.
# JP: クラス `NoParamsAction` を定義する。
class NoParamsAction(BaseModel):
	"""
	Accepts absolutely anything in the incoming data
	and discards it, so the final parsed model is empty.
	"""

	model_config = ConfigDict(extra='ignore')
	# No fields defined - all inputs are ignored automatically


# EN: Define class `GetDropdownOptionsAction`.
# JP: クラス `GetDropdownOptionsAction` を定義する。
class GetDropdownOptionsAction(BaseModel):
	index: int = Field(ge=1, description='index of the dropdown element to get the option values for')


# EN: Define class `SelectDropdownOptionAction`.
# JP: クラス `SelectDropdownOptionAction` を定義する。
class SelectDropdownOptionAction(BaseModel):
	index: int = Field(ge=1, description='index of the dropdown element to select an option for')
	text: str = Field(description='the text or exact value of the option to select')


# Scratchpad Actions - 外部メモ機能


# EN: Define class `ScratchpadAddAction`.
# JP: クラス `ScratchpadAddAction` を定義する。
class ScratchpadAddAction(BaseModel):
	"""Scratchpadにエントリを追加するアクション"""

	key: str = Field(description='エントリのキー（例: 店名、項目名）')
	data: dict = Field(description='構造化データ（例: {"座敷": "あり", "評価": 4.5}）')
	source_url: str | None = Field(default=None, description='情報取得元のURL（省略可）')
	notes: str | None = Field(default=None, description='追加メモ（省略可）')


# EN: Define class `ScratchpadUpdateAction`.
# JP: クラス `ScratchpadUpdateAction` を定義する。
class ScratchpadUpdateAction(BaseModel):
	"""Scratchpadの既存エントリを更新するアクション"""

	key: str = Field(description='更新するエントリのキー')
	data: dict | None = Field(default=None, description='更新するデータ')
	notes: str | None = Field(default=None, description='更新するメモ')
	merge: bool = Field(default=True, description='Trueで既存データとマージ、Falseで置換')


# EN: Define class `ScratchpadRemoveAction`.
# JP: クラス `ScratchpadRemoveAction` を定義する。
class ScratchpadRemoveAction(BaseModel):
	"""Scratchpadからエントリを削除するアクション"""

	key: str = Field(description='削除するエントリのキー')


# EN: Define class `ScratchpadGetAction`.
# JP: クラス `ScratchpadGetAction` を定義する。
class ScratchpadGetAction(BaseModel):
	"""Scratchpadの内容を取得するアクション"""

	key: str | None = Field(default=None, description='取得するエントリのキー（省略時は全エントリのサマリー）')


# EN: Define class `ScratchpadClearAction`.
# JP: クラス `ScratchpadClearAction` を定義する。
class ScratchpadClearAction(BaseModel):
	"""Scratchpadをクリアするアクション"""

	pass

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Generic, TypeVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


# Action Input Models
# EN: Define class `SearchGoogleAction`.
# JP: クラス `SearchGoogleAction` を定義する。
class SearchGoogleAction(BaseModel):
	# EN: Assign annotated value to query.
	# JP: query に型付きの値を代入する。
	query: str


# EN: Define class `GoToUrlAction`.
# JP: クラス `GoToUrlAction` を定義する。
class GoToUrlAction(BaseModel):
	# EN: Assign annotated value to url.
	# JP: url に型付きの値を代入する。
	url: str
	# EN: Assign annotated value to new_tab.
	# JP: new_tab に型付きの値を代入する。
	new_tab: bool = False  # True to open in new tab, False to navigate in current tab


# EN: Define class `ClickElementAction`.
# JP: クラス `ClickElementAction` を定義する。
class ClickElementAction(BaseModel):
	# EN: Assign annotated value to index.
	# JP: index に型付きの値を代入する。
	index: int = Field(ge=1, description='index of the element to click')
	# EN: Assign annotated value to while_holding_ctrl.
	# JP: while_holding_ctrl に型付きの値を代入する。
	while_holding_ctrl: bool | None = Field(
		default=None,
		description='Set to True to open the navigation in a new background tab (Ctrl+Click behavior). Optional.',
	)
	# expect_download: bool = Field(default=False, description='set True if expecting a download, False otherwise')  # moved to downloads_watchdog.py
	# click_count: int = 1  # TODO


# EN: Define class `InputTextAction`.
# JP: クラス `InputTextAction` を定義する。
class InputTextAction(BaseModel):
	# EN: Assign annotated value to index.
	# JP: index に型付きの値を代入する。
	index: int = Field(
		ge=0,
		description='index of the element to input text into, 0 is the page',
		validation_alias=AliasChoices('index', 'element_index'),
	)
	# EN: Assign annotated value to text.
	# JP: text に型付きの値を代入する。
	text: str
	# EN: Assign annotated value to clear_existing.
	# JP: clear_existing に型付きの値を代入する。
	clear_existing: bool = Field(default=True, description='set True to clear existing text, False to append to existing text')


# EN: Define class `DoneAction`.
# JP: クラス `DoneAction` を定義する。
class DoneAction(BaseModel):
	# EN: Assign annotated value to text.
	# JP: text に型付きの値を代入する。
	text: str
	# EN: Assign annotated value to success.
	# JP: success に型付きの値を代入する。
	success: bool
	# EN: Assign annotated value to files_to_display.
	# JP: files_to_display に型付きの値を代入する。
	files_to_display: list[str] | None = []


# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `StructuredOutputAction`.
# JP: クラス `StructuredOutputAction` を定義する。
class StructuredOutputAction(BaseModel, Generic[T]):
	# EN: Assign annotated value to success.
	# JP: success に型付きの値を代入する。
	success: bool = True
	# EN: Assign annotated value to data.
	# JP: data に型付きの値を代入する。
	data: T


# EN: Define class `SwitchTabAction`.
# JP: クラス `SwitchTabAction` を定義する。
class SwitchTabAction(BaseModel):
	# EN: Assign annotated value to tab_id.
	# JP: tab_id に型付きの値を代入する。
	tab_id: str = Field(
		min_length=4,
		max_length=4,
		description='Last 4 chars of TargetID',
	)  # last 4 chars of TargetID


# EN: Define class `CloseTabAction`.
# JP: クラス `CloseTabAction` を定義する。
class CloseTabAction(BaseModel):
	# EN: Assign annotated value to tab_id.
	# JP: tab_id に型付きの値を代入する。
	tab_id: str = Field(min_length=4, max_length=4, description='4 character Tab ID')  # last 4 chars of TargetID


# EN: Define class `ScrollAction`.
# JP: クラス `ScrollAction` を定義する。
class ScrollAction(BaseModel):
	# EN: Assign annotated value to down.
	# JP: down に型付きの値を代入する。
	down: bool  # True to scroll down, False to scroll up
	# EN: Assign annotated value to num_pages.
	# JP: num_pages に型付きの値を代入する。
	num_pages: float  # Number of pages to scroll (0.5 = half page, 1.0 = one page, etc.)
	# EN: Assign annotated value to frame_element_index.
	# JP: frame_element_index に型付きの値を代入する。
	frame_element_index: int | None = None  # Optional element index to find scroll container for


# EN: Define class `SendKeysAction`.
# JP: クラス `SendKeysAction` を定義する。
class SendKeysAction(BaseModel):
	# EN: Assign annotated value to keys.
	# JP: keys に型付きの値を代入する。
	keys: str


# EN: Define class `UploadFileAction`.
# JP: クラス `UploadFileAction` を定義する。
class UploadFileAction(BaseModel):
	# EN: Assign annotated value to index.
	# JP: index に型付きの値を代入する。
	index: int
	# EN: Assign annotated value to path.
	# JP: path に型付きの値を代入する。
	path: str


# EN: Define class `ExtractPageContentAction`.
# JP: クラス `ExtractPageContentAction` を定義する。
class ExtractPageContentAction(BaseModel):
	# EN: Assign annotated value to value.
	# JP: value に型付きの値を代入する。
	value: str


# EN: Define class `NoParamsAction`.
# JP: クラス `NoParamsAction` を定義する。
class NoParamsAction(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Accepts absolutely anything in the incoming data
	and discards it, so the final parsed model is empty.
	"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(extra='ignore')
	# No fields defined - all inputs are ignored automatically


# EN: Define class `GetDropdownOptionsAction`.
# JP: クラス `GetDropdownOptionsAction` を定義する。
class GetDropdownOptionsAction(BaseModel):
	# EN: Assign annotated value to index.
	# JP: index に型付きの値を代入する。
	index: int = Field(ge=1, description='index of the dropdown element to get the option values for')


# EN: Define class `SelectDropdownOptionAction`.
# JP: クラス `SelectDropdownOptionAction` を定義する。
class SelectDropdownOptionAction(BaseModel):
	# EN: Assign annotated value to index.
	# JP: index に型付きの値を代入する。
	index: int = Field(ge=1, description='index of the dropdown element to select an option for')
	# EN: Assign annotated value to text.
	# JP: text に型付きの値を代入する。
	text: str = Field(description='the text or exact value of the option to select')


# Scratchpad Actions - 外部メモ機能


# EN: Define class `ScratchpadAddAction`.
# JP: クラス `ScratchpadAddAction` を定義する。
class ScratchpadAddAction(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Scratchpadにエントリを追加するアクション"""

	# EN: Assign annotated value to key.
	# JP: key に型付きの値を代入する。
	key: str = Field(description='エントリのキー（例: 店名、項目名）')
	# EN: Assign annotated value to data.
	# JP: data に型付きの値を代入する。
	data: dict = Field(description='構造化データ（例: {"座敷": "あり", "評価": 4.5}）')
	# EN: Assign annotated value to source_url.
	# JP: source_url に型付きの値を代入する。
	source_url: str | None = Field(default=None, description='情報取得元のURL（省略可）')
	# EN: Assign annotated value to notes.
	# JP: notes に型付きの値を代入する。
	notes: str | None = Field(default=None, description='追加メモ（省略可）')


# EN: Define class `ScratchpadUpdateAction`.
# JP: クラス `ScratchpadUpdateAction` を定義する。
class ScratchpadUpdateAction(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Scratchpadの既存エントリを更新するアクション"""

	# EN: Assign annotated value to key.
	# JP: key に型付きの値を代入する。
	key: str = Field(description='更新するエントリのキー')
	# EN: Assign annotated value to data.
	# JP: data に型付きの値を代入する。
	data: dict | None = Field(default=None, description='更新するデータ')
	# EN: Assign annotated value to notes.
	# JP: notes に型付きの値を代入する。
	notes: str | None = Field(default=None, description='更新するメモ')
	# EN: Assign annotated value to merge.
	# JP: merge に型付きの値を代入する。
	merge: bool = Field(default=True, description='Trueで既存データとマージ、Falseで置換')


# EN: Define class `ScratchpadRemoveAction`.
# JP: クラス `ScratchpadRemoveAction` を定義する。
class ScratchpadRemoveAction(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Scratchpadからエントリを削除するアクション"""

	# EN: Assign annotated value to key.
	# JP: key に型付きの値を代入する。
	key: str = Field(description='削除するエントリのキー')


# EN: Define class `ScratchpadGetAction`.
# JP: クラス `ScratchpadGetAction` を定義する。
class ScratchpadGetAction(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Scratchpadの内容を取得するアクション"""

	# EN: Assign annotated value to key.
	# JP: key に型付きの値を代入する。
	key: str | None = Field(default=None, description='取得するエントリのキー（省略時は全エントリのサマリー）')


# EN: Define class `ScratchpadClearAction`.
# JP: クラス `ScratchpadClearAction` を定義する。
class ScratchpadClearAction(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Scratchpadをクリアするアクション"""

	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Callable
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, ConfigDict

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.scratchpad import Scratchpad
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser import BrowserSession
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystem
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `RegisteredAction`.
# JP: クラス `RegisteredAction` を定義する。
class RegisteredAction(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Model for a registered action"""

	# EN: Assign annotated value to name.
	# JP: name に型付きの値を代入する。
	name: str
	# EN: Assign annotated value to description.
	# JP: description に型付きの値を代入する。
	description: str
	# EN: Assign annotated value to function.
	# JP: function に型付きの値を代入する。
	function: Callable
	# EN: Assign annotated value to param_model.
	# JP: param_model に型付きの値を代入する。
	param_model: type[BaseModel]

	# filters: provide specific domains to determine whether the action should be available on the given URL or not
	# EN: Assign annotated value to domains.
	# JP: domains に型付きの値を代入する。
	domains: list[str] | None = None  # e.g. ['*.google.com', 'www.bing.com', 'yahoo.*]

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True)

	# EN: Define function `prompt_description`.
	# JP: 関数 `prompt_description` を定義する。
	def prompt_description(self) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get a description of the action for the prompt"""
		# EN: Assign value to skip_keys.
		# JP: skip_keys に値を代入する。
		skip_keys = ['title']
		# EN: Assign value to s.
		# JP: s に値を代入する。
		s = f'{self.description}: \n'
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		s += '{' + str(self.name) + ': '
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		s += str(
			{
				k: {sub_k: sub_v for sub_k, sub_v in v.items() if sub_k not in skip_keys}
				for k, v in self.param_model.model_json_schema()['properties'].items()
			}
		)
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		s += '}'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return s


# EN: Define class `ActionModel`.
# JP: クラス `ActionModel` を定義する。
class ActionModel(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Base model for dynamically created action models"""

	# this will have all the registered actions, e.g.
	# click_element = param_model = ClickElementParams
	# done = param_model = None
	#
	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')

	# EN: Define function `get_index`.
	# JP: 関数 `get_index` を定義する。
	def get_index(self) -> int | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the index of the action"""
		# {'clicked_element': {'index':5}}
		# EN: Assign value to params.
		# JP: params に値を代入する。
		params = self.model_dump(exclude_unset=True).values()
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not params:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for param in params:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if param is not None and 'index' in param:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return param['index']
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

	# EN: Define function `set_index`.
	# JP: 関数 `set_index` を定義する。
	def set_index(self, index: int):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Overwrite the index of the action"""
		# Get the action name and params
		# EN: Assign value to action_data.
		# JP: action_data に値を代入する。
		action_data = self.model_dump(exclude_unset=True)
		# EN: Assign value to action_name.
		# JP: action_name に値を代入する。
		action_name = next(iter(action_data.keys()))
		# EN: Assign value to action_params.
		# JP: action_params に値を代入する。
		action_params = getattr(self, action_name)

		# Update the index directly on the model
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if hasattr(action_params, 'index'):
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			action_params.index = index


# EN: Define class `ActionRegistry`.
# JP: クラス `ActionRegistry` を定義する。
class ActionRegistry(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Model representing the action registry"""

	# EN: Assign annotated value to actions.
	# JP: actions に型付きの値を代入する。
	actions: dict[str, RegisteredAction] = {}

	# EN: Define function `_match_domains`.
	# JP: 関数 `_match_domains` を定義する。
	@staticmethod
	def _match_domains(domains: list[str] | None, url: str) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Match a list of domain glob patterns against a URL.

		Args:
			domains: A list of domain patterns that can include glob patterns (* wildcard)
			url: The URL to match against

		Returns:
			True if the URL's domain matches the pattern, False otherwise
		"""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if domains is None or not url:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return True

		# Use the centralized URL matching logic from utils
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from browser_use.utils import match_url_with_domain_pattern

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for domain_pattern in domains:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if match_url_with_domain_pattern(url, domain_pattern):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False

	# EN: Define function `get_prompt_description`.
	# JP: 関数 `get_prompt_description` を定義する。
	def get_prompt_description(self, page_url: str | None = None) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get a description of all actions for the prompt

		Args:
			page_url: If provided, filter actions by URL using domain filters.

		Returns:
			A string description of available actions.
			- If page is None: return only actions with no page_filter and no domains (for system prompt)
			- If page is provided: return only filtered actions that match the current page (excluding unfiltered actions)
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if page_url is None:
			# For system prompt (no URL provided), include only actions with no filters
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return '\n'.join(action.prompt_description() for action in self.actions.values() if action.domains is None)

		# only include filtered actions for the current page URL
		# EN: Assign value to filtered_actions.
		# JP: filtered_actions に値を代入する。
		filtered_actions = []
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for action in self.actions.values():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not action.domains:
				# skip actions with no filters, they are already included in the system prompt
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# Check domain filter
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self._match_domains(action.domains, page_url):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				filtered_actions.append(action)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(action.prompt_description() for action in filtered_actions)


# EN: Define class `SpecialActionParameters`.
# JP: クラス `SpecialActionParameters` を定義する。
class SpecialActionParameters(BaseModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Model defining all special parameters that can be injected into actions"""

	# EN: Assign value to model_config.
	# JP: model_config に値を代入する。
	model_config = ConfigDict(arbitrary_types_allowed=True)

	# optional user-provided context object passed down from Agent(context=...)
	# e.g. can contain anything, external db connections, file handles, queues, runtime config objects, etc.
	# that you might want to be able to access quickly from within many of your actions
	# browser-use code doesn't use this at all, we just pass it down to your actions for convenience
	# EN: Assign annotated value to context.
	# JP: context に型付きの値を代入する。
	context: Any | None = None

	# browser-use session object, can be used to create new tabs, navigate, access CDP
	# EN: Assign annotated value to browser_session.
	# JP: browser_session に型付きの値を代入する。
	browser_session: BrowserSession | None = None

	# Current page URL for filtering and context
	# EN: Assign annotated value to page_url.
	# JP: page_url に型付きの値を代入する。
	page_url: str | None = None

	# CDP client for direct Chrome DevTools Protocol access
	# EN: Assign annotated value to cdp_client.
	# JP: cdp_client に型付きの値を代入する。
	cdp_client: Any | None = None  # CDPClient type from cdp_use

	# extra injected config if the action asks for these arg names
	# EN: Assign annotated value to page_extraction_llm.
	# JP: page_extraction_llm に型付きの値を代入する。
	page_extraction_llm: BaseChatModel | None = None
	# EN: Assign annotated value to file_system.
	# JP: file_system に型付きの値を代入する。
	file_system: FileSystem | None = None
	# EN: Assign annotated value to available_file_paths.
	# JP: available_file_paths に型付きの値を代入する。
	available_file_paths: list[str] | None = None
	# EN: Assign annotated value to has_sensitive_data.
	# JP: has_sensitive_data に型付きの値を代入する。
	has_sensitive_data: bool = False
	# EN: Assign annotated value to scratchpad.
	# JP: scratchpad に型付きの値を代入する。
	scratchpad: Scratchpad | None = None

	# EN: Define function `get_browser_requiring_params`.
	# JP: 関数 `get_browser_requiring_params` を定義する。
	@classmethod
	def get_browser_requiring_params(cls) -> set[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get parameter names that require browser_session"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {'browser_session', 'cdp_client', 'page_url'}

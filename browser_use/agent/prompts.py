# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import importlib.resources
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from datetime import datetime
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, Literal, Optional

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import NodeType, SimplifiedNode
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import ContentPartImageParam, ContentPartTextParam, ImageURL, SystemMessage, UserMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe_debug
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import is_new_tab_page

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.agent.views import AgentStepInfo
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser.views import BrowserStateSummary
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.filesystem.file_system import FileSystem


# EN: Define class `SystemPrompt`.
# JP: クラス `SystemPrompt` を定義する。
class SystemPrompt:
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		action_description: str,
		max_actions_per_step: int = 10,
		override_system_message: str | None = None,
		extend_system_message: str | None = None,
		use_thinking: bool = True,
		flash_mode: bool = False,
	):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.default_action_description = action_description
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.max_actions_per_step = max_actions_per_step
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.use_thinking = use_thinking
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.flash_mode = flash_mode
		# EN: Assign value to now.
		# JP: now に値を代入する。
		now = datetime.now().astimezone()
		# EN: Assign value to weekday_ja.
		# JP: weekday_ja に値を代入する。
		weekday_ja = '月火水木金土日'[now.weekday()]
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.current_datetime_line = (
			f'{now.strftime("%Y-%m-%d %H:%M %Z (UTC%z, %A)")}'
			f' / ローカル日時: {now.strftime("%Y年%m月%d日")}({weekday_ja}) {now.strftime("%H時%M分")} {now.strftime("%Z")}'
		)
		# EN: Assign value to prompt.
		# JP: prompt に値を代入する。
		prompt = ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if override_system_message:
			# EN: Assign value to prompt.
			# JP: prompt に値を代入する。
			prompt = override_system_message
		else:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._load_prompt_template()
			# EN: Assign value to prompt.
			# JP: prompt に値を代入する。
			prompt = self.prompt_template.format(
				max_actions=self.max_actions_per_step,
				current_datetime=self.current_datetime_line,
			)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if extend_system_message:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			prompt += f'\n{extend_system_message}'

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.system_message = SystemMessage(content=prompt, cache=True)

	# EN: Define function `_load_prompt_template`.
	# JP: 関数 `_load_prompt_template` を定義する。
	def _load_prompt_template(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Load the prompt template from the markdown file."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Choose the appropriate template based on flash_mode and use_thinking settings
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.flash_mode:
				# EN: Assign value to template_filename.
				# JP: template_filename に値を代入する。
				template_filename = 'system_prompt_flash.md'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif self.use_thinking:
				# EN: Assign value to template_filename.
				# JP: template_filename に値を代入する。
				template_filename = 'system_prompt.md'
			else:
				# EN: Assign value to template_filename.
				# JP: template_filename に値を代入する。
				template_filename = 'system_prompt_no_thinking.md'

			# This works both in development and when installed as a package
			# EN: Execute logic with managed resources.
			# JP: リソース管理付きで処理を実行する。
			with importlib.resources.files('browser_use.agent').joinpath(template_filename).open('r', encoding='utf-8') as f:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				self.prompt_template = f.read()
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError(f'Failed to load system prompt template: {e}')

	# EN: Define function `get_system_message`.
	# JP: 関数 `get_system_message` を定義する。
	def get_system_message(self) -> SystemMessage:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Get the system prompt for the agent.

		Returns:
		    SystemMessage: Formatted system prompt
		"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.system_message


# Functions:
# {self.default_action_description}

# Example:
# {self.example_response()}
# Your AVAILABLE ACTIONS:
# {self.default_action_description}


# EN: Define class `AgentMessagePrompt`.
# JP: クラス `AgentMessagePrompt` を定義する。
class AgentMessagePrompt:
	# EN: Assign annotated value to vision_detail_level.
	# JP: vision_detail_level に型付きの値を代入する。
	vision_detail_level: Literal['auto', 'low', 'high']

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		browser_state_summary: 'BrowserStateSummary',
		file_system: 'FileSystem',
		agent_history_description: str | None = None,
		read_state_description: str | None = None,
		task: str | None = None,
		include_attributes: list[str] | None = None,
		step_info: Optional['AgentStepInfo'] = None,
		page_filtered_actions: str | None = None,
		max_clickable_elements_length: int = 40000,
		sensitive_data: str | None = None,
		available_file_paths: list[str] | None = None,
		screenshots: list[str] | None = None,
		vision_detail_level: Literal['auto', 'low', 'high'] = 'auto',
		include_recent_events: bool = False,
		sample_images: list[ContentPartTextParam | ContentPartImageParam] | None = None,
	):
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.browser_state: 'BrowserStateSummary' = browser_state_summary
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.file_system: 'FileSystem | None' = file_system
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.agent_history_description: str | None = agent_history_description
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.read_state_description: str | None = read_state_description
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.task: str | None = task
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.include_attributes = include_attributes
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.step_info = step_info
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.page_filtered_actions: str | None = page_filtered_actions
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.max_clickable_elements_length: int = max_clickable_elements_length
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.sensitive_data: str | None = sensitive_data
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self.available_file_paths: list[str] | None = available_file_paths
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.screenshots = screenshots or []
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.vision_detail_level = vision_detail_level
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.include_recent_events = include_recent_events
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.sample_images = sample_images or []
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert self.browser_state

	# EN: Define function `_extract_page_statistics`.
	# JP: 関数 `_extract_page_statistics` を定義する。
	def _extract_page_statistics(self) -> dict[str, int]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract high-level page statistics from DOM tree for LLM context"""
		# EN: Assign value to stats.
		# JP: stats に値を代入する。
		stats = {
			'links': 0,
			'iframes': 0,
			'shadow_open': 0,
			'shadow_closed': 0,
			'scroll_containers': 0,
			'images': 0,
			'interactive_elements': 0,
			'total_elements': 0,
		}

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self.browser_state.dom_state or not self.browser_state.dom_state._root:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return stats

		# EN: Define function `traverse_node`.
		# JP: 関数 `traverse_node` を定義する。
		def traverse_node(node: SimplifiedNode) -> None:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Recursively traverse simplified DOM tree to count elements"""
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not node or not node.original_node:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return

			# EN: Assign value to original.
			# JP: original に値を代入する。
			original = node.original_node
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			stats['total_elements'] += 1

			# Count by node type and tag
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if original.node_type == NodeType.ELEMENT_NODE:
				# EN: Assign value to tag.
				# JP: tag に値を代入する。
				tag = original.tag_name.lower() if original.tag_name else ''

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if tag == 'a':
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					stats['links'] += 1
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif tag in ('iframe', 'frame'):
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					stats['iframes'] += 1
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif tag == 'img':
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					stats['images'] += 1

				# Check if scrollable
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if original.is_actually_scrollable:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					stats['scroll_containers'] += 1

				# Check if interactive
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node.interactive_index is not None:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					stats['interactive_elements'] += 1

				# Check if this element hosts shadow DOM
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node.is_shadow_host:
					# Check if any shadow children are closed
					# EN: Assign value to has_closed_shadow.
					# JP: has_closed_shadow に値を代入する。
					has_closed_shadow = any(
						child.original_node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE
						and child.original_node.shadow_root_type
						and child.original_node.shadow_root_type.lower() == 'closed'
						for child in node.children
					)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if has_closed_shadow:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						stats['shadow_closed'] += 1
					else:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						stats['shadow_open'] += 1

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif original.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
				# Shadow DOM fragment - these are the actual shadow roots
				# But don't double-count since we count them at the host level above
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass

			# Traverse children
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for child in node.children:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				traverse_node(child)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		traverse_node(self.browser_state.dom_state._root)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return stats

	# EN: Define function `_get_browser_state_description`.
	# JP: 関数 `_get_browser_state_description` を定義する。
	@observe_debug(ignore_input=True, ignore_output=True, name='_get_browser_state_description')
	def _get_browser_state_description(self) -> str:
		# Extract page statistics first
		# EN: Assign value to page_stats.
		# JP: page_stats に値を代入する。
		page_stats = self._extract_page_statistics()

		# Format statistics for LLM
		# EN: Assign value to stats_text.
		# JP: stats_text に値を代入する。
		stats_text = '<page_stats>'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if page_stats['total_elements'] < 10:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			stats_text += 'Page appears empty (SPA not loaded?) - '
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		stats_text += f'{page_stats["links"]} links, {page_stats["interactive_elements"]} interactive, '
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		stats_text += f'{page_stats["iframes"]} iframes, {page_stats["scroll_containers"]} scroll containers'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if page_stats['shadow_open'] > 0 or page_stats['shadow_closed'] > 0:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			stats_text += f', {page_stats["shadow_open"]} shadow(open), {page_stats["shadow_closed"]} shadow(closed)'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if page_stats['images'] > 0:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			stats_text += f', {page_stats["images"]} images'
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		stats_text += f', {page_stats["total_elements"]} total elements'
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		stats_text += '</page_stats>\n\n'

		# EN: Assign value to elements_text.
		# JP: elements_text に値を代入する。
		elements_text = self.browser_state.dom_state.llm_representation(include_attributes=self.include_attributes)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(elements_text) > self.max_clickable_elements_length:
			# EN: Assign value to elements_text.
			# JP: elements_text に値を代入する。
			elements_text = elements_text[: self.max_clickable_elements_length]
			# EN: Assign value to truncated_text.
			# JP: truncated_text に値を代入する。
			truncated_text = f' (truncated to {self.max_clickable_elements_length} characters)'
		else:
			# EN: Assign value to truncated_text.
			# JP: truncated_text に値を代入する。
			truncated_text = ''

		# EN: Assign value to has_content_above.
		# JP: has_content_above に値を代入する。
		has_content_above = False
		# EN: Assign value to has_content_below.
		# JP: has_content_below に値を代入する。
		has_content_below = False
		# Enhanced page information for the model
		# EN: Assign value to page_info_text.
		# JP: page_info_text に値を代入する。
		page_info_text = ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_state.page_info:
			# EN: Assign value to pi.
			# JP: pi に値を代入する。
			pi = self.browser_state.page_info
			# Compute page statistics dynamically
			# EN: Assign value to pages_above.
			# JP: pages_above に値を代入する。
			pages_above = pi.pixels_above / pi.viewport_height if pi.viewport_height > 0 else 0
			# EN: Assign value to pages_below.
			# JP: pages_below に値を代入する。
			pages_below = pi.pixels_below / pi.viewport_height if pi.viewport_height > 0 else 0
			# EN: Assign value to has_content_above.
			# JP: has_content_above に値を代入する。
			has_content_above = pages_above > 0
			# EN: Assign value to has_content_below.
			# JP: has_content_below に値を代入する。
			has_content_below = pages_below > 0
			# EN: Assign value to total_pages.
			# JP: total_pages に値を代入する。
			total_pages = pi.page_height / pi.viewport_height if pi.viewport_height > 0 else 0
			# EN: Assign value to current_page_position.
			# JP: current_page_position に値を代入する。
			current_page_position = pi.scroll_y / max(pi.page_height - pi.viewport_height, 1)
			# EN: Assign value to page_info_text.
			# JP: page_info_text に値を代入する。
			page_info_text = '<page_info>'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			page_info_text += f'{pages_above:.1f} pages above, '
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			page_info_text += f'{pages_below:.1f} pages below, '
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			page_info_text += f'{total_pages:.1f} total pages'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			page_info_text += '</page_info>\n'
			# , at {current_page_position:.0%} of page
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if elements_text != '':
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if has_content_above:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.browser_state.page_info:
					# EN: Assign value to pi.
					# JP: pi に値を代入する。
					pi = self.browser_state.page_info
					# EN: Assign value to pages_above.
					# JP: pages_above に値を代入する。
					pages_above = pi.pixels_above / pi.viewport_height if pi.viewport_height > 0 else 0
					# EN: Assign value to elements_text.
					# JP: elements_text に値を代入する。
					elements_text = f'... {pages_above:.1f} pages above - scroll to see more or extract structured data if you are looking for specific information ...\n{elements_text}'
			else:
				# EN: Assign value to elements_text.
				# JP: elements_text に値を代入する。
				elements_text = f'[Start of page]\n{elements_text}'
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if has_content_below:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if self.browser_state.page_info:
					# EN: Assign value to pi.
					# JP: pi に値を代入する。
					pi = self.browser_state.page_info
					# EN: Assign value to pages_below.
					# JP: pages_below に値を代入する。
					pages_below = pi.pixels_below / pi.viewport_height if pi.viewport_height > 0 else 0
					# EN: Assign value to elements_text.
					# JP: elements_text に値を代入する。
					elements_text = f'{elements_text}\n... {pages_below:.1f} pages below - scroll to see more or extract structured data if you are looking for specific information ...'
			else:
				# EN: Assign value to elements_text.
				# JP: elements_text に値を代入する。
				elements_text = f'{elements_text}\n[End of page]'
		else:
			# EN: Assign value to elements_text.
			# JP: elements_text に値を代入する。
			elements_text = 'empty page'

		# EN: Assign value to tabs_text.
		# JP: tabs_text に値を代入する。
		tabs_text = ''
		# EN: Assign value to current_tab_candidates.
		# JP: current_tab_candidates に値を代入する。
		current_tab_candidates = []

		# Find tabs that match both URL and title to identify current tab more reliably
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for tab in self.browser_state.tabs:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if tab.url == self.browser_state.url and tab.title == self.browser_state.title:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				current_tab_candidates.append(tab.target_id)

		# If we have exactly one match, mark it as current
		# Otherwise, don't mark any tab as current to avoid confusion
		# EN: Assign value to current_target_id.
		# JP: current_target_id に値を代入する。
		current_target_id = current_tab_candidates[0] if len(current_tab_candidates) == 1 else None

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for tab in self.browser_state.tabs:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			tabs_text += f'Tab {tab.target_id[-4:]}: {tab.url} - {tab.title[:30]}\n'

		# EN: Assign value to current_tab_text.
		# JP: current_tab_text に値を代入する。
		current_tab_text = f'Current tab: {current_target_id[-4:]}' if current_target_id is not None else ''

		# Check if current page is a PDF viewer and add appropriate message
		# EN: Assign value to pdf_message.
		# JP: pdf_message に値を代入する。
		pdf_message = ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.browser_state.is_pdf_viewer:
			# EN: Assign value to pdf_message.
			# JP: pdf_message に値を代入する。
			pdf_message = 'PDF viewer cannot be rendered. In this page, DO NOT use the extract_structured_data action as PDF content cannot be rendered. Use the read_file action on the downloaded PDF in available_file_paths to read the full content.\n\n'

		# Add recent events if available and requested
		# EN: Assign value to recent_events_text.
		# JP: recent_events_text に値を代入する。
		recent_events_text = ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.include_recent_events and self.browser_state.recent_events:
			# EN: Assign value to recent_events_text.
			# JP: recent_events_text に値を代入する。
			recent_events_text = f'Recent browser events: {self.browser_state.recent_events}\n'

		# EN: Assign value to browser_state.
		# JP: browser_state に値を代入する。
		browser_state = f"""{stats_text}{current_tab_text}
Available tabs:
{tabs_text}
{page_info_text}
{recent_events_text}{pdf_message}Elements you can interact with inside the viewport{truncated_text}:
{elements_text}
"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return browser_state

	# EN: Define function `_get_current_datetime_line`.
	# JP: 関数 `_get_current_datetime_line` を定義する。
	def _get_current_datetime_line(self) -> str:
		# EN: Assign value to now.
		# JP: now に値を代入する。
		now = datetime.now().astimezone()
		# EN: Assign value to weekday_ja.
		# JP: weekday_ja に値を代入する。
		weekday_ja = '月火水木金土日'[now.weekday()]
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (
			f'{now.strftime("%Y-%m-%d %H:%M %Z (UTC%z, %A)")}'
			f' / ローカル日時: {now.strftime("%Y年%m月%d日")}({weekday_ja}) {now.strftime("%H時%M分")} {now.strftime("%Z")}'
		)

	# EN: Define function `_get_agent_state_description`.
	# JP: 関数 `_get_agent_state_description` を定義する。
	def _get_agent_state_description(self) -> str:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.step_info:
			# EN: Assign value to step_info_description.
			# JP: step_info_description に値を代入する。
			step_info_description = f'Step {self.step_info.step_number + 1}. Maximum steps: {self.step_info.max_steps}\n'
		else:
			# EN: Assign value to step_info_description.
			# JP: step_info_description に値を代入する。
			step_info_description = ''

		# EN: Assign value to current_datetime_line.
		# JP: current_datetime_line に値を代入する。
		current_datetime_line = self._get_current_datetime_line()
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		step_info_description += f'Current datetime (authoritative): {current_datetime_line}'

		# EN: Assign value to _todo_contents.
		# JP: _todo_contents に値を代入する。
		_todo_contents = self.file_system.get_todo_contents() if self.file_system else ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not len(_todo_contents):
			# EN: Assign value to _todo_contents.
			# JP: _todo_contents に値を代入する。
			_todo_contents = '[Current todo.md is empty, fill it with your plan when applicable]'

		# EN: Assign value to agent_state.
		# JP: agent_state に値を代入する。
		agent_state = f"""
<current_datetime>
{current_datetime_line}
</current_datetime>
<user_request>
{self.task}
</user_request>
<file_system>
{self.file_system.describe() if self.file_system else 'No file system available'}
</file_system>
<todo_contents>
{_todo_contents}
</todo_contents>
"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.sensitive_data:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			agent_state += f'<sensitive_data>\n{self.sensitive_data}\n</sensitive_data>\n'

		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		agent_state += f'<step_info>\n{step_info_description}\n</step_info>\n'
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.available_file_paths:
			# EN: Assign value to available_file_paths_text.
			# JP: available_file_paths_text に値を代入する。
			available_file_paths_text = '\n'.join(self.available_file_paths)
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			agent_state += f'<available_file_paths>\n{available_file_paths_text}\nUse absolute full paths when referencing these files.\n</available_file_paths>\n'
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return agent_state

	# EN: Define function `get_user_message`.
	# JP: 関数 `get_user_message` を定義する。
	@observe_debug(ignore_input=True, ignore_output=True, name='get_user_message')
	def get_user_message(self, use_vision: bool = True) -> UserMessage:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get complete state as a single cached message"""
		# Don't pass screenshot to model if page is a new tab page, step is 0, and there's only one tab
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if (
			is_new_tab_page(self.browser_state.url)
			and self.step_info is not None
			and self.step_info.step_number == 0
			and len(self.browser_state.tabs) == 1
		):
			# EN: Assign value to use_vision.
			# JP: use_vision に値を代入する。
			use_vision = False

		# Build complete state description
		# EN: Assign value to state_description.
		# JP: state_description に値を代入する。
		state_description = (
			'<agent_history>\n'
			+ (self.agent_history_description.strip('\n') if self.agent_history_description else '')
			+ '\n</agent_history>\n\n'
		)
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		state_description += '<agent_state>\n' + self._get_agent_state_description().strip('\n') + '\n</agent_state>\n'
		# EN: Update variable with augmented assignment.
		# JP: 複合代入で変数を更新する。
		state_description += '<browser_state>\n' + self._get_browser_state_description().strip('\n') + '\n</browser_state>\n'
		# Only add read_state if it has content
		# EN: Assign value to read_state_description.
		# JP: read_state_description に値を代入する。
		read_state_description = self.read_state_description.strip('\n').strip() if self.read_state_description else ''
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if read_state_description:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			state_description += '<read_state>\n' + read_state_description + '\n</read_state>\n'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.page_filtered_actions:
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			state_description += '<page_specific_actions>\n'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			state_description += self.page_filtered_actions + '\n'
			# EN: Update variable with augmented assignment.
			# JP: 複合代入で変数を更新する。
			state_description += '</page_specific_actions>\n'

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if use_vision is True and self.screenshots:
			# Start with text description
			# EN: Assign annotated value to content_parts.
			# JP: content_parts に型付きの値を代入する。
			content_parts: list[ContentPartTextParam | ContentPartImageParam] = [ContentPartTextParam(text=state_description)]

			# Add sample images
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			content_parts.extend(self.sample_images)

			# Add screenshots with labels
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, screenshot in enumerate(self.screenshots):
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if i == len(self.screenshots) - 1:
					# EN: Assign value to label.
					# JP: label に値を代入する。
					label = 'Current screenshot:'
				else:
					# Use simple, accurate labeling since we don't have actual step timing info
					# EN: Assign value to label.
					# JP: label に値を代入する。
					label = 'Previous screenshot:'

				# Add label as text content
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_parts.append(ContentPartTextParam(text=label))

				# Add the screenshot
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				content_parts.append(
					ContentPartImageParam(
						image_url=ImageURL(
							url=f'data:image/png;base64,{screenshot}',
							media_type='image/png',
							detail=self.vision_detail_level,
						),
					)
				)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return UserMessage(content=content_parts, cache=True)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return UserMessage(content=state_description, cache=True)

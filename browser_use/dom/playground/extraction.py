# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import anyio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pyperclip
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import tiktoken

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.prompts import AgentMessagePrompt
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser import BrowserProfile, BrowserSession
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.events import ClickElementEvent, TypeTextEvent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.profile import ViewportSize
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.service import DomService
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import DEFAULT_INCLUDE_ATTRIBUTES
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystem

# EN: Assign value to TIMEOUT.
# JP: TIMEOUT に値を代入する。
TIMEOUT = 60


# EN: Define async function `test_focus_vs_all_elements`.
# JP: 非同期関数 `test_focus_vs_all_elements` を定義する。
async def test_focus_vs_all_elements():
	# EN: Assign value to browser_session.
	# JP: browser_session に値を代入する。
	browser_session = BrowserSession(
		browser_profile=BrowserProfile(
			# executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
			window_size=ViewportSize(width=1100, height=1000),
			disable_security=False,
			wait_for_network_idle_page_load_time=1,
			headless=False,
			args=['--incognito'],
			paint_order_filtering=True,
		),
	)

	# 10 Sample websites with various interactive elements
	# EN: Assign value to sample_websites.
	# JP: sample_websites に値を代入する。
	sample_websites = [
		'https://www.google.com/travel/flights',
		'https://v0-simple-ui-test-site.vercel.app',
		'https://browser-use.github.io/stress-tests/challenges/iframe-inception-level1.html',
		'https://browser-use.github.io/stress-tests/challenges/angular-form.html',
		'https://www.google.com/travel/flights',
		'https://www.amazon.com/s?k=laptop',
		'https://github.com/trending',
		'https://www.reddit.com',
		'https://www.ycombinator.com/companies',
		'https://www.kayak.com/flights',
		'https://www.booking.com',
		'https://www.airbnb.com',
		'https://www.linkedin.com/jobs',
		'https://stackoverflow.com/questions',
	]

	# 5 Difficult websites with complex elements (iframes, canvas, dropdowns, etc.)
	# EN: Assign value to difficult_websites.
	# JP: difficult_websites に値を代入する。
	difficult_websites = [
		'https://www.w3schools.com/html/tryit.asp?filename=tryhtml_iframe',  # Nested iframes
		'https://semantic-ui.com/modules/dropdown.html',  # Complex dropdowns
		'https://www.dezlearn.com/nested-iframes-example/',  # Cross-origin nested iframes
		'https://codepen.io/towc/pen/mJzOWJ',  # Canvas elements with interactions
		'https://jqueryui.com/accordion/',  # Complex accordion/dropdown widgets
		'https://v0-simple-landing-page-seven-xi.vercel.app/',  # Simple landing page with iframe
		'https://www.unesco.org/en',
	]

	# Descriptions for difficult websites
	# EN: Assign value to difficult_descriptions.
	# JP: difficult_descriptions に値を代入する。
	difficult_descriptions = {
		'https://www.w3schools.com/html/tryit.asp?filename=tryhtml_iframe': '🔸 NESTED IFRAMES: Multiple iframe layers',
		'https://semantic-ui.com/modules/dropdown.html': '🔸 COMPLEX DROPDOWNS: Custom dropdown components',
		'https://www.dezlearn.com/nested-iframes-example/': '🔸 CROSS-ORIGIN IFRAMES: Different domain iframes',
		'https://codepen.io/towc/pen/mJzOWJ': '🔸 CANVAS ELEMENTS: Interactive canvas graphics',
		'https://jqueryui.com/accordion/': '🔸 ACCORDION WIDGETS: Collapsible content sections',
	}

	# EN: Assign value to websites.
	# JP: websites に値を代入する。
	websites = sample_websites + difficult_websites
	# EN: Assign value to current_website_index.
	# JP: current_website_index に値を代入する。
	current_website_index = 0

	# EN: Define function `get_website_list_for_prompt`.
	# JP: 関数 `get_website_list_for_prompt` を定義する。
	def get_website_list_for_prompt() -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get a compact website list for the input prompt."""
		# EN: Assign value to lines.
		# JP: lines に値を代入する。
		lines = []
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		lines.append('📋 Websites:')

		# Sample websites (1-10)
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, site in enumerate(sample_websites, 1):
			# EN: Assign value to current_marker.
			# JP: current_marker に値を代入する。
			current_marker = ' ←' if (i - 1) == current_website_index else ''
			# EN: Assign value to domain.
			# JP: domain に値を代入する。
			domain = site.replace('https://', '').split('/')[0]
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(f'  {i:2d}.{domain[:15]:<15}{current_marker}')

		# Difficult websites (11-15)
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, site in enumerate(difficult_websites, len(sample_websites) + 1):
			# EN: Assign value to current_marker.
			# JP: current_marker に値を代入する。
			current_marker = ' ←' if (i - 1) == current_website_index else ''
			# EN: Assign value to domain.
			# JP: domain に値を代入する。
			domain = site.replace('https://', '').split('/')[0]
			# EN: Assign value to desc.
			# JP: desc に値を代入する。
			desc = difficult_descriptions.get(site, '')
			# EN: Assign value to challenge.
			# JP: challenge に値を代入する。
			challenge = desc.split(': ')[1][:15] if ': ' in desc else ''
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			lines.append(f'  {i:2d}.{domain[:15]:<15} ({challenge}){current_marker}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return '\n'.join(lines)

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	await browser_session.start()

	# Show startup info
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('\n🌐 BROWSER-USE DOM EXTRACTION TESTER')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print(f'📊 {len(websites)} websites total: {len(sample_websites)} standard + {len(difficult_websites)} complex')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('🔧 Controls: Type 1-15 to jump | Enter to re-run | "n" next | "q" quit')
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	print('💾 Outputs: tmp/user_message.txt & tmp/element_tree.json\n')

	# EN: Assign value to dom_service.
	# JP: dom_service に値を代入する。
	dom_service = DomService(browser_session)

	# EN: Repeat logic while a condition is true.
	# JP: 条件が真の間、処理を繰り返す。
	while True:
		# Cycle through websites
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if current_website_index >= len(websites):
			# EN: Assign value to current_website_index.
			# JP: current_website_index に値を代入する。
			current_website_index = 0
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('Cycled back to first website!')

		# EN: Assign value to website.
		# JP: website に値を代入する。
		website = websites[current_website_index]
		# sleep 2
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await browser_session._cdp_navigate(website)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		await asyncio.sleep(1)

		# EN: Assign value to last_clicked_index.
		# JP: last_clicked_index に値を代入する。
		last_clicked_index = None  # Track the index for text input
		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while True:
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# 	all_elements_state = await dom_service.get_serialized_dom_tree()

				# EN: Assign value to website_type.
				# JP: website_type に値を代入する。
				website_type = 'DIFFICULT' if website in difficult_websites else 'SAMPLE'
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print(f'\n{"=" * 60}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print(f'[{current_website_index + 1}/{len(websites)}] [{website_type}] Testing: {website}')
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if website in difficult_descriptions:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					print(f'{difficult_descriptions[website]}')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print(f'{"=" * 60}')

				# Get/refresh the state (includes removing old highlights)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('\nGetting page state...')

				# EN: Assign value to start_time.
				# JP: start_time に値を代入する。
				start_time = time.time()
				# EN: Assign value to all_elements_state.
				# JP: all_elements_state に値を代入する。
				all_elements_state = await browser_session.get_browser_state_summary(True)
				# EN: Assign value to end_time.
				# JP: end_time に値を代入する。
				end_time = time.time()
				# EN: Assign value to get_state_time.
				# JP: get_state_time に値を代入する。
				get_state_time = end_time - start_time
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print(f'get_state_summary took {get_state_time:.2f} seconds')

				# Get detailed timing info from DOM service
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('\nGetting detailed DOM timing...')
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				serialized_state, _, timing_info = await dom_service.get_serialized_dom_tree()

				# Combine all timing info
				# EN: Assign value to all_timing.
				# JP: all_timing に値を代入する。
				all_timing = {'get_state_summary_total': get_state_time, **timing_info}

				# EN: Assign value to selector_map.
				# JP: selector_map に値を代入する。
				selector_map = all_elements_state.dom_state.selector_map
				# EN: Assign value to total_elements.
				# JP: total_elements に値を代入する。
				total_elements = len(selector_map.keys())
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print(f'Total number of elements: {total_elements}')

				# print(all_elements_state.element_tree.clickable_elements_to_string())
				# EN: Assign value to prompt.
				# JP: prompt に値を代入する。
				prompt = AgentMessagePrompt(
					browser_state_summary=all_elements_state,
					file_system=FileSystem(base_dir='./tmp'),
					include_attributes=DEFAULT_INCLUDE_ATTRIBUTES,
					step_info=None,
				)
				# Write the user message to a file for analysis
				# EN: Assign value to user_message.
				# JP: user_message に値を代入する。
				user_message = prompt.get_user_message(use_vision=False).text

				# clickable_elements_str = all_elements_state.element_tree.clickable_elements_to_string()

				# EN: Assign value to text_to_save.
				# JP: text_to_save に値を代入する。
				text_to_save = user_message

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				os.makedirs('./tmp', exist_ok=True)
				# EN: Execute async logic with managed resources.
				# JP: リソース管理付きで非同期処理を実行する。
				async with await anyio.open_file('./tmp/user_message.txt', 'w', encoding='utf-8') as f:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await f.write(text_to_save)

				# save pure clickable elements to a file
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if all_elements_state.dom_state._root:
					# EN: Execute async logic with managed resources.
					# JP: リソース管理付きで非同期処理を実行する。
					async with await anyio.open_file('./tmp/simplified_element_tree.json', 'w', encoding='utf-8') as f:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await f.write(json.dumps(all_elements_state.dom_state._root.__json__(), indent=2))

					# EN: Execute async logic with managed resources.
					# JP: リソース管理付きで非同期処理を実行する。
					async with await anyio.open_file('./tmp/original_element_tree.json', 'w', encoding='utf-8') as f:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						await f.write(json.dumps(all_elements_state.dom_state._root.original_node.__json__(), indent=2))

				# copy the user message to the clipboard
				# pyperclip.copy(text_to_save)

				# EN: Assign value to encoding.
				# JP: encoding に値を代入する。
				encoding = tiktoken.encoding_for_model('gpt-4o')
				# EN: Assign value to token_count.
				# JP: token_count に値を代入する。
				token_count = len(encoding.encode(text_to_save))
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print(f'Token count: {token_count}')

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('User message written to ./tmp/user_message.txt')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('Element tree written to ./tmp/simplified_element_tree.json')
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('Original element tree written to ./tmp/original_element_tree.json')

				# Save timing information
				# EN: Assign value to timing_text.
				# JP: timing_text に値を代入する。
				timing_text = '🔍 DOM EXTRACTION PERFORMANCE ANALYSIS\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				timing_text += f'{"=" * 50}\n\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				timing_text += f'📄 Website: {website}\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				timing_text += f'📊 Total Elements: {total_elements}\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				timing_text += f'🎯 Token Count: {token_count}\n\n'

				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				timing_text += '⏱️  TIMING BREAKDOWN:\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				timing_text += f'{"─" * 30}\n'
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for key, value in all_timing.items():
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					timing_text += f'{key:<35}: {value * 1000:>8.2f} ms\n'

				# Calculate percentages
				# EN: Assign value to total_time.
				# JP: total_time に値を代入する。
				total_time = all_timing.get('get_state_summary_total', 0)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if total_time > 0 and total_elements > 0:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					timing_text += '\n📈 PERCENTAGE BREAKDOWN:\n'
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					timing_text += f'{"─" * 30}\n'
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for key, value in all_timing.items():
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if key != 'get_state_summary_total':
							# EN: Assign value to percentage.
							# JP: percentage に値を代入する。
							percentage = (value / total_time) * 100
							# EN: Update variable with augmented assignment.
							# JP: 複合代入で変数を更新する。
							timing_text += f'{key:<35}: {percentage:>7.1f}%\n'

				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				timing_text += '\n🎯 CLICKABLE DETECTION ANALYSIS:\n'
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				timing_text += f'{"─" * 35}\n'
				# EN: Assign value to clickable_time.
				# JP: clickable_time に値を代入する。
				clickable_time = all_timing.get('clickable_detection_time', 0)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if clickable_time > 0 and total_elements > 0:
					# EN: Assign value to avg_per_element.
					# JP: avg_per_element に値を代入する。
					avg_per_element = (clickable_time / total_elements) * 1000000  # microseconds
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					timing_text += f'Total clickable detection time: {clickable_time * 1000:.2f} ms\n'
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					timing_text += f'Average per element: {avg_per_element:.2f} μs\n'
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					timing_text += f'Clickable detection calls: ~{total_elements} (approx)\n'

				# EN: Execute async logic with managed resources.
				# JP: リソース管理付きで非同期処理を実行する。
				async with await anyio.open_file('./tmp/timing_analysis.txt', 'w', encoding='utf-8') as f:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					await f.write(timing_text)

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print('Timing analysis written to ./tmp/timing_analysis.txt')

				# also save all_elements_state.element_tree.clickable_elements_to_string() to a file
				# with open('./tmp/clickable_elements.json', 'w', encoding='utf-8') as f:
				# 	f.write(json.dumps(all_elements_state.element_tree.__json__(), indent=2))
				# print('Clickable elements written to ./tmp/clickable_elements.json')

				# EN: Assign value to website_list.
				# JP: website_list に値を代入する。
				website_list = get_website_list_for_prompt()
				# EN: Assign value to answer.
				# JP: answer に値を代入する。
				answer = input(
					"🎮 Enter: element index | 'index' click (clickable) | 'index,text' input | 'c,index' copy | Enter re-run | 'n' next | 'q' quit: "
				)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if answer.lower() == 'q':
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return  # Exit completely
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif answer.lower() == 'n':
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					print('Moving to next website...')
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					current_website_index += 1
					# EN: Exit the current loop.
					# JP: 現在のループを終了する。
					break  # Break inner loop to go to next website
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif answer.strip() == '':
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					print('Re-running extraction on current page state...')
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue  # Continue inner loop to re-extract DOM without reloading page
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif answer.strip().isdigit():
					# Click element format: index
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# EN: Assign value to clicked_index.
						# JP: clicked_index に値を代入する。
						clicked_index = int(answer)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if clicked_index in selector_map:
							# EN: Assign value to element_node.
							# JP: element_node に値を代入する。
							element_node = selector_map[clicked_index]
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							print(f'Clicking element {clicked_index}: {element_node.tag_name}')
							# EN: Assign value to event.
							# JP: event に値を代入する。
							event = browser_session.event_bus.dispatch(ClickElementEvent(node=element_node))
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							await event
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							print('Click successful.')
					except ValueError:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						print(f"Invalid input: '{answer}'. Enter an index, 'index,text', 'c,index', or 'q'.")
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if answer.lower().startswith('c,'):
						# Copy element JSON format: c,index
						# EN: Assign value to parts.
						# JP: parts に値を代入する。
						parts = answer.split(',', 1)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if len(parts) == 2:
							# EN: Handle exceptions around this block.
							# JP: このブロックで例外処理を行う。
							try:
								# EN: Assign value to target_index.
								# JP: target_index に値を代入する。
								target_index = int(parts[1].strip())
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if target_index in selector_map:
									# EN: Assign value to element_node.
									# JP: element_node に値を代入する。
									element_node = selector_map[target_index]
									# EN: Assign value to element_json.
									# JP: element_json に値を代入する。
									element_json = json.dumps(element_node.__json__(), indent=2, default=str)
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									pyperclip.copy(element_json)
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									print(f'Copied element {target_index} JSON to clipboard: {element_node.tag_name}')
								else:
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									print(f'Invalid index: {target_index}')
							except ValueError:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								print(f'Invalid index format: {parts[1]}')
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							print("Invalid input format. Use 'c,index'.")
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif ',' in answer:
						# Input text format: index,text
						# EN: Assign value to parts.
						# JP: parts に値を代入する。
						parts = answer.split(',', 1)
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if len(parts) == 2:
							# EN: Handle exceptions around this block.
							# JP: このブロックで例外処理を行う。
							try:
								# EN: Assign value to target_index.
								# JP: target_index に値を代入する。
								target_index = int(parts[0].strip())
								# EN: Assign value to text_to_input.
								# JP: text_to_input に値を代入する。
								text_to_input = parts[1]
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if target_index in selector_map:
									# EN: Assign value to element_node.
									# JP: element_node に値を代入する。
									element_node = selector_map[target_index]
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									print(
										f"Inputting text '{text_to_input}' into element {target_index}: {element_node.tag_name}"
									)

									# EN: Assign value to event.
									# JP: event に値を代入する。
									event = await browser_session.event_bus.dispatch(
										TypeTextEvent(node=element_node, text=text_to_input)
									)

									# EN: Evaluate an expression.
									# JP: 式を評価する。
									print('Input successful.')
								else:
									# EN: Evaluate an expression.
									# JP: 式を評価する。
									print(f'Invalid index: {target_index}')
							except ValueError:
								# EN: Evaluate an expression.
								# JP: 式を評価する。
								print(f'Invalid index format: {parts[0]}')
						else:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							print("Invalid input format. Use 'index,text'.")

				except Exception as action_e:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					print(f'Action failed: {action_e}')

			# No explicit highlight removal here, get_state handles it at the start of the loop

			except Exception as e:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				print(f'Error in loop: {e}')
				# Optionally add a small delay before retrying
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await asyncio.sleep(1)


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(test_focus_vs_all_elements())
	# asyncio.run(test_process_html_file()) # Commented out the other test

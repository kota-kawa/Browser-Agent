# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import time

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import aiofiles

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser import BrowserProfile, BrowserSession
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.types import ViewportSize
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.service import DomService
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import EnhancedDOMTreeNode


# EN: Define async function `main`.
# JP: 非同期関数 `main` を定義する。
async def main():
	# async with async_playwright() as p:
	# 	playwright_browser = await p.chromium.launch(args=['--remote-debugging-port=9222'], headless=False)
	# EN: Assign value to browser.
	# JP: browser に値を代入する。
	browser = BrowserSession(
		browser_profile=BrowserProfile(
			# executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
			window_size=ViewportSize(width=1100, height=1000),
			disable_security=True,
			wait_for_network_idle_page_load_time=1,
			headless=False,
			args=['--incognito'],
		),
	)
	# async with httpx.AsyncClient() as client:
	# 	version_info = await client.get('http://localhost:9222/json/version')
	# 	browser.cdp_url = version_info.json()['webSocketDebuggerUrl']

	# if not browser.cdp_url:
	# 	raise ValueError('CDP URL is not set')  # can't happen in this case actually

	# await browser.create_new_tab('https://en.wikipedia.org/wiki/Apple_Inc.')
	# await browser.create_new_tab('https://semantic-ui.com/modules/dropdown.html#/definition')
	# await browser.navigate('https://v0-website-with-clickable-elements.vercel.app/iframe-buttons')
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.browser.events import NavigateToUrlEvent

	# EN: Assign value to nav_event.
	# JP: nav_event に値を代入する。
	nav_event = browser.event_bus.dispatch(
		NavigateToUrlEvent(url='https://v0-website-with-clickable-elements.vercel.app/nested-iframe')
	)
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	await nav_event

	# Wait a moment for page to fully load
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	await asyncio.sleep(2)

	# EN: Repeat logic while a condition is true.
	# JP: 条件が真の間、処理を繰り返す。
	while True:
		# EN: Execute async logic with managed resources.
		# JP: リソース管理付きで非同期処理を実行する。
		async with DomService(browser) as dom_service:
			# EN: Assign value to start.
			# JP: start に値を代入する。
			start = time.time()
			# Get current target ID from browser session
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if browser.agent_focus and browser.agent_focus.target_id:
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = browser.agent_focus.target_id
			else:
				# Get first available target
				# EN: Assign value to targets.
				# JP: targets に値を代入する。
				targets = await browser._cdp_get_all_pages()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not targets:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError('No targets available')
				# EN: Assign value to target_id.
				# JP: target_id に値を代入する。
				target_id = targets[0]['targetId']

			# EN: Assign value to result.
			# JP: result に値を代入する。
			result = await dom_service.get_dom_tree(target_id)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(result, tuple):
				# EN: Assign value to dom_tree.
				# JP: dom_tree に値を代入する。
				dom_tree = result[0]
				# EN: Assign value to dom_timing.
				# JP: dom_timing に値を代入する。
				dom_timing = result[1] if len(result) > 1 else {}
			else:
				# EN: Assign value to dom_tree.
				# JP: dom_tree に値を代入する。
				dom_tree = result
				# EN: Assign value to dom_timing.
				# JP: dom_timing に値を代入する。
				dom_timing = {}

			# EN: Assign value to end.
			# JP: end に値を代入する。
			end = time.time()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'Time taken: {end - start} seconds')

			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with aiofiles.open('tmp/enhanced_dom_tree.json', 'w') as f:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await f.write(json.dumps(dom_tree.__json__(), indent=1))

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('Saved enhanced dom tree to tmp/enhanced_dom_tree.json')

			# Print some sample information about visible/clickable elements
			# EN: Assign value to visible_clickable_count.
			# JP: visible_clickable_count に値を代入する。
			visible_clickable_count = 0
			# EN: Assign value to total_with_snapshot.
			# JP: total_with_snapshot に値を代入する。
			total_with_snapshot = 0

			# EN: Define function `count_elements`.
			# JP: 関数 `count_elements` を定義する。
			def count_elements(node: EnhancedDOMTreeNode):
				# EN: Execute this statement.
				# JP: この文を実行する。
				nonlocal visible_clickable_count, total_with_snapshot
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node.snapshot_node:
					# EN: Update variable with augmented assignment.
					# JP: 複合代入で変数を更新する。
					total_with_snapshot += 1
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if node.is_visible and node.snapshot_node.is_clickable:
						# EN: Update variable with augmented assignment.
						# JP: 複合代入で変数を更新する。
						visible_clickable_count += 1
						# print(f'Visible clickable element: {node.node_name} (cursor: {node.snapshot_node.cursor_style})')

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if node.children_nodes:
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for child in node.children_nodes:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						count_elements(child)

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			count_elements(dom_tree)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(
				f'Found {visible_clickable_count} visible clickable elements out of {total_with_snapshot} elements with snapshot data'
			)

			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			serialized_dom_state, timing_info = await dom_service.get_serialized_dom_tree()

			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with aiofiles.open('tmp/serialized_dom_tree.txt', 'w') as f:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await f.write(serialized_dom_state.llm_representation())

			# print(serialized)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('Saved serialized dom tree to tmp/serialized_dom_tree.txt')

			# EN: Assign value to start.
			# JP: start に値を代入する。
			start = time.time()
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			snapshot, dom_tree, ax_tree, _ = await dom_service._get_all_trees()
			# EN: Assign value to end.
			# JP: end に値を代入する。
			end = time.time()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print(f'Time taken: {end - start} seconds')

			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with aiofiles.open('tmp/snapshot.json', 'w') as f:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await f.write(json.dumps(snapshot, indent=1))

			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with aiofiles.open('tmp/dom_tree.json', 'w') as f:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await f.write(json.dumps(dom_tree, indent=1))

			# EN: Execute async logic with managed resources.
			# JP: リソース管理付きで非同期処理を実行する。
			async with aiofiles.open('tmp/ax_tree.json', 'w') as f:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				await f.write(json.dumps(ax_tree, indent=1))

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('saved dom tree to tmp/dom_tree.json')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('saved snapshot to tmp/snapshot.json')
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			print('saved ax tree to tmp/ax_tree.json')

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			input('Done. Press Enter to continue...')


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(main())

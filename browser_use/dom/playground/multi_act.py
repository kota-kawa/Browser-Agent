# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use import Agent
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser import BrowserProfile, BrowserSession
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.types import ViewportSize
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm import ChatAzureOpenAI

# Initialize the Azure OpenAI client
# EN: Assign value to llm.
# JP: llm に値を代入する。
llm = ChatAzureOpenAI(
	model='gpt-4.1-mini',
)


# EN: Assign value to TASK.
# JP: TASK に値を代入する。
TASK = """
Go to https://browser-use.github.io/stress-tests/challenges/react-native-web-form.html and complete the React Native Web form by filling in all required fields and submitting.
"""


# EN: Define async function `main`.
# JP: 非同期関数 `main` を定義する。
async def main():
	# EN: Assign value to browser.
	# JP: browser に値を代入する。
	browser = BrowserSession(
		browser_profile=BrowserProfile(
			window_size=ViewportSize(width=1100, height=1000),
		)
	)

	# EN: Assign value to agent.
	# JP: agent に値を代入する。
	agent = Agent(task=TASK, llm=llm)

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	await agent.run()


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import asyncio

	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(main())

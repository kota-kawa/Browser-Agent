# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm import ContentText
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.groq.chat import ChatGroq
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import SystemMessage, UserMessage

# EN: Assign value to llm.
# JP: llm に値を代入する。
llm = ChatGroq(
	model='llama-3.1-8b-instant',
	temperature=0.5,
)
# llm = ChatOpenAI(model='gpt-4.1-mini')


# EN: Define async function `main`.
# JP: 非同期関数 `main` を定義する。
async def main():
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from pydantic import BaseModel

	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from browser_use.tokens.service import TokenCost

	# EN: Assign value to tk.
	# JP: tk に値を代入する。
	tk = TokenCost().register_llm(llm)

	# EN: Define class `Output`.
	# JP: クラス `Output` を定義する。
	class Output(BaseModel):
		# EN: Assign annotated value to reasoning.
		# JP: reasoning に型付きの値を代入する。
		reasoning: str
		# EN: Assign annotated value to answer.
		# JP: answer に型付きの値を代入する。
		answer: str

	# EN: Assign value to message.
	# JP: message に値を代入する。
	message = [
		SystemMessage(content='You are a helpful assistant that can answer questions and help with tasks.'),
		UserMessage(
			content=[
				ContentText(
					text=r"Why is the sky blue? write exactly this into reasoning make sure to output ' with  exactly like in the input : "
				),
				ContentText(
					text="""
	The user's request is to find the lowest priced women's plus size one piece swimsuit in color black with a customer rating of at least 5 on Kohls.com. I am currently on the homepage of Kohls. The page has a search bar and various category links. To begin, I need to navigate to the women's section and search for swimsuits. I will start by clicking on the 'Women' category link."""
				),
			]
		),
	]

	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for i in range(10):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('-' * 50)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'start loop {i}')
		# EN: Assign value to response.
		# JP: response に値を代入する。
		response = await llm.ainvoke(message, output_format=Output)
		# EN: Assign value to completion.
		# JP: completion に値を代入する。
		completion = response.completion
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'start reasoning: {completion.reasoning}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print(f'answer: {completion.answer}')
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		print('-' * 50)


# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if __name__ == '__main__':
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	asyncio.run(main())

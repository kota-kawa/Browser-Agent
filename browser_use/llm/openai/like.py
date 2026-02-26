# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.openai.chat import ChatOpenAI


# EN: Define class `ChatOpenAILike`.
# JP: クラス `ChatOpenAILike` を定義する。
@dataclass
class ChatOpenAILike(ChatOpenAI):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A class for to interact with any provider using the OpenAI API schema.

	Args:
	    model (str): The name of the OpenAI model to use.
	"""

	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str

# EN: Define class `LLMException`.
# JP: クラス `LLMException` を定義する。
class LLMException(Exception):
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, status_code, message):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.status_code = status_code
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.message = message
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__(f'Error {status_code}: {message}')

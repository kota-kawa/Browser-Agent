# EN: Define class `LLMException`.
# JP: クラス `LLMException` を定義する。
class LLMException(Exception):
	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, status_code, message):
		self.status_code = status_code
		self.message = message
		super().__init__(f'Error {status_code}: {message}')

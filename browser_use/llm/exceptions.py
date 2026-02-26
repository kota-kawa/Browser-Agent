# EN: Define class `ModelError`.
# JP: クラス `ModelError` を定義する。
class ModelError(Exception):
	# EN: Keep a placeholder statement.
	# JP: プレースホルダー文を維持する。
	pass


# EN: Define class `ModelProviderError`.
# JP: クラス `ModelProviderError` を定義する。
class ModelProviderError(ModelError):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Exception raised when a model provider returns an error."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		message: str,
		status_code: int = 502,
		model: str | None = None,
	):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__(message, status_code)
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.model = model


# EN: Define class `ModelRateLimitError`.
# JP: クラス `ModelRateLimitError` を定義する。
class ModelRateLimitError(ModelProviderError):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Exception raised when a model provider returns a rate limit error."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		message: str,
		status_code: int = 429,
		model: str | None = None,
	):
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		super().__init__(message, status_code, model)

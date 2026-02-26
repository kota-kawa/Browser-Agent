# EN: Define class `ModelError`.
# JP: クラス `ModelError` を定義する。
class ModelError(Exception):
	pass


# EN: Define class `ModelProviderError`.
# JP: クラス `ModelProviderError` を定義する。
class ModelProviderError(ModelError):
	"""Exception raised when a model provider returns an error."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		message: str,
		status_code: int = 502,
		model: str | None = None,
	):
		super().__init__(message, status_code)
		self.model = model


# EN: Define class `ModelRateLimitError`.
# JP: クラス `ModelRateLimitError` を定義する。
class ModelRateLimitError(ModelProviderError):
	"""Exception raised when a model provider returns a rate limit error."""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(
		self,
		message: str,
		status_code: int = 429,
		model: str | None = None,
	):
		super().__init__(message, status_code, model)

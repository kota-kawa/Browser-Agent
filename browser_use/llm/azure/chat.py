# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import os
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import httpx
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai import AsyncAzureOpenAI as AsyncAzureOpenAIClient
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from openai.types.shared import ChatModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.openai.like import ChatOpenAILike


# EN: Define class `ChatAzureOpenAI`.
# JP: クラス `ChatAzureOpenAI` を定義する。
@dataclass
class ChatAzureOpenAI(ChatOpenAILike):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	A class for to interact with any provider using the OpenAI API schema.

	Args:
	    model (str): The name of the OpenAI model to use. Defaults to "not-provided".
	    api_key (Optional[str]): The API key to use. Defaults to "not-provided".
	"""

	# Model configuration
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str | ChatModel

	# Client initialization parameters
	# EN: Assign annotated value to api_key.
	# JP: api_key に型付きの値を代入する。
	api_key: str | None = None
	# EN: Assign annotated value to api_version.
	# JP: api_version に型付きの値を代入する。
	api_version: str | None = '2024-12-01-preview'
	# EN: Assign annotated value to azure_endpoint.
	# JP: azure_endpoint に型付きの値を代入する。
	azure_endpoint: str | None = None
	# EN: Assign annotated value to azure_deployment.
	# JP: azure_deployment に型付きの値を代入する。
	azure_deployment: str | None = None
	# EN: Assign annotated value to base_url.
	# JP: base_url に型付きの値を代入する。
	base_url: str | None = None
	# EN: Assign annotated value to azure_ad_token.
	# JP: azure_ad_token に型付きの値を代入する。
	azure_ad_token: str | None = None
	# EN: Assign annotated value to azure_ad_token_provider.
	# JP: azure_ad_token_provider に型付きの値を代入する。
	azure_ad_token_provider: Any | None = None

	# EN: Assign annotated value to default_headers.
	# JP: default_headers に型付きの値を代入する。
	default_headers: dict[str, str] | None = None
	# EN: Assign annotated value to default_query.
	# JP: default_query に型付きの値を代入する。
	default_query: dict[str, Any] | None = None

	# EN: Assign annotated value to client.
	# JP: client に型付きの値を代入する。
	client: AsyncAzureOpenAIClient | None = None

	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'azure'

	# EN: Define function `_get_client_params`.
	# JP: 関数 `_get_client_params` を定義する。
	def _get_client_params(self) -> dict[str, Any]:
		# EN: Assign annotated value to _client_params.
		# JP: _client_params に型付きの値を代入する。
		_client_params: dict[str, Any] = {}

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.api_key = self.api_key or os.getenv('AZURE_OPENAI_API_KEY')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.azure_endpoint = self.azure_endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.azure_deployment = self.azure_deployment or os.getenv('AZURE_OPENAI_DEPLOYMENT')
		# EN: Assign value to params_mapping.
		# JP: params_mapping に値を代入する。
		params_mapping = {
			'api_key': self.api_key,
			'api_version': self.api_version,
			'organization': self.organization,
			'azure_endpoint': self.azure_endpoint,
			'azure_deployment': self.azure_deployment,
			'base_url': self.base_url,
			'azure_ad_token': self.azure_ad_token,
			'azure_ad_token_provider': self.azure_ad_token_provider,
			'http_client': self.http_client,
		}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.default_headers is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			_client_params['default_headers'] = self.default_headers
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.default_query is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			_client_params['default_query'] = self.default_query

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		_client_params.update({k: v for k, v in params_mapping.items() if v is not None})

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return _client_params

	# EN: Define function `get_client`.
	# JP: 関数 `get_client` を定義する。
	def get_client(self) -> AsyncAzureOpenAIClient:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Returns an asynchronous OpenAI client.

		Returns:
			AsyncAzureOpenAIClient: An instance of the asynchronous OpenAI client.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.client:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.client

		# EN: Assign annotated value to _client_params.
		# JP: _client_params に型付きの値を代入する。
		_client_params: dict[str, Any] = self._get_client_params()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.http_client:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			_client_params['http_client'] = self.http_client
		else:
			# Create a new async HTTP client with custom limits
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			_client_params['http_client'] = httpx.AsyncClient(
				limits=httpx.Limits(max_connections=20, max_keepalive_connections=6)
			)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.client = AsyncAzureOpenAIClient(**_client_params)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.client

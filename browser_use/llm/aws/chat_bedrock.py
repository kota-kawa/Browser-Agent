# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from os import getenv
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING, Any, TypeVar, overload

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.aws.serializer import AWSBedrockMessageSerializer
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.messages import BaseMessage
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from boto3 import client as AwsClient  # type: ignore
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from boto3.session import Session  # type: ignore

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define class `ChatAWSBedrock`.
# JP: クラス `ChatAWSBedrock` を定義する。
@dataclass
class ChatAWSBedrock(BaseChatModel):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	AWS Bedrock chat model supporting multiple providers (Anthropic, Meta, etc.).

	This class provides access to various models via AWS Bedrock,
	supporting both text generation and structured output via tool calling.

	To use this model, you need to either:
	1. Set the following environment variables:
	   - AWS_ACCESS_KEY_ID
	   - AWS_SECRET_ACCESS_KEY
	   - AWS_REGION
	2. Or provide a boto3 Session object
	3. Or use AWS SSO authentication
	"""

	# Model configuration
	# EN: Assign annotated value to model.
	# JP: model に型付きの値を代入する。
	model: str = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
	# EN: Assign annotated value to max_tokens.
	# JP: max_tokens に型付きの値を代入する。
	max_tokens: int | None = 4096
	# EN: Assign annotated value to temperature.
	# JP: temperature に型付きの値を代入する。
	temperature: float | None = None
	# EN: Assign annotated value to top_p.
	# JP: top_p に型付きの値を代入する。
	top_p: float | None = None
	# EN: Assign annotated value to seed.
	# JP: seed に型付きの値を代入する。
	seed: int | None = None
	# EN: Assign annotated value to stop_sequences.
	# JP: stop_sequences に型付きの値を代入する。
	stop_sequences: list[str] | None = None

	# AWS credentials and configuration
	# EN: Assign annotated value to aws_access_key_id.
	# JP: aws_access_key_id に型付きの値を代入する。
	aws_access_key_id: str | None = None
	# EN: Assign annotated value to aws_secret_access_key.
	# JP: aws_secret_access_key に型付きの値を代入する。
	aws_secret_access_key: str | None = None
	# EN: Assign annotated value to aws_region.
	# JP: aws_region に型付きの値を代入する。
	aws_region: str | None = None
	# EN: Assign annotated value to aws_sso_auth.
	# JP: aws_sso_auth に型付きの値を代入する。
	aws_sso_auth: bool = False
	# EN: Assign annotated value to session.
	# JP: session に型付きの値を代入する。
	session: 'Session | None' = None

	# Request parameters
	# EN: Assign annotated value to request_params.
	# JP: request_params に型付きの値を代入する。
	request_params: dict[str, Any] | None = None

	# Static
	# EN: Define function `provider`.
	# JP: 関数 `provider` を定義する。
	@property
	def provider(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return 'aws_bedrock'

	# EN: Define function `_get_client`.
	# JP: 関数 `_get_client` を定義する。
	def _get_client(self) -> 'AwsClient':  # type: ignore
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the AWS Bedrock client."""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from boto3 import client as AwsClient  # type: ignore
		except ImportError:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ImportError(
				'`boto3` not installed. Please install using `pip install browser-use[aws] or pip install browser-use[all]`'
			)

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.session:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return self.session.client('bedrock-runtime')

		# Get credentials from environment or instance parameters
		# EN: Assign value to access_key.
		# JP: access_key に値を代入する。
		access_key = self.aws_access_key_id or getenv('AWS_ACCESS_KEY_ID')
		# EN: Assign value to secret_key.
		# JP: secret_key に値を代入する。
		secret_key = self.aws_secret_access_key or getenv('AWS_SECRET_ACCESS_KEY')
		# EN: Assign value to region.
		# JP: region に値を代入する。
		region = self.aws_region or getenv('AWS_REGION') or getenv('AWS_DEFAULT_REGION')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.aws_sso_auth:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return AwsClient(service_name='bedrock-runtime', region_name=region)
		else:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not access_key or not secret_key:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(
					message='AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or provide a boto3 session.',
					model=self.name,
				)

			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return AwsClient(
				service_name='bedrock-runtime',
				region_name=region,
				aws_access_key_id=access_key,
				aws_secret_access_key=secret_key,
			)

	# EN: Define function `name`.
	# JP: 関数 `name` を定義する。
	@property
	def name(self) -> str:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return str(self.model)

	# EN: Define function `_get_inference_config`.
	# JP: 関数 `_get_inference_config` を定義する。
	def _get_inference_config(self) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the inference configuration for the request."""
		# EN: Assign value to config.
		# JP: config に値を代入する。
		config = {}
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.max_tokens is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['maxTokens'] = self.max_tokens
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.temperature is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['temperature'] = self.temperature
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.top_p is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['topP'] = self.top_p
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.stop_sequences is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['stopSequences'] = self.stop_sequences
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.seed is not None:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			config['seed'] = self.seed
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return config

	# EN: Define function `_format_tools_for_request`.
	# JP: 関数 `_format_tools_for_request` を定義する。
	def _format_tools_for_request(self, output_format: type[BaseModel]) -> list[dict[str, Any]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Format a Pydantic model as a tool for structured output."""
		# EN: Assign value to schema.
		# JP: schema に値を代入する。
		schema = output_format.model_json_schema()

		# Convert Pydantic schema to Bedrock tool format
		# EN: Assign value to properties.
		# JP: properties に値を代入する。
		properties = {}
		# EN: Assign value to required.
		# JP: required に値を代入する。
		required = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for prop_name, prop_info in schema.get('properties', {}).items():
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			properties[prop_name] = {
				'type': prop_info.get('type', 'string'),
				'description': prop_info.get('description', ''),
			}

		# Add required fields
		# EN: Assign value to required.
		# JP: required に値を代入する。
		required = schema.get('required', [])

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return [
			{
				'toolSpec': {
					'name': f'extract_{output_format.__name__.lower()}',
					'description': f'Extract information in the format of {output_format.__name__}',
					'inputSchema': {'json': {'type': 'object', 'properties': properties, 'required': required}},
				}
			}
		]

	# EN: Define function `_get_usage`.
	# JP: 関数 `_get_usage` を定義する。
	def _get_usage(self, response: dict[str, Any]) -> ChatInvokeUsage | None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Extract usage information from the response."""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if 'usage' not in response:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return None

		# EN: Assign value to usage_data.
		# JP: usage_data に値を代入する。
		usage_data = response['usage']
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return ChatInvokeUsage(
			prompt_tokens=usage_data.get('inputTokens', 0),
			completion_tokens=usage_data.get('outputTokens', 0),
			total_tokens=usage_data.get('totalTokens', 0),
			prompt_cached_tokens=None,  # Bedrock doesn't provide this
			prompt_cache_creation_tokens=None,
			prompt_image_tokens=None,
		)

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	async def ainvoke(self, messages: list[BaseMessage], output_format: None = None) -> ChatInvokeCompletion[str]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	@overload
	# EN: Evaluate an expression.
	# JP: 式を評価する。
	async def ainvoke(self, messages: list[BaseMessage], output_format: type[T]) -> ChatInvokeCompletion[T]: ...

	# EN: Define async function `ainvoke`.
	# JP: 非同期関数 `ainvoke` を定義する。
	async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Invoke the AWS Bedrock model with the given messages.

		Args:
			messages: List of chat messages
			output_format: Optional Pydantic model class for structured output

		Returns:
			Either a string response or an instance of output_format
		"""
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from botocore.exceptions import ClientError  # type: ignore
		except ImportError:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ImportError(
				'`boto3` not installed. Please install using `pip install browser-use[aws] or pip install browser-use[all]`'
			)

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		bedrock_messages, system_message = AWSBedrockMessageSerializer.serialize_messages(messages)

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Prepare the request body
			# EN: Assign annotated value to body.
			# JP: body に型付きの値を代入する。
			body: dict[str, Any] = {}

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if system_message:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				body['system'] = system_message

			# EN: Assign value to inference_config.
			# JP: inference_config に値を代入する。
			inference_config = self._get_inference_config()
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if inference_config:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				body['inferenceConfig'] = inference_config

			# Handle structured output via tool calling
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format is not None:
				# EN: Assign value to tools.
				# JP: tools に値を代入する。
				tools = self._format_tools_for_request(output_format)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				body['toolConfig'] = {'tools': tools}

			# Add any additional request parameters
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if self.request_params:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				body.update(self.request_params)

			# Filter out None values
			# EN: Assign value to body.
			# JP: body に値を代入する。
			body = {k: v for k, v in body.items() if v is not None}

			# Make the API call
			# EN: Assign value to client.
			# JP: client に値を代入する。
			client = self._get_client()
			# EN: Assign value to response.
			# JP: response に値を代入する。
			response = client.converse(modelId=self.model, messages=bedrock_messages, **body)

			# EN: Assign value to usage.
			# JP: usage に値を代入する。
			usage = self._get_usage(response)

			# Extract the response content
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'output' in response and 'message' in response['output']:
				# EN: Assign value to message.
				# JP: message に値を代入する。
				message = response['output']['message']
				# EN: Assign value to content.
				# JP: content に値を代入する。
				content = message.get('content', [])

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if output_format is None:
					# Return text response
					# EN: Assign value to text_content.
					# JP: text_content に値を代入する。
					text_content = []
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for item in content:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if 'text' in item:
							# EN: Evaluate an expression.
							# JP: 式を評価する。
							text_content.append(item['text'])

					# EN: Assign value to response_text.
					# JP: response_text に値を代入する。
					response_text = '\n'.join(text_content) if text_content else ''
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return ChatInvokeCompletion(
						completion=response_text,
						usage=usage,
					)
				else:
					# Handle structured output from tool calls
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for item in content:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if 'toolUse' in item:
							# EN: Assign value to tool_use.
							# JP: tool_use に値を代入する。
							tool_use = item['toolUse']
							# EN: Assign value to tool_input.
							# JP: tool_input に値を代入する。
							tool_input = tool_use.get('input', {})

							# EN: Handle exceptions around this block.
							# JP: このブロックで例外処理を行う。
							try:
								# Validate and return the structured output
								# EN: Return a value from the function.
								# JP: 関数から値を返す。
								return ChatInvokeCompletion(
									completion=output_format.model_validate(tool_input),
									usage=usage,
								)
							except Exception as e:
								# If validation fails, try to parse as JSON first
								# EN: Branch logic based on a condition.
								# JP: 条件に応じて処理を分岐する。
								if isinstance(tool_input, str):
									# EN: Handle exceptions around this block.
									# JP: このブロックで例外処理を行う。
									try:
										# EN: Assign value to data.
										# JP: data に値を代入する。
										data = json.loads(tool_input)
										# EN: Return a value from the function.
										# JP: 関数から値を返す。
										return ChatInvokeCompletion(
											completion=output_format.model_validate(data),
											usage=usage,
										)
									except json.JSONDecodeError:
										# EN: Keep a placeholder statement.
										# JP: プレースホルダー文を維持する。
										pass
								# EN: Raise an exception.
								# JP: 例外を送出する。
								raise ModelProviderError(
									message=f'Failed to validate structured output: {str(e)}',
									model=self.name,
								) from e

					# If no tool use found but output_format was requested
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ModelProviderError(
						message='Expected structured output but no tool use found in response',
						model=self.name,
					)

			# If no valid content found
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if output_format is None:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return ChatInvokeCompletion(
					completion='',
					usage=usage,
				)
			else:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(
					message='No valid content found in response',
					model=self.name,
				)

		except ClientError as e:
			# EN: Assign value to error_code.
			# JP: error_code に値を代入する。
			error_code = e.response.get('Error', {}).get('Code', 'Unknown')
			# EN: Assign value to error_message.
			# JP: error_message に値を代入する。
			error_message = e.response.get('Error', {}).get('Message', str(e))

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if error_code in ['ThrottlingException', 'TooManyRequestsException']:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelRateLimitError(message=error_message, model=self.name) from e
			else:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ModelProviderError(message=error_message, model=self.name) from e
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ModelProviderError(message=str(e), model=self.name) from e

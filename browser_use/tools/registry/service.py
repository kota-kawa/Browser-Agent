# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import asyncio
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import functools
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import inspect
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections.abc import Callable
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from inspect import Parameter, iscoroutinefunction, signature
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from types import UnionType
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any, Generic, Optional, TypeVar, Union, get_args, get_origin

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import pyotp
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel, Field, RootModel, create_model

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.agent.scratchpad import Scratchpad
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser import BrowserSession
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.filesystem.file_system import FileSystem
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.llm.base import BaseChatModel
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.observability import observe_debug
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.telemetry.service import ProductTelemetry
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.tools.registry.views import (
	ActionModel,
	ActionRegistry,
	RegisteredAction,
	SpecialActionParameters,
)
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.utils import is_new_tab_page, match_url_with_domain_pattern, time_execution_async

# EN: Assign value to Context.
# JP: Context に値を代入する。
Context = TypeVar('Context')

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define class `Registry`.
# JP: クラス `Registry` を定義する。
class Registry(Generic[Context]):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Service for registering and managing actions"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, exclude_actions: list[str] | None = None):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.registry = ActionRegistry()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.telemetry = ProductTelemetry()
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.exclude_actions = exclude_actions if exclude_actions is not None else []

	# EN: Define function `_get_special_param_types`.
	# JP: 関数 `_get_special_param_types` を定義する。
	def _get_special_param_types(self) -> dict[str, type | UnionType | None]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get the expected types for special parameters from SpecialActionParameters"""
		# Manually define the expected types to avoid issues with Optional handling.
		# we should try to reduce this list to 0 if possible, give as few standardized objects to all the actions
		# but each driver should decide what is relevant to expose the action methods,
		# e.g. CDP client, 2fa code getters, sensitive_data wrappers, other context, etc.
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return {
			'context': None,  # Context is a TypeVar, so we can't validate type
			'browser_session': BrowserSession,
			'page_url': str,
			'cdp_client': None,  # CDPClient type from cdp_use, but we don't import it here
			'page_extraction_llm': BaseChatModel,
			'available_file_paths': list,
			'has_sensitive_data': bool,
			'file_system': FileSystem,
			'scratchpad': Scratchpad,
		}

	# EN: Define function `_normalize_action_function_signature`.
	# JP: 関数 `_normalize_action_function_signature` を定義する。
	def _normalize_action_function_signature(
		self,
		func: Callable,
		description: str,
		param_model: type[BaseModel] | None = None,
	) -> tuple[Callable, type[BaseModel]]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Normalize action function to accept only kwargs.

		Returns:
			- Normalized function that accepts (*_, params: ParamModel, **special_params)
			- The param model to use for registration
		"""
		# EN: Assign value to sig.
		# JP: sig に値を代入する。
		sig = signature(func)
		# EN: Assign value to parameters.
		# JP: parameters に値を代入する。
		parameters = list(sig.parameters.values())
		# EN: Assign value to special_param_types.
		# JP: special_param_types に値を代入する。
		special_param_types = self._get_special_param_types()
		# EN: Assign value to special_param_names.
		# JP: special_param_names に値を代入する。
		special_param_names = set(special_param_types.keys())

		# Step 1: Validate no **kwargs in original function signature
		# if it needs default values it must use a dedicated param_model: BaseModel instead
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for param in parameters:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if param.kind == Parameter.VAR_KEYWORD:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(
					f"Action '{func.__name__}' has **{param.name} which is not allowed. "
					f'Actions must have explicit positional parameters only.'
				)

		# Step 2: Separate special and action parameters
		# EN: Assign value to action_params.
		# JP: action_params に値を代入する。
		action_params = []
		# EN: Assign value to special_params.
		# JP: special_params に値を代入する。
		special_params = []
		# EN: Assign value to param_model_provided.
		# JP: param_model_provided に値を代入する。
		param_model_provided = param_model is not None

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for i, param in enumerate(parameters):
			# Check if this is a Type 1 pattern (first param is BaseModel)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if i == 0 and param_model_provided and param.name not in special_param_names:
				# This is Type 1 pattern - skip the params argument
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if param.name in special_param_names:
				# Validate special parameter type
				# EN: Assign value to expected_type.
				# JP: expected_type に値を代入する。
				expected_type = special_param_types.get(param.name)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if param.annotation != Parameter.empty and expected_type is not None:
					# Handle Optional types - normalize both sides
					# EN: Assign value to param_type.
					# JP: param_type に値を代入する。
					param_type = param.annotation
					# EN: Assign value to origin.
					# JP: origin に値を代入する。
					origin = get_origin(param_type)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if origin is Union:
						# EN: Assign value to args.
						# JP: args に値を代入する。
						args = get_args(param_type)
						# Find non-None type
						# EN: Assign value to param_type.
						# JP: param_type に値を代入する。
						param_type = next((arg for arg in args if arg is not type(None)), param_type)

					# Check if types are compatible (exact match, subclass, or generic list)
					# EN: Assign value to types_compatible.
					# JP: types_compatible に値を代入する。
					types_compatible = (
						param_type == expected_type
						or (
							inspect.isclass(param_type)
							and inspect.isclass(expected_type)
							and issubclass(param_type, expected_type)
						)
						or
						# Handle list[T] vs list comparison
						(expected_type is list and (param_type is list or get_origin(param_type) is list))
					)

					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if not types_compatible:
						# EN: Assign value to expected_type_name.
						# JP: expected_type_name に値を代入する。
						expected_type_name = getattr(expected_type, '__name__', str(expected_type))
						# EN: Assign value to param_type_name.
						# JP: param_type_name に値を代入する。
						param_type_name = getattr(param_type, '__name__', str(param_type))
						# EN: Raise an exception.
						# JP: 例外を送出する。
						raise ValueError(
							f"Action '{func.__name__}' parameter '{param.name}: {param_type_name}' "
							f"conflicts with special argument injected by tools: '{param.name}: {expected_type_name}'"
						)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				special_params.append(param)
			else:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				action_params.append(param)

		# Step 3: Create or validate param model
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not param_model_provided:
			# Type 2: Generate param model from action params
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if action_params:
				# EN: Assign value to params_dict.
				# JP: params_dict に値を代入する。
				params_dict = {}
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for param in action_params:
					# EN: Assign value to annotation.
					# JP: annotation に値を代入する。
					annotation = param.annotation if param.annotation != Parameter.empty else str
					# EN: Assign value to default.
					# JP: default に値を代入する。
					default = ... if param.default == Parameter.empty else param.default
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					params_dict[param.name] = (annotation, default)

				# EN: Assign value to param_model.
				# JP: param_model に値を代入する。
				param_model = create_model(f'{func.__name__}_Params', __base__=ActionModel, **params_dict)
			else:
				# No action params, create empty model
				# EN: Assign value to param_model.
				# JP: param_model に値を代入する。
				param_model = create_model(
					f'{func.__name__}_Params',
					__base__=ActionModel,
				)
		# EN: Validate a required condition.
		# JP: 必須条件を検証する。
		assert param_model is not None, f'param_model is None for {func.__name__}'

		# Step 4: Create normalized wrapper function
		# EN: Define async function `normalized_wrapper`.
		# JP: 非同期関数 `normalized_wrapper` を定義する。
		@functools.wraps(func)
		async def normalized_wrapper(*args, params: BaseModel | None = None, **kwargs):
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Normalized action that only accepts kwargs"""
			# Validate no positional args
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if args:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise TypeError(f'{func.__name__}() does not accept positional arguments, only keyword arguments are allowed')

			# Prepare arguments for original function
			# EN: Assign value to call_args.
			# JP: call_args に値を代入する。
			call_args = []
			# EN: Assign value to call_kwargs.
			# JP: call_kwargs に値を代入する。
			call_kwargs = {}

			# Handle Type 1 pattern (first arg is the param model)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if param_model_provided and parameters and parameters[0].name not in special_param_names:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if params is None:
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise ValueError(f"{func.__name__}() missing required 'params' argument")
				# For Type 1, we'll use the params object as first argument
				# EN: Keep a placeholder statement.
				# JP: プレースホルダー文を維持する。
				pass
			else:
				# Type 2 pattern - need to unpack params
				# If params is None, try to create it from kwargs
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if params is None and action_params:
					# Extract action params from kwargs
					# EN: Assign value to action_kwargs.
					# JP: action_kwargs に値を代入する。
					action_kwargs = {}
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for param in action_params:
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if param.name in kwargs:
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							action_kwargs[param.name] = kwargs[param.name]
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if action_kwargs:
						# Use the param_model which has the correct types defined
						# EN: Assign value to params.
						# JP: params に値を代入する。
						params = param_model(**action_kwargs)

			# Build call_args by iterating through original function parameters in order
			# EN: Assign value to params_dict.
			# JP: params_dict に値を代入する。
			params_dict = params.model_dump() if params is not None else {}

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for i, param in enumerate(parameters):
				# Skip first param for Type 1 pattern (it's the model itself)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if param_model_provided and i == 0 and param.name not in special_param_names:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					call_args.append(params)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif param.name in special_param_names:
					# This is a special parameter
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if param.name in kwargs:
						# EN: Assign value to value.
						# JP: value に値を代入する。
						value = kwargs[param.name]
						# Check if required special param is None
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if value is None and param.default == Parameter.empty:
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if param.name == 'browser_session':
								# EN: Raise an exception.
								# JP: 例外を送出する。
								raise ValueError(f'Action {func.__name__} requires browser_session but none provided.')
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							elif param.name == 'page_extraction_llm':
								# EN: Raise an exception.
								# JP: 例外を送出する。
								raise ValueError(f'Action {func.__name__} requires page_extraction_llm but none provided.')
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							elif param.name == 'file_system':
								# EN: Raise an exception.
								# JP: 例外を送出する。
								raise ValueError(f'Action {func.__name__} requires file_system but none provided.')
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							elif param.name == 'page':
								# EN: Raise an exception.
								# JP: 例外を送出する。
								raise ValueError(f'Action {func.__name__} requires page but none provided.')
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							elif param.name == 'available_file_paths':
								# EN: Raise an exception.
								# JP: 例外を送出する。
								raise ValueError(f'Action {func.__name__} requires available_file_paths but none provided.')
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							elif param.name == 'file_system':
								# EN: Raise an exception.
								# JP: 例外を送出する。
								raise ValueError(f'Action {func.__name__} requires file_system but none provided.')
							else:
								# EN: Raise an exception.
								# JP: 例外を送出する。
								raise ValueError(f"{func.__name__}() missing required special parameter '{param.name}'")
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						call_args.append(value)
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif param.default != Parameter.empty:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						call_args.append(param.default)
					else:
						# Special param is required but not provided
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if param.name == 'browser_session':
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise ValueError(f'Action {func.__name__} requires browser_session but none provided.')
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif param.name == 'page_extraction_llm':
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise ValueError(f'Action {func.__name__} requires page_extraction_llm but none provided.')
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif param.name == 'file_system':
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise ValueError(f'Action {func.__name__} requires file_system but none provided.')
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif param.name == 'page':
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise ValueError(f'Action {func.__name__} requires page but none provided.')
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif param.name == 'available_file_paths':
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise ValueError(f'Action {func.__name__} requires available_file_paths but none provided.')
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif param.name == 'file_system':
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise ValueError(f'Action {func.__name__} requires file_system but none provided.')
						else:
							# EN: Raise an exception.
							# JP: 例外を送出する。
							raise ValueError(f"{func.__name__}() missing required special parameter '{param.name}'")
				else:
					# This is an action parameter
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if param.name in params_dict:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						call_args.append(params_dict[param.name])
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif param.default != Parameter.empty:
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						call_args.append(param.default)
					else:
						# EN: Raise an exception.
						# JP: 例外を送出する。
						raise ValueError(f"{func.__name__}() missing required parameter '{param.name}'")

			# Call original function with positional args
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if iscoroutinefunction(func):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await func(*call_args)
			else:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await asyncio.to_thread(func, *call_args)

		# Update wrapper signature to be kwargs-only
		# EN: Assign value to new_params.
		# JP: new_params に値を代入する。
		new_params = [Parameter('params', Parameter.KEYWORD_ONLY, default=None, annotation=Optional[param_model])]

		# Add special params as keyword-only
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for sp in special_params:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			new_params.append(Parameter(sp.name, Parameter.KEYWORD_ONLY, default=sp.default, annotation=sp.annotation))

		# Add **kwargs to accept and ignore extra params
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		new_params.append(Parameter('kwargs', Parameter.VAR_KEYWORD))

		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		normalized_wrapper.__signature__ = sig.replace(parameters=new_params)  # type: ignore[attr-defined]

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return normalized_wrapper, param_model

	# @time_execution_sync('--create_param_model')
	# EN: Define function `_create_param_model`.
	# JP: 関数 `_create_param_model` を定義する。
	def _create_param_model(self, function: Callable) -> type[BaseModel]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Creates a Pydantic model from function signature"""
		# EN: Assign value to sig.
		# JP: sig に値を代入する。
		sig = signature(function)
		# EN: Assign value to special_param_names.
		# JP: special_param_names に値を代入する。
		special_param_names = set(SpecialActionParameters.model_fields.keys())
		# EN: Assign value to params.
		# JP: params に値を代入する。
		params = {
			name: (param.annotation, ... if param.default == param.empty else param.default)
			for name, param in sig.parameters.items()
			if name not in special_param_names
		}
		# TODO: make the types here work
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return create_model(
			f'{function.__name__}_parameters',
			__base__=ActionModel,
			**params,  # type: ignore
		)

	# EN: Define function `action`.
	# JP: 関数 `action` を定義する。
	def action(
		self,
		description: str,
		param_model: type[BaseModel] | None = None,
		domains: list[str] | None = None,
		allowed_domains: list[str] | None = None,
	):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Decorator for registering actions"""
		# Handle aliases: domains and allowed_domains are the same parameter
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if allowed_domains is not None and domains is not None:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError("Cannot specify both 'domains' and 'allowed_domains' - they are aliases for the same parameter")

		# EN: Assign value to final_domains.
		# JP: final_domains に値を代入する。
		final_domains = allowed_domains if allowed_domains is not None else domains

		# EN: Define function `decorator`.
		# JP: 関数 `decorator` を定義する。
		def decorator(func: Callable):
			# Skip registration if action is in exclude_actions
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if func.__name__ in self.exclude_actions:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return func

			# Normalize the function signature
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			normalized_func, actual_param_model = self._normalize_action_function_signature(func, description, param_model)

			# EN: Assign value to action.
			# JP: action に値を代入する。
			action = RegisteredAction(
				name=func.__name__,
				description=description,
				function=normalized_func,
				param_model=actual_param_model,
				domains=final_domains,
			)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self.registry.actions[func.__name__] = action

			# Return the normalized function so it can be called with kwargs
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return normalized_func

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return decorator

	# EN: Define async function `execute_action`.
	# JP: 非同期関数 `execute_action` を定義する。
	@observe_debug(ignore_input=True, ignore_output=True, name='execute_action')
	@time_execution_async('--execute_action')
	async def execute_action(
		self,
		action_name: str,
		params: dict,
		browser_session: BrowserSession | None = None,
		page_extraction_llm: BaseChatModel | None = None,
		file_system: FileSystem | None = None,
		sensitive_data: dict[str, str | dict[str, str]] | None = None,
		available_file_paths: list[str] | None = None,
		scratchpad: Scratchpad | None = None,
	) -> Any:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Execute a registered action with simplified parameter handling"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if action_name not in self.registry.actions:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError(f'Action {action_name} not found')

		# EN: Assign value to action.
		# JP: action に値を代入する。
		action = self.registry.actions[action_name]
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# Create the validated Pydantic model
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to validated_params.
				# JP: validated_params に値を代入する。
				validated_params = action.param_model(**params)
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise ValueError(f'Invalid parameters {params} for action {action_name}: {type(e)}: {e}') from e

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if sensitive_data:
				# Get current URL if browser_session is provided
				# EN: Assign value to current_url.
				# JP: current_url に値を代入する。
				current_url = None
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if browser_session and browser_session.current_target_id:
					# EN: Handle exceptions around this block.
					# JP: このブロックで例外処理を行う。
					try:
						# Get current page info using CDP
						# EN: Assign value to targets.
						# JP: targets に値を代入する。
						targets = await browser_session.cdp_client.send.Target.getTargets()
						# EN: Iterate over items in a loop.
						# JP: ループで要素を順に処理する。
						for target in targets.get('targetInfos', []):
							# EN: Branch logic based on a condition.
							# JP: 条件に応じて処理を分岐する。
							if target.get('targetId') == browser_session.current_target_id:
								# EN: Assign value to current_url.
								# JP: current_url に値を代入する。
								current_url = target.get('url')
								# EN: Exit the current loop.
								# JP: 現在のループを終了する。
								break
					except Exception:
						# EN: Keep a placeholder statement.
						# JP: プレースホルダー文を維持する。
						pass
				# EN: Assign value to validated_params.
				# JP: validated_params に値を代入する。
				validated_params = self._replace_sensitive_data(validated_params, sensitive_data, current_url)

			# Build special context dict
			# EN: Assign value to special_context.
			# JP: special_context に値を代入する。
			special_context = {
				'browser_session': browser_session,
				'page_extraction_llm': page_extraction_llm,
				'available_file_paths': available_file_paths,
				'has_sensitive_data': action_name == 'input_text' and bool(sensitive_data),
				'file_system': file_system,
				'scratchpad': scratchpad,
			}

			# Only pass sensitive_data to actions that explicitly need it (input_text)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if action_name == 'input_text':
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				special_context['sensitive_data'] = sensitive_data

			# Add CDP-related parameters if browser_session is available
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if browser_session:
				# Add page_url
				# EN: Handle exceptions around this block.
				# JP: このブロックで例外処理を行う。
				try:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					special_context['page_url'] = await browser_session.get_current_page_url()
				except Exception:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					special_context['page_url'] = None

				# Add cdp_client
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				special_context['cdp_client'] = browser_session.cdp_client

			# All functions are now normalized to accept kwargs only
			# Call with params and unpacked special context
			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return await action.function(params=validated_params, **special_context)
			except Exception as e:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise

		except ValueError as e:
			# Preserve ValueError messages from validation
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'requires browser_session but none provided' in str(e) or 'requires page_extraction_llm but none provided' in str(
				e
			):
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError(str(e)) from e
			else:
				# EN: Raise an exception.
				# JP: 例外を送出する。
				raise RuntimeError(f'Error executing action {action_name}: {str(e)}') from e
		except TimeoutError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError(f'Error executing action {action_name} due to timeout.') from e
		except Exception as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise RuntimeError(f'Error executing action {action_name}: {str(e)}') from e

	# EN: Define function `_log_sensitive_data_usage`.
	# JP: 関数 `_log_sensitive_data_usage` を定義する。
	def _log_sensitive_data_usage(self, placeholders_used: set[str], current_url: str | None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Log when sensitive data is being used on a page"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if placeholders_used:
			# EN: Assign value to url_info.
			# JP: url_info に値を代入する。
			url_info = f' on {current_url}' if current_url and not is_new_tab_page(current_url) else ''
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'🔒 Using sensitive data placeholders: {", ".join(sorted(placeholders_used))}{url_info}')

	# EN: Define function `_replace_sensitive_data`.
	# JP: 関数 `_replace_sensitive_data` を定義する。
	def _replace_sensitive_data(
		self, params: BaseModel, sensitive_data: dict[str, Any], current_url: str | None = None
	) -> BaseModel:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Replaces sensitive data placeholders in params with actual values.

		Args:
			params: The parameter object containing <secret>placeholder</secret> tags
			sensitive_data: Dictionary of sensitive data, either in old format {key: value}
						   or new format {domain_pattern: {key: value}}
			current_url: Optional current URL for domain matching

		Returns:
			BaseModel: The parameter object with placeholders replaced by actual values
		"""
		# EN: Assign value to secret_pattern.
		# JP: secret_pattern に値を代入する。
		secret_pattern = re.compile(r'<secret>(.*?)</secret>')

		# Set to track all missing placeholders across the full object
		# EN: Assign value to all_missing_placeholders.
		# JP: all_missing_placeholders に値を代入する。
		all_missing_placeholders = set()
		# Set to track successfully replaced placeholders
		# EN: Assign value to replaced_placeholders.
		# JP: replaced_placeholders に値を代入する。
		replaced_placeholders = set()

		# Process sensitive data based on format and current URL
		# EN: Assign value to applicable_secrets.
		# JP: applicable_secrets に値を代入する。
		applicable_secrets = {}

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for domain_or_key, content in sensitive_data.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(content, dict):
				# New format: {domain_pattern: {key: value}}
				# Only include secrets for domains that match the current URL
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if current_url and not is_new_tab_page(current_url):
					# it's a real url, check it using our custom allowed_domains scheme://*.example.com glob matching
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if match_url_with_domain_pattern(current_url, domain_or_key):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						applicable_secrets.update(content)
			else:
				# Old format: {key: value}, expose to all domains (only allowed for legacy reasons)
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				applicable_secrets[domain_or_key] = content

		# Filter out empty values
		# EN: Assign value to applicable_secrets.
		# JP: applicable_secrets に値を代入する。
		applicable_secrets = {k: v for k, v in applicable_secrets.items() if v}

		# EN: Define function `recursively_replace_secrets`.
		# JP: 関数 `recursively_replace_secrets` を定義する。
		def recursively_replace_secrets(value: str | dict | list) -> str | dict | list:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(value, str):
				# EN: Assign value to matches.
				# JP: matches に値を代入する。
				matches = secret_pattern.findall(value)
				# check if the placeholder key, like x_password is in the output parameters of the LLM and replace it with the sensitive data
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for placeholder in matches:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if placeholder in applicable_secrets:
						# generate a totp code if secret is a 2fa secret
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if 'bu_2fa_code' in placeholder:
							# EN: Assign value to totp.
							# JP: totp に値を代入する。
							totp = pyotp.TOTP(applicable_secrets[placeholder], digits=6)
							# EN: Assign value to replacement_value.
							# JP: replacement_value に値を代入する。
							replacement_value = totp.now()
						else:
							# EN: Assign value to replacement_value.
							# JP: replacement_value に値を代入する。
							replacement_value = applicable_secrets[placeholder]

						# EN: Assign value to value.
						# JP: value に値を代入する。
						value = value.replace(f'<secret>{placeholder}</secret>', replacement_value)
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						replaced_placeholders.add(placeholder)
					else:
						# Keep track of missing placeholders
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						all_missing_placeholders.add(placeholder)
						# Don't replace the tag, keep it as is

				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return value
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(value, dict):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return {k: recursively_replace_secrets(v) for k, v in value.items()}
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(value, list):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [recursively_replace_secrets(v) for v in value]
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return value

		# EN: Assign value to params_dump.
		# JP: params_dump に値を代入する。
		params_dump = params.model_dump()
		# EN: Assign value to processed_params.
		# JP: processed_params に値を代入する。
		processed_params = recursively_replace_secrets(params_dump)

		# Log sensitive data usage
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._log_sensitive_data_usage(replaced_placeholders, current_url)

		# Log a warning if any placeholders are missing
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if all_missing_placeholders:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(f'Missing or empty keys in sensitive_data dictionary: {", ".join(all_missing_placeholders)}')

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return type(params).model_validate(processed_params)

	# @time_execution_sync('--create_action_model')
	# EN: Define function `create_action_model`.
	# JP: 関数 `create_action_model` を定義する。
	def create_action_model(self, include_actions: list[str] | None = None, page_url: str | None = None) -> type[ActionModel]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Creates a Union of individual action models from registered actions,
		used by LLM APIs that support tool calling & enforce a schema.

		Each action model contains only the specific action being used,
		rather than all actions with most set to None.
		"""
		# EN: Import required modules.
		# JP: 必要なモジュールをインポートする。
		from typing import Union

		# Filter actions based on page_url if provided:
		#   if page_url is None, only include actions with no filters
		#   if page_url is provided, only include actions that match the URL

		# EN: Assign annotated value to available_actions.
		# JP: available_actions に型付きの値を代入する。
		available_actions: dict[str, RegisteredAction] = {}
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for name, action in self.registry.actions.items():
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if include_actions is not None and name not in include_actions:
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# If no page_url provided, only include actions with no filters
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if page_url is None:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if action.domains is None:
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					available_actions[name] = action
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# Check domain filter if present
			# EN: Assign value to domain_is_allowed.
			# JP: domain_is_allowed に値を代入する。
			domain_is_allowed = self.registry._match_domains(action.domains, page_url)

			# Include action if domain filter matches
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if domain_is_allowed:
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				available_actions[name] = action

		# Create individual action models for each action
		# EN: Assign annotated value to individual_action_models.
		# JP: individual_action_models に型付きの値を代入する。
		individual_action_models: list[type[BaseModel]] = []

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for name, action in available_actions.items():
			# Create an individual model for each action that contains only one field
			# EN: Assign value to individual_model.
			# JP: individual_model に値を代入する。
			individual_model = create_model(
				f'{name.title().replace("_", "")}ActionModel',
				__base__=ActionModel,
				**{
					name: (
						action.param_model,
						Field(description=action.description),
					)  # type: ignore
				},
			)
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			individual_action_models.append(individual_model)

		# If no actions available, return empty ActionModel
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not individual_action_models:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return create_model('EmptyActionModel', __base__=ActionModel)

		# Create proper Union type that maintains ActionModel interface
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(individual_action_models) == 1:
			# If only one action, return it directly (no Union needed)
			# EN: Assign value to result_model.
			# JP: result_model に値を代入する。
			result_model = individual_action_models[0]

		# Meaning the length is more than 1
		else:
			# Create a Union type using RootModel that properly delegates ActionModel methods
			# EN: Assign value to union_type.
			# JP: union_type に値を代入する。
			union_type = Union[tuple(individual_action_models)]  # type: ignore : Typing doesn't understand that the length is >= 2 (by design)

			# EN: Define class `ActionModelUnion`.
			# JP: クラス `ActionModelUnion` を定義する。
			class ActionModelUnion(RootModel[union_type]):  # type: ignore
				# EN: Describe this block with a docstring.
				# JP: このブロックの説明をドキュメント文字列で記述する。
				"""Union of all available action models that maintains ActionModel interface"""

				# EN: Define function `get_index`.
				# JP: 関数 `get_index` を定義する。
				def get_index(self) -> int | None:
					# EN: Describe this block with a docstring.
					# JP: このブロックの説明をドキュメント文字列で記述する。
					"""Delegate get_index to the underlying action model"""
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if hasattr(self.root, 'get_index'):
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return self.root.get_index()  # type: ignore
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return None

				# EN: Define function `set_index`.
				# JP: 関数 `set_index` を定義する。
				def set_index(self, index: int):
					# EN: Describe this block with a docstring.
					# JP: このブロックの説明をドキュメント文字列で記述する。
					"""Delegate set_index to the underlying action model"""
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if hasattr(self.root, 'set_index'):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						self.root.set_index(index)  # type: ignore

				# EN: Define function `model_dump`.
				# JP: 関数 `model_dump` を定義する。
				def model_dump(self, **kwargs):
					# EN: Describe this block with a docstring.
					# JP: このブロックの説明をドキュメント文字列で記述する。
					"""Delegate model_dump to the underlying action model"""
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if hasattr(self.root, 'model_dump'):
						# EN: Return a value from the function.
						# JP: 関数から値を返す。
						return self.root.model_dump(**kwargs)  # type: ignore
					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return super().model_dump(**kwargs)

			# Set the name for better debugging
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			ActionModelUnion.__name__ = 'ActionModel'
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			ActionModelUnion.__qualname__ = 'ActionModel'

			# EN: Assign value to result_model.
			# JP: result_model に値を代入する。
			result_model = ActionModelUnion

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return result_model  # type:ignore

	# EN: Define function `get_prompt_description`.
	# JP: 関数 `get_prompt_description` を定義する。
	def get_prompt_description(self, page_url: str | None = None) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Get a description of all actions for the prompt

		If page_url is provided, only include actions that are available for that URL
		based on their domain filters
		"""
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.registry.get_prompt_description(page_url=page_url)

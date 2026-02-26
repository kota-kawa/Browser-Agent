# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TYPE_CHECKING

# Type stubs for lazy imports
# EN: Branch logic based on a condition.
# JP: 条件に応じて処理を分岐する。
if TYPE_CHECKING:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from .profile import BrowserProfile, ProxySettings
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from .session import BrowserSession


# Lazy imports mapping for heavy browser components
# EN: Assign value to _LAZY_IMPORTS.
# JP: _LAZY_IMPORTS に値を代入する。
_LAZY_IMPORTS = {
	'ProxySettings': ('.profile', 'ProxySettings'),
	'BrowserProfile': ('.profile', 'BrowserProfile'),
	'BrowserSession': ('.session', 'BrowserSession'),
}


# EN: Define function `__getattr__`.
# JP: 関数 `__getattr__` を定義する。
def __getattr__(name: str):
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Lazy import mechanism for heavy browser components."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if name in _LAZY_IMPORTS:
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		module_path, attr_name = _LAZY_IMPORTS[name]
		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Import required modules.
			# JP: 必要なモジュールをインポートする。
			from importlib import import_module

			# Use relative import for current package
			# EN: Assign value to full_module_path.
			# JP: full_module_path に値を代入する。
			full_module_path = f'browser_use.browser{module_path}'
			# EN: Assign value to module.
			# JP: module に値を代入する。
			module = import_module(full_module_path)
			# EN: Assign value to attr.
			# JP: attr に値を代入する。
			attr = getattr(module, attr_name)
			# Cache the imported attribute in the module's globals
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			globals()[name] = attr
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return attr
		except ImportError as e:
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ImportError(f'Failed to import {name} from {full_module_path}: {e}') from e

	# EN: Raise an exception.
	# JP: 例外を送出する。
	raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# EN: Assign value to __all__.
# JP: __all__ に値を代入する。
__all__ = [
	'BrowserSession',
	'BrowserProfile',
	'ProxySettings',
]

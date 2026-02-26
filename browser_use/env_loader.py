# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dotenv import load_dotenv

# EN: Assign value to _ENV_CANDIDATES.
# JP: _ENV_CANDIDATES に値を代入する。
_ENV_CANDIDATES = [
	Path(__file__).resolve().parents[1] / 'secrets.env',
	Path(__file__).resolve().parent / 'secrets.env',
]


# EN: Define function `load_secrets_env`.
# JP: 関数 `load_secrets_env` を定義する。
def load_secrets_env() -> None:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Load secrets.env files for the browser agent with a legacy fallback."""

	# EN: Assign value to loaded.
	# JP: loaded に値を代入する。
	loaded = False
	# EN: Iterate over items in a loop.
	# JP: ループで要素を順に処理する。
	for env_path in _ENV_CANDIDATES:
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if load_dotenv(env_path, override=False):
			# EN: Assign value to loaded.
			# JP: loaded に値を代入する。
			loaded = True
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not loaded:
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		load_dotenv()

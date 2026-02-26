# EN: Define function `cap_text_length`.
# JP: 関数 `cap_text_length` を定義する。
def cap_text_length(text: str, max_length: int) -> str:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Cap text length for display."""
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if len(text) <= max_length:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return text
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return text[:max_length] + '...'

# EN: Define function `cap_text_length`.
# JP: 関数 `cap_text_length` を定義する。
def cap_text_length(text: str, max_length: int) -> str:
	"""Cap text length for display."""
	if len(text) <= max_length:
		return text
	return text[:max_length] + '...'

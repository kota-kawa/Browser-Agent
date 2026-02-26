# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import json
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import TypeVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from groq import APIStatusError
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel

# EN: Assign value to T.
# JP: T に値を代入する。
T = TypeVar('T', bound=BaseModel)


# EN: Define function `try_parse_groq_failed_generation`.
# JP: 関数 `try_parse_groq_failed_generation` を定義する。
def try_parse_groq_failed_generation(e: APIStatusError, output_format: type[T]) -> T:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Known issue with Groq is that it sometimes fails to generate a valid JSON object,
	but the content is still in the response body. This function tries to extract the
	content and parse it as the output format.
	"""
	# Extract the response text from the exception
	# EN: Assign value to response_text.
	# JP: response_text に値を代入する。
	response_text = e.response.text

	# Find the JSON part of the response
	# This regex looks for a JSON object that might be embedded in the text
	# EN: Assign value to match.
	# JP: match に値を代入する。
	match = re.search(r'\{.*\}', response_text, re.DOTALL)
	# EN: Branch logic based on a condition.
	# JP: 条件に応じて処理を分岐する。
	if not match:
		# EN: Raise an exception.
		# JP: 例外を送出する。
		raise ValueError('No JSON object found in the response text')

	# EN: Assign value to json_text.
	# JP: json_text に値を代入する。
	json_text = match.group(0)

	# Clean up the JSON text (e.g., remove trailing commas)
	# EN: Assign value to json_text.
	# JP: json_text に値を代入する。
	json_text = re.sub(r',\s*\}', '}', json_text)
	# EN: Assign value to json_text.
	# JP: json_text に値を代入する。
	json_text = re.sub(r',\s*\]', ']', json_text)

	# Parse the JSON and validate with the Pydantic model
	# EN: Assign value to parsed_json.
	# JP: parsed_json に値を代入する。
	parsed_json = json.loads(json_text)
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return output_format.model_validate(parsed_json)

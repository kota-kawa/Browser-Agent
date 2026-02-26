# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Utilities for creating optimized Pydantic schemas for LLM usage.
"""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Any

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pydantic import BaseModel


# EN: Define class `SchemaOptimizer`.
# JP: クラス `SchemaOptimizer` を定義する。
class SchemaOptimizer:
	# EN: Define function `create_optimized_json_schema`.
	# JP: 関数 `create_optimized_json_schema` を定義する。
	@staticmethod
	def create_optimized_json_schema(model: type[BaseModel]) -> dict[str, Any]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Create the most optimized schema by flattening all $ref/$defs while preserving
		FULL descriptions and ALL action definitions. Also ensures OpenAI strict mode compatibility.

		Args:
			model: The Pydantic model to optimize

		Returns:
			Optimized schema with all $refs resolved and strict mode compatibility
		"""
		# Generate original schema
		# EN: Assign value to original_schema.
		# JP: original_schema に値を代入する。
		original_schema = model.model_json_schema()

		# Extract $defs for reference resolution, then flatten everything
		# EN: Assign value to defs_lookup.
		# JP: defs_lookup に値を代入する。
		defs_lookup = original_schema.get('$defs', {})

		# EN: Define function `optimize_schema`.
		# JP: 関数 `optimize_schema` を定義する。
		def optimize_schema(
			obj: Any,
			defs_lookup: dict[str, Any] | None = None,
			*,
			in_properties: bool = False,  # NEW: track context
		) -> Any:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Apply all optimization techniques including flattening all $ref/$defs"""
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(obj, dict):
				# EN: Assign annotated value to optimized.
				# JP: optimized に型付きの値を代入する。
				optimized: dict[str, Any] = {}
				# EN: Assign annotated value to flattened_ref.
				# JP: flattened_ref に型付きの値を代入する。
				flattened_ref: dict[str, Any] | None = None

				# Skip unnecessary fields AND $defs (we'll inline everything)
				# EN: Assign value to skip_fields.
				# JP: skip_fields に値を代入する。
				skip_fields = ['additionalProperties', '$defs']

				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for key, value in obj.items():
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if key in skip_fields:
						# EN: Continue to the next loop iteration.
						# JP: ループの次の反復に進む。
						continue

					# Skip metadata "title" unless we're iterating inside an actual `properties` map
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if key == 'title' and not in_properties:
						# EN: Continue to the next loop iteration.
						# JP: ループの次の反復に進む。
						continue

					# Preserve FULL descriptions without truncation
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key == 'description':
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						optimized[key] = value

					# Handle type field
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key == 'type':
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						optimized[key] = value

					# FLATTEN: Resolve $ref by inlining the actual definition
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key == '$ref' and defs_lookup:
						# EN: Assign value to ref_path.
						# JP: ref_path に値を代入する。
						ref_path = value.split('/')[-1]  # Get the definition name from "#/$defs/SomeName"
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if ref_path in defs_lookup:
							# Get the referenced definition and flatten it
							# EN: Assign value to referenced_def.
							# JP: referenced_def に値を代入する。
							referenced_def = defs_lookup[ref_path]
							# EN: Assign value to flattened_ref.
							# JP: flattened_ref に値を代入する。
							flattened_ref = optimize_schema(referenced_def, defs_lookup)

					# Keep all anyOf structures (action unions) and resolve any $refs within
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key == 'anyOf' and isinstance(value, list):
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						optimized[key] = [optimize_schema(item, defs_lookup) for item in value]

					# Recursively optimize nested structures
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key in ['properties', 'items']:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						optimized[key] = optimize_schema(
							value,
							defs_lookup,
							in_properties=(key == 'properties'),
						)

					# Keep essential validation fields
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					elif key in ['type', 'required', 'minimum', 'maximum', 'minItems', 'maxItems', 'pattern', 'default']:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						optimized[key] = value if not isinstance(value, (dict, list)) else optimize_schema(value, defs_lookup)

					# Recursively process all other fields
					else:
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						optimized[key] = optimize_schema(value, defs_lookup) if isinstance(value, (dict, list)) else value

				# If we have a flattened reference, merge it with the optimized properties
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if flattened_ref is not None and isinstance(flattened_ref, dict):
					# Start with the flattened reference as the base
					# EN: Assign value to result.
					# JP: result に値を代入する。
					result = flattened_ref.copy()

					# Merge in any sibling properties that were processed
					# EN: Iterate over items in a loop.
					# JP: ループで要素を順に処理する。
					for key, value in optimized.items():
						# Preserve descriptions from the original object if they exist
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						if key == 'description' and 'description' not in result:
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							result[key] = value
						# EN: Branch logic based on a condition.
						# JP: 条件に応じて処理を分岐する。
						elif key != 'description':  # Don't overwrite description from flattened ref
							# EN: Assign value to target variable.
							# JP: target variable に値を代入する。
							result[key] = value

					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return result
				else:
					# No $ref, just return the optimized object
					# CRITICAL: Add additionalProperties: false to ALL objects for OpenAI strict mode
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if optimized.get('type') == 'object':
						# EN: Assign value to target variable.
						# JP: target variable に値を代入する。
						optimized['additionalProperties'] = False

					# EN: Return a value from the function.
					# JP: 関数から値を返す。
					return optimized

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(obj, list):
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return [optimize_schema(item, defs_lookup, in_properties=in_properties) for item in obj]
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return obj

		# Create optimized schema with flattening
		# EN: Assign value to optimized_result.
		# JP: optimized_result に値を代入する。
		optimized_result = optimize_schema(original_schema, defs_lookup)

		# Ensure we have a dictionary (should always be the case for schema root)
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not isinstance(optimized_result, dict):
			# EN: Raise an exception.
			# JP: 例外を送出する。
			raise ValueError('Optimized schema result is not a dictionary')

		# EN: Assign annotated value to optimized_schema.
		# JP: optimized_schema に型付きの値を代入する。
		optimized_schema: dict[str, Any] = optimized_result

		# Additional pass to ensure ALL objects have additionalProperties: false
		# EN: Define function `ensure_additional_properties_false`.
		# JP: 関数 `ensure_additional_properties_false` を定義する。
		def ensure_additional_properties_false(obj: Any) -> None:
			# EN: Describe this block with a docstring.
			# JP: このブロックの説明をドキュメント文字列で記述する。
			"""Ensure all objects have additionalProperties: false"""
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if isinstance(obj, dict):
				# If it's an object type, ensure additionalProperties is false
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if obj.get('type') == 'object':
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					obj['additionalProperties'] = False

				# Recursively apply to all values
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for value in obj.values():
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if isinstance(value, (dict, list)):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						ensure_additional_properties_false(value)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			elif isinstance(obj, list):
				# EN: Iterate over items in a loop.
				# JP: ループで要素を順に処理する。
				for item in obj:
					# EN: Branch logic based on a condition.
					# JP: 条件に応じて処理を分岐する。
					if isinstance(item, (dict, list)):
						# EN: Evaluate an expression.
						# JP: 式を評価する。
						ensure_additional_properties_false(item)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		ensure_additional_properties_false(optimized_schema)
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		SchemaOptimizer._make_strict_compatible(optimized_schema)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return optimized_schema

	# EN: Define function `_make_strict_compatible`.
	# JP: 関数 `_make_strict_compatible` を定義する。
	@staticmethod
	def _make_strict_compatible(schema: dict[str, Any] | list[Any]) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Ensure all properties are required for OpenAI strict mode"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if isinstance(schema, dict):
			# First recursively apply to nested objects
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for key, value in schema.items():
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if isinstance(value, (dict, list)) and key != 'required':
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					SchemaOptimizer._make_strict_compatible(value)

			# Then update required for this level
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if 'properties' in schema and 'type' in schema and schema['type'] == 'object':
				# Add all properties to required array
				# EN: Assign value to all_props.
				# JP: all_props に値を代入する。
				all_props = list(schema['properties'].keys())
				# EN: Assign value to target variable.
				# JP: target variable に値を代入する。
				schema['required'] = all_props  # Set all properties as required

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		elif isinstance(schema, list):
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for item in schema:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				SchemaOptimizer._make_strict_compatible(item)

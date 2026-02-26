# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Utility helpers for creating and tracking named :class:`~bubus.EventBus` objects."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from __future__ import annotations

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import re
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import unicodedata
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import ClassVar

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from bubus import EventBus
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from uuid_extensions import uuid7str


# EN: Define class `EventBusFactory`.
# JP: クラス `EventBusFactory` を定義する。
class EventBusFactory:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Factory that produces uniquely named :class:`EventBus` instances."""

	# EN: Assign annotated value to _ACTIVE_NAMES.
	# JP: _ACTIVE_NAMES に型付きの値を代入する。
	_ACTIVE_NAMES: ClassVar[set[str]] = set()
	# EN: Assign annotated value to _PREFIX.
	# JP: _PREFIX に型付きの値を代入する。
	_PREFIX: ClassVar[str] = 'Agent'
	# EN: Assign annotated value to _SANITIZE_PATTERN.
	# JP: _SANITIZE_PATTERN に型付きの値を代入する。
	_SANITIZE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r'[^0-9A-Za-z_]')
	# EN: Assign annotated value to _COLLAPSE_PATTERN.
	# JP: _COLLAPSE_PATTERN に型付きの値を代入する。
	_COLLAPSE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r'_+')

	# EN: Define function `clear_active_names`.
	# JP: 関数 `clear_active_names` を定義する。
	@classmethod
	def clear_active_names(cls) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Reset the internal registry of reserved EventBus identifiers."""

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		cls._ACTIVE_NAMES.clear()

	# EN: Define function `release`.
	# JP: 関数 `release` を定義する。
	@classmethod
	def release(cls, name: str | None) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Release a previously-reserved EventBus *name* if provided."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if name:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cls._ACTIVE_NAMES.discard(name)

	# -- name generation -------------------------------------------------
	# EN: Define function `_random_name`.
	# JP: 関数 `_random_name` を定義する。
	@classmethod
	def _random_name(cls) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return a random, identifier-safe EventBus name."""

		# EN: Assign value to suffix.
		# JP: suffix に値を代入する。
		suffix = uuid7str().replace('-', '')
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'{cls._PREFIX}_{suffix}'

	# EN: Define function `_candidate_from_agent`.
	# JP: 関数 `_candidate_from_agent` を定義する。
	@classmethod
	def _candidate_from_agent(cls, agent_id: str, *, force_random: bool) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return a raw candidate derived from *agent_id* or a random fallback."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if force_random:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return cls._random_name()

		# Take the most identifying characters from the agent id to build a stable suffix.
		# EN: Assign value to alnum.
		# JP: alnum に値を代入する。
		alnum = ''.join(ch for ch in str(agent_id) if ch.isalnum())
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not alnum:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return cls._random_name()

		# EN: Assign value to suffix.
		# JP: suffix に値を代入する。
		suffix = alnum[-12:]
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return f'{cls._PREFIX}_{suffix}'

	# EN: Define function `sanitize`.
	# JP: 関数 `sanitize` を定義する。
	@classmethod
	def sanitize(cls, raw_name: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Normalise *raw_name* into a safe, identifier-valid EventBus name."""

		# EN: Assign value to candidate.
		# JP: candidate に値を代入する。
		candidate = unicodedata.normalize('NFKC', raw_name or '')
		# EN: Assign value to sanitized.
		# JP: sanitized に値を代入する。
		sanitized = cls._SANITIZE_PATTERN.sub('_', candidate)
		# EN: Assign value to sanitized.
		# JP: sanitized に値を代入する。
		sanitized = cls._COLLAPSE_PATTERN.sub('_', sanitized).strip('_')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not sanitized:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return cls._random_name()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not sanitized.startswith(cls._PREFIX):
			# EN: Assign value to sanitized.
			# JP: sanitized に値を代入する。
			sanitized = f'{cls._PREFIX}_{sanitized}'

		# Trim overlong identifiers to keep them readable while remaining valid.
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if len(sanitized) > 64:
			# EN: Assign value to sanitized.
			# JP: sanitized に値を代入する。
			sanitized = sanitized[:64].rstrip('_')

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if sanitized in {cls._PREFIX, f'{cls._PREFIX}_'}:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return cls._random_name()

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not sanitized.isidentifier():
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return cls._random_name()

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return sanitized

	# EN: Define function `_ensure_unique`.
	# JP: 関数 `_ensure_unique` を定義する。
	@classmethod
	def _ensure_unique(cls, sanitized: str) -> str:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Return a unique name based on *sanitized*, adding random suffixes if needed."""

		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if sanitized not in cls._ACTIVE_NAMES:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return sanitized

		# Try a handful of deterministic collisions before falling back to a fresh random name.
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for _ in range(5):
			# EN: Assign value to random_suffix.
			# JP: random_suffix に値を代入する。
			random_suffix = uuid7str().replace('-', '')[:6]
			# EN: Assign value to candidate.
			# JP: candidate に値を代入する。
			candidate = cls.sanitize(f'{sanitized}_{random_suffix}')
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if candidate not in cls._ACTIVE_NAMES:
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return candidate

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return cls._random_name()

	# -- EventBus creation -----------------------------------------------
	# EN: Define function `create`.
	# JP: 関数 `create` を定義する。
	@classmethod
	def create(
		cls,
		*,
		agent_id: str,
		force_random: bool = False,
		logger: logging.Logger | None = None,
	) -> tuple[EventBus, str]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""Instantiate an :class:`EventBus` with a unique, sanitised identifier."""

		# EN: Assign value to log.
		# JP: log に値を代入する。
		log = logger or logging.getLogger(__name__)
		# EN: Assign annotated value to attempts.
		# JP: attempts に型付きの値を代入する。
		attempts: list[tuple[str, str]] = [('preferred', cls._candidate_from_agent(agent_id, force_random=force_random))]

		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while attempts:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			label, raw_name = attempts.pop(0)
			# EN: Assign value to sanitized.
			# JP: sanitized に値を代入する。
			sanitized = cls.sanitize(raw_name)
			# EN: Assign value to unique_name.
			# JP: unique_name に値を代入する。
			unique_name = cls._ensure_unique(sanitized)
			# EN: Assign value to unique_name.
			# JP: unique_name に値を代入する。
			unique_name = cls.sanitize(unique_name)

			# EN: Handle exceptions around this block.
			# JP: このブロックで例外処理を行う。
			try:
				# EN: Assign value to bus.
				# JP: bus に値を代入する。
				bus = EventBus(name=unique_name)
			except AssertionError as exc:  # pragma: no cover - defensive logging path
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				log.warning(
					'Failed to create EventBus name=%s (source=%s, raw=%s): %s',
					unique_name,
					label,
					raw_name,
					exc,
				)
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if label == 'preferred':
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					attempts.append(('fallback', cls._candidate_from_agent(agent_id, force_random=True)))
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				elif label == 'fallback':
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					attempts.append(('emergency', cls._random_name()))
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue
			except Exception:  # pragma: no cover - defensive logging path
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				log.exception(
					'Unexpected error while creating EventBus name=%s (source=%s, raw=%s).',
					unique_name,
					label,
					raw_name,
				)
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				attempts.append(('emergency', cls._random_name()))
				# EN: Continue to the next loop iteration.
				# JP: ループの次の反復に進む。
				continue

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			cls._ACTIVE_NAMES.add(bus.name)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return bus, bus.name

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		log.error('Exhausted candidate names for EventBus; falling back to anonymous EventBus().')
		# EN: Assign value to fallback_bus.
		# JP: fallback_bus に値を代入する。
		fallback_bus = EventBus()
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return fallback_bus, fallback_bus.name

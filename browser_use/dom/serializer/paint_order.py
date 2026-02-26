# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from collections import defaultdict
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from dataclasses import dataclass

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.dom.views import SimplifiedNode

# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""
Helper class for maintaining a union of rectangles (used for order of elements calculation)
"""


# EN: Define class `Rect`.
# JP: クラス `Rect` を定義する。
@dataclass(frozen=True, slots=True)
class Rect:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Closed axis-aligned rectangle with (x1,y1) bottom-left, (x2,y2) top-right."""

	# EN: Assign annotated value to x1.
	# JP: x1 に型付きの値を代入する。
	x1: float
	# EN: Assign annotated value to y1.
	# JP: y1 に型付きの値を代入する。
	y1: float
	# EN: Assign annotated value to x2.
	# JP: x2 に型付きの値を代入する。
	x2: float
	# EN: Assign annotated value to y2.
	# JP: y2 に型付きの値を代入する。
	y2: float

	# EN: Define function `__post_init__`.
	# JP: 関数 `__post_init__` を定義する。
	def __post_init__(self):
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not (self.x1 <= self.x2 and self.y1 <= self.y2):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

	# --- fast relations ----------------------------------------------------
	# EN: Define function `area`.
	# JP: 関数 `area` を定義する。
	def area(self) -> float:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return (self.x2 - self.x1) * (self.y2 - self.y1)

	# EN: Define function `intersects`.
	# JP: 関数 `intersects` を定義する。
	def intersects(self, other: 'Rect') -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return not (self.x2 <= other.x1 or other.x2 <= self.x1 or self.y2 <= other.y1 or other.y2 <= self.y1)

	# EN: Define function `contains`.
	# JP: 関数 `contains` を定義する。
	def contains(self, other: 'Rect') -> bool:
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return self.x1 <= other.x1 and self.y1 <= other.y1 and self.x2 >= other.x2 and self.y2 >= other.y2


# EN: Define class `RectUnionPure`.
# JP: クラス `RectUnionPure` を定義する。
class RectUnionPure:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Maintains a *disjoint* set of rectangles.
	No external dependencies - fine for a few thousand rectangles.
	"""

	# EN: Assign value to __slots__.
	# JP: __slots__ に値を代入する。
	__slots__ = ('_rects',)

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self):
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._rects: list[Rect] = []

	# -----------------------------------------------------------------
	# EN: Define function `_split_diff`.
	# JP: 関数 `_split_diff` を定義する。
	def _split_diff(self, a: Rect, b: Rect) -> list[Rect]:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		r"""
		Return list of up to 4 rectangles = a \ b.
		Assumes a intersects b.
		"""
		# EN: Assign value to parts.
		# JP: parts に値を代入する。
		parts = []

		# Bottom slice
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if a.y1 < b.y1:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(Rect(a.x1, a.y1, a.x2, b.y1))
		# Top slice
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if b.y2 < a.y2:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(Rect(a.x1, b.y2, a.x2, a.y2))

		# Middle (vertical) strip: y overlap is [max(a.y1,b.y1), min(a.y2,b.y2)]
		# EN: Assign value to y_lo.
		# JP: y_lo に値を代入する。
		y_lo = max(a.y1, b.y1)
		# EN: Assign value to y_hi.
		# JP: y_hi に値を代入する。
		y_hi = min(a.y2, b.y2)

		# Left slice
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if a.x1 < b.x1:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(Rect(a.x1, y_lo, b.x1, y_hi))
		# Right slice
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if b.x2 < a.x2:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			parts.append(Rect(b.x2, y_lo, a.x2, y_hi))

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return parts

	# -----------------------------------------------------------------
	# EN: Define function `contains`.
	# JP: 関数 `contains` を定義する。
	def contains(self, r: Rect) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		True iff r is fully covered by the current union.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._rects:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Assign value to stack.
		# JP: stack に値を代入する。
		stack = [r]
		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for s in self._rects:
			# EN: Assign value to new_stack.
			# JP: new_stack に値を代入する。
			new_stack = []
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for piece in stack:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if s.contains(piece):
					# piece completely gone
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if piece.intersects(s):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					new_stack.extend(self._split_diff(piece, s))
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					new_stack.append(piece)
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if not new_stack:  # everything eaten – covered
				# EN: Return a value from the function.
				# JP: 関数から値を返す。
				return True
			# EN: Assign value to stack.
			# JP: stack に値を代入する。
			stack = new_stack
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return False  # something survived

	# -----------------------------------------------------------------
	# EN: Define function `add`.
	# JP: 関数 `add` を定義する。
	def add(self, r: Rect) -> bool:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Insert r unless it is already covered.
		Returns True if the union grew.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if self.contains(r):
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return False

		# EN: Assign value to pending.
		# JP: pending に値を代入する。
		pending = [r]
		# EN: Assign value to i.
		# JP: i に値を代入する。
		i = 0
		# EN: Repeat logic while a condition is true.
		# JP: 条件が真の間、処理を繰り返す。
		while i < len(self._rects):
			# EN: Assign value to s.
			# JP: s に値を代入する。
			s = self._rects[i]
			# EN: Assign value to new_pending.
			# JP: new_pending に値を代入する。
			new_pending = []
			# EN: Assign value to changed.
			# JP: changed に値を代入する。
			changed = False
			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for piece in pending:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if piece.intersects(s):
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					new_pending.extend(self._split_diff(piece, s))
					# EN: Assign value to changed.
					# JP: changed に値を代入する。
					changed = True
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					new_pending.append(piece)
			# EN: Assign value to pending.
			# JP: pending に値を代入する。
			pending = new_pending
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if changed:
				# s unchanged; proceed with next existing rectangle
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				i += 1
			else:
				# EN: Update variable with augmented assignment.
				# JP: 複合代入で変数を更新する。
				i += 1

		# Any left‑over pieces are new, non‑overlapping areas
		# EN: Evaluate an expression.
		# JP: 式を評価する。
		self._rects.extend(pending)
		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return True


# EN: Define class `PaintOrderRemover`.
# JP: クラス `PaintOrderRemover` を定義する。
class PaintOrderRemover:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Calculates which elements should be removed based on the paint order parameter.
	"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, root: SimplifiedNode):
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.root = root

	# EN: Define function `calculate_paint_order`.
	# JP: 関数 `calculate_paint_order` を定義する。
	def calculate_paint_order(self) -> None:
		# EN: Assign annotated value to all_simplified_nodes_with_paint_order.
		# JP: all_simplified_nodes_with_paint_order に型付きの値を代入する。
		all_simplified_nodes_with_paint_order: list[SimplifiedNode] = []

		# EN: Define function `collect_paint_order`.
		# JP: 関数 `collect_paint_order` を定義する。
		def collect_paint_order(node: SimplifiedNode) -> None:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if (
				node.original_node.snapshot_node
				and node.original_node.snapshot_node.paint_order is not None
				and node.original_node.snapshot_node.bounds is not None
			):
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				all_simplified_nodes_with_paint_order.append(node)

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for child in node.children:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				collect_paint_order(child)

		# EN: Evaluate an expression.
		# JP: 式を評価する。
		collect_paint_order(self.root)

		# EN: Assign annotated value to grouped_by_paint_order.
		# JP: grouped_by_paint_order に型付きの値を代入する。
		grouped_by_paint_order: defaultdict[int, list[SimplifiedNode]] = defaultdict(list)

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for node in all_simplified_nodes_with_paint_order:
			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if node.original_node.snapshot_node and node.original_node.snapshot_node.paint_order is not None:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				grouped_by_paint_order[node.original_node.snapshot_node.paint_order].append(node)

		# EN: Assign value to rect_union.
		# JP: rect_union に値を代入する。
		rect_union = RectUnionPure()

		# EN: Iterate over items in a loop.
		# JP: ループで要素を順に処理する。
		for paint_order, nodes in sorted(grouped_by_paint_order.items(), key=lambda x: -x[0]):
			# EN: Assign value to rects_to_add.
			# JP: rects_to_add に値を代入する。
			rects_to_add = []

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for node in nodes:
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if not node.original_node.snapshot_node or not node.original_node.snapshot_node.bounds:
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue  # shouldn't happen by how we filter them out in the first place

				# EN: Assign value to rect.
				# JP: rect に値を代入する。
				rect = Rect(
					x1=node.original_node.snapshot_node.bounds.x,
					y1=node.original_node.snapshot_node.bounds.y,
					x2=node.original_node.snapshot_node.bounds.x + node.original_node.snapshot_node.bounds.width,
					y2=node.original_node.snapshot_node.bounds.y + node.original_node.snapshot_node.bounds.height,
				)

				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if rect_union.contains(rect):
					# EN: Assign value to target variable.
					# JP: target variable に値を代入する。
					node.ignored_by_paint_order = True

				# don't add to the nodes if opacity is less then 0.95 or background-color is transparent
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if (
					node.original_node.snapshot_node.computed_styles
					and node.original_node.snapshot_node.computed_styles.get('background-color', 'rgba(0, 0, 0, 0)')
					== 'rgba(0, 0, 0, 0)'
				) or (
					node.original_node.snapshot_node.computed_styles
					and float(node.original_node.snapshot_node.computed_styles.get('opacity', '1'))
					< 0.8  # this is highly vibes based number
				):
					# EN: Continue to the next loop iteration.
					# JP: ループの次の反復に進む。
					continue

				# EN: Evaluate an expression.
				# JP: 式を評価する。
				rects_to_add.append(rect)

			# EN: Iterate over items in a loop.
			# JP: ループで要素を順に処理する。
			for rect in rects_to_add:
				# EN: Evaluate an expression.
				# JP: 式を評価する。
				rect_union.add(rect)

		# EN: Return a value from the function.
		# JP: 関数から値を返す。
		return None

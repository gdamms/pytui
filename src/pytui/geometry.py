"""Basic geometry primitives: rectangles and box edges."""

from __future__ import annotations

from typing import NamedTuple


class Rect(NamedTuple):
    """An axis-aligned rectangle in terminal cells."""

    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def empty(self) -> bool:
        return self.width <= 0 or self.height <= 0

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.right and self.y <= y < self.bottom

    def intersect(self, other: Rect) -> Rect:
        x, y = max(self.x, other.x), max(self.y, other.y)
        right, bottom = min(self.right, other.right), min(self.bottom, other.bottom)
        return Rect(x, y, max(0, right - x), max(0, bottom - y))

    def inset(self, edges: Edges) -> Rect:
        return Rect(
            self.x + edges.left,
            self.y + edges.top,
            max(0, self.width - edges.left - edges.right),
            max(0, self.height - edges.top - edges.bottom),
        )


class Edges(NamedTuple):
    """Sizes of the four sides of a box, in CSS order."""

    top: int = 0
    right: int = 0
    bottom: int = 0
    left: int = 0

    @classmethod
    def parse(cls, value: int | tuple[int, ...] | None) -> Edges:
        """Parse CSS-like shorthand: ``1``, ``(vertical, horizontal)`` or ``(t, r, b, l)``."""
        if value is None:
            return cls()
        if isinstance(value, Edges):
            return value
        if isinstance(value, int):
            return cls(value, value, value, value)
        if len(value) == 1:
            return cls(value[0], value[0], value[0], value[0])
        if len(value) == 2:
            return cls(value[0], value[1], value[0], value[1])
        if len(value) == 4:
            return cls(*value)
        raise ValueError(f"expected 1, 2 or 4 values for edges, got {value!r}")

    @property
    def horizontal(self) -> int:
        return self.left + self.right

    @property
    def vertical(self) -> int:
        return self.top + self.bottom

    def plus(self, other: Edges) -> Edges:
        return Edges(
            self.top + other.top,
            self.right + other.right,
            self.bottom + other.bottom,
            self.left + other.left,
        )

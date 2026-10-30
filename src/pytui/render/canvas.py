"""A grid of styled cells that widgets draw into, and its display on a screen."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, NamedTuple

from ..geometry import Rect
from ..style import Color, ComputedStyle
from ..text import char_width, text_width

if TYPE_CHECKING:
    from ..screen import Screen


class CellStyle(NamedTuple):
    """The visual attributes of a single cell."""

    fg: Color = None
    bg: Color = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    reverse: bool = False

    @classmethod
    def from_style(cls, style: ComputedStyle) -> CellStyle:
        return cls(
            style.fg,
            style.bg,
            bool(style.bold),
            bool(style.dim),
            bool(style.italic),
            bool(style.underline),
            bool(style.strike),
            bool(style.reverse),
        )


_BLANK = CellStyle()


class Canvas:
    """A ``width`` x ``height`` grid of cells with a clipping stack.

    A wide character occupies two cells: the character itself followed by an
    empty-string placeholder.

    The canvas holds what should be displayed; its ``screen`` decides how to show it.
    """

    def __init__(self, width: int, height: int, screen: Screen | None = None) -> None:
        self.width = self.height = 0
        self.chars: list[list[str]] = []
        self.styles: list[list[CellStyle]] = []
        self.screen = screen
        self.resize(width, height)

    def resize(self, width: int, height: int) -> None:
        """Change the size, blanking the canvas if it differs."""
        width, height = max(0, width), max(0, height)
        if (width, height) == (self.width, self.height):
            return
        self.width, self.height = width, height
        self.clear()

    def clear(self) -> None:
        """Blank every cell and reset the clip, ready to draw a new frame."""
        self.chars = [[" "] * self.width for _ in range(self.height)]
        self.styles = [[_BLANK] * self.width for _ in range(self.height)]
        self._clip = Rect(0, 0, self.width, self.height)

    @property
    def clip_rect(self) -> Rect:
        return self._clip

    @contextmanager
    def clip(self, rect: Rect) -> Iterator[None]:
        """Restrict drawing to ``rect`` (intersected with the current clip)."""
        previous = self._clip
        self._clip = previous.intersect(rect)
        try:
            yield
        finally:
            self._clip = previous

    def set(self, x: int, y: int, char: str, style: CellStyle) -> None:
        """Set a single-width cell, respecting the clip."""
        if self._clip.contains(x, y):
            self._put(x, y, char, style)

    def _put(self, x: int, y: int, char: str, style: CellStyle) -> None:
        row = self.chars[y]
        # Break up any wide character we are overwriting half of.
        if row[x] == "" and x > 0:
            row[x - 1] = " "
        if x + 1 < self.width and row[x + 1] == "" and char != "":
            row[x + 1] = " "
        row[x] = char
        self.styles[y][x] = style

    def fill(self, rect: Rect, style: CellStyle, char: str = " ") -> None:
        area = self._clip.intersect(rect)
        for y in range(area.y, area.bottom):
            for x in range(area.x, area.right):
                self._put(x, y, char, style)

    def text(self, x: int, y: int, text: str, style: CellStyle) -> int:
        """Draw a single line of text; returns the number of cells advanced."""
        clip = self._clip
        if not clip.y <= y < clip.bottom:
            return text_width(text)
        start = x
        for char in text:
            w = char_width(char)
            if w == 0:
                if char >= " " and clip.contains(x - 1, y) and self.chars[y][x - 1]:
                    self.chars[y][x - 1] += char
                continue
            if w == 1:
                if clip.x <= x < clip.right:
                    self._put(x, y, char, style)
            elif clip.x <= x and x + 1 < clip.right:
                self._put(x, y, char, style)
                self._put(x + 1, y, "", style)
            elif clip.x <= x < clip.right or clip.x <= x + 1 < clip.right:
                self._put(max(x, clip.x), y, " ", style)
            x += w
        return x - start

    def border(self, rect: Rect, chars: str, style: CellStyle) -> None:
        """Draw a box border along the edges of ``rect``."""
        if rect.width < 2 or rect.height < 2:
            return
        tl, t, tr, r, bl, b, br, left = chars
        x, y, right, bottom = rect.x, rect.y, rect.right - 1, rect.bottom - 1
        inner = rect.width - 2
        self.text(x, y, tl + t * inner + tr, style)
        self.text(x, bottom, bl + b * inner + br, style)
        for row in range(y + 1, bottom):
            self.set(x, row, left, style)
            self.set(right, row, r, style)

    def lines(self) -> list[str]:
        """The canvas content as plain text lines."""
        return ["".join(row) for row in self.chars]

    def present(self) -> None:
        """Show the canvas on its screen."""
        if self.screen is None:
            raise RuntimeError("the canvas has no screen to present to")
        self.screen.display(self)

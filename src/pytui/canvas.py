"""A grid of styled cells that widgets draw into, and its conversion to ANSI output."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import NamedTuple

from .geometry import Rect
from .style import Color, Style, color_code
from .text import char_width, text_width, truncate


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
    def from_style(cls, style: Style) -> CellStyle:
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


@lru_cache(maxsize=1024)
def sgr(style: CellStyle) -> str:
    """The escape sequence that switches the terminal to ``style``."""
    codes = ["0"]
    for flag, code in (
        (style.bold, "1"),
        (style.dim, "2"),
        (style.italic, "3"),
        (style.underline, "4"),
        (style.reverse, "7"),
        (style.strike, "9"),
    ):
        if flag:
            codes.append(code)
    if style.fg is not None:
        codes.append(color_code(style.fg))
    if style.bg is not None:
        codes.append(color_code(style.bg, background=True))
    return f"\x1b[{';'.join(codes)}m"


_BLANK = CellStyle()


class Canvas:
    """A ``width`` x ``height`` grid of cells with a clipping stack.

    A wide character occupies two cells: the character itself followed by an
    empty-string placeholder.
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = max(0, width)
        self.height = max(0, height)
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

    def border(self, rect: Rect, chars: str, style: CellStyle, title: str | None = None) -> None:
        """Draw a box border along the edges of ``rect``, with an optional title on top."""
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
        if title and rect.width >= 5:
            self.text(x + 2, y, truncate(f" {title} ", rect.width - 4), style)

    def lines(self) -> list[str]:
        """The canvas content as plain text lines."""
        return ["".join(row) for row in self.chars]

    def render(self, previous: Canvas | None = None) -> str:
        """ANSI output that turns ``previous`` (or a blank screen) into this canvas."""
        if previous is not None and (previous.width, previous.height) != (self.width, self.height):
            previous = None
        out: list[str] = []
        current_style: CellStyle | None = None
        cursor: tuple[int, int] | None = None
        for y in range(self.height):
            chars, styles = self.chars[y], self.styles[y]
            old_chars = previous.chars[y] if previous else None
            old_styles = previous.styles[y] if previous else None
            x = 0
            while x < self.width:
                char, style = chars[x], styles[x]
                if char == "" or (
                    old_chars is not None and old_chars[x] == char and old_styles[x] == style
                ):
                    x += 1
                    continue
                if cursor != (x, y):
                    out.append(f"\x1b[{y + 1};{x + 1}H")
                if style != current_style:
                    out.append(sgr(style))
                    current_style = style
                out.append(char)
                x += 2 if x + 1 < self.width and chars[x + 1] == "" else 1
                cursor = (x, y) if x < self.width else None
        if out:
            out.append("\x1b[0m")
        return "".join(out)

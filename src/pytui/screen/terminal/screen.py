"""A screen that is a real terminal, updated by sending only the cells that changed."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..screen import Screen
from .ansi import CLEAR, RESET, SYNC_END, SYNC_START, move, sgr

if TYPE_CHECKING:
    from ...render import Canvas, CellStyle
    from .terminal import Terminal


class TerminalScreen(Screen):
    """Displays canvases on a :class:`Terminal`, each frame drawn atomically."""

    def __init__(self, terminal: Terminal) -> None:
        self.terminal = terminal
        self._shown: tuple[list[list[str]], list[list[CellStyle]]] | None = None
        self._size = (0, 0)

    def invalidate(self) -> None:
        self._shown = None

    def display(self, canvas: Canvas) -> None:
        if (canvas.width, canvas.height) != self._size:
            self.invalidate()
        old_chars, old_styles = self._shown or (None, None)
        out: list[str] = [] if old_chars is not None else [RESET + CLEAR]
        current_style: CellStyle | None = None
        cursor: tuple[int, int] | None = None
        for y in range(canvas.height):
            chars, styles = canvas.chars[y], canvas.styles[y]
            old_row = old_chars[y] if old_chars is not None else None
            old_row_styles = old_styles[y] if old_styles is not None else None
            x = 0
            while x < canvas.width:
                char, style = chars[x], styles[x]
                if char == "" or (
                    old_row is not None and old_row[x] == char and old_row_styles[x] == style
                ):
                    x += 1
                    continue
                if cursor != (x, y):
                    out.append(move(x, y))
                if style != current_style:
                    out.append(sgr(style))
                    current_style = style
                out.append(char)
                x += 2 if x + 1 < canvas.width and chars[x + 1] == "" else 1
                cursor = (x, y) if x < canvas.width else None
        if current_style is not None:
            out.append(RESET)
        if out:
            self.terminal.write(SYNC_START + "".join(out) + SYNC_END)
        self._shown = ([row[:] for row in canvas.chars], [row[:] for row in canvas.styles])
        self._size = (canvas.width, canvas.height)

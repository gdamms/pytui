"""A screen that is a text file, rewritten with each frame."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from .screen import Screen
from .terminal.ansi import RESET, sgr

if TYPE_CHECKING:
    from ..render import Canvas, CellStyle


class FileScreen(Screen):
    """Writes each frame to ``path``, replacing the previous one.

    Plain text by default; with ``colors=True`` styles are kept as ANSI escape
    sequences (view with ``cat`` or ``less -R``).
    """

    def __init__(self, path: str | os.PathLike[str], colors: bool = False) -> None:
        self.path = path
        self.colors = colors

    def invalidate(self) -> None:
        pass  # every frame is written in full

    def display(self, canvas: Canvas) -> None:
        if self.colors:
            rows = zip(canvas.chars, canvas.styles, strict=True)
            lines = [_styled_line(chars, styles) for chars, styles in rows]
        else:
            lines = [line.rstrip() for line in canvas.lines()]
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("".join(line + "\n" for line in lines))


def _styled_line(chars: list[str], styles: list[CellStyle]) -> str:
    out: list[str] = []
    current: CellStyle | None = None
    for char, style in zip(chars, styles, strict=True):
        if char == "":
            continue
        if style != current:
            out.append(sgr(style))
            current = style
        out.append(char)
    return "".join(out) + RESET

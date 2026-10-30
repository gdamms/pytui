"""Border presets and custom border strings."""

from __future__ import annotations

BORDERS: dict[str, str] = {
    "single": "┌─┐│└─┘│",
    "double": "╔═╗║╚═╝║",
    "rounded": "╭─╮│╰─╯│",
    "heavy": "┏━┓┃┗━┛┃",
    "ascii": "+-+|+-+|",
    "blank": "        ",
}
"""Border presets. Custom borders are 8-character strings in the order:
top-left, top, top-right, right, bottom-left, bottom, bottom-right, left."""


def border_chars(border: str) -> str | None:
    """The 8 border characters for a border name or custom string, ``None`` for no border."""
    if border == "none":
        return None
    if border in BORDERS:
        return BORDERS[border]
    if len(border) == 8:
        return border
    raise ValueError(f"invalid border: {border!r} (use a preset name or 8 characters)")

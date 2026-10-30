"""Colors: names, 256-color indexes and ``#rrggbb``, and their SGR codes."""

from __future__ import annotations

import re

Color = str | int | None
"""A color: a name (``"red"``, ``"bright_blue"``, ``"default"``), ``"#rrggbb"`` or 0-255."""

_COLOR_NAMES = {
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7,
}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def color_code(color: Color, background: bool = False) -> str:
    """SGR parameter string for a color."""
    if color is None or color == "default":
        return "49" if background else "39"
    if isinstance(color, int) and not isinstance(color, bool):
        if not 0 <= color <= 255:
            raise ValueError(f"256-color index must be in 0-255, got {color}")
        return f"{48 if background else 38};5;{color}"
    if isinstance(color, str):
        if _HEX.match(color):
            r, g, b = (int(color[i : i + 2], 16) for i in (1, 3, 5))
            return f"{48 if background else 38};2;{r};{g};{b}"
        name = color.lower().replace("-", "_")
        if name in ("gray", "grey"):
            name = "bright_black"
        bright = name.startswith("bright_")
        base = _COLOR_NAMES.get(name[7:] if bright else name)
        if base is not None:
            offset = (100 if background else 90) if bright else (40 if background else 30)
            return str(offset + base)
    raise ValueError(f"invalid color: {color!r}")

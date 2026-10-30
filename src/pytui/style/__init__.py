"""Styles: how widgets look and are laid out."""

from .border import BORDERS, border_chars
from .color import Color, color_code
from .style import DEFAULTS, ComputedStyle, Size, Spacing, Style

__all__ = [
    "BORDERS",
    "DEFAULTS",
    "Color",
    "ComputedStyle",
    "Size",
    "Spacing",
    "Style",
    "border_chars",
    "color_code",
]

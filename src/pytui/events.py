"""Input events delivered to widgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MouseAction = Literal[
    "down", "up", "move", "drag", "scroll_up", "scroll_down", "scroll_left", "scroll_right"
]
MouseButton = Literal["left", "middle", "right"]


@dataclass(frozen=True)
class KeyEvent:
    """A key press.

    ``key`` is a normalized name usable in bindings, e.g. ``"a"``, ``"A"``,
    ``"enter"``, ``"space"``, ``"ctrl+s"``, ``"shift+tab"``, ``"alt+left"``.
    ``char`` is the printable text produced by the key, if any.
    """

    name: str
    char: str | None = None
    ctrl: bool = False
    alt: bool = False
    shift: bool = False

    @property
    def key(self) -> str:
        prefix = "ctrl+" * self.ctrl + "alt+" * self.alt + "shift+" * self.shift
        return prefix + self.name

    @property
    def is_printable(self) -> bool:
        """True for keys that should insert text (no ctrl/alt modifier)."""
        return self.char is not None and not self.ctrl and not self.alt


@dataclass(frozen=True)
class MouseEvent:
    """A mouse action at screen coordinates ``(x, y)`` (0-based)."""

    action: MouseAction
    x: int
    y: int
    button: MouseButton | None = None
    ctrl: bool = False
    alt: bool = False
    shift: bool = False


@dataclass(frozen=True)
class PasteEvent:
    """Text pasted into the terminal (bracketed paste)."""

    text: str


@dataclass(frozen=True)
class ResizeEvent:
    """The terminal was resized."""

    width: int
    height: int


Event = KeyEvent | MouseEvent | PasteEvent | ResizeEvent


def normalize_key(key: str) -> str:
    """Normalize a binding like ``"Ctrl+Shift+Up"`` to ``"ctrl+shift+up"``."""
    parts = key.split("+")
    if key.endswith("+") and len(key) > 1:  # the "+" key itself, e.g. "ctrl++"
        parts = parts[:-2] + ["+"]
    *modifiers, name = parts
    mods = {m.strip().lower() for m in modifiers}
    unknown = mods - {"ctrl", "alt", "shift"}
    if unknown:
        raise ValueError(f"unknown modifier(s) in {key!r}: {', '.join(sorted(unknown))}")
    if len(name) > 1:
        name = name.lower()
    prefix = "ctrl+" * ("ctrl" in mods) + "alt+" * ("alt" in mods) + "shift+" * ("shift" in mods)
    return prefix + name

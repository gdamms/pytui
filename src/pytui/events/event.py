"""Input events delivered to widgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ..widgets import Widget

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


@dataclass(frozen=True)
class ClickEvent:
    """A click on ``widget`` (the deepest widget clicked, the event bubbles up).

    ``mouse`` is the mouse release that completed the click, or ``None`` when the
    click came from the keyboard (Enter or Space on a button) or from code.
    """

    widget: Widget
    mouse: MouseEvent | None = None


@dataclass(frozen=True)
class ChangeEvent:
    """Field ``name`` of ``widget.value`` changed from ``old`` to ``value``."""

    widget: Widget
    name: str
    value: Any
    old: Any


Event = KeyEvent | MouseEvent | PasteEvent | ResizeEvent

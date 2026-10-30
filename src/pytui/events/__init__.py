"""Input events: what they are, key names, and parsing raw terminal input."""

from .event import (
    ChangeEvent,
    ClickEvent,
    Event,
    KeyEvent,
    MouseAction,
    MouseButton,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
)
from .input import InputParser
from .keys import KEY_NAMES, MODIFIERS, normalize_key, parse_key

__all__ = [
    "KEY_NAMES",
    "MODIFIERS",
    "ChangeEvent",
    "ClickEvent",
    "Event",
    "InputParser",
    "KeyEvent",
    "MouseAction",
    "MouseButton",
    "MouseEvent",
    "PasteEvent",
    "ResizeEvent",
    "normalize_key",
    "parse_key",
]

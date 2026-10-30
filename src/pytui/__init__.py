"""pytui: build terminal user interfaces with a flexbox-style layout engine."""

from .app import App, Timer
from .events import (
    ChangeEvent,
    ClickEvent,
    Event,
    KeyEvent,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
)
from .geometry import Edges, Rect
from .render import Canvas, CellStyle
from .screen import FileScreen, Screen, Terminal, TerminalScreen
from .style import BORDERS, Style
from .widgets import (
    Box,
    Button,
    Checkbox,
    CheckboxValue,
    Column,
    Cursor,
    ProgressBar,
    ProgressBarValue,
    Row,
    Text,
    TextArea,
    TextAreaValue,
    Value,
    Widget,
)

__all__ = [
    "BORDERS",
    "App",
    "Box",
    "Button",
    "Canvas",
    "CellStyle",
    "ChangeEvent",
    "Checkbox",
    "CheckboxValue",
    "ClickEvent",
    "Column",
    "Cursor",
    "Edges",
    "Event",
    "FileScreen",
    "KeyEvent",
    "MouseEvent",
    "PasteEvent",
    "ProgressBar",
    "ProgressBarValue",
    "Rect",
    "ResizeEvent",
    "Row",
    "Screen",
    "Style",
    "Terminal",
    "TerminalScreen",
    "Text",
    "TextArea",
    "TextAreaValue",
    "Timer",
    "Value",
    "Widget",
]

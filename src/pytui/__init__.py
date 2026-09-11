"""pytui: build terminal user interfaces with a flexbox-style layout engine."""

from .app import App, Timer
from .canvas import Canvas, CellStyle
from .events import Event, KeyEvent, MouseEvent, PasteEvent, ResizeEvent
from .geometry import Edges, Rect
from .style import BORDERS, Style
from .widget import Widget
from .widgets import (
    Box,
    Button,
    Checkbox,
    Column,
    Input,
    ListView,
    ProgressBar,
    Row,
    Text,
    TextArea,
)

__all__ = [
    "BORDERS",
    "App",
    "Box",
    "Button",
    "Canvas",
    "CellStyle",
    "Checkbox",
    "Column",
    "Edges",
    "Event",
    "Input",
    "KeyEvent",
    "ListView",
    "MouseEvent",
    "PasteEvent",
    "ProgressBar",
    "Rect",
    "ResizeEvent",
    "Row",
    "Style",
    "Text",
    "TextArea",
    "Timer",
    "Widget",
]

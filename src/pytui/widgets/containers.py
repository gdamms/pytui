"""Containers: generic boxes, rows and columns."""

from __future__ import annotations

from ..style import Style
from .widget import Widget

Box = Widget
"""A generic container, like an HTML ``<div>``."""


class Row(Widget):
    """A widget laying out its children horizontally."""

    DEFAULT_STYLE = Style(direction="row")


class Column(Widget):
    """A widget laying out its children vertically."""

    DEFAULT_STYLE = Style(direction="column")

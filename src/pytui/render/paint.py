"""Painting the widget tree onto a canvas, and finding widgets by position."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..geometry import Edges, Rect
from ..style import border_chars
from .canvas import Canvas, CellStyle

if TYPE_CHECKING:
    from ..widgets import Widget


def _padding_box(widget: Widget) -> Rect:
    border = 0 if widget.computed.border == "none" else 1
    return widget.region.inset(Edges(border, border, border, border))


def _paint_order(widget: Widget) -> list[Widget]:
    children = [c for c in widget.children if c.computed.display != "none"]
    return [c for c in children if c.computed.position != "absolute"] + [
        c for c in children if c.computed.position == "absolute"
    ]


def _child_clip(widget: Widget, child: Widget, clip: Rect) -> Rect:
    """Where ``child`` may draw: absolute children may also cover the parent's border."""
    if widget.computed.overflow == "visible":
        return clip
    if child.computed.position == "absolute":
        return clip.intersect(widget.region)
    return clip.intersect(_padding_box(widget))


def paint(widget: Widget, canvas: Canvas) -> None:
    s = widget.computed
    if s.display == "none":
        return
    if s.overflow != "visible" and widget.region.intersect(canvas.clip_rect).empty:
        return  # fully clipped, e.g. scrolled out of view: so are its children
    visible = s.visibility == "visible"
    if visible:
        style = widget.text_style
        if widget._paints_background:
            canvas.fill(widget.region, style)
        chars = border_chars(s.border)
        if chars is not None:
            border_style = CellStyle(fg=s.border_fg or s.fg, bg=s.bg, dim=bool(s.dim))
            canvas.border(widget.region, chars, border_style)
        with canvas.clip(widget.content_region):
            widget.render(canvas)

    clip = canvas.clip_rect
    for child in _paint_order(widget):
        with canvas.clip(_child_clip(widget, child, clip)):
            paint(child, canvas)

    if visible:
        with canvas.clip(widget.content_region):
            widget.render_cursor(canvas)
        if s.overflow == "scroll":
            _paint_scrollbar(widget, canvas)


def _paint_scrollbar(widget: Widget, canvas: Canvas) -> None:
    s = widget.computed
    viewport = widget.content_region.height
    total = widget.virtual_height
    has_border = s.border != "none"
    region = widget.region
    x = region.right - 1
    top = region.y + has_border
    height = region.height - 2 * has_border
    if height <= 0 or total <= viewport:
        return
    thumb = max(1, round(height * viewport / total))
    start = round((height - thumb) * widget.scroll_y / max(1, total - viewport))
    style = CellStyle(fg=s.border_fg or s.fg, bg=s.bg)
    for i in range(height):
        if start <= i < start + thumb:
            canvas.set(x, top + i, "┃" if has_border else "▐", style)
        elif not has_border:
            canvas.set(x, top + i, " ", style)


def widget_at(widget: Widget, x: int, y: int, clip: Rect | None = None) -> Widget | None:
    """The top-most visible widget under ``(x, y)``."""
    s = widget.computed
    if s.display == "none":
        return None
    if clip is not None and not clip.contains(x, y):
        return None
    for child in reversed(_paint_order(widget)):
        found = widget_at(child, x, y, _child_clip(widget, child, clip or widget.region))
        if found is not None:
            return found
    if s.visibility == "visible" and widget.region.contains(x, y):
        return widget
    return None

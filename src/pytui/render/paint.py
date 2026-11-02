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
    """Where ``child`` may draw: absolute children may also cover the parent's border.

    Each axis is clipped independently, so ``overflow_x="visible"`` lets children
    spill out horizontally while still being clipped vertically.
    """
    s = widget.computed
    clip_x, clip_y = s.overflow_x != "visible", s.overflow_y != "visible"
    if not clip_x and not clip_y:
        return clip
    box = widget.region if child.computed.position == "absolute" else _padding_box(widget)
    x, right = (box.x, box.right) if clip_x else (clip.x, clip.right)
    y, bottom = (box.y, box.bottom) if clip_y else (clip.y, clip.bottom)
    return clip.intersect(Rect(x, y, right - x, bottom - y))


def paint(widget: Widget, canvas: Canvas) -> None:
    s = widget.computed
    if s.display == "none":
        return
    clips = s.overflow_x != "visible" and s.overflow_y != "visible"
    if clips and widget.region.intersect(canvas.clip_rect).empty:
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
        if s.scrolls(False):
            _paint_scrollbar(widget, canvas, horizontal=False)
        if s.scrolls(True):
            _paint_scrollbar(widget, canvas, horizontal=True)


def _paint_scrollbar(widget: Widget, canvas: Canvas, horizontal: bool) -> None:
    """Draw a scrollbar on the bottom (``horizontal``) or right border, or in its gutter."""
    s = widget.computed
    region = widget.region
    has_border = s.border != "none"
    # Without a border, the other scrollbar's gutter takes the corner cell.
    corner = 0 if has_border else int(s.scrolls(not horizontal))
    if horizontal:
        viewport, total, scroll = widget.content_region.width, widget.virtual_width, widget.scroll_x
        length = region.width - 2 * has_border - corner
    else:
        viewport, total = widget.content_region.height, widget.virtual_height
        scroll = widget.scroll_y
        length = region.height - 2 * has_border - corner
    if length <= 0 or total <= viewport:
        return
    thumb = max(1, round(length * viewport / total))
    start = round((length - thumb) * scroll / max(1, total - viewport))
    style = CellStyle(fg=s.border_fg or s.fg, bg=s.bg)
    if horizontal:
        bar = "━" if has_border else "▄"
    else:
        bar = "┃" if has_border else "▐"
    for i in range(length):
        if horizontal:
            x, y = region.x + has_border + i, region.bottom - 1
        else:
            x, y = region.right - 1, region.y + has_border + i
        if start <= i < start + thumb:
            canvas.set(x, y, bar, style)
        elif not has_border:
            canvas.set(x, y, " ", style)


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

"""Flexbox-style layout engine.

Layout runs in two steps per widget: children's sizes along the main axis are
resolved (flex basis, then grow/shrink), then children are positioned
(``justify_content``) and aligned on the cross axis (``align_items``).
Intrinsic ("auto") sizes are measured on demand and cached for one pass.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .geometry import Edges, Rect
from .style import ComputedStyle, Size

if TYPE_CHECKING:
    from .widget import Widget

_EMPTY = Rect()


def resolve_length(value: Size, reference: int | None) -> int | None:
    """Cells for a length, ``None`` for auto (or a percentage of an unknown size)."""
    if value is None or value == "auto":
        return None
    if isinstance(value, str):
        if reference is None:
            return None
        return int(reference * float(value[:-1]) / 100)
    return value


def insets(style: ComputedStyle) -> Edges:
    """Space between a widget's border box and its content box."""
    border = 0 if style.border == "none" else 1
    gutter = 1 if style.overflow == "scroll" and not border else 0
    pad = style.padding
    return Edges(
        pad.top + border, pad.right + border + gutter, pad.bottom + border, pad.left + border
    )


def _margins(widget: Widget, horizontal: bool) -> tuple[int, int]:
    m = widget.computed.margin
    return (m.left, m.right) if horizontal else (m.top, m.bottom)


def _partition(widget: Widget) -> tuple[list[Widget], list[Widget], list[Widget]]:
    flow, absolute, hidden = [], [], []
    for child in widget.children:
        s = child.computed
        if s.display == "none":
            hidden.append(child)
        elif s.position == "absolute":
            absolute.append(child)
        else:
            flow.append(child)
    return flow, absolute, hidden


def _clear(widget: Widget) -> None:
    widget.region = widget.content_region = _EMPTY
    for child in widget.children:
        _clear(child)


def _distribute(
    sizes: list[float], factors: list[float], lo: list[float], hi: list[float], free: float
) -> list[float]:
    """Share ``free`` space by ``factors``, respecting min/max (CSS flexible lengths)."""
    sizes = list(sizes)
    frozen = [f <= 0 for f in factors]
    while True:
        active = [i for i, done in enumerate(frozen) if not done]
        total = sum(factors[i] for i in active)
        if not active or total <= 0 or abs(free) < 1e-9:
            return sizes
        targets = {i: sizes[i] + free * factors[i] / total for i in active}
        clamped = {i: min(max(t, lo[i]), hi[i]) for i, t in targets.items()}
        violation = sum(clamped[i] - targets[i] for i in active)
        if abs(violation) < 1e-9:
            for i in active:
                sizes[i] = clamped[i]
            return sizes
        for i in active:
            if (violation > 0 and clamped[i] > targets[i]) or (
                violation < 0 and clamped[i] < targets[i]
            ):
                free -= clamped[i] - sizes[i]
                sizes[i] = clamped[i]
                frozen[i] = True


def _round(sizes: list[float]) -> list[int]:
    """Round sizes to integers while keeping their running total exact."""
    out, total, previous = [], 0.0, 0
    for size in sizes:
        total += size
        current = math.floor(total + 0.5)
        out.append(current - previous)
        previous = current
    return out


class LayoutEngine:
    def __init__(self) -> None:
        self._widths: dict[tuple[int, int | None], int] = {}
        self._heights: dict[tuple[int, int, int | None], int] = {}
        self._inset_cache: dict[int, Edges] = {}

    def layout(self, root: Widget, width: int, height: int) -> None:
        """Compute ``region`` and ``content_region`` for every widget in the tree."""
        self._widths.clear()
        self._heights.clear()
        self._inset_cache.clear()
        m = root.computed.margin
        w = self._explicit(root, True, width)
        w = max(0, width - m.horizontal) if w is None else w
        h = self._explicit(root, False, height)
        h = max(0, height - m.vertical) if h is None else h
        self._place(root, Rect(m.left, m.top, w, h))

    # --- sizing helpers ---------------------------------------------------

    def _insets(self, widget: Widget) -> Edges:
        style = widget.computed
        cached = self._inset_cache.get(id(style))
        if cached is None:
            cached = self._inset_cache[id(style)] = insets(style)
        return cached

    def _to_border_box(self, widget: Widget, horizontal: bool, value: int) -> int:
        if widget.computed.box_sizing == "content-box":
            e = self._insets(widget)
            value += e.horizontal if horizontal else e.vertical
        return value

    def _limits(self, widget: Widget, horizontal: bool, ref: int | None) -> tuple[int, float]:
        s = widget.computed
        e = self._insets(widget)
        floor = e.horizontal if horizontal else e.vertical
        lo = resolve_length(s.min_width if horizontal else s.min_height, ref)
        hi = resolve_length(s.max_width if horizontal else s.max_height, ref)
        lo = floor if lo is None else max(floor, self._to_border_box(widget, horizontal, lo))
        hi_value = math.inf if hi is None else max(lo, self._to_border_box(widget, horizontal, hi))
        return lo, hi_value

    def _clamp(self, widget: Widget, horizontal: bool, size: float, ref: int | None) -> int:
        lo, hi = self._limits(widget, horizontal, ref)
        return int(min(max(size, lo), hi))

    def _explicit(self, widget: Widget, horizontal: bool, ref: int | None) -> int | None:
        s = widget.computed
        value = resolve_length(s.width if horizontal else s.height, ref)
        if value is None:
            return None
        return self._clamp(widget, horizontal, self._to_border_box(widget, horizontal, value), ref)

    # --- intrinsic sizes --------------------------------------------------

    def preferred_width(self, widget: Widget, ref: int | None = None) -> int:
        """Border-box width the widget would like, without wrapping."""
        key = (id(widget), ref)
        cached = self._widths.get(key)
        if cached is not None:
            return cached
        width = self._explicit(widget, True, ref)
        if width is None:
            s = widget.computed
            content = widget.content_width()
            flow, _, _ = _partition(widget)
            if flow:
                outer = [self.preferred_width(c) + sum(_margins(c, True)) for c in flow]
                if s.direction == "row":
                    content = max(content, sum(outer) + s.gap * (len(flow) - 1))
                else:
                    content = max(content, max(outer))
            width = self._clamp(widget, True, content + self._insets(widget).horizontal, ref)
        self._widths[key] = width
        return width

    def preferred_height(self, widget: Widget, width: int, ref: int | None = None) -> int:
        """Border-box height the widget needs when given ``width``."""
        key = (id(widget), width, ref)
        cached = self._heights.get(key)
        if cached is not None:
            return cached
        height = self._explicit(widget, False, ref)
        if height is None:
            s = widget.computed
            e = self._insets(widget)
            content_width = max(0, width - e.horizontal)
            content = widget.content_height(content_width)
            flow, _, _ = _partition(widget)
            if flow:
                if s.direction == "row":
                    widths = self._main_sizes(widget, flow, content_width, None)
                    content = max(
                        content,
                        max(
                            self._cross_size(widget, c, w, None) + sum(_margins(c, False))
                            for c, w in zip(flow, widths, strict=True)
                        ),
                    )
                else:
                    heights = self._main_sizes(widget, flow, None, content_width)
                    margins = sum(sum(_margins(c, False)) for c in flow)
                    content = max(content, sum(heights) + margins + s.gap * (len(flow) - 1))
            height = self._clamp(widget, False, content + e.vertical, ref)
        self._heights[key] = height
        return height

    # --- flex algorithm ---------------------------------------------------

    def _align(self, parent: Widget, child: Widget) -> str:
        align = child.computed.align_self
        return parent.computed.align_items if align == "auto" else align

    def _cross_size(
        self, parent: Widget, child: Widget, main: int | None, available: int | None
    ) -> int:
        """Child size on the parent's cross axis (height in a row, width in a column)."""
        horizontal = parent.computed.direction == "column"
        explicit = self._explicit(child, horizontal, available)
        if explicit is not None:
            return explicit
        margin = sum(_margins(child, horizontal))
        if self._align(parent, child) == "stretch" and available is not None:
            return self._clamp(child, horizontal, available - margin, available)
        if horizontal:
            width = self.preferred_width(child, available)
            if available is not None:
                width = min(width, max(0, available - margin))
            return width
        assert main is not None
        return self.preferred_height(child, main, available)

    def _main_sizes(
        self, parent: Widget, flow: list[Widget], available: int | None, cross: int | None
    ) -> list[int]:
        """Children sizes on the main axis, flexed to fit ``available`` when known."""
        s = parent.computed
        row = s.direction == "row"
        bases: list[int] = []
        margins = 0
        for child in flow:
            if row:
                bases.append(self.preferred_width(child, available))
            else:
                width = self._cross_size(parent, child, None, cross)
                bases.append(self.preferred_height(child, width, available))
            margins += sum(_margins(child, row))
        if available is None or not flow:
            return bases
        free = available - sum(bases) - margins - s.gap * (len(flow) - 1)
        if free > 0:
            factors = [float(c.computed.flex_grow) for c in flow]
        elif free < 0 and s.overflow != "scroll":
            factors = [c.computed.flex_shrink * b for c, b in zip(flow, bases, strict=True)]
        else:
            return bases
        if not any(f > 0 for f in factors):
            return bases
        limits = [self._limits(c, row, available) for c in flow]
        sizes = _distribute(
            [float(b) for b in bases],
            factors,
            [lo for lo, _ in limits],
            [hi for _, hi in limits],
            free,
        )
        return _round(sizes)

    # --- placement --------------------------------------------------------

    def _place(self, widget: Widget, rect: Rect) -> None:
        s = widget.computed
        widget.region = rect
        content = rect.inset(self._insets(widget))
        widget.content_region = content
        flow, absolute, hidden = _partition(widget)
        for child in hidden:
            _clear(child)

        row = s.direction == "row"
        main_space, cross_space = (
            (content.width, content.height) if row else (content.height, content.width)
        )
        mains = self._main_sizes(widget, flow, main_space, cross_space)
        crosses = [
            self._cross_size(widget, c, m, cross_space) for c, m in zip(flow, mains, strict=True)
        ]
        main_margins = [_margins(c, row) for c in flow]
        cross_margins = [_margins(c, not row) for c in flow]

        used = sum(mains) + sum(a + b for a, b in main_margins) + s.gap * max(0, len(flow) - 1)
        cross_extent = max(
            (a + size + b for (a, b), size in zip(cross_margins, crosses, strict=True)), default=0
        )
        virtual_w, virtual_h = (used, cross_extent) if row else (cross_extent, used)
        if s.overflow == "scroll":
            virtual_h = max(virtual_h, widget.content_height(content.width))
            widget.virtual_width, widget.virtual_height = virtual_w, virtual_h
            widget.scroll_x = max(0, min(widget.scroll_x, virtual_w - content.width))
            widget.scroll_y = max(0, min(widget.scroll_y, virtual_h - content.height))
        else:
            widget.virtual_width, widget.virtual_height = content.width, content.height
            widget.scroll_x = widget.scroll_y = 0

        offset, spacing = self._justify(s.justify_content, max(0, main_space - used), len(flow))
        position = float(offset)
        for i, child in enumerate(flow):
            before, after = main_margins[i]
            cross_before, cross_after = cross_margins[i]
            main, cross = mains[i], crosses[i]
            slack = max(0, cross_space - cross_before - cross - cross_after)
            align = self._align(widget, child)
            cross_offset = cross_before + (
                slack // 2 if align == "center" else slack if align == "end" else 0
            )
            main_offset = math.floor(position + before + 0.5)
            if row:
                x, y, w, h = main_offset, cross_offset, main, cross
            else:
                x, y, w, h = cross_offset, main_offset, cross, main
            self._place(
                child, Rect(content.x + x - widget.scroll_x, content.y + y - widget.scroll_y, w, h)
            )
            position += before + main + after + s.gap + spacing

        self._place_absolute(widget, absolute)

    @staticmethod
    def _justify(mode: str, free: int, count: int) -> tuple[float, float]:
        """Initial offset and extra spacing between items for ``justify_content``."""
        if count == 0 or free <= 0:
            return 0, 0
        if mode == "center":
            return free // 2, 0
        if mode == "end":
            return free, 0
        if mode == "space-between":
            return 0, (free / (count - 1) if count > 1 else 0)
        if mode == "space-around":
            return free / count / 2, free / count
        if mode == "space-evenly":
            return free / (count + 1), free / (count + 1)
        return 0, 0

    def _place_absolute(self, widget: Widget, children: list[Widget]) -> None:
        """Position absolute children relative to the parent's padding box."""
        if not children:
            return
        border = 0 if widget.computed.border == "none" else 1
        box = widget.region.inset(Edges(border, border, border, border))
        for child in children:
            s = child.computed
            m = s.margin
            width = self._explicit(child, True, box.width)
            if width is None:
                if s.left is not None and s.right is not None:
                    width = self._clamp(
                        child, True, box.width - s.left - s.right - m.horizontal, box.width
                    )
                else:
                    width = min(
                        self.preferred_width(child, box.width), max(0, box.width - m.horizontal)
                    )
            height = self._explicit(child, False, box.height)
            if height is None:
                if s.top is not None and s.bottom is not None:
                    height = self._clamp(
                        child, False, box.height - s.top - s.bottom - m.vertical, box.height
                    )
                else:
                    height = self.preferred_height(child, width, box.height)
            if s.left is not None:
                x = box.x + s.left + m.left
            elif s.right is not None:
                x = box.right - s.right - m.right - width
            else:
                x = box.x + m.left
            if s.top is not None:
                y = box.y + s.top + m.top
            elif s.bottom is not None:
                y = box.bottom - s.bottom - m.bottom - height
            else:
                y = box.y + m.top
            self._place(child, Rect(x, y, width, height))

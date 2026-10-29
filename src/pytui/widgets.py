"""Ready-made widgets."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .canvas import Canvas, CellStyle
from .events import KeyEvent, MouseEvent, PasteEvent
from .style import Style
from .text import index_at_cell, slice_cells, text_width, truncate, wrap
from .widget import Widget


class Box(Widget):
    """A generic container, like an HTML ``<div>``. ``title`` is drawn on the top border."""

    def __init__(self, *children: Widget, title: str | None = None, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self.border_title = title

    @property
    def title(self) -> str | None:
        return self.border_title

    @title.setter
    def title(self, value: str | None) -> None:
        self.border_title = value


class Row(Box):
    """A box laying out its children horizontally."""

    DEFAULT_STYLE = Style(direction="row")


class Column(Box):
    """A box laying out its children vertically."""

    DEFAULT_STYLE = Style(direction="column")


class Text(Widget):
    """Static text. Wraps to the available width unless ``text_wrap=False``."""

    def __init__(self, text: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.text = text
        self._cache: tuple[str, int, bool, list[str]] | None = None

    def lines(self, width: int) -> list[str]:
        wrapping = bool(self.computed.text_wrap)
        cache = self._cache
        if cache is not None and cache[:3] == (self.text, width, wrapping):
            return cache[3]
        lines = wrap(self.text, width) if wrapping else self.text.expandtabs(4).split("\n")
        self._cache = (self.text, width, wrapping, lines)
        return lines

    def content_width(self) -> int:
        return max((text_width(line) for line in self.text.expandtabs(4).split("\n")), default=0)

    def content_height(self, width: int) -> int:
        return len(self.lines(width))

    def render(self, canvas: Canvas) -> None:
        area = self.content_region
        style = self.text_style
        align = self.computed.text_align
        for row, line in enumerate(self.lines(area.width)[self.scroll_y :]):
            if row >= area.height:
                break
            line = truncate(line, area.width)
            offset = 0
            if align != "left":
                slack = area.width - text_width(line)
                offset = slack // 2 if align == "center" else slack
            canvas.text(area.x + offset, area.y + row, line, style)


class Button(Widget):
    """A clickable button. ``on_press`` is called on click, Enter or Space."""

    FOCUSABLE = True
    DEFAULT_STYLE = Style(
        padding=(0, 1),
        align_self="start",
        text_align="center",
        text_wrap=False,
        fg="bright_white",
        bg="bright_black",
        hover=Style(fg="black", bg="white"),
        focus=Style(fg="bright_white", bg="blue", bold=True),
        disabled=Style(fg="white", dim=True),
    )

    def __init__(
        self, label: str, on_press: Callable[[], Any] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.label = label
        self.on_press = on_press

    def press(self) -> None:
        if self.on_press is not None and not self.is_disabled:
            self.on_press()

    def content_width(self) -> int:
        return text_width(self.label)

    def content_height(self, width: int) -> int:
        return 1

    def render(self, canvas: Canvas) -> None:
        area = self.content_region
        label = truncate(self.label, area.width)
        offset = (area.width - text_width(label)) // 2
        canvas.text(area.x + offset, area.y + (area.height - 1) // 2, label, self.text_style)

    def on_key(self, event: KeyEvent) -> bool:
        if event.key in ("enter", "space"):
            self.press()
            return True
        return False

    def on_click(self, event: MouseEvent) -> bool:
        self.press()
        return True


class Checkbox(Widget):
    """A toggle with a label. ``on_change(checked)`` is called when toggled."""

    FOCUSABLE = True
    DEFAULT_STYLE = Style(
        align_self="start",
        text_wrap=False,
        hover=Style(underline=True),
        focus=Style(fg="bright_cyan", bold=True),
        disabled=Style(dim=True),
    )

    def __init__(
        self,
        label: str = "",
        checked: bool = False,
        on_change: Callable[[bool], Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.label = label
        self.checked = checked
        self.on_change = on_change

    def toggle(self) -> None:
        self.checked = not self.checked
        if self.on_change is not None:
            self.on_change(self.checked)

    def content_width(self) -> int:
        return 3 + (1 + text_width(self.label) if self.label else 0)

    def content_height(self, width: int) -> int:
        return 1

    def render(self, canvas: Canvas) -> None:
        area = self.content_region
        text = f"[{'x' if self.checked else ' '}]" + (f" {self.label}" if self.label else "")
        canvas.text(area.x, area.y, truncate(text, area.width), self.text_style)

    def on_key(self, event: KeyEvent) -> bool:
        if event.key in ("enter", "space"):
            self.toggle()
            return True
        return False

    def on_click(self, event: MouseEvent) -> bool:
        self.toggle()
        return True


class Input(Widget):
    """A single-line text field.

    ``on_change(value)`` is called on every edit, ``on_submit(value)`` on Enter.
    """

    FOCUSABLE = True
    DEFAULT_STYLE = Style(
        height=1,
        min_width=3,
        fg="white",
        bg="bright_black",
        focus=Style(fg="bright_white"),
        disabled=Style(dim=True),
    )
    PLACEHOLDER_STYLE = Style(dim=True)

    def __init__(
        self,
        value: str = "",
        *,
        placeholder: str = "",
        password: bool = False,
        on_change: Callable[[str], Any] | None = None,
        on_submit: Callable[[str], Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._value = value
        self.cursor = len(value)
        self.placeholder = placeholder
        self.password = password
        self.on_change = on_change
        self.on_submit = on_submit
        self._offset = 0

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        self._value = value
        self.cursor = min(self.cursor, len(value))

    def _set(self, value: str, cursor: int) -> None:
        changed = value != self._value
        self._value = value
        self.cursor = max(0, min(cursor, len(value)))
        if changed and self.on_change is not None:
            self.on_change(value)

    def insert(self, text: str) -> None:
        text = text.replace("\r", "").replace("\n", " ").replace("\t", " ")
        v, c = self._value, self.cursor
        self._set(v[:c] + text + v[c:], c + len(text))

    def _display(self) -> str:
        return "•" * len(self._value) if self.password else self._value

    def _word_left(self) -> int:
        i = self.cursor
        while i > 0 and not self._value[i - 1].isalnum():
            i -= 1
        while i > 0 and self._value[i - 1].isalnum():
            i -= 1
        return i

    def _word_right(self) -> int:
        i, n = self.cursor, len(self._value)
        while i < n and not self._value[i].isalnum():
            i += 1
        while i < n and self._value[i].isalnum():
            i += 1
        return i

    def content_width(self) -> int:
        return 20

    def content_height(self, width: int) -> int:
        return 1

    def on_key(self, event: KeyEvent) -> bool:
        if event.is_printable:
            self.insert(event.char)  # type: ignore[arg-type]
            return True
        v, c = self._value, self.cursor
        key = event.key
        if key == "backspace" and c > 0:
            self._set(v[: c - 1] + v[c:], c - 1)
        elif key == "delete" and c < len(v):
            self._set(v[:c] + v[c + 1 :], c)
        elif key in ("ctrl+w", "alt+backspace", "ctrl+backspace"):
            start = self._word_left()
            self._set(v[:start] + v[c:], start)
        elif key == "ctrl+u":
            self._set(v[c:], 0)
        elif key == "ctrl+k":
            self._set(v[:c], c)
        elif key in ("left", "ctrl+b"):
            self.cursor = max(0, c - 1)
        elif key in ("right", "ctrl+f"):
            self.cursor = min(len(v), c + 1)
        elif key in ("ctrl+left", "alt+left", "alt+b"):
            self.cursor = self._word_left()
        elif key in ("ctrl+right", "alt+right", "alt+f"):
            self.cursor = self._word_right()
        elif key in ("home", "ctrl+a"):
            self.cursor = 0
        elif key in ("end", "ctrl+e"):
            self.cursor = len(v)
        elif key == "enter":
            if self.on_submit is not None:
                self.on_submit(v)
        elif key not in ("backspace", "delete"):
            return False
        return True

    def on_paste(self, event: PasteEvent) -> bool:
        self.insert(event.text)
        return True

    def on_mouse(self, event: MouseEvent) -> bool:
        if event.action == "down" and event.button == "left":
            display = self._display()
            cell = text_width(display[: self._offset]) + event.x - self.content_region.x
            self.cursor = min(len(self._value), index_at_cell(display, cell))
            return True
        return False

    def render(self, canvas: Canvas) -> None:
        area = self.content_region
        if area.width <= 0:
            return
        style = self.text_style
        if not self._value and self.placeholder:
            placeholder = CellStyle.from_style(self.computed | self.PLACEHOLDER_STYLE)
            canvas.text(area.x, area.y, truncate(self.placeholder, area.width), placeholder)
        display = self._display()
        # Keep the cursor visible (one cell is reserved for it at the end).
        self._offset = min(self._offset, self.cursor)
        while text_width(display[self._offset : self.cursor]) >= area.width:
            self._offset += 1
        visible = slice_cells(display[self._offset :], 0, area.width)
        canvas.text(area.x, area.y, visible, style)
        if self.has_focus:
            under = display[self.cursor] if self.cursor < len(display) else " "
            x = area.x + text_width(display[self._offset : self.cursor])
            canvas.text(x, area.y, under, style._replace(reverse=not style.reverse))


class TextArea(Widget):
    """A multi-line text editor. ``on_change(value)`` is called on every edit.

    Tab is not captured so that focus can still move with the keyboard.
    """

    FOCUSABLE = True
    DEFAULT_STYLE = Style(min_height=1, disabled=Style(dim=True))

    def __init__(
        self, value: str = "", *, on_change: Callable[[str], Any] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self._lines = [""]
        self.value = value
        self.on_change = on_change
        self._top = 0
        self._left = 0
        self._follow_cursor = True
        self._goal_cell: int | None = None

    @property
    def value(self) -> str:
        return "\n".join(self._lines)

    @value.setter
    def value(self, value: str) -> None:
        self._lines = value.replace("\r\n", "\n").expandtabs(4).split("\n")
        self.row = min(getattr(self, "row", 0), len(self._lines) - 1)
        self.col = min(getattr(self, "col", 0), len(self._lines[self.row]))

    @property
    def cursor(self) -> tuple[int, int]:
        """``(row, column)`` of the cursor, as character indexes."""
        return self.row, self.col

    def move_cursor(self, row: int, col: int) -> None:
        self.row = max(0, min(row, len(self._lines) - 1))
        self.col = max(0, min(col, len(self._lines[self.row])))
        self._follow_cursor = True

    def _changed(self) -> None:
        self._follow_cursor = True
        if self.on_change is not None:
            self.on_change(self.value)

    def insert(self, text: str) -> None:
        text = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)
        line = self._lines[self.row]
        head, tail = line[: self.col], line[self.col :]
        parts = text.split("\n")
        if len(parts) == 1:
            self._lines[self.row] = head + text + tail
            self.col += len(text)
        else:
            new = [head + parts[0], *parts[1:-1], parts[-1] + tail]
            self._lines[self.row : self.row + 1] = new
            self.row += len(parts) - 1
            self.col = len(parts[-1])
        self._goal_cell = None
        self._changed()

    def _vertical(self, rows: int) -> None:
        line = self._lines[self.row]
        if self._goal_cell is None:
            self._goal_cell = text_width(line[: self.col])
        self.row = max(0, min(self.row + rows, len(self._lines) - 1))
        self.col = index_at_cell(self._lines[self.row], self._goal_cell)
        self._follow_cursor = True

    def on_key(self, event: KeyEvent) -> bool:
        if event.is_printable:
            self.insert(event.char)  # type: ignore[arg-type]
            return True
        key = event.key
        lines, row, col = self._lines, self.row, self.col
        if key in ("up", "down"):
            self._vertical(-1 if key == "up" else 1)
            return True
        if key in ("pageup", "pagedown"):
            page = max(1, self.content_region.height - 1)
            self._vertical(-page if key == "pageup" else page)
            return True
        self._goal_cell = None
        if key == "enter":
            self.insert("\n")
        elif key == "backspace":
            if col > 0:
                lines[row] = lines[row][: col - 1] + lines[row][col:]
                self.col -= 1
                self._changed()
            elif row > 0:
                self.col = len(lines[row - 1])
                lines[row - 1] += lines.pop(row)
                self.row -= 1
                self._changed()
        elif key == "delete":
            if col < len(lines[row]):
                lines[row] = lines[row][:col] + lines[row][col + 1 :]
                self._changed()
            elif row + 1 < len(lines):
                lines[row] += lines.pop(row + 1)
                self._changed()
        elif key == "left":
            if col > 0:
                self.move_cursor(row, col - 1)
            elif row > 0:
                self.move_cursor(row - 1, len(lines[row - 1]))
        elif key == "right":
            if col < len(lines[row]):
                self.move_cursor(row, col + 1)
            elif row + 1 < len(lines):
                self.move_cursor(row + 1, 0)
        elif key in ("home", "ctrl+a"):
            self.move_cursor(row, 0)
        elif key in ("end", "ctrl+e"):
            self.move_cursor(row, len(lines[row]))
        elif key == "ctrl+home":
            self.move_cursor(0, 0)
        elif key == "ctrl+end":
            self.move_cursor(len(lines) - 1, len(lines[-1]))
        else:
            return False
        return True

    def on_paste(self, event: PasteEvent) -> bool:
        self.insert(event.text)
        return True

    def on_mouse(self, event: MouseEvent) -> bool:
        area = self.content_region
        if event.action in ("down", "drag") and event.button == "left":
            row = self._top + event.y - area.y
            row = max(0, min(row, len(self._lines) - 1))
            self.move_cursor(row, index_at_cell(self._lines[row], self._left + event.x - area.x))
            self._goal_cell = None
            return True
        if event.action in ("scroll_up", "scroll_down"):
            limit = max(0, len(self._lines) - area.height)
            step = -3 if event.action == "scroll_up" else 3
            self._top = max(0, min(self._top + step, limit))
            self._follow_cursor = False
            return True
        return False

    def content_width(self) -> int:
        return 20  # like <textarea cols=20>: content must not resize the layout

    def content_height(self, width: int) -> int:
        return len(self._lines)

    def render(self, canvas: Canvas) -> None:
        area = self.content_region
        if area.empty:
            return
        cursor_cell = text_width(self._lines[self.row][: self.col])
        if self._follow_cursor:
            self._top = min(self._top, self.row)
            self._top = max(self._top, self.row - area.height + 1)
            self._left = min(self._left, cursor_cell)
            self._left = max(self._left, cursor_cell - area.width + 1)
        self._top = max(0, min(self._top, max(0, len(self._lines) - 1)))
        style = self.text_style
        for i, line in enumerate(self._lines[self._top : self._top + area.height]):
            canvas.text(area.x, area.y + i, slice_cells(line, self._left, area.width), style)
        if self.has_focus and self._top <= self.row < self._top + area.height:
            line = self._lines[self.row]
            under = line[self.col] if self.col < len(line) else " "
            x = area.x + cursor_cell - self._left
            canvas.text(
                x, area.y + self.row - self._top, under, style._replace(reverse=not style.reverse)
            )


class ListView(Widget):
    """A scrollable list of strings with a highlighted row.

    ``on_select(index, item)`` is called on Enter or click,
    ``on_highlight(index, item)`` whenever the highlighted row changes.
    """

    FOCUSABLE = True
    DEFAULT_STYLE = Style(text_wrap=False, disabled=Style(dim=True))
    HIGHLIGHT_STYLE = Style(reverse=True)

    def __init__(
        self,
        items: Iterable[str] = (),
        *,
        on_select: Callable[[int, str], Any] | None = None,
        on_highlight: Callable[[int, str], Any] | None = None,
        highlight_style: Style | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._items = list(items)
        self._index: int | None = 0 if self._items else None
        self.on_select = on_select
        self.on_highlight = on_highlight
        self.highlight_style = highlight_style or self.HIGHLIGHT_STYLE
        self._top = 0
        self._follow = True

    @property
    def items(self) -> list[str]:
        return list(self._items)

    @items.setter
    def items(self, items: Iterable[str]) -> None:
        self._items = list(items)
        if not self._items:
            self._index = None
        else:
            self._index = min(self._index or 0, len(self._items) - 1)
        self._follow = True

    def append(self, item: str) -> None:
        self._items.append(item)
        if self._index is None:
            self._index = 0

    @property
    def index(self) -> int | None:
        return self._index

    @index.setter
    def index(self, value: int | None) -> None:
        if not self._items or value is None:
            new = None
        else:
            new = max(0, min(value, len(self._items) - 1))
        self._follow = True
        if new != self._index:
            self._index = new
            if new is not None and self.on_highlight is not None:
                self.on_highlight(new, self._items[new])

    @property
    def selected(self) -> str | None:
        return None if self._index is None else self._items[self._index]

    def select(self) -> None:
        if self._index is not None and self.on_select is not None:
            self.on_select(self._index, self._items[self._index])

    def content_width(self) -> int:
        return max((text_width(item) for item in self._items), default=0)

    def content_height(self, width: int) -> int:
        return len(self._items)

    def on_key(self, event: KeyEvent) -> bool:
        if not self._items:
            return False
        page = max(1, self.content_region.height - 1)
        index = self._index or 0
        moves = {
            "up": index - 1,
            "down": index + 1,
            "pageup": index - page,
            "pagedown": index + page,
            "home": 0,
            "end": len(self._items) - 1,
        }
        if event.key in moves:
            self.index = moves[event.key]
            return True
        if event.key in ("enter", "space"):
            self.select()
            return True
        return False

    def on_mouse(self, event: MouseEvent) -> bool:
        area = self.content_region
        if event.action == "down" and event.button == "left":
            row = self._top + event.y - area.y
            if 0 <= row < len(self._items):
                self.index = row
            return True
        if event.action in ("scroll_up", "scroll_down"):
            limit = max(0, len(self._items) - area.height)
            step = -3 if event.action == "scroll_up" else 3
            self._top = max(0, min(self._top + step, limit))
            self._follow = False
            return True
        return False

    def on_click(self, event: MouseEvent) -> bool:
        row = self._top + event.y - self.content_region.y
        if 0 <= row < len(self._items):
            self.select()
        return True

    def render(self, canvas: Canvas) -> None:
        area = self.content_region
        if area.empty:
            return
        if self._follow and self._index is not None:
            self._top = min(self._top, self._index)
            self._top = max(self._top, self._index - area.height + 1)
        self._top = max(0, min(self._top, max(0, len(self._items) - area.height)))
        style = self.text_style
        highlight = CellStyle.from_style(self.computed | self.highlight_style)
        for i, item in enumerate(self._items[self._top : self._top + area.height]):
            row_style = highlight if self._top + i == self._index else style
            y = area.y + i
            if row_style is highlight:
                canvas.fill(area._replace(y=y, height=1), highlight)
            canvas.text(area.x, y, truncate(item, area.width), row_style)


class ProgressBar(Widget):
    """A horizontal bar showing ``value`` between 0 and 1."""

    DEFAULT_STYLE = Style(height=1, fg="green", bg="bright_black")
    _PARTIAL = " ▏▎▍▌▋▊▉"

    def __init__(self, value: float = 0.0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.value = value

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, float(value)))

    def content_width(self) -> int:
        return 20

    def content_height(self, width: int) -> int:
        return 1

    def render(self, canvas: Canvas) -> None:
        area = self.content_region
        eighths = round(self._value * area.width * 8)
        full, partial = divmod(eighths, 8)
        bar = "█" * full + (self._PARTIAL[partial] if partial else "")
        for y in range(area.y, area.bottom):
            canvas.text(area.x, y, bar, self.text_style)

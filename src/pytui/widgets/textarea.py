"""An editable, multi-line text field."""

from __future__ import annotations

from typing import Any

from ..events import ChangeEvent, KeyEvent, MouseEvent, PasteEvent
from ..style import Style
from ..text import clean_text
from .values import Cursor, Value
from .widget import Text, Widget


class TextAreaValue(Value):
    text: str = ""

    def coerce(self, name: str, value: Any) -> Any:
        return clean_text(value)


class TextArea(Widget):
    """A text editor. ``textarea.value.text`` holds the text.

    The usual word and line shortcuts work, Shift extends the selection, and
    ``placeholder`` is shown dimmed while the text is empty. Tab is not
    captured so that focus can still move with the keyboard. For a single-line
    field, use ``height=1, text_wrap=False`` and bind Enter.
    """

    FOCUSABLE = True
    DEFAULT_STYLE = Style(min_height=1, disabled=Style(dim=True))
    PLACEHOLDER_STYLE = Style(dim=True)

    value: TextAreaValue  # type: ignore[assignment]

    def __init__(self, text: str = "", *, placeholder: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.placeholder = Text(placeholder, style=self.PLACEHOLDER_STYLE)
        self.mount(self.placeholder)
        self._goal_x: int | None = None
        self.value = TextAreaValue(text=text)
        self.cursor = len(self.value.text)

    # --- editing ------------------------------------------------------------

    def _caret(self) -> Cursor:
        return self.cursor or Cursor.at(len(self.value.text))

    def replace(self, start: int, end: int, text: str = "") -> None:
        """Replace ``value.text[start:end]`` with ``text`` and put the caret after it."""
        text = clean_text(text)
        current = self.value.text
        self._goal_x = None
        self.cursor = start + len(text)
        self.value.text = current[:start] + text + current[end:]

    def insert(self, text: str) -> None:
        """Insert ``text`` at the caret, replacing the selection."""
        cursor = self._caret()
        self.replace(cursor.start, cursor.end, text)

    def _move(self, index: int, extend: bool) -> None:
        index = max(0, min(index, len(self.value.text)))
        self.cursor = Cursor(self._caret().anchor if extend else index, index)

    def _word_left(self, i: int) -> int:
        text = self.value.text
        while i > 0 and not text[i - 1].isalnum():
            i -= 1
        while i > 0 and text[i - 1].isalnum():
            i -= 1
        return i

    def _word_right(self, i: int) -> int:
        text, n = self.value.text, len(self.value.text)
        while i < n and not text[i].isalnum():
            i += 1
        while i < n and text[i].isalnum():
            i += 1
        return i

    def _line_start(self, i: int) -> int:
        return self.value.text.rfind("\n", 0, i) + 1

    def _line_end(self, i: int) -> int:
        end = self.value.text.find("\n", i)
        return len(self.value.text) if end == -1 else end

    def _vertical(self, rows: int, extend: bool) -> None:
        x, y = self.position_of(self._caret().head)
        if self._goal_x is None:
            self._goal_x = x + self.scroll_x
        self._move(self.index_at(self._goal_x - self.scroll_x, y + rows), extend)

    # --- built-in behaviour -------------------------------------------------

    def handle_key(self, event: KeyEvent) -> bool:
        if event.is_printable:
            self.insert(event.char)  # type: ignore[arg-type]
            return True
        key = event.key
        cursor = self._caret()
        head, n = cursor.head, len(self.value.text)
        plain = key.replace("shift+", "")
        extend = event.shift

        page = max(1, self.content_region.height - 1)
        rows = {"up": -1, "down": 1, "pageup": -page, "pagedown": page}.get(plain)
        if rows is not None:
            self._vertical(rows, extend)
            return True
        self._goal_x = None

        moves = {
            "left": cursor.start if not cursor.collapsed and not extend else head - 1,
            "right": cursor.end if not cursor.collapsed and not extend else head + 1,
            "ctrl+left": self._word_left(head),
            "alt+left": self._word_left(head),
            "alt+b": self._word_left(head),
            "ctrl+right": self._word_right(head),
            "alt+right": self._word_right(head),
            "alt+f": self._word_right(head),
            "home": self._line_start(head),
            "ctrl+a": self._line_start(head),
            "end": self._line_end(head),
            "ctrl+e": self._line_end(head),
            "ctrl+home": 0,
            "ctrl+end": n,
        }
        if plain in moves:
            self._move(moves[plain], extend)
            return True

        if not cursor.collapsed and key in (
            "backspace",
            "delete",
            "ctrl+w",
            "alt+backspace",
            "ctrl+backspace",
            "alt+delete",
            "ctrl+delete",
            "alt+d",
        ):
            self.replace(cursor.start, cursor.end)
        elif key == "enter":
            self.insert("\n")
        elif key == "backspace":
            self.replace(max(0, head - 1), head)
        elif key == "delete":
            self.replace(head, min(n, head + 1))
        elif key in ("ctrl+w", "alt+backspace", "ctrl+backspace"):
            self.replace(self._word_left(head), head)
        elif key in ("alt+delete", "ctrl+delete", "alt+d"):
            self.replace(head, self._word_right(head))
        elif key == "ctrl+u":
            self.replace(self._line_start(head), head)
        elif key == "ctrl+k":
            self.replace(head, self._line_end(head))
        else:
            return super().handle_key(event)
        return True

    def handle_paste(self, event: PasteEvent) -> bool:
        self.insert(event.text)
        return True

    def handle_mouse(self, event: MouseEvent) -> bool:
        if event.button == "left" and event.action in ("down", "drag"):
            index = self.index_at(event.x, event.y)
            anchor = self._caret().anchor if event.action == "drag" else index
            self.cursor = Cursor(anchor, index)
            self._goal_x = None
            return True
        if event.action in ("scroll_up", "scroll_down"):
            self.scroll_by(dy=-3 if event.action == "scroll_up" else 3)
            return True
        return False

    def handle_change(self, event: ChangeEvent) -> bool:
        if event.widget is self:
            self.text = event.value
            self.placeholder.hidden = bool(event.value)
            n = len(self.text)
            cursor = self.cursor
            if cursor is not None and cursor.end > n:
                self.cursor = Cursor(min(cursor.anchor, n), min(cursor.head, n))
        return False

    def content_width(self) -> int:
        return 20  # like <textarea cols=20>: content must not resize the layout

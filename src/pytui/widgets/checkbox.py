"""A checkbox with a label."""

from __future__ import annotations

from typing import Any

from ..events import ChangeEvent, ClickEvent, KeyEvent
from ..style import Style
from .containers import Row
from .values import Value
from .widget import Text, Widget


class CheckboxValue(Value):
    checked: bool = False


class Checkbox(Row):
    """A mark (``[x]``) followed by its children, toggled by click, Enter or Space.

    ``checkbox.value.checked`` holds the state.
    """

    FOCUSABLE = True
    CHECKED = "[x]"
    UNCHECKED = "[ ]"
    DEFAULT_STYLE = Row.DEFAULT_STYLE | Style(
        gap=1,
        align_self="start",
        text_wrap=False,
        hover=Style(underline=True),
        focus=Style(fg="bright_cyan", bold=True),
        disabled=Style(dim=True),
    )

    value: CheckboxValue  # type: ignore[assignment]

    def __init__(self, *children: Widget | str, checked: bool = False, **kwargs: Any) -> None:
        self.mark = Text(self.UNCHECKED)
        super().__init__(self.mark, *children, **kwargs)
        self.value = CheckboxValue(checked=checked)

    def toggle(self) -> None:
        self.value.checked = not self.value.checked

    def handle_click(self, event: ClickEvent) -> bool:
        self.toggle()
        return True

    def handle_key(self, event: KeyEvent) -> bool:
        if event.key in ("enter", "space"):
            self.click()
            return True
        return super().handle_key(event)

    def handle_change(self, event: ChangeEvent) -> bool:
        if event.widget is self:
            self.mark.text = self.CHECKED if event.value else self.UNCHECKED
        return False

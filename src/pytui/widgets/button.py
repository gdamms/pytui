"""A clickable button."""

from __future__ import annotations

from ..events import KeyEvent
from ..style import Style
from .widget import Widget


class Button(Widget):
    """A focusable widget for which Enter and Space count as a click::

    Button("Save", on_click=lambda event: save())
    """

    FOCUSABLE = True
    DEFAULT_STYLE = Style(
        padding=(0, 1),
        align_self="start",
        justify_content="center",
        text_align="center",
        text_wrap=False,
        fg="bright_white",
        bg="bright_black",
        hover=Style(fg="black", bg="white"),
        focus=Style(fg="bright_white", bg="blue", bold=True),
        disabled=Style(fg="white", dim=True),
    )

    def handle_key(self, event: KeyEvent) -> bool:
        if event.key in ("enter", "space"):
            self.click()
            return True
        return super().handle_key(event)

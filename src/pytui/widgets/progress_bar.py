"""A horizontal progress bar."""

from __future__ import annotations

from typing import Any

from ..events import ChangeEvent
from ..style import Style
from .containers import Row
from .values import Value
from .widget import Text


class ProgressBarValue(Value):
    progress: float = 0.0

    def coerce(self, name: str, value: Any) -> Any:
        return max(0.0, min(1.0, float(value)))


class ProgressBar(Row):
    """A bar showing ``value.progress`` between 0 and 1.

    It is made of two lines of ``━``: the done part (in the bar's ``fg``) and
    the rest, sharing the width in proportion to the progress.
    """

    BAR = "━" * 512
    DEFAULT_STYLE = Row.DEFAULT_STYLE | Style(height=1, text_wrap=False, fg="magenta")

    value: ProgressBarValue  # type: ignore[assignment]

    def __init__(self, progress: float = 0.0, **kwargs: Any) -> None:
        self.done = Text(self.BAR, width=0)
        self.rest = Text(self.BAR, width=0, flex_grow=1, fg="bright_black")
        super().__init__(self.done, self.rest, **kwargs)
        self.value = ProgressBarValue(progress=progress)

    def handle_change(self, event: ChangeEvent) -> bool:
        if event.widget is self:
            self.done.set_style(flex_grow=event.value)
            self.rest.set_style(flex_grow=1 - event.value)
        return False

    def content_width(self) -> int:
        return 20

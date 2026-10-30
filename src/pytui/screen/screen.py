"""The interface between a canvas and wherever it is displayed."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..render import Canvas


class Screen(ABC):
    """Displays canvases; each screen decides how to bring itself up to date."""

    @abstractmethod
    def display(self, canvas: Canvas) -> None:
        """Make the screen show ``canvas``."""

    @abstractmethod
    def invalidate(self) -> None:
        """Forget what the screen shows: the next :meth:`display` redraws everything."""

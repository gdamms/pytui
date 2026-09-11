"""The base class of everything on screen."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from .canvas import Canvas, CellStyle
from .events import KeyEvent, MouseEvent, PasteEvent, normalize_key
from .geometry import Rect
from .style import DEFAULTS, Style

if TYPE_CHECKING:
    from .app import App

W = TypeVar("W", bound="Widget")

_SCROLL_KEYS = {"up", "down", "left", "right", "pageup", "pagedown", "home", "end"}


class Widget:
    """A node of the UI tree: a styled box that can hold children.

    Style can be given as a :class:`Style`, as keyword arguments, or both
    (keywords win)::

        Widget(Text("hi"), style=card, padding=1, border="rounded")

    Subclasses customize behaviour by overriding the hooks: ``content_width``,
    ``content_height`` and ``render`` for content, ``on_key``, ``on_mouse``,
    ``on_click``, ``on_paste``, ``on_focus`` and ``on_blur`` for interaction.
    """

    DEFAULT_STYLE: ClassVar[Style] = Style()
    """Base style for the class, overridden by the instance ``style``."""
    FOCUSABLE: ClassVar[bool] = False

    def __init__(
        self,
        *children: Widget,
        id: str | None = None,
        style: Style | None = None,
        focusable: bool | None = None,
        disabled: bool = False,
        **style_kwargs: Any,
    ) -> None:
        self.id = id
        self.style: Style = (style or Style()) | (Style(**style_kwargs) if style_kwargs else None)
        self.focusable = self.FOCUSABLE if focusable is None else focusable
        self.disabled = disabled
        self.border_title: str | None = None

        self.parent: Widget | None = None
        self._children: list[Widget] = []
        self._app: App | None = None
        self._bindings: dict[str, Callable[[], Any]] = {}

        # Set by the app on every frame.
        self.computed: Style = DEFAULTS
        self.region = Rect()
        self.content_region = Rect()
        self.virtual_width = 0
        self.virtual_height = 0
        self.scroll_x = 0
        self.scroll_y = 0
        self._paints_background = False
        self._effectively_disabled = disabled
        self._style_cache: tuple[object, ...] | None = None

        self.mount(*children)

    def __repr__(self) -> str:
        name = type(self).__name__
        return f"{name}(id={self.id!r})" if self.id else f"{name}()"

    # --- tree ---------------------------------------------------------------

    @property
    def children(self) -> tuple[Widget, ...]:
        return tuple(self._children)

    def mount(self, *widgets: Widget, index: int | None = None) -> None:
        """Add children (at the end, or before position ``index``)."""
        for offset, widget in enumerate(widgets):
            if widget is self or widget in self.ancestors():
                raise ValueError("a widget cannot contain itself")
            if widget.parent is not None:
                widget.remove()
            widget.parent = self
            if index is None:
                self._children.append(widget)
            else:
                self._children.insert(index + offset, widget)

    def remove(self) -> None:
        """Detach this widget from its parent."""
        if self.parent is not None:
            self.parent._children.remove(self)
            self.parent = None

    def clear(self) -> None:
        """Remove all children."""
        for child in self._children:
            child.parent = None
        self._children.clear()

    def walk(self) -> Iterator[Widget]:
        """This widget and all its descendants, depth-first in tree order."""
        yield self
        for child in self._children:
            yield from child.walk()

    def ancestors(self) -> Iterator[Widget]:
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def find(self, id: str) -> Widget | None:
        """The first descendant (or self) with the given id."""
        return next((w for w in self.walk() if w.id == id), None)

    def get(self, id: str, kind: type[W] = None) -> W:  # type: ignore[assignment]
        """Like :meth:`find` but raises if missing (and checks the type if given)."""
        widget = self.find(id)
        if widget is None:
            raise LookupError(f"no widget with id {id!r}")
        if kind is not None and not isinstance(widget, kind):
            raise TypeError(f"widget {id!r} is a {type(widget).__name__}, not {kind.__name__}")
        return widget  # type: ignore[return-value]

    def find_all(self, kind: type[W]) -> list[W]:
        return [w for w in self.walk() if isinstance(w, kind)]

    @property
    def app(self) -> App | None:
        node: Widget = self
        while node.parent is not None:
            node = node.parent
        return node._app

    # --- style & state ------------------------------------------------------

    def set_style(self, style: Style | None = None, **style_kwargs: Any) -> None:
        """Merge ``style`` and keyword style fields into this widget's style."""
        self.style = self.style | style | (Style(**style_kwargs) if style_kwargs else None)

    @property
    def hidden(self) -> bool:
        return self.style.display == "none"

    @hidden.setter
    def hidden(self, value: bool) -> None:
        values = self.style.set_fields()
        values["display"] = "none" if value else "flex"
        self.style = Style(**values)

    @property
    def is_disabled(self) -> bool:
        return self.disabled or any(a.disabled for a in self.ancestors())

    @property
    def has_focus(self) -> bool:
        app = self.app
        return app is not None and app.focused is self

    @property
    def is_hovered(self) -> bool:
        app = self.app
        return (
            app is not None
            and app.hovered is not None
            and (app.hovered is self or self in app.hovered.ancestors())
        )

    @property
    def can_focus(self) -> bool:
        if not self.focusable or self.is_disabled:
            return False
        if self.computed.visibility != "visible":
            return False
        return all(w.computed.display != "none" for w in (self, *self.ancestors()))

    def focus(self) -> None:
        app = self.app
        if app is None:
            raise RuntimeError("widget is not attached to an app")
        app.focus(self)

    @property
    def text_style(self) -> CellStyle:
        """Cell style for drawing this widget's text."""
        return CellStyle.from_style(self.computed)

    # --- key bindings -------------------------------------------------------

    def bind(self, keys: str, handler: Callable[[], Any]) -> None:
        """Call ``handler`` when a key is pressed while focus is in this widget.

        ``keys`` can list several keys separated by spaces: ``"ctrl+s f2"``.
        """
        for key in keys.split():
            self._bindings[normalize_key(key)] = handler

    def unbind(self, keys: str) -> None:
        for key in keys.split():
            self._bindings.pop(normalize_key(key), None)

    # --- scrolling ----------------------------------------------------------

    @property
    def max_scroll_x(self) -> int:
        return max(0, self.virtual_width - self.content_region.width)

    @property
    def max_scroll_y(self) -> int:
        return max(0, self.virtual_height - self.content_region.height)

    def scroll_to(self, x: int | None = None, y: int | None = None) -> None:
        if x is not None:
            self.scroll_x = max(0, min(x, self.max_scroll_x))
        if y is not None:
            self.scroll_y = max(0, min(y, self.max_scroll_y))

    def scroll_by(self, dx: int = 0, dy: int = 0) -> None:
        self.scroll_to(self.scroll_x + dx, self.scroll_y + dy)

    # --- hooks --------------------------------------------------------------

    def content_width(self) -> int:
        """Intrinsic width of the widget's own content (excluding children)."""
        return 0

    def content_height(self, width: int) -> int:
        """Height of the widget's own content when laid out ``width`` cells wide."""
        return 0

    def render(self, canvas: Canvas) -> None:
        """Draw the widget's own content inside ``self.content_region``.

        Background, border and children are drawn by the app.
        """

    def on_key(self, event: KeyEvent) -> bool:
        """Handle a key; return True to stop propagation to ancestors."""
        if self.computed.overflow != "scroll" or event.key not in _SCROLL_KEYS:
            return False
        page = max(1, self.content_region.height - 1)
        dx, dy = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
            "pageup": (0, -page),
            "pagedown": (0, page),
            "home": (0, -self.virtual_height),
            "end": (0, self.virtual_height),
        }[event.key]
        self.scroll_by(dx, dy)
        return True

    def on_mouse(self, event: MouseEvent) -> bool:
        """Handle a mouse event; return True to stop propagation to ancestors."""
        if self.computed.overflow != "scroll":
            return False
        delta = {
            "scroll_up": (0, -3),
            "scroll_down": (0, 3),
            "scroll_left": (-3, 0),
            "scroll_right": (3, 0),
        }
        if event.action not in delta:
            return False
        before = (self.scroll_x, self.scroll_y)
        self.scroll_by(*delta[event.action])
        return (self.scroll_x, self.scroll_y) != before

    def on_click(self, event: MouseEvent) -> bool:
        """Handle a left click (press and release on this widget)."""
        return False

    def on_paste(self, event: PasteEvent) -> bool:
        return False

    def on_focus(self) -> None:
        pass

    def on_blur(self) -> None:
        pass

"""The base class of everything on screen."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from ..events import ChangeEvent, ClickEvent, KeyEvent, MouseEvent, PasteEvent, normalize_key
from ..geometry import Rect
from ..render.canvas import Canvas, CellStyle
from ..style import DEFAULTS, ComputedStyle, Style
from ..text import clean_text, index_at_cell, text_width, wrap_spans
from .values import Cursor, Value

if TYPE_CHECKING:
    from ..app import App

W = TypeVar("W", bound="Widget")

_SCROLL_KEYS = {"up", "down", "left", "right", "pageup", "pagedown", "home", "end"}


class Widget:
    """Everything on screen: a styled box that can show text, hold state,
    contain children and react to input.

    ``text`` is painted inside the box like a background; children are laid out
    over it, and the box is as big as whichever needs more room. Strings among
    the children become :class:`Text` widgets. Style can be given as a
    :class:`Style`, as keyword arguments, or both (keywords win)::

        Widget("hi", style=card, padding=1, border="rounded")

    ``on_click``, ``on_key`` and ``on_change`` are your callbacks: they receive
    the event and stop it from going further only by returning ``True``.
    Built-in behaviour lives in the ``handle_*`` methods, which run after your
    callbacks (except ``handle_change``, which runs first so ``on_change`` sees
    an up-to-date widget) and stop the event unless they return ``False``.
    """

    DEFAULT_STYLE: ClassVar[Style] = Style()
    """Base style for the class, overridden by the instance ``style``."""
    FOCUSABLE: ClassVar[bool] = False

    def __init__(
        self,
        *children: Widget | str,
        text: str = "",
        cursor: Cursor | int | None = None,
        on_click: Callable[[ClickEvent], Any] | None = None,
        on_key: Callable[[KeyEvent], Any] | None = None,
        on_change: Callable[[ChangeEvent], Any] | None = None,
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
        self.on_click = on_click
        self.on_key = on_key
        self.on_change = on_change
        self.text = text
        self.cursor = cursor
        self._value: Value | None = None
        self._spans: tuple[str, int, bool, list[tuple[int, int]]] | None = None
        self._revealed: object = None

        self.parent: Widget | None = None
        self._children: list[Widget] = []
        self._app: App | None = None
        self._bindings: dict[str, Callable[[], Any]] = {}

        # Set by the app on every frame.
        self.computed: ComputedStyle = DEFAULTS.resolve(None)
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

    def mount(self, *widgets: Widget | str, index: int | None = None) -> None:
        """Add children (at the end, or before position ``index``); strings become Text."""
        for offset, item in enumerate(widgets):
            widget = Text(item) if isinstance(item, str) else item
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
    def text(self) -> str:
        """Text painted inside the box, under the children."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = clean_text(value)

    @property
    def cursor(self) -> Cursor | None:
        """Caret and selection in ``text``, drawn while the widget has focus."""
        return self._cursor

    @cursor.setter
    def cursor(self, value: Cursor | int | None) -> None:
        self._cursor = Cursor.at(value) if isinstance(value, int) else value

    @property
    def value(self) -> Value | None:
        """The widget's state; assigning its fields triggers ``on_change``."""
        return self._value

    @value.setter
    def value(self, value: Value | None) -> None:
        if self._value is not None:
            object.__setattr__(self._value, "_owner", None)
        self._value = value
        if value is not None:
            object.__setattr__(value, "_owner", self)
            for name in value._fields:  # let the built-in behaviour sync with the new state
                self.handle_change(ChangeEvent(self, name, getattr(value, name), None))

    def _value_changed(self, name: str, value: Any, old: Any) -> None:
        event = ChangeEvent(self, name, value, old)
        for widget in (self, *self.ancestors()):
            stop = widget.handle_change(event) is not False
            if widget.on_change is not None and widget.on_change(event) is True:
                stop = True
            if stop:
                return

    def click(self, mouse: MouseEvent | None = None) -> None:
        """Click this widget: ``on_click`` then ``handle_click``, bubbling up."""
        event = ClickEvent(self, mouse)
        for widget in (self, *self.ancestors()):
            if widget.is_disabled:
                continue
            if widget.on_click is not None and widget.on_click(event) is True:
                return
            if widget.handle_click(event) is not False:
                return

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

    # --- text layout --------------------------------------------------------

    def text_lines(self, width: int) -> list[tuple[int, int]]:
        """Lines of ``text`` laid out ``width`` cells wide, as ``(start, end)`` offsets."""
        wrapping = bool(self.computed.text_wrap)
        cache = self._spans
        if cache is not None and cache[:3] == (self._text, width, wrapping):
            return cache[3]
        spans = wrap_spans(self._text, width if wrapping else 0)
        self._spans = (self._text, width, wrapping, spans)
        return spans

    def text_size(self, width: int) -> tuple[int, int]:
        """Cells needed by ``text`` laid out ``width`` cells wide (room for the caret included)."""
        caret = self._cursor is not None and not self.computed.text_wrap
        if not self._text:
            return int(caret), 0
        spans = self.text_lines(width)
        widest = max(text_width(self._text[s:e]) for s, e in spans)
        return widest + caret, len(spans)

    def _line_x(self, start: int, end: int) -> int:
        area = self.content_region
        align = self.computed.text_align
        offset = 0
        if align != "left":
            slack = max(0, area.width - text_width(self._text[start:end]))
            offset = slack // 2 if align == "center" else slack
        return area.x + offset - self.scroll_x

    def position_of(self, index: int) -> tuple[int, int]:
        """Screen cell where the character at ``index`` of ``text`` is drawn."""
        area = self.content_region
        spans = self.text_lines(area.width)
        index = max(0, min(index, len(self._text)))
        row = max(0, bisect_right([s for s, _ in spans], index) - 1)
        start, end = spans[row]
        x = self._line_x(start, end) + text_width(self._text[start : min(index, end)])
        return x, area.y + row - self.scroll_y

    def index_at(self, x: int, y: int) -> int:
        """Index in ``text`` of the character drawn at screen cell ``(x, y)`` (clamped)."""
        area = self.content_region
        spans = self.text_lines(area.width)
        row = max(0, min(y - area.y + self.scroll_y, len(spans) - 1))
        start, end = spans[row]
        cell = x - self._line_x(start, end)
        return start + index_at_cell(self._text[start:end], max(0, cell))

    def reveal_cursor(self) -> None:
        """Scroll so the caret is visible, if the cursor or text moved since last time."""
        area = self.content_region
        key = (self._cursor, self._text, area.width, area.height)
        if self._cursor is None or key == self._revealed:
            return
        self._revealed = key
        x, y = self.position_of(self._cursor.head)
        dx = dy = 0
        if y < area.y:
            dy = y - area.y
        elif y >= area.bottom:
            dy = y - area.bottom + 1
        if x < area.x:
            dx = x - area.x
        elif x >= area.right:
            dx = x - area.right + 1
        self.scroll_by(dx, dy)

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
        if not self._text:
            return 0
        return max(text_width(line) for line in self._text.split("\n"))

    def content_height(self, width: int) -> int:
        """Height of the widget's own content when laid out ``width`` cells wide."""
        return len(self.text_lines(width)) if self._text else 0

    def render(self, canvas: Canvas) -> None:
        """Draw the widget's own content (its text) inside ``self.content_region``.

        Background, border, children and the cursor are drawn by the app.
        """
        if not self._text:
            return
        area = self.content_region
        style = self.text_style
        spans = self.text_lines(area.width)
        for row in range(area.height):
            if row + self.scroll_y >= len(spans):
                break
            start, end = spans[row + self.scroll_y]
            canvas.text(self._line_x(start, end), area.y + row, self._text[start:end], style)

    def render_cursor(self, canvas: Canvas) -> None:
        """Draw the selection and caret over the text and children (only while focused)."""
        cursor = self._cursor
        if cursor is None or not self.has_focus:
            return
        area = self.content_region
        style = self.text_style
        inverse = style._replace(reverse=not style.reverse)
        text = self._text
        if cursor.collapsed:
            head = min(cursor.head, len(text))
            x, y = self.position_of(head)
            under = text[head] if head < len(text) and text[head] != "\n" else " "
            canvas.text(x, y, under, inverse)
            return
        sel_start, sel_end = min(cursor.start, len(text)), min(cursor.end, len(text))
        for row, (start, end) in enumerate(self.text_lines(area.width)):
            lo, hi = max(start, sel_start), min(end, sel_end)
            if lo < hi:
                x = self._line_x(start, end) + text_width(text[start:lo])
                canvas.text(x, area.y + row - self.scroll_y, text[lo:hi], inverse)

    def handle_key(self, event: KeyEvent) -> bool:
        """Built-in key handling; return False to let the key go to the parent."""
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

    def handle_mouse(self, event: MouseEvent) -> bool:
        """Built-in mouse handling; return False to let the event go to the parent."""
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

    def handle_click(self, event: ClickEvent) -> bool:
        """Built-in click behaviour; return False to let the click go to the parent."""
        return False

    def handle_change(self, event: ChangeEvent) -> bool:
        """Built-in reaction to a value change (also called with ``old=None`` when
        a value is assigned); return False to let the change bubble up."""
        return False

    def handle_paste(self, event: PasteEvent) -> bool:
        return False

    def handle_focus(self) -> None:
        pass

    def handle_blur(self) -> None:
        pass


class Text(Widget):
    """Just text: ``Text("hi")`` is ``Widget(text="hi")``."""

    def __init__(self, text: str = "", **kwargs: Any) -> None:
        super().__init__(text=text, **kwargs)

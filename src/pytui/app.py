"""The application: event loop, focus, event dispatch, timers and rendering."""

from __future__ import annotations

import heapq
import itertools
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator
from functools import partial
from typing import Any

from .events import (
    Event,
    InputParser,
    KeyEvent,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
    normalize_key,
    parse_key,
)
from .layout import LayoutEngine
from .render import Canvas, paint, widget_at
from .screen import Terminal, TerminalScreen
from .widgets import Widget

ESCAPE_TIMEOUT = 0.05
"""Seconds to wait before treating a lone ESC byte as the Escape key."""


class Timer:
    """A scheduled callback, returned by :meth:`App.call_later` and :meth:`App.set_interval`."""

    def __init__(self, when: float, interval: float | None, callback: Callable[[], Any]) -> None:
        self.when = when
        self.interval = interval
        self.callback = callback
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


def _chain(widget: Widget | None) -> Iterator[Widget]:
    while widget is not None:
        yield widget
        widget = widget.parent


class App:
    """Runs a widget tree in the terminal.

    ::

        app = App(Box("Hello", Button("Quit", on_click=lambda e: app.exit())))
        app.run()

    ``ctrl+c`` exits by default; ``tab``/``shift+tab`` move focus.
    """

    def __init__(self, root: Widget, *, mouse: bool = True, autofocus: bool = True) -> None:
        if root.parent is not None:
            raise ValueError("the root widget must not have a parent")
        self.root = root
        root._app = self
        self.mouse = mouse
        self.autofocus = autofocus
        self.size: tuple[int, int] = (80, 24)
        self.focused: Widget | None = None
        self.hovered: Widget | None = None

        self._bindings: dict[str, Callable[[], Any]] = {}
        self._pressed: Widget | None = None
        self._reveal: Widget | None = None
        self._parser = InputParser()
        self._layout = LayoutEngine()
        self._timers: list[tuple[float, int, Timer]] = []
        self._timer_ids = itertools.count()
        self._calls: deque[Callable[[], Any]] = deque()
        self._lock = threading.Lock()
        self._terminal: Terminal | None = None
        self.canvas = Canvas(*self.size)
        self._rendered = False
        self._running = False
        self._result: Any = None

        self.bind("ctrl+c", self.exit)

    # --- running ------------------------------------------------------------

    def run(self) -> Any:
        """Take over the terminal until :meth:`exit` is called; returns the exit value."""
        if self._running:
            raise RuntimeError("app is already running")
        with Terminal(mouse=self.mouse) as terminal:
            self._terminal = terminal
            self._running = True
            previous_screen = self.canvas.screen
            self.canvas.screen = TerminalScreen(terminal)
            try:
                self.size = terminal.size()
                self._draw()
                self._loop(terminal)
            finally:
                self._running = False
                self._terminal = None
                self.canvas.screen = previous_screen
        return self._result

    def _loop(self, terminal: Terminal) -> None:
        last_input = time.monotonic()
        while self._running:
            data = terminal.read(self._timeout())
            now = time.monotonic()
            events: list[Event] = []
            if data:
                events.extend(self._parser.feed(data))
                last_input = now
            elif self._parser.pending and now - last_input >= ESCAPE_TIMEOUT:
                events.extend(self._parser.flush())
            size = terminal.size()
            if size != self.size:
                events.append(ResizeEvent(*size))
            for event in events:
                self.dispatch(event)
            busy = self._run_timers(time.monotonic())
            busy = self._run_calls() or busy
            if self._running and (events or busy):
                self._draw()

    def exit(self, result: Any = None) -> None:
        """Stop the app; :meth:`run` returns ``result``."""
        self._result = result
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def _timeout(self) -> float | None:
        timeout = None
        if self._timers:
            timeout = max(0.0, self._timers[0][0] - time.monotonic())
        if self._parser.pending:
            timeout = ESCAPE_TIMEOUT if timeout is None else min(timeout, ESCAPE_TIMEOUT)
        with self._lock:
            if self._calls:
                timeout = 0
        return timeout

    def _draw(self) -> None:
        self.render()
        self.canvas.present()

    # --- timers & threads ---------------------------------------------------

    def call_later(self, delay: float, callback: Callable[[], Any]) -> Timer:
        """Run ``callback`` once after ``delay`` seconds."""
        return self._schedule(Timer(time.monotonic() + delay, None, callback))

    def set_interval(self, interval: float, callback: Callable[[], Any]) -> Timer:
        """Run ``callback`` every ``interval`` seconds until the timer is cancelled."""
        if interval <= 0:
            raise ValueError("interval must be positive")
        return self._schedule(Timer(time.monotonic() + interval, interval, callback))

    def _schedule(self, timer: Timer) -> Timer:
        heapq.heappush(self._timers, (timer.when, next(self._timer_ids), timer))
        return timer

    def _run_timers(self, now: float) -> bool:
        ran = False
        while self._timers and self._timers[0][0] <= now:
            _, _, timer = heapq.heappop(self._timers)
            if timer.cancelled:
                continue
            timer.callback()
            ran = True
            if timer.interval is not None and not timer.cancelled:
                timer.when = max(timer.when + timer.interval, now)
                self._schedule(timer)
        return ran

    def call_from_thread(self, callback: Callable[..., Any], *args: Any) -> None:
        """Run ``callback(*args)`` on the UI thread (thread-safe); the screen is redrawn after."""
        with self._lock:
            self._calls.append(partial(callback, *args))
        if self._terminal is not None:
            self._terminal.wake()

    def _run_calls(self) -> bool:
        with self._lock:
            calls = list(self._calls)
            self._calls.clear()
        for call in calls:
            call()
        return bool(calls)

    # --- focus --------------------------------------------------------------

    def focus(self, widget: Widget | None) -> None:
        """Give keyboard focus to ``widget`` (or remove focus with ``None``)."""
        if widget is self.focused:
            return
        previous, self.focused = self.focused, widget
        if previous is not None:
            previous.handle_blur()
        if widget is not None:
            widget.handle_focus()
            self._reveal = widget

    def focus_next(self, step: int = 1) -> None:
        candidates = [w for w in self.root.walk() if w.can_focus]
        if not candidates:
            return
        if self.focused in candidates:
            index = (candidates.index(self.focused) + step) % len(candidates)
        else:
            index = 0 if step > 0 else len(candidates) - 1
        self.focus(candidates[index])

    def focus_previous(self) -> None:
        self.focus_next(-1)

    # --- bindings -----------------------------------------------------------

    def bind(self, keys: str, handler: Callable[[], Any]) -> None:
        """Global key binding, used when no focused widget handles the key."""
        for key in keys.split():
            self._bindings[normalize_key(key)] = handler

    def unbind(self, keys: str) -> None:
        for key in keys.split():
            self._bindings.pop(normalize_key(key), None)

    # --- events -------------------------------------------------------------

    def dispatch(self, event: Event) -> None:
        if isinstance(event, KeyEvent):
            self._dispatch_key(event)
        elif isinstance(event, MouseEvent):
            self._dispatch_mouse(event)
        elif isinstance(event, PasteEvent):
            for widget in self._enabled_chain(self.focused):
                if widget.handle_paste(event) is not False:
                    break
        elif isinstance(event, ResizeEvent):
            self.size = (event.width, event.height)
            if self.canvas.screen is not None:
                self.canvas.screen.invalidate()

    def _enabled_chain(self, widget: Widget | None) -> Iterator[Widget]:
        return (w for w in _chain(widget) if not w.is_disabled)

    def _dispatch_key(self, event: KeyEvent) -> None:
        """For each widget from the focused one up: bindings, ``on_key``, ``handle_key``."""
        key = event.key
        for widget in self._enabled_chain(self.focused or self.root):
            handler = widget._bindings.get(key)
            if handler is not None:
                handler()
                return
            if widget.on_key is not None and widget.on_key(event) is True:
                return
            if widget.handle_key(event) is not False:
                return
        handler = self._bindings.get(key)
        if handler is not None:
            handler()
        elif key == "tab":
            self.focus_next()
        elif key == "shift+tab":
            self.focus_previous()

    def _dispatch_mouse(self, event: MouseEvent) -> None:
        if not self._rendered:
            self.render()
        target = widget_at(self.root, event.x, event.y)
        self.hovered = target
        if event.action == "down":
            for widget in _chain(target):
                if widget.can_focus:
                    self.focus(widget)
                    break
            self._pressed = target if event.button == "left" else None
        for widget in self._enabled_chain(target):
            if widget.handle_mouse(event) is not False:
                break
        if event.action == "up" and event.button in ("left", None):
            pressed, self._pressed = self._pressed, None
            clicked = None
            if pressed is not None and target is not None:
                if pressed is target or pressed in target.ancestors():
                    clicked = pressed
                elif target in pressed.ancestors():
                    clicked = target
            if clicked is not None:
                clicked.click(event)

    # --- rendering ----------------------------------------------------------

    def _update_styles(
        self, widget: Widget, parent: Widget | None, focus_path: set[int], hover_path: set[int]
    ) -> None:
        disabled = widget.disabled or (parent is not None and parent._effectively_disabled)
        widget._effectively_disabled = disabled
        state = (
            disabled,
            id(widget) in focus_path,
            id(widget) in hover_path,
            widget is self.focused,
        )
        default, own = type(widget).DEFAULT_STYLE, widget.style
        parent_style = parent.computed if parent is not None else None
        cache = widget._style_cache
        # Styles are immutable: recompute only when an input changed, and keep the
        # previous object when the result is equal so that children stay cached too.
        if (
            cache is None
            or cache[0] is not default
            or cache[1] is not own
            or cache[2] != state
            or cache[3] is not parent_style
        ):
            base = default | own
            style = base
            if disabled:
                style = style | base.disabled
            else:
                if state[1]:
                    style = style | base.focus_within
                if state[2]:
                    style = style | base.hover
                if state[3]:
                    style = style | base.focus
            widget._paints_background = style.bg is not None or bool(style.reverse)
            computed = style.resolve(parent_style)
            if computed != widget.computed:
                widget.computed = computed
            widget._style_cache = (default, own, state, parent_style)
        for child in widget.children:
            self._update_styles(child, widget, focus_path, hover_path)

    def render(self, width: int | None = None, height: int | None = None) -> None:
        """Lay out and draw the UI into :attr:`canvas` (no terminal needed).

        Useful for tests: ``app.render(40, 10)`` then ``app.canvas.lines()``. To display
        it without a terminal, give the canvas a screen:
        ``app.canvas.screen = FileScreen(path)`` then ``app.canvas.present()``.
        """
        if width is not None and height is not None:
            self.size = (width, height)
        w, h = self.size

        focused = self.focused
        if focused is not None and (
            focused.is_disabled or self.root not in (focused, *focused.ancestors())
        ):
            self.focus(None)

        self._compose(w, h)
        if self.focused is not None and not self.focused.can_focus:
            self.focus(None)
        if self.autofocus and self.focused is None and not self._rendered:
            self.focus_next()
            if self.focused is not None:
                self._compose(w, h)
        if self._reveal is not None:
            widget, self._reveal = self._reveal, None
            if self._scroll_into_view(widget):
                self._compose(w, h)

        canvas = self.canvas
        canvas.resize(w, h)
        canvas.clear()
        paint(self.root, canvas)
        self._rendered = True

    def _compose(self, width: int, height: int) -> None:
        focus_path = {id(w) for w in _chain(self.focused)}
        hover_path = {id(w) for w in _chain(self.hovered)}
        self._update_styles(self.root, None, focus_path, hover_path)
        self._layout.layout(self.root, width, height)

    def _scroll_into_view(self, widget: Widget) -> bool:
        """Scroll ancestors so ``widget`` is visible; True if anything moved."""
        region = widget.region
        top, bottom, left, right = region.y, region.bottom, region.x, region.right
        moved = False
        for ancestor in widget.ancestors():
            if ancestor.computed.overflow != "scroll":
                continue
            view = ancestor.content_region
            dy = 0
            if bottom > view.bottom:
                dy = bottom - view.bottom
            if top - dy < view.y:
                dy = top - view.y
            dx = 0
            if right > view.right:
                dx = right - view.right
            if left - dx < view.x:
                dx = left - view.x
            old = (ancestor.scroll_x, ancestor.scroll_y)
            ancestor.scroll_by(dx, dy)
            dx, dy = ancestor.scroll_x - old[0], ancestor.scroll_y - old[1]
            top, bottom, left, right = top - dy, bottom - dy, left - dx, right - dx
            moved = moved or (dx, dy) != (0, 0)
        return moved

    # --- testing helpers ----------------------------------------------------

    def snapshot(self, width: int | None = None, height: int | None = None) -> str:
        """Render to plain text (trailing spaces stripped), handy for tests."""
        self.render(width, height)
        return "\n".join(line.rstrip() for line in self.canvas.lines())

    def feed(self, data: str) -> None:
        """Simulate terminal input (keys, escape sequences, mouse reports) without a terminal."""
        if not self._rendered:
            self.render()
        for event in self._parser.feed(data) + self._parser.flush():
            self.dispatch(event)
            self._run_calls()
            self.render()
        if self._run_calls():
            self.render()

    def press(self, *keys: str) -> None:
        """Simulate key presses by binding name, e.g. ``app.press("tab", "enter", "ctrl+s")``."""
        for key in keys:
            mods, name = parse_key(key)
            char = name if len(name) == 1 else (" " if name == "space" else None)
            event = KeyEvent(
                name, char, ctrl="ctrl" in mods, alt="alt" in mods, shift="shift" in mods
            )
            if not self._rendered:
                self.render()
            self.dispatch(event)
            self._run_calls()
            self.render()

    def click(self, x: int, y: int, button: str = "left") -> None:
        """Simulate a mouse click at screen coordinates."""
        for action in ("down", "up"):
            if not self._rendered:
                self.render()
            self.dispatch(MouseEvent(action, x, y, button))  # type: ignore[arg-type]
            self.render()

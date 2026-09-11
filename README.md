# pytui

Build terminal user interfaces in Python with ideas borrowed from HTML/CSS:
a tree of widgets, typed styles, and a flexbox layout engine.

- **Flexbox layout**: `direction`, `flex_grow`/`flex_shrink`, `gap`, `justify_content`,
  `align_items`, percentages, min/max sizes, margins, padding, borders, absolute positioning,
  scrollable containers.
- **Styles as objects**: `Style(...)` merged with `|`, inherited text attributes, and
  `hover` / `focus` / `focus_within` / `disabled` state variants.
- **Widgets**: `Box`, `Row`, `Column`, `Text`, `Button`, `Checkbox`, `Input`, `TextArea`,
  `ListView`, `ProgressBar`, and an easy way to write your own.
- **Input**: keyboard with modifiers, mouse (click, drag, hover, wheel), bracketed paste,
  focus navigation with Tab.
- **Efficient rendering**: an in-memory cell buffer diffed against the previous frame, so only
  changed cells are written. Wide (CJK/emoji) characters are handled.
- **Testable**: render to text and simulate input without a terminal.
- **Zero dependencies**, pure Python >= 3.11 (Linux/macOS). (Might work with lower Python versions, but not tested.)

## Install

```sh
git clone https://github.com/gdamms/pytui.git
uv add pytui
```

One day, I'll publish it to PyPI...

## Quick start

```python
from pytui import App, Box, Button, Row, Text

count = Text("Clicked 0 times")
clicks = 0

def on_click():
    global clicks
    clicks += 1
    count.text = f"Clicked {clicks} times"

app = App(
    Box(
        Text("Hello from pytui!", bold=True, fg="cyan"),
        count,
        Row(Button("Click me", on_press=on_click), Button("Quit", on_press=lambda: app.exit()), gap=2),
        border="rounded", title="hello", padding=(1, 2), gap=1,
        align_items="center", justify_content="center",
    )
)
app.run()
```

The screen is redrawn automatically after every event, timer or thread callback, so
changing widget attributes (`count.text = ...`) is all it takes to update the UI.

Try the examples:

```sh
uv run examples/hello.py      # from the quick start
uv run examples/notes.py      # list + editor, key bindings, focus styles
uv run examples/dashboard.py  # timers, background thread, scrolling log
```

## Layout

Every widget is a flex container, like `display: flex` in CSS. Children are laid out along the
main axis (`direction`, default `"column"`) and aligned on the cross axis.

| Property | Values | Default |
| --- | --- | --- |
| `width`, `height` | `int` cells, `"50%"` of the parent, `"auto"` | `"auto"` (fit content) |
| `min_width`, `max_width`, `min_height`, `max_height` | same | none |
| `box_sizing` | `"border-box"`, `"content-box"` | `"border-box"` |
| `margin`, `padding` | `1`, `(vertical, horizontal)`, `(top, right, bottom, left)` | `0` |
| `border` | `"none"`, `"single"`, `"double"`, `"rounded"`, `"heavy"`, `"ascii"`, `"blank"` or 8 custom chars | `"none"` |
| `direction` | `"row"`, `"column"` | `"column"` |
| `gap` | `int` | `0` |
| `justify_content` | `"start"`, `"center"`, `"end"`, `"space-between"`, `"space-around"`, `"space-evenly"` | `"start"` |
| `align_items` | `"start"`, `"center"`, `"end"`, `"stretch"` | `"stretch"` |
| `align_self` | `"auto"` or an `align_items` value | `"auto"` |
| `flex_grow`, `flex_shrink` | `float` | `0`, `1` |
| `position` | `"relative"`, `"absolute"` (with `top`/`right`/`bottom`/`left`) | `"relative"` |
| `display` | `"flex"`, `"none"` (removed from layout) | `"flex"` |
| `visibility` | `"visible"`, `"hidden"` (keeps its space) | `"visible"` |
| `overflow` | `"hidden"`, `"visible"`, `"scroll"` | `"hidden"` |

```python
Row(
    Box(sidebar, width=30, flex_shrink=0, border="rounded", title="Files"),
    Box(editor, flex_grow=1, border="rounded"),               # takes the remaining space
    Box(help_panel, width="25%", display="none", id="help"),  # toggled later
)
```

`overflow="scroll"` makes a container scrollable. Its children keep their natural size, and it
scrolls with the mouse wheel, with the keyboard when it is focusable (`focusable=True`), and
automatically to reveal the focused widget. A scrollbar is drawn on the right border, or in a
reserved column if there is no border.

## Styling

Style fields can be passed as keyword arguments or as a `Style` object. Styles combine with
`|`, and the right-hand side wins:

```python
from pytui import Style

card = Style(border="rounded", padding=(0, 1), border_fg="bright_black")
active = card | Style(border_fg="cyan", bold=True)

Box(Text("hello"), style=card, margin=1)  # keywords are merged on top of `style`
widget.set_style(fg="red")                # change it later
```

- **Text attributes** `fg`, `bg`, `bold`, `dim`, `italic`, `underline`, `strike`, `reverse`,
  `text_align`, `text_wrap` are **inherited** by children.
- **Colors**: names (`"red"`, `"bright_blue"`, `"gray"`, `"default"`), `"#rrggbb"`, or a
  256-color index.
- **States** are nested styles applied while the state is active:

```python
Button("Save", style=Style(
    bg="green",
    hover=Style(bg="bright_green"),
    focus=Style(bold=True, underline=True),
    disabled=Style(dim=True),
))
Box(..., focus_within=Style(border_fg="cyan"))  # when a descendant has focus
```

Each widget class has a `DEFAULT_STYLE` that instance styles override. To theme a widget
everywhere, subclass it:

```python
class DangerButton(Button):
    DEFAULT_STYLE = Button.DEFAULT_STYLE | Style(bg="red", focus=Style(bg="bright_red"))
```

## Widgets

| Widget | Purpose | Callbacks |
| --- | --- | --- |
| `Box(*children, title=None)` | Generic container (`Row` / `Column` preset the direction) | |
| `Text(text)` | Text, word-wrapped unless `text_wrap=False` | |
| `Button(label)` | Pressed with click, Enter or Space | `on_press()` |
| `Checkbox(label, checked)` | Toggle | `on_change(checked)` |
| `Input(value, placeholder=, password=)` | Single-line text field | `on_change(value)`, `on_submit(value)` |
| `TextArea(value)` | Multi-line editor | `on_change(value)` |
| `ListView(items)` | Scrollable list with a highlighted row | `on_select(i, item)`, `on_highlight(i, item)` |
| `ProgressBar(value)` | `value` between 0 and 1 | |

Common widget API: `id=`, `disabled=`, `focusable=`, `mount(*children)`, `remove()`,
`clear()`, `find(id)`, `get(id, Type)`, `walk()`, `focus()`, `hidden = True`, `bind(key, fn)`,
`scroll_to()`, and `region` / `content_region` (screen rectangles after layout).

## Events, focus and key bindings

- Keys go to the focused widget, then bubble up through its ancestors, then to app bindings.
  Tab / Shift+Tab move focus if nothing handled the key.
- Mouse events go to the widget under the pointer and bubble up. A press focuses the nearest
  focusable widget, and press+release on the same widget is a click.
- Key names look like `"a"`, `"A"`, `"space"`, `"enter"`, `"escape"`, `"tab"`, `"shift+tab"`,
  `"up"`, `"pageup"`, `"f5"`, `"ctrl+s"`, `"alt+x"`, `"ctrl+shift+left"`.

```python
app.bind("ctrl+q", app.exit)                      # global
editor.bind("ctrl+s", save)                       # only while focus is inside `editor`
app.bind("f1 ctrl+h", lambda: help.set_style(display="flex"))
```

`ctrl+c` exits by default (`app.unbind("ctrl+c")` to disable). `app.run()` returns the value
passed to `app.exit(value)`.

## Timers and threads

```python
timer = app.set_interval(1.0, update_clock)  # timer.cancel() to stop
app.call_later(0.5, lambda: status.set_style(display="none"))

def worker():                                # in another thread
    result = slow_computation()
    app.call_from_thread(show_result, result)  # thread-safe, redraws afterwards
```

## Custom widgets

Subclass `Widget`, describe the content size, and draw into the canvas:

```python
from pytui import Style, Widget

class Counter(Widget):
    FOCUSABLE = True
    DEFAULT_STYLE = Style(padding=(0, 1), focus=Style(reverse=True))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = 0

    def content_width(self) -> int:
        return len(f"count: {self.value}")

    def content_height(self, width: int) -> int:
        return 1

    def render(self, canvas):
        area = self.content_region
        canvas.text(area.x, area.y, f"count: {self.value}", self.text_style)

    def on_key(self, event) -> bool:
        if event.key in ("up", "+"):
            self.value += 1
            return True  # handled: stop propagation
        if event.key in ("down", "-"):
            self.value -= 1
            return True
        return False
```

Background, border, children and clipping are handled for you. Other hooks are `on_mouse`,
`on_click`, `on_paste`, `on_focus` and `on_blur`.

## Testing your UI

No terminal needed: render to text and simulate input.

```python
def test_login_form():
    name = Input(id="name")
    submitted = []
    app = App(Box(name, Button("Login", on_press=lambda: submitted.append(name.value))))

    app.render(40, 5)
    app.feed("alice")          # raw terminal input: text, escape sequences, mouse reports
    app.press("tab", "enter")  # key names
    assert submitted == ["alice"]
    assert "alice" in app.snapshot()
    app.click(0, 1)            # mouse click at screen coordinates
```

# Custom widgets

Subclass {class}`~pytui.Widget`, keep the state in a {class}`~pytui.Value`, and put the
built-in behaviour in the `handle_*` methods (`handle_key`, `handle_click`, `handle_change`,
`handle_mouse`, `handle_paste`, `handle_focus`, `handle_blur`). They run after the user's
callbacks (except `handle_change`, which runs first) and stop the event unless they return
`False`:

```python
from pytui import Style, Value, Widget

class CounterValue(Value):
    count: int = 0

class Counter(Widget):
    FOCUSABLE = True
    DEFAULT_STYLE = Style(padding=(0, 1), focus=Style(reverse=True))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = CounterValue()

    def handle_change(self, event) -> bool:
        if event.widget is self:
            self.text = f"count: {event.value}"
        return False  # let the change bubble up

    def handle_key(self, event) -> bool:
        if event.key in ("up", "+"):
            self.value.count += 1
            return True  # handled: stop propagation
        if event.key in ("down", "-"):
            self.value.count -= 1
            return True
        return super().handle_key(event)
```

Background, border, text, cursor, children and clipping are handled for you. For content that
is not text, override `content_width`, `content_height` and `render(canvas)`.

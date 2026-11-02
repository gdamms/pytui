# Getting started

## Install

```sh
git clone https://github.com/gdamms/pytui.git
uv add pytui
```

## Quick start

```python
from pytui import App, Box, Button, Row, Text

count = Text("Clicked 0 times")
clicks = 0

def on_click(event):
    global clicks
    clicks += 1
    count.text = f"Clicked {clicks} times"

app = App(
    Box(
        Text("Hello from pytui!", bold=True, fg="cyan"),
        count,
        Row(Button("Click me", on_click=on_click), Button("Quit", on_click=lambda e: app.exit()), gap=2),
        border="rounded", padding=(1, 2), gap=1,
        align_items="center", justify_content="center",
    )
)
app.run()
```

The screen is redrawn automatically after every event, timer or thread callback, so
changing widget attributes (`count.text = ...`) is all it takes to update the UI.

## Examples

```sh
uv run examples/hello.py      # from the quick start
uv run examples/notes.py      # list + editor, key bindings, focus styles
uv run examples/dashboard.py  # timers, background thread, scrolling log
```

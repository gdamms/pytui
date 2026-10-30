"""The smallest useful pytui app.

Run with: uv run examples/hello.py
"""

from pytui import App, Box, Button, Row, Text


def main() -> None:
    count = Text("Clicked 0 times")
    clicks = 0

    def on_click(event: object) -> None:
        nonlocal clicks
        clicks += 1
        count.text = f"Clicked {clicks} time{'s' * (clicks != 1)}"

    app = App(
        Box(
            Text(" hello ", position="absolute", top=-1, left=1),
            Text("Hello from pytui!", bold=True, fg="cyan"),
            count,
            Row(
                Button("Click me", on_click=on_click),
                Button("Quit", on_click=lambda event: app.exit()),
                gap=2,
            ),
            Text("Tab / Shift+Tab to move focus, Enter to press, Ctrl+C to quit.", dim=True),
            border="rounded",
            padding=(1, 2),
            gap=1,
            align_items="center",
            justify_content="center",
        )
    )
    app.run()


if __name__ == "__main__":
    main()

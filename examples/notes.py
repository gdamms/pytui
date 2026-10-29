"""A small notes app: a list of notes on the left, an editor on the right.

Run with: uv run examples/notes.py
"""

from pytui import App, Box, Button, Input, ListView, Row, Style, Text, TextArea

PANEL = Style(
    border="rounded",
    border_fg="bright_black",
    focus_within=Style(border_fg="cyan"),
)


class Notes:
    def __init__(self) -> None:
        self.notes = {
            "Welcome": "Pick a note on the left and edit it here.\n\n"
            "Tab moves focus, Ctrl+N creates a note, Ctrl+Q quits.",
            "Todo": "- try the layout engine\n- build something",
        }
        self.current = "Welcome"

        self.list = ListView(self.notes, on_highlight=self.open, flex_grow=1)
        self.name = Input(placeholder="new note name", on_submit=self.create)
        self.editor = TextArea(self.notes[self.current], on_change=self.save, flex_grow=1)
        self.editor_panel = Box(self.editor, style=PANEL, title=self.current, flex_grow=1)
        self.status = Text("", fg="bright_black", padding=(0, 1))

        sidebar = Box(
            self.list,
            self.name,
            Row(
                Button("New", on_press=lambda: self.create(self.name.value)),
                Button("Delete", on_press=self.delete),
                gap=1,
            ),
            style=PANEL,
            title="Notes",
            width=28,
            flex_shrink=0,
            gap=1,
        )
        root = Box(Row(sidebar, self.editor_panel, flex_grow=1), self.status)

        self.app = App(root)
        self.app.bind("ctrl+q", self.app.exit)
        self.app.bind("ctrl+n", self.name.focus)

    def open(self, index: int, name: str) -> None:
        self.current = name
        self.editor.value = self.notes[name]
        self.editor.move_cursor(0, 0)
        self.editor_panel.title = name
        self.status.text = f"Opened {name!r}"

    def save(self, value: str) -> None:
        self.notes[self.current] = value
        self.status.text = f"{self.current}: {len(value)} characters"

    def create(self, name: str) -> None:
        name = name.strip() or f"Note {len(self.notes) + 1}"
        while name in self.notes:
            name += "'"
        self.notes[name] = ""
        self.list.items = self.notes
        self.list.index = list(self.notes).index(name)
        self.open(self.list.index, name)
        self.name.value = ""
        self.editor.focus()

    def delete(self) -> None:
        if len(self.notes) <= 1:
            self.status.text = "Can't delete the last note"
            return
        del self.notes[self.current]
        self.list.items = self.notes
        index = self.list.index or 0
        self.open(index, self.list.items[index])

    def run(self) -> None:
        self.app.run()


if __name__ == "__main__":
    Notes().run()

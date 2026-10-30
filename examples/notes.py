"""A small notes app: a list of notes on the left, an editor on the right.

The list is built from plain widgets: each note is a focusable line, and the
open one is highlighted by changing its style.

Run with: uv run examples/notes.py
"""

from pytui import App, Box, Button, ChangeEvent, Column, Row, Style, Text, TextArea, Widget

PANEL = Style(
    border="rounded",
    border_fg="bright_black",
    focus_within=Style(border_fg="cyan"),
)
ITEM = Style(padding=(0, 1), text_wrap=False, focus=Style(bold=True), hover=Style(underline=True))


def title(text: str) -> Text:
    """A title drawn on the parent's top border."""
    return Text(f" {text} ", position="absolute", top=-1, left=1)


class Notes:
    def __init__(self) -> None:
        self.notes = {
            "Welcome": "Pick a note on the left and edit it here.\n\n"
            "Up/Down browse the list, Tab moves focus, Ctrl+N creates a note, Ctrl+Q quits.",
            "Todo": "- try the layout engine\n- build something",
        }
        self.current = ""

        self.list = Column(flex_grow=1, overflow="scroll")
        self.list.bind("up", lambda: self.step(-1))
        self.list.bind("down", lambda: self.step(1))
        self.name = TextArea(
            placeholder="new note name", height=1, text_wrap=False, bg="bright_black"
        )
        self.name.bind("enter", lambda: self.create(self.name.value.text))
        self.editor = TextArea(on_change=self.save, flex_grow=1)
        self.editor_title = title("")
        self.status = Text("", fg="bright_black", padding=(0, 1))

        sidebar = Box(
            title("Notes"),
            self.list,
            self.name,
            Row(
                Button("New", on_click=lambda e: self.create(self.name.value.text)),
                Button("Delete", on_click=lambda e: self.delete()),
                gap=1,
            ),
            style=PANEL,
            width=28,
            flex_shrink=0,
            gap=1,
        )
        editor_panel = Box(self.editor_title, self.editor, style=PANEL, flex_grow=1)
        root = Box(Row(sidebar, editor_panel, flex_grow=1), self.status)

        self.app = App(root)
        self.app.bind("ctrl+q", self.app.exit)
        self.app.bind("ctrl+n", self.name.focus)
        self.refresh()
        self.open("Welcome")

    def refresh(self) -> None:
        """Rebuild the list from ``self.notes``."""
        self.list.clear()
        for name in self.notes:
            self.list.mount(
                Widget(
                    text=name,
                    id=name,
                    style=ITEM,
                    focusable=True,
                    on_click=lambda e, name=name: self.open(name),
                )
            )

    def step(self, delta: int) -> None:
        names = list(self.notes)
        index = (names.index(self.current) + delta) % len(names)
        self.open(names[index])
        self.list.get(names[index]).focus()

    def open(self, name: str) -> None:
        if self.current in self.notes:
            self.list.get(self.current).set_style(reverse=False)
        self.current = name
        self.list.get(name).set_style(reverse=True)
        self.editor.value.text = self.notes[name]
        self.editor.cursor = 0
        self.editor_title.text = f" {name} "
        self.status.text = f"Opened {name!r}"

    def save(self, event: ChangeEvent) -> None:
        self.notes[self.current] = event.value
        self.status.text = f"{self.current}: {len(event.value)} characters"

    def create(self, name: str) -> None:
        name = name.strip() or f"Note {len(self.notes) + 1}"
        while name in self.notes:
            name += "'"
        self.notes[name] = ""
        self.refresh()
        self.open(name)
        self.name.value.text = ""
        self.editor.focus()

    def delete(self) -> None:
        if len(self.notes) <= 1:
            self.status.text = "Can't delete the last note"
            return
        names = list(self.notes)
        index = names.index(self.current)
        del self.notes[self.current]
        self.refresh()
        self.open(list(self.notes)[min(index, len(self.notes) - 1)])

    def run(self) -> None:
        self.app.run()


if __name__ == "__main__":
    Notes().run()

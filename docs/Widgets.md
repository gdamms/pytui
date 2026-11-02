# Widgets

Everything on screen is a {class}`~pytui.Widget`:

```python
Widget(*children, text="", on_click=None, on_key=None, on_change=None, **style)
```

- **`text` is a background**: it is painted inside the box (wrapped unless `text_wrap=False`,
  aligned with `text_align`) and the children are laid out on their own, over it. The two only
  interact through size: the widget is as big as whichever needs more room. Empty text takes no
  space.
- **Strings among the children become `Text` widgets**: `Column("a", "b")` shows two lines.
- **`value` is the state** of the widget (`checkbox.value.checked`, `textarea.value.text`,
  `bar.value.progress`). Assigning a field, from your code or from input, calls `on_change`.
- **`cursor`** (`None` by default) is a caret or selection in `text`, drawn while focused.

## Built-in widgets

The helpers are presets and compositions of `Widget`:

| Helper | What it is | State |
| --- | --- | --- |
| `Box` | `Widget` itself | |
| `Row(*children)`, `Column(*children)` | `direction` preset | |
| `Text(text)` | `Widget(text=text)` | |
| `Button(*children)` | Focusable, Enter and Space count as a click | |
| `Checkbox(*children, checked=False)` | A `[x]` mark followed by its children, toggled by click, Enter or Space | `value.checked` |
| `TextArea(text="", placeholder="")` | Editor with word/line shortcuts, Shift+arrows selection and a dimmed placeholder | `value.text` |
| `ProgressBar(progress=0.0)` | A `━━━━━━━━━━` bar, progress between 0 and 1 | `value.progress` |

```python
Button("Save", on_click=lambda event: save())
Checkbox("Dark mode", on_change=lambda event: set_theme(event.value))
name = TextArea(placeholder="your name", height=1, text_wrap=False)
name.bind("enter", lambda: greet(name.value.text))  # a single-line field
```

There is no list widget and no "selected" state: build lists from plain widgets and highlight
items by changing their style (`item.set_style(reverse=True)`), as `examples/notes.py` does.

## Common API

`id=`, `disabled=`, `focusable=`, `mount(*children)`, `remove()`, `clear()`, `find(id)`,
`get(id, Type)`, `walk()`, `focus()`, `click()`, `hidden = True`, `bind(key, fn)`,
`scroll_to()`, and `region` / `content_region` (screen rectangles after layout).
See {class}`~pytui.Widget` for the full reference.

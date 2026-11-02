# Events, focus and key bindings

Every widget accepts the same callbacks, which receive an event:

| Callback | Event | Fields |
| --- | --- | --- |
| `on_click` | {class}`~pytui.ClickEvent` | `widget` (clicked), `mouse` (`None` when triggered by the keyboard) |
| `on_key` | {class}`~pytui.KeyEvent` | `key`, `char`, `ctrl`, `alt`, `shift` |
| `on_change` | {class}`~pytui.ChangeEvent` | `widget` (whose value changed), `name`, `value`, `old` |

## Propagation

- Events bubble up from the focused widget (keys), the widget under the pointer (clicks) or the
  widget whose value changed. A callback stops the event only by **returning `True`**, so
  callbacks that just observe are safe.
- For each key press, at each widget: its key bindings run first, then your `on_key`, then the
  widget's built-in behaviour. Return `True` from `on_key` to override a built-in. Then come
  app bindings, and Tab / Shift+Tab move focus if nothing handled the key.
- A change first runs the widget's built-in reaction (e.g. `TextArea` repaints its text), then
  your `on_change`, then bubbles: `Column(*checkboxes, on_change=...)` observes the whole group.
- A mouse press focuses the nearest focusable widget, and press+release on the same widget is
  a click.

## Key bindings

Key names look like `"a"`, `"A"`, `"+"`, `"space"`, `"enter"`, `"escape"`, `"tab"`,
`"shift+tab"`, `"up"`, `"pageup"`, `"f5"`, `"ctrl+s"`, `"alt+x"`, `"ctrl+shift+left"`,
`"ctrl++"`. Modifiers are case-insensitive, `esc`, `return`, `del`, `pgup`, `pgdn` and `plus`
are accepted as aliases, and unknown names raise `ValueError`.

```python
app.bind("ctrl+q", app.exit)                      # global
editor.bind("ctrl+s", save)                       # only while focus is inside `editor`
app.bind("f1 ctrl+h", lambda: help.set_style(display="flex"))
```

`ctrl+c` exits by default (`app.unbind("ctrl+c")` to disable). `app.run()` returns the value
passed to `app.exit(value)`.

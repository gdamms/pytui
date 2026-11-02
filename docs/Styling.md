# Styling

Style fields can be passed as keyword arguments or as a {class}`~pytui.Style` object. Styles
combine with `|`, and the right-hand side wins:

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

## States

States are nested styles applied while the state is active:

```python
Button("Save", style=Style(
    bg="green",
    hover=Style(bg="bright_green"),
    focus=Style(bold=True, underline=True),
    disabled=Style(dim=True),
))
Box(..., focus_within=Style(border_fg="cyan"))  # when a descendant has focus
```

## Theming

Each widget class has a `DEFAULT_STYLE` that instance styles override. To theme a widget
everywhere, subclass it:

```python
class DangerButton(Button):
    DEFAULT_STYLE = Button.DEFAULT_STYLE | Style(bg="red", focus=Style(bg="bright_red"))
```

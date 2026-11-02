# Layout

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
| `overflow_x`, `overflow_y` | `"hidden"`, `"visible"`, `"scroll"`, `"wrap"` | `"hidden"` |
| `overflow` | shorthand for both axes (no `"wrap"`); an explicit `overflow_x`/`overflow_y` wins | |

```python
Row(
    Box(sidebar, width=30, flex_shrink=0, border="rounded"),
    Box(editor, flex_grow=1, border="rounded"),               # takes the remaining space
    Box(help_panel, width="25%", display="none", id="help"),  # toggled later
)
```

As in CSS `flex: 1`, a child with `flex_grow` starts from its minimum size and shares the free
space, rather than starting from its content size.

## Absolute positioning

Absolute children are positioned in the parent's padding box but may draw over its border,
which is how you give a box a title:

```python
Box(Text(" Files ", position="absolute", top=-1, left=1), sidebar, border="rounded")
```

## Scrolling

`overflow="scroll"` makes a container scrollable (`overflow_x`/`overflow_y` for a single axis).
Its children keep their natural size, and it scrolls with the mouse wheel, with the keyboard
when it is focusable (`focusable=True`), and automatically to reveal the focused widget.
Scrollbars are drawn on the right and bottom borders, or in a reserved column/row if there is
no border. A scrolling axis takes no size from its content, so size it with `flex_grow`, a
`width`/`height` or stretch; long content never pushes its siblings away. A `Text` scrolls its
own lines horizontally when `text_wrap=False` and `overflow_x="scroll"`.

## Wrapping

`"wrap"` on the main axis flows children onto new lines: `overflow_x="wrap"` on a `Row` adds
rows downward, `overflow_y="wrap"` on a `Column` adds columns rightward. `gap` also separates
the lines. It combines with scrolling on the other axis:

```python
Row(*tags, overflow_x="wrap", overflow_y="scroll", gap=1, height=4)
```

Each axis is clipped independently, so `overflow_x="visible"` lets children spill out sideways
while they are still clipped vertically.

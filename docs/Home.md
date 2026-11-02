# pytui

```{image} https://raw.githubusercontent.com/gdamms/pytui/main/assets/screenshot.png
:alt: Screenshot
```

Build terminal user interfaces in Python with ideas borrowed from HTML/CSS:
a tree of widgets, typed styles, and a flexbox layout engine.

- **Flexbox layout**: `direction`, `flex_grow`/`flex_shrink`, `gap`, `justify_content`,
  `align_items`, percentages, min/max sizes, margins, padding, borders, absolute positioning,
  scrollable containers.
- **Styles as objects**: `Style(...)` merged with `|`, inherited text attributes, and
  `hover` / `focus` / `focus_within` / `disabled` state variants.
- **One building block**: everything is a `Widget` (a styled box that shows text, holds state,
  contains children and reacts to input). `Row`, `Column`, `Text`, `Button`, `Checkbox`,
  `TextArea` and `ProgressBar` are small helpers built from it.
- **Input**: keyboard with modifiers, mouse (click, drag, hover, wheel), bracketed paste,
  focus navigation with Tab.
- **Efficient rendering**: an in-memory cell buffer diffed against the previous frame, so only
  changed cells are written. Wide (CJK/emoji) characters are handled.
- **Testable**: render to text and simulate input without a terminal.
- **Zero dependencies**, pure Python >= 3.11 (Linux/macOS).

```{toctree}
:caption: Guide
:maxdepth: 1

Getting-Started
Layout
Styling
Widgets
Events
Timers-and-Threads
Custom-Widgets
Testing
```

```{toctree}
:caption: API reference
:maxdepth: 1

API-App
API-Widgets
API-Style
API-Events
API-Rendering
```

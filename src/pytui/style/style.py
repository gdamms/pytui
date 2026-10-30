"""Styles: a typed, CSS-inspired description of how a widget looks and is laid out.

Every field defaults to ``None`` which means "not set". Styles are combined
with ``|``, the right-hand side winning for every field it sets::

    base = Style(padding=1, border="rounded")
    danger = base | Style(fg="red", bold=True)

State variants (``hover``, ``focus``, ``focus_within``, ``disabled``) are
nested styles merged on top of the widget style while the state is active.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, replace
from typing import Any, Literal

from ..geometry import Edges
from .border import border_chars
from .color import Color, color_code

Size = int | str | None
"""A length: cells (``10``), a percentage of the parent (``"50%"``) or ``"auto"``."""

Spacing = int | tuple[int, int] | tuple[int, int, int, int] | Edges | None
"""Box edges: ``1``, ``(vertical, horizontal)`` or ``(top, right, bottom, left)``."""

_PERCENT = re.compile(r"^\d+(\.\d+)?%$")


@dataclass(frozen=True, kw_only=True)
class Style:
    # --- sizing -----------------------------------------------------------
    width: Size = None
    height: Size = None
    min_width: Size = None
    min_height: Size = None
    max_width: Size = None
    max_height: Size = None
    box_sizing: Literal["border-box", "content-box"] | None = None
    """Whether ``width``/``height`` include padding and border (default ``border-box``)."""

    # --- box model --------------------------------------------------------
    margin: Spacing = None
    padding: Spacing = None
    border: str | None = None
    """``"none"``, a name from ``BORDERS`` or a custom 8-character string."""
    border_fg: Color = None

    # --- flex container ---------------------------------------------------
    direction: Literal["row", "column"] | None = None
    gap: int | None = None
    justify_content: (
        Literal["start", "center", "end", "space-between", "space-around", "space-evenly"] | None
    ) = None
    align_items: Literal["start", "center", "end", "stretch"] | None = None

    # --- flex item --------------------------------------------------------
    flex_grow: float | None = None
    flex_shrink: float | None = None
    align_self: Literal["auto", "start", "center", "end", "stretch"] | None = None

    # --- positioning ------------------------------------------------------
    position: Literal["relative", "absolute"] | None = None
    top: int | None = None
    right: int | None = None
    bottom: int | None = None
    left: int | None = None

    # --- display ----------------------------------------------------------
    display: Literal["flex", "none"] | None = None
    visibility: Literal["visible", "hidden"] | None = None
    overflow: Literal["hidden", "visible", "scroll"] | None = None

    # --- text (inherited by children) -------------------------------------
    fg: Color = None
    bg: Color = None
    bold: bool | None = None
    dim: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strike: bool | None = None
    reverse: bool | None = None
    text_align: Literal["left", "center", "right"] | None = None
    text_wrap: bool | None = None

    # --- state variants ---------------------------------------------------
    hover: Style | None = None
    focus: Style | None = None
    focus_within: Style | None = None
    disabled: Style | None = None

    def __post_init__(self) -> None:
        for name, choices in _CHOICES.items():
            value = getattr(self, name)
            if value is not None and value not in choices:
                raise ValueError(f"invalid {name}: {value!r} (expected one of {choices})")
        for name in _SIZE_FIELDS:
            value = getattr(self, name)
            if value is None or value == "auto":
                continue
            valid_int = isinstance(value, int) and not isinstance(value, bool) and value >= 0
            if not valid_int and not (isinstance(value, str) and _PERCENT.match(value)):
                raise ValueError(f"invalid {name}: {value!r} (expected int >= 0, 'N%' or 'auto')")
        for name in ("fg", "bg", "border_fg"):
            color_code(getattr(self, name))
        if self.border is not None:
            border_chars(self.border)
        for name in ("margin", "padding"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, Edges.parse(value))
        for name in _STATE_FIELDS:
            value = getattr(self, name)
            if value is not None and not isinstance(value, Style):
                raise TypeError(f"{name} must be a Style, got {type(value).__name__}")

    def __or__(self, other: Style | None) -> Style:
        if other is None:
            return self
        if not isinstance(other, Style):
            return NotImplemented
        mine, theirs = self.__dict__, other.__dict__
        values = {n: mine[n] if theirs[n] is None else theirs[n] for n in _FIELD_NAMES}
        for name in _STATE_FIELDS:
            if mine[name] is not None and theirs[name] is not None:
                values[name] = mine[name] | theirs[name]
        return _build(values)

    def set_fields(self) -> dict[str, Any]:
        """The fields explicitly set on this style."""
        return {n: v for n in _FIELD_NAMES if (v := getattr(self, n)) is not None}

    def resolve(self, parent: ComputedStyle | None) -> ComputedStyle:
        """Fill unset fields from ``parent`` (inherited fields) or the defaults."""
        mine, defaults = self.__dict__, DEFAULTS.__dict__
        inherited = defaults if parent is None else parent.__dict__
        values = {}
        for name in _COMPUTED_NAMES:
            value = mine[name]
            if value is None:
                value = inherited[name] if name in _INHERITED else defaults[name]
            values[name] = value
        return _build_computed(values)


@dataclass(frozen=True, kw_only=True)
class ComputedStyle:
    """A fully resolved :class:`Style`: nothing left to inherit or default.

    Produced by :meth:`Style.resolve`. Fields that are ``None`` here are
    genuinely absent (``auto`` sizes, unset offsets, default colors).
    """

    width: Size
    height: Size
    min_width: Size
    min_height: Size
    max_width: Size
    max_height: Size
    box_sizing: Literal["border-box", "content-box"]

    margin: Edges
    padding: Edges
    border: str
    border_fg: Color

    direction: Literal["row", "column"]
    gap: int
    justify_content: Literal[
        "start", "center", "end", "space-between", "space-around", "space-evenly"
    ]
    align_items: Literal["start", "center", "end", "stretch"]

    flex_grow: float
    flex_shrink: float
    align_self: Literal["auto", "start", "center", "end", "stretch"]

    position: Literal["relative", "absolute"]
    top: int | None
    right: int | None
    bottom: int | None
    left: int | None

    display: Literal["flex", "none"]
    visibility: Literal["visible", "hidden"]
    overflow: Literal["hidden", "visible", "scroll"]

    fg: Color
    bg: Color
    bold: bool
    dim: bool
    italic: bool
    underline: bool
    strike: bool
    reverse: bool
    text_align: Literal["left", "center", "right"]
    text_wrap: bool

    def __or__(self, other: Style | None) -> ComputedStyle:
        """Override with the fields ``other`` sets (state variants are ignored)."""
        if other is None:
            return self
        if not isinstance(other, Style):
            return NotImplemented
        changes = {n: v for n, v in other.set_fields().items() if n in _COMPUTED_SET}
        return replace(self, **changes)


def _build(values: dict[str, object]) -> Style:
    """Create a Style without re-running validation (values are already valid)."""
    style = object.__new__(Style)
    style.__dict__.update(values)
    return style


def _build_computed(values: dict[str, object]) -> ComputedStyle:
    style = object.__new__(ComputedStyle)
    style.__dict__.update(values)
    return style


_FIELD_NAMES = tuple(f.name for f in fields(Style))
_STATE_FIELDS = frozenset({"hover", "focus", "focus_within", "disabled"})
_COMPUTED_NAMES = tuple(n for n in _FIELD_NAMES if n not in _STATE_FIELDS)
_COMPUTED_SET = frozenset(_COMPUTED_NAMES)
assert _COMPUTED_NAMES == tuple(f.name for f in fields(ComputedStyle)), (
    "ComputedStyle fields must mirror Style fields (minus state variants), in order"
)
_SIZE_FIELDS = ("width", "height", "min_width", "min_height", "max_width", "max_height")
_INHERITED = frozenset(
    {
        "fg",
        "bg",
        "bold",
        "dim",
        "italic",
        "underline",
        "strike",
        "reverse",
        "text_align",
        "text_wrap",
        "visibility",
    }
)
_CHOICES: dict[str, tuple[str, ...]] = {
    "box_sizing": ("border-box", "content-box"),
    "direction": ("row", "column"),
    "justify_content": (
        "start",
        "center",
        "end",
        "space-between",
        "space-around",
        "space-evenly",
    ),
    "align_items": ("start", "center", "end", "stretch"),
    "align_self": ("auto", "start", "center", "end", "stretch"),
    "position": ("relative", "absolute"),
    "display": ("flex", "none"),
    "visibility": ("visible", "hidden"),
    "overflow": ("hidden", "visible", "scroll"),
    "text_align": ("left", "center", "right"),
}

DEFAULTS = Style(
    box_sizing="border-box",
    margin=0,
    padding=0,
    border="none",
    direction="column",
    gap=0,
    justify_content="start",
    align_items="stretch",
    flex_grow=0,
    flex_shrink=1,
    align_self="auto",
    position="relative",
    display="flex",
    visibility="visible",
    overflow="hidden",
    bold=False,
    dim=False,
    italic=False,
    underline=False,
    strike=False,
    reverse=False,
    text_align="left",
    text_wrap=True,
)
"""Values used for fields that are neither set nor inherited."""

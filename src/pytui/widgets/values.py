"""Widget state: observable values and text cursors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from .widget import Widget


@dataclass(frozen=True)
class Cursor:
    """A caret in a widget's text, as character offsets.

    ``head`` is where the caret is drawn; ``anchor != head`` means the text
    between them is selected.
    """

    anchor: int
    head: int

    @classmethod
    def at(cls, index: int) -> Cursor:
        return cls(index, index)

    @property
    def start(self) -> int:
        return min(self.anchor, self.head)

    @property
    def end(self) -> int:
        return max(self.anchor, self.head)

    @property
    def collapsed(self) -> bool:
        """True when nothing is selected."""
        return self.anchor == self.head


class Value:
    """The state of a widget. Assigning a field notifies the owning widget.

    Subclasses declare their fields as annotated class attributes with defaults::

        class CheckboxValue(Value):
            checked: bool = False

    Assigning a field to an equal value does nothing; otherwise the widget runs
    its ``handle_change`` then its ``on_change``, and the change bubbles up.
    """

    _fields: ClassVar[tuple[str, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        fields = list(cls._fields)
        for name in cls.__dict__.get("__annotations__", {}):
            if not name.startswith("_") and name not in fields:
                fields.append(name)
        cls._fields = tuple(fields)

    def __init__(self, **values: Any) -> None:
        object.__setattr__(self, "_owner", None)
        for name, value in values.items():
            setattr(self, name, value)

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in self._fields:
            raise AttributeError(f"{type(self).__name__} has no field {name!r}")
        value = self.coerce(name, value)
        old = getattr(self, name)
        if old == value:
            return
        object.__setattr__(self, name, value)
        owner: Widget | None = self._owner  # type: ignore[attr-defined]
        if owner is not None:
            owner._value_changed(name, value, old)

    def coerce(self, name: str, value: Any) -> Any:
        """Normalize a value before it is stored (e.g. clamp it)."""
        return value

    def __repr__(self) -> str:
        fields = ", ".join(f"{n}={getattr(self, n)!r}" for n in self._fields)
        return f"{type(self).__name__}({fields})"

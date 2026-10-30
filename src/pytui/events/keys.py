"""Key names: parsing and normalizing binding strings like ``"ctrl+s"``."""

from __future__ import annotations

MODIFIERS = ("ctrl", "alt", "shift")
KEY_NAMES = frozenset(
    {
        "enter",
        "tab",
        "backspace",
        "escape",
        "space",
        "up",
        "down",
        "left",
        "right",
        "home",
        "end",
        "insert",
        "delete",
        "pageup",
        "pagedown",
        *(f"f{i}" for i in range(1, 13)),
    }
)
"""Names of the non-character keys (character keys are named by the character)."""

_ALIASES = {
    "plus": "+",
    "esc": "escape",
    "return": "enter",
    "del": "delete",
    "ins": "insert",
    "pgup": "pageup",
    "pgdn": "pagedown",
}


def parse_key(key: str) -> tuple[frozenset[str], str]:
    """Split a key like ``"Ctrl+Shift++"`` into ``({"ctrl", "shift"}, "+")``.

    Modifiers are case-insensitive, named keys are checked against
    :data:`KEY_NAMES` (with a few aliases such as ``esc`` or ``pgup``) and the
    key itself can be ``+``. Raises :class:`ValueError` on unknown names.
    """
    text = key.strip()
    if not text:
        raise ValueError("empty key")
    if text.endswith("+"):
        name, rest = "+", text[:-1]
        if rest and not rest.endswith("+"):
            raise ValueError(f"invalid key {key!r}: missing key after {rest!r}")
        modifiers = rest[:-1].split("+") if rest else []
    else:
        *modifiers, name = text.split("+")
    mods = frozenset(m.strip().lower() for m in modifiers)
    unknown = mods - set(MODIFIERS)
    if unknown:
        names = ", ".join(sorted(repr(m) for m in unknown))
        raise ValueError(f"unknown modifier(s) in {key!r}: {names}")
    name = name.strip()
    if len(name) != 1:
        name = _ALIASES.get(name.lower(), name.lower())
        if len(name) != 1 and name not in KEY_NAMES:
            raise ValueError(f"unknown key {name!r} in {key!r}")
    return mods, name


def normalize_key(key: str) -> str:
    """Normalize a binding like ``"Ctrl+Shift+Up"`` to ``"ctrl+shift+up"``."""
    mods, name = parse_key(key)
    return "".join(f"{m}+" for m in MODIFIERS if m in mods) + name

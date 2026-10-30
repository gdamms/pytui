"""Incremental parser turning raw terminal input into events."""

from __future__ import annotations

from .event import Event, KeyEvent, MouseEvent, PasteEvent

_PASTE_START = "\x1b[200~"
_PASTE_END = "\x1b[201~"

_CSI_LETTERS = {
    "A": "up",
    "B": "down",
    "C": "right",
    "D": "left",
    "H": "home",
    "F": "end",
    "P": "f1",
    "Q": "f2",
    "R": "f3",
    "S": "f4",
}
_CSI_TILDE = {
    "1": "home",
    "2": "insert",
    "3": "delete",
    "4": "end",
    "5": "pageup",
    "6": "pagedown",
    "7": "home",
    "8": "end",
    "11": "f1",
    "12": "f2",
    "13": "f3",
    "14": "f4",
    "15": "f5",
    "17": "f6",
    "18": "f7",
    "19": "f8",
    "20": "f9",
    "21": "f10",
    "23": "f11",
    "24": "f12",
}
_MOUSE_BUTTONS = {0: "left", 1: "middle", 2: "right"}
_WHEEL = {0: "scroll_up", 1: "scroll_down", 2: "scroll_left", 3: "scroll_right"}


def _char_key(char: str) -> KeyEvent:
    code = ord(char)
    if char in ("\r", "\n"):
        return KeyEvent("enter")
    if char == "\t":
        return KeyEvent("tab")
    if char in ("\x7f", "\x08"):
        return KeyEvent("backspace")
    if char == "\x1b":
        return KeyEvent("escape")
    if code == 0:
        return KeyEvent("space", ctrl=True)
    if 1 <= code <= 26:
        return KeyEvent(chr(code + 96), ctrl=True)
    if 28 <= code <= 31:
        return KeyEvent("\\]^_"[code - 28], ctrl=True)
    if char == " ":
        return KeyEvent("space", char=" ")
    return KeyEvent(char, char=char)


def _modified(name: str, modifier_param: str) -> KeyEvent:
    bits = int(modifier_param) - 1 if modifier_param.isdigit() else 0
    return KeyEvent(name, ctrl=bool(bits & 4), alt=bool(bits & 2), shift=bool(bits & 1))


def _parse_csi(params: str, final: str) -> Event | str | None:
    if params.startswith("<") and final in "Mm":
        try:
            code, x, y = (int(p) for p in params[1:].split(";"))
        except ValueError:
            return None
        mods = {"shift": bool(code & 4), "alt": bool(code & 8), "ctrl": bool(code & 16)}
        low = code & 3
        if code & 64:
            return MouseEvent(_WHEEL[low], x - 1, y - 1, **mods)
        if code & 32:
            button = _MOUSE_BUTTONS.get(low)
            return MouseEvent("drag" if button else "move", x - 1, y - 1, button, **mods)
        action = "down" if final == "M" else "up"
        return MouseEvent(action, x - 1, y - 1, _MOUSE_BUTTONS.get(low), **mods)
    if final == "~" and params == "200":
        return _PASTE_START
    parts = params.split(";")
    modifier = parts[1] if len(parts) > 1 else ""
    if final == "~" and parts[0] in _CSI_TILDE:
        return _modified(_CSI_TILDE[parts[0]], modifier)
    if final in _CSI_LETTERS and not params.startswith("?"):
        return _modified(_CSI_LETTERS[final], modifier)
    if final == "Z":
        return KeyEvent("tab", shift=True)
    return None  # focus reports, device replies, unsupported sequences


class InputParser:
    """Feed raw text in, get events out.

    Escape sequences can arrive split across reads, so incomplete input is kept
    until more data arrives. A lone ``ESC`` is ambiguous (Escape key or start of
    a sequence): call :meth:`flush` once no more input arrived for a short while.
    """

    def __init__(self) -> None:
        self._buffer = ""
        self._paste: list[str] | None = None

    @property
    def pending(self) -> bool:
        return bool(self._buffer) and self._paste is None

    def feed(self, data: str) -> list[Event]:
        self._buffer += data
        events: list[Event] = []
        while self._buffer:
            if self._paste is not None:
                if not self._consume_paste(events):
                    break
                continue
            event, consumed = self._parse_one(self._buffer)
            if consumed == 0:
                break
            self._buffer = self._buffer[consumed:]
            if event == _PASTE_START:
                self._paste = []
            elif event is not None:
                events.append(event)  # type: ignore[arg-type]
        return events

    def flush(self) -> list[Event]:
        """Interpret buffered incomplete input literally (e.g. a lone Escape)."""
        events: list[Event] = []
        while self.pending:
            events.append(_char_key(self._buffer[0]))
            self._buffer = self._buffer[1:]
            events.extend(self.feed(""))
        return events

    def _consume_paste(self, events: list[Event]) -> bool:
        assert self._paste is not None
        end = self._buffer.find(_PASTE_END)
        if end == -1:
            keep = 0  # hold back a possible partial end marker
            for size in range(min(len(_PASTE_END) - 1, len(self._buffer)), 0, -1):
                if _PASTE_END.startswith(self._buffer[-size:]):
                    keep = size
                    break
            self._paste.append(self._buffer[: len(self._buffer) - keep])
            self._buffer = self._buffer[len(self._buffer) - keep :]
            return False
        self._paste.append(self._buffer[:end])
        text = "".join(self._paste).replace("\r\n", "\n").replace("\r", "\n")
        events.append(PasteEvent(text))
        self._paste = None
        self._buffer = self._buffer[end + len(_PASTE_END) :]
        return True

    @staticmethod
    def _parse_one(buf: str) -> tuple[Event | str | None, int]:
        if buf[0] != "\x1b":
            return _char_key(buf[0]), 1
        if len(buf) == 1:
            return None, 0
        second = buf[1]
        if second == "[":
            i = 2
            while i < len(buf) and "0" <= buf[i] <= "?":
                i += 1
            while i < len(buf) and " " <= buf[i] <= "/":
                i += 1
            if i >= len(buf):
                return None, 0
            final = buf[i]
            if not "@" <= final <= "~":
                return KeyEvent("escape"), 1
            return _parse_csi(buf[2:i], final), i + 1
        if second == "O":
            if len(buf) < 3:
                return None, 0
            name = _CSI_LETTERS.get(buf[2])
            return (KeyEvent(name) if name else None), 3
        if second == "\x1b":
            return KeyEvent("escape"), 1
        key = _char_key(second)
        return KeyEvent(key.name, None, key.ctrl, True, key.shift), 2

"""The escape sequences pytui sends to the terminal."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from ...style import color_code

if TYPE_CHECKING:
    from ...render import CellStyle

ENTER = (
    "\x1b[?1049h"  # alternate screen
    "\x1b[?25l"  # hide cursor
    "\x1b[?2004h"  # bracketed paste
    "\x1b[H"  # cursor to top-left
    "\x1b[2J"  # clear the whole screen
)
LEAVE = (
    "\x1b[0m"  # reset colors and attributes
    "\x1b[?2004l"  # no bracketed paste
    "\x1b[?25h"  # show cursor
    "\x1b[?1049l"  # back to the normal screen
)
MOUSE_ON = (
    "\x1b[?1000h"  # report button presses and releases
    "\x1b[?1002h"  # also report motion while a button is held (drag)
    "\x1b[?1003h"  # also report motion with no button held (hover)
    "\x1b[?1006h"  # SGR encoding: no 223-column limit, release reports which button
)
MOUSE_OFF = (
    "\x1b[?1006l"  # disable SGR mouse encoding
    "\x1b[?1003l"  # disable mouse motion reporting with no button held (hover)
    "\x1b[?1002l"  # disable mouse motion reporting while a button is held (drag)
    "\x1b[?1000l"  # disable mouse button press/release reporting
)
SYNC_START = "\x1b[?2026h"  # tell terminal to wait whole frame is drawn before updating the screen
SYNC_END = "\x1b[?2026l"  # tell terminal the frame is drawn and it can update the screen now

RESET = "\x1b[0m"  # reset colors and attributes
CLEAR = "\x1b[H\x1b[2J"  # cursor to top-left, then clear the whole screen


def move(x: int, y: int) -> str:
    """Move the cursor to column ``x``, row ``y`` (0-based)."""
    return f"\x1b[{y + 1};{x + 1}H"


@lru_cache(maxsize=1024)
def sgr(style: CellStyle) -> str:
    """The escape sequence that switches the terminal to ``style``."""
    codes = ["0"]
    for flag, code in (
        (style.bold, "1"),
        (style.dim, "2"),
        (style.italic, "3"),
        (style.underline, "4"),
        (style.reverse, "7"),
        (style.strike, "9"),
    ):
        if flag:
            codes.append(code)
    if style.fg is not None:
        codes.append(color_code(style.fg))
    if style.bg is not None:
        codes.append(color_code(style.bg, background=True))
    return f"\x1b[{';'.join(codes)}m"

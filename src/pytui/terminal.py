"""Low-level POSIX terminal handling: raw mode, alternate screen, reading input."""

from __future__ import annotations

import codecs
import os
import select
import signal
import sys
import termios
from types import TracebackType
from typing import TextIO

ENTER = (
    "\x1b[?1049h"  # alternate screen
    "\x1b[?25l"  # hide cursor
    "\x1b[?2004h"  # bracketed paste
    "\x1b[H\x1b[2J"
)
LEAVE = "\x1b[0m\x1b[?2004l\x1b[?25h\x1b[?1049l"
MOUSE_ON = "\x1b[?1000h\x1b[?1002h\x1b[?1003h\x1b[?1006h"
MOUSE_OFF = "\x1b[?1006l\x1b[?1003l\x1b[?1002l\x1b[?1000l"
SYNC_START = "\x1b[?2026h"
SYNC_END = "\x1b[?2026l"


class Terminal:
    """Context manager putting the terminal in raw, full-screen mode."""

    def __init__(
        self, stdin: TextIO | None = None, stdout: TextIO | None = None, mouse: bool = True
    ) -> None:
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout
        self._mouse = mouse
        self._in_fd = self._stdin.fileno()
        self._out_fd = self._stdout.fileno()
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._saved_attrs: list | None = None
        self._wake_r = self._wake_w = -1
        self._saved_handlers: dict[int, object] = {}
        self._signals = False

    def __enter__(self) -> Terminal:
        if not os.isatty(self._in_fd) or not os.isatty(self._out_fd):
            raise RuntimeError(
                "pytui needs an interactive terminal (stdin and stdout must be a TTY)"
            )
        self._saved_attrs = termios.tcgetattr(self._in_fd)
        attrs = termios.tcgetattr(self._in_fd)
        attrs[0] &= ~(
            termios.BRKINT | termios.ICRNL | termios.INPCK | termios.ISTRIP | termios.IXON
        )
        attrs[2] |= termios.CS8
        attrs[3] &= ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)
        attrs[6][termios.VMIN] = 1
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self._in_fd, termios.TCSAFLUSH, attrs)

        self._wake_r, self._wake_w = os.pipe()
        os.set_blocking(self._wake_r, False)
        os.set_blocking(self._wake_w, False)
        try:
            self._saved_handlers[signal.SIGWINCH] = signal.signal(
                signal.SIGWINCH, lambda *_: self.wake()
            )
            self._saved_handlers[signal.SIGTERM] = signal.signal(
                signal.SIGTERM, lambda *_: sys.exit(143)
            )
            self._signals = True
        except ValueError:  # not in the main thread
            self._signals = False

        self.write(ENTER + (MOUSE_ON if self._mouse else ""))
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            self.write((MOUSE_OFF if self._mouse else "") + LEAVE)
        finally:
            for sig, handler in self._saved_handlers.items():
                signal.signal(sig, handler)  # type: ignore[arg-type]
            self._saved_handlers.clear()
            if self._saved_attrs is not None:
                termios.tcsetattr(self._in_fd, termios.TCSAFLUSH, self._saved_attrs)
            for fd in (self._wake_r, self._wake_w):
                if fd >= 0:
                    os.close(fd)
            self._wake_r = self._wake_w = -1

    def size(self) -> tuple[int, int]:
        try:
            size = os.get_terminal_size(self._out_fd)
        except OSError:
            return 80, 24
        return size.columns, size.lines

    def write(self, data: str) -> None:
        view = memoryview(data.encode("utf-8"))
        while view:
            written = os.write(self._out_fd, view)
            view = view[written:]

    def wake(self) -> None:
        """Interrupt a blocking :meth:`read` (safe from threads and signal handlers)."""
        try:
            os.write(self._wake_w, b"\0")
        except (BlockingIOError, OSError):
            pass

    def read(self, timeout: float | None) -> str:
        """Wait up to ``timeout`` seconds (forever if None) for input."""
        if not self._signals:  # no SIGWINCH: poll so resizes are noticed
            timeout = 0.25 if timeout is None else min(timeout, 0.25)
        try:
            ready, _, _ = select.select([self._in_fd, self._wake_r], [], [], timeout)
        except InterruptedError:
            return ""
        if self._wake_r in ready:
            try:
                while os.read(self._wake_r, 1024):
                    pass
            except BlockingIOError:
                pass
        if self._in_fd in ready:
            data = os.read(self._in_fd, 65536)
            if not data:
                raise EOFError("terminal input closed")
            return self._decoder.decode(data)
        return ""

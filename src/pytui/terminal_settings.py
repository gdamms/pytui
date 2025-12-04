import termios
import sys
from typing import Any


class TerminalSettings:
    def __init__(self):
        self._settings = termios.tcgetattr(sys.stdin.fileno())

    def __getitem__(self, item: int):
        return self._settings[item]

    def __setitem__(self, item: int, value: Any):
        self._settings[item] = value

    def __enter__(self):
        self._saved_settings = termios.tcgetattr(sys.stdin.fileno())
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, self._settings)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, self._saved_settings)

        return False  # don't suppress exceptions

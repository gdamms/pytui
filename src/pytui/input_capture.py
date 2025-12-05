import sys
import termios
import select
import os

from .terminal_settings import TerminalSettings
from .event import split_input_codes, input_code_to_event


class InputCapture:
    def __init__(self):
        self._term_settings = TerminalSettings()
        self._term_settings[3] = self._term_settings[3] & ~(termios.ECHO | termios.ICANON)  # lflags
        self._term_settings[6][termios.VMIN] = 0  # cc
        self._term_settings[6][termios.VTIME] = 0  #

    def enable_mouse(self):
        sys.stdout.write("\x1b[?1000h")
        sys.stdout.write("\x1b[?1006h")
        sys.stdout.flush()

    def disable_mouse(self):
        sys.stdout.write("\x1b[?1000l")
        sys.stdout.write("\x1b[?1006l")
        sys.stdout.flush()

    def __enter__(self):
        self._term_settings.__enter__()
        self.enable_mouse()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disable_mouse()
        self._term_settings.__exit__(exc_type, exc_val, exc_tb)
        return False  # don't suppress exceptions

    def get_input_code(self):
        if select.select([sys.stdin], [], [], 0.1)[0]:
            ch_set = ''
            ch = os.read(sys.stdin.fileno(), 1)
            while ch is not None and ch != b'':
                ch_set += ch.decode('ISO-8859-1')
                ch = os.read(sys.stdin.fileno(), 1)
            return ch_set
        return None

    def get_inputs(self):
        input_codes = self.get_input_code()
        if input_codes is None:
            return []

        codes = split_input_codes(input_codes)
        events = [input_code_to_event(code) for code in codes]

        return events

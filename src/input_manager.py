import sys
import termios
import select
import re
import os


class TerminalSettings:
    def __init__(self, fd: int, old_settings):
        self.fd = fd
        self.old_settings = old_settings


old_terminal_settings = None


def enable_input_capture():
    global old_terminal_settings
    if old_terminal_settings is not None:
        raise RuntimeError("Input capture already enabled")

    # save old terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    # set new terminal settings
    new_settings = termios.tcgetattr(sys.stdin)
    new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)  # lflags
    new_settings[6][termios.VMIN] = 0  # cc
    new_settings[6][termios.VTIME] = 0  # cc

    # apply new terminal settings
    termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, new_settings)
    new_settings[6][termios.VTIME] = 0  # cc

    # store old settings for later restoration
    old_terminal_settings = TerminalSettings(fd, old_settings)


def restore_terminal():
    global old_terminal_settings
    if old_terminal_settings is None:
        raise RuntimeError("Input capture not enabled, nothing to restore")

    termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, old_terminal_settings.old_settings)


def enable_mouse():
    sys.stdout.write("\x1b[?1000h")
    sys.stdout.write("\x1b[?1006h")
    sys.stdout.flush()


def disable_mouse():
    sys.stdout.write("\x1b[?1000l")
    sys.stdout.write("\x1b[?1006l")
    sys.stdout.flush()


def get_input_code():
    global old_terminal_settings
    if old_terminal_settings is None:
        raise RuntimeError("Input capture not enabled, cannot get key")
    if select.select([sys.stdin], [], [], 0.1)[0]:
        ch_set = ''
        ch = os.read(old_terminal_settings.fd, 1)
        while ch is not None and ch != b'':
            ch_set += ch.decode('ISO-8859-1')
            ch = os.read(old_terminal_settings.fd, 1)
        return ch_set
    return None


class MouseEvent:

    PRESS = 'PRESS'
    RELEASE = 'RELEASE'
    DRAG = 'DRAG'
    MOVE = 'MOVE'
    SCROLL_UP = 'SCROLL_UP'
    SCROLL_DOWN = 'SCROLL_DOWN'

    BUTTON_LEFT = 'BUTTON_LEFT'
    BUTTON_MIDDLE = 'BUTTON_MIDDLE'
    BUTTON_RIGHT = 'BUTTON_RIGHT'

    INPUT_CODE_EXPR = r'\x1b\[<(?P<button>\d+);(?P<x>\d+);(?P<y>\d+)(?P<type>[mM])'
    INPUT_CODE_PATTERN = re.compile(INPUT_CODE_EXPR)

    def __init__(self, event_type: str, x: int, y: int, button: str):
        self.event_type = event_type
        self.x = x
        self.y = y
        self.button = button

    @staticmethod
    def from_input_code(input_code: str):
        match = re.match(MouseEvent.INPUT_CODE_EXPR, input_code)
        if match is None:
            return None  # not a mouse event

        button_code = int(match.group('button'))
        x = int(match.group('x'))
        y = int(match.group('y'))

        if button_code == 64:
            return MouseEvent(MouseEvent.SCROLL_UP, x, y, MouseEvent.BUTTON_MIDDLE)
        if button_code == 65:
            return MouseEvent(MouseEvent.SCROLL_DOWN, x, y, MouseEvent.BUTTON_MIDDLE)

        type_code = match.group('type')
        if type_code == 'm':
            event_type = MouseEvent.RELEASE
        elif type_code == 'M':
            event_type = MouseEvent.PRESS
        else:
            raise ValueError("Unknown mouse event type code")

        if button_code == 0:
            button = MouseEvent.BUTTON_LEFT
        elif button_code == 1:
            button = MouseEvent.BUTTON_MIDDLE
        elif button_code == 2:
            button = MouseEvent.BUTTON_RIGHT
        else:
            raise ValueError("Unknown mouse button code")

        return MouseEvent(event_type, x, y, button)

    def __str__(self):
        return f"MouseEvent({self.event_type}, x={self.x}, y={self.y}, button={self.button})"


class KeyEvent:

    CODES = {
        '\x1b[A': 'UP',
        '\x1b[B': 'DOWN',
        '\x1b[C': 'RIGHT',
        '\x1b[D': 'LEFT',
        '\x1b[3~': 'DELETE',
        '\x1b[5~': 'PAGE_UP',
        '\x1b[6~': 'PAGE_DOWN',
        '\x1bOH': 'HOME',
        '\x1bOF': 'END',
        '\x7f': 'BACKSPACE',
        '\t': 'TAB',
        '\n': 'ENTER',
        '\r': 'ENTER',
        '\x1b': 'ESCAPE',
    }

    INPUT_CODE_EXPR = r'(\x1b\[[0-9;]*[A-Za-z]|\x1bO[A-Za-z]|\x1b|\t|\n|\r|\x7f|.)'
    INPUT_CODE_PATTERN = re.compile(INPUT_CODE_EXPR)

    def __init__(self, key: str):
        self.key = key

    @staticmethod
    def from_input_code(input_code: str):
        if input_code in KeyEvent.CODES:
            return KeyEvent(KeyEvent.CODES[input_code])
        elif len(input_code) == 1 and 32 <= ord(input_code) <= 126:
            return KeyEvent(input_code)
        else:
            return None  # not a recognized key event

    def __str__(self):
        return f"KeyEvent({self.key})"


INPUT_CODE_REGEX = f'{MouseEvent.INPUT_CODE_EXPR}|{KeyEvent.INPUT_CODE_EXPR}'
INPUT_CODE_PATTERN = re.compile(INPUT_CODE_REGEX)


def split_input_codes(input_codes: str):
    matches = re.finditer(INPUT_CODE_PATTERN, input_codes)
    return [match.group(0) for match in matches] if matches is not None else []


def get_inputs():
    input_codes = get_input_code()
    if input_codes is None:
        return []

    codes = split_input_codes(input_codes)
    events = []
    for code in codes:
        mouse_event = MouseEvent.from_input_code(code)
        if mouse_event is not None:
            events.append(mouse_event)
            continue

        key_event = KeyEvent.from_input_code(code)
        if key_event is not None:
            events.append(key_event)
            continue

        print(f"Unrecognized input code: {repr(code)}", file=sys.stderr)  # for debugging

    return events

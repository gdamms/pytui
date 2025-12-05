import re


class KeyEvent():

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

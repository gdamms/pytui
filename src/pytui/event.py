import re

from pytui.mouse_event import MouseEvent
from pytui.key_event import KeyEvent


INPUT_CODE_REGEX = f'{MouseEvent.INPUT_CODE_EXPR}|{KeyEvent.INPUT_CODE_EXPR}'
INPUT_CODE_PATTERN = re.compile(INPUT_CODE_REGEX)


def split_input_codes(input_codes: str):
    matches = re.finditer(INPUT_CODE_PATTERN, input_codes)
    return [match.group(0) for match in matches] if matches is not None else []


class Event:
    @staticmethod
    def from_input_code(input_code: str) -> 'Event':
        mouse_event = MouseEvent.from_input_code(input_code)
        if mouse_event is not None:
            return mouse_event

        key_event = KeyEvent.from_input_code(input_code)
        if key_event is not None:
            return key_event

        raise ValueError(f"Unrecognized input code: {repr(input_code)}")

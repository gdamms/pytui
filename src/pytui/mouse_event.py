import re

from .event import Event


class MouseEvent(Event):

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
        x = int(match.group('x')) - 1  # convert to 0-based
        y = int(match.group('y')) - 1  # convert to 0-based

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

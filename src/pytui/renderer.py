import sys

from .ansi import ANSI


class Renderer:
    def __init__(self):
        self._buffer = ''

    def write(self, item):
        self._buffer += item

    def clear(self):
        self._buffer = ''

    def blit(self, textIO=sys.stdout):
        textIO.write(self._buffer)
        textIO.flush()
        self.clear()

    def hide_cursor(self):
        self.write(ANSI.HIDE_CURSOR)

    def show_cursor(self):
        self.write(ANSI.SHOW_CURSOR)

    def primary_context(self):
        self.write(ANSI.PRIMARY_CONTEXT)

    def secondary_context(self):
        self.write(ANSI.SECONDARY_CONTEXT)

    def clear_screen(self):
        self.write(ANSI.CLEAR_SCREEN)

    def move_cursor(self, x, y):
        self.write(ANSI.MOVE_CURSOR.format(y + 1, x + 1))  # ANSI is 1-indexed

    def invert_colors(self):
        self.write(ANSI.INVERT_COLORS)

    def revert_colors(self):
        self.write(ANSI.REVERT_COLORS)

    def reset_color(self):
        self.write(ANSI.RESET_COLOR)

    def color(self, foreground=None, background=None):
        if foreground is None and background is None:
            self.reset_color()
            return

        if foreground in ANSI.FOREGROUND_COLORS:
            self.write(ANSI.FOREGROUND_COLORS[foreground])
        if background in ANSI.BACKGROUND_COLORS:
            self.write(ANSI.BACKGROUND_COLORS[background])

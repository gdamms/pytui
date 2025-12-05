import os
import sys

from .ansi import *


class Renderer:
    def __init__(self, textIO=sys.stdout):
        self._textIO = textIO
        self._buffer = ''

    def write(self, item):
        self._buffer += item

    def clear(self):
        self._buffer = ''

    def blit(self):
        self._textIO.write(self._buffer)
        self._textIO.flush()
        self.clear()

    def get_terminal_size(self):
        size = os.get_terminal_size()
        return size.columns, size.lines

    def hide_cursor(self):
        self.write(HIDE_CURSOR)

    def show_cursor(self):
        self.write(SHOW_CURSOR)

    def primary_context(self):
        self.write(PRIMARY_CONTEXT)

    def secondary_context(self):
        self.write(SECONDARY_CONTEXT)

    def clear_screen(self):
        self.write(CLEAR_SCREEN)

    def move_cursor(self, x, y):
        self.write(MOVE_CURSOR.format(y + 1, x + 1))  # ANSI is 1-indexed

    def invert_colors(self):
        self.write(INVERT_COLORS)

    def revert_colors(self):
        self.write(REVERT_COLORS)

    def reset_colors(self):
        self.write(RESET_COLOR)

    def color(self, foreground=None, background=None):
        if foreground is None and background is None:
            self.reset_colors()
            return

        if foreground in FOREGROUND_COLORS:
            self.write(FOREGROUND_COLORS[foreground])
        if background in BACKGROUND_COLORS:
            self.write(BACKGROUND_COLORS[background])

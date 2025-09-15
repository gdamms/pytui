import os
import select
import sys
import termios

from .renderer import Renderer
from .element import Element


class PyTUI:
    def __init__(self):
        self.renderer = Renderer()

        self.root_element = Element()
        self.root_element.width = Element.FILL_PARENT
        self.root_element.height = Element.FILL_PARENT

    def start(self):
        self.enable_input_capture()
        self.renderer.secondary_context()
        self.renderer.hide_cursor()
        self.renderer.clear_screen()
        self.renderer.blit()
        self.enable_mouse()

    def stop(self):
        self.disable_mouse()
        self.renderer.show_cursor()
        self.renderer.primary_context()
        self.renderer.blit()
        self.restore_terminal()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False  # don't suppress exceptions

    def render(self):
        self.root_element.render(self.renderer)
        self.renderer.blit()

    def enable_input_capture(self):
        # save old terminal settings
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)

        # set new terminal settings
        new_settings = termios.tcgetattr(sys.stdin)
        new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)  # lflags
        new_settings[6][termios.VMIN] = 0  # cc
        new_settings[6][termios.VTIME] = 0  # cc

        # apply new terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, new_settings)

    def restore_terminal(self):
        self.disable_mouse()
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, self.old_settings)

    def enable_mouse(self):
        # enable mouse tracking
        sys.stdout.write("\x1b[?1000h")
        sys.stdout.write("\x1b[?1006h")
        sys.stdout.flush()

    def disable_mouse(self):
        # disable mouse tracking
        sys.stdout.write("\x1b[?1000l")
        sys.stdout.write("\x1b[?1006l")
        sys.stdout.flush()

    def get_key(self):
        if select.select([sys.stdin], [], [], 0.1)[0]:
            ch_set = ''
            ch = os.read(self.fd, 1)
            while ch is not None and ch != b'':
                ch_set += ch.decode('ISO-8859-1')
                ch = os.read(self.fd, 1)
            return ch_set
        return None

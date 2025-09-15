import sys
import termios


class TerminalSettings:
    def __init__(self, fd : int, old_settings):
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


def restore_terminal(self):
    global old_terminal_settings
    if old_terminal_settings is None:
        raise RuntimeError("Input capture not enabled, nothing to restore")

    termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, old_terminal_settings.old_settings)

import time
import sys

from .renderer import Renderer
from .element import Element
from .input_manager import InputCapture
from .input_manager import KeyEvent, MouseEvent


class PyTUI:
    def __init__(self, refresh_rate: float = 1):
        self.renderer = Renderer()
        self.input_capture = InputCapture()

        self.root_element = Element()
        self.root_element.width = Element.FILL_PARENT
        self.root_element.height = Element.FILL_PARENT

        self.render_time = 0
        self.refresh_rate = refresh_rate
        self.running = False
        self.terminal_size = self.renderer.get_terminal_size()

        self.key_event_listeners = []
        self.mouse_event_listeners = []
        self.render_listeners = []
        self.terminal_resize_listeners = []

    def quit(self):
        self.running = False

    def __enter__(self):
        self.input_capture.__enter__()
        self.renderer.secondary_context()
        self.renderer.hide_cursor()
        self.renderer.clear_screen()
        self.renderer.blit()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.renderer.show_cursor()
        self.renderer.primary_context()
        self.renderer.blit()
        self.input_capture.__exit__(exc_type, exc_val, exc_tb)
        return False  # don't suppress exceptions

    def handle_input(self):
        inputs = self.input_capture.get_inputs()
        for input_event in inputs:
            if isinstance(input_event, KeyEvent):
                for listener in self.key_event_listeners:
                    listener(self, input_event)
                for element in self.root_element.get_all_children():
                    if not element.focused:
                        continue
                    element.on_key_event(input_event)
            elif isinstance(input_event, MouseEvent):
                for listener in self.mouse_event_listeners:
                    listener(self, input_event)
                self.root_element.propagate_mouse_event(input_event)
            else:
                raise RuntimeError(f"Unknown input event type: {type(input_event)}")

    def run(self):
        self.running = True
        while self.running:
            self.renderer.clear_screen()
            self.root_element.render(self.renderer)
            current_time = time.time()
            time.sleep(max(0, 1 / self.refresh_rate - (current_time - self.render_time)))
            self.render_time = current_time
            self.renderer.blit()
            for listener in self.render_listeners:
                listener(self)
            new_terminal_size = self.renderer.get_terminal_size()
            if new_terminal_size != self.terminal_size:
                self.terminal_size = new_terminal_size
                for listener in self.terminal_resize_listeners:
                    listener(self, new_terminal_size)
            self.handle_input()

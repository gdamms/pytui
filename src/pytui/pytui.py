import time
import sys

from .renderer import Renderer
from .element import Element
from .input_manager import enable_input_capture, restore_terminal, enable_mouse, disable_mouse, get_inputs
from .input_manager import KeyEvent, MouseEvent


class PyTUI:
    def __init__(self, refresh_rate: float = 1):
        self.renderer = Renderer()

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

    def start(self):
        enable_input_capture()
        self.renderer.secondary_context()
        self.renderer.hide_cursor()
        self.renderer.clear_screen()
        self.renderer.blit()
        enable_mouse()

    def stop(self):
        disable_mouse()
        self.renderer.show_cursor()
        self.renderer.primary_context()
        self.renderer.blit()
        restore_terminal()

    def quit(self):
        self.running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False  # don't suppress exceptions

    def handle_input(self):
        inputs = get_inputs()
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

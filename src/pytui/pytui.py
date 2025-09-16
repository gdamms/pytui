import time
import sys

from .renderer import Renderer
from .element import Element
from .input_manager import enable_input_capture, restore_terminal, enable_mouse, disable_mouse, get_inputs
from .input_manager import KeyEvent, MouseEvent


class PyTUI:
    def __init__(self, refresh_rate=1):
        self.renderer = Renderer()

        self.root_element = Element()
        self.root_element.width = Element.FILL_PARENT
        self.root_element.height = Element.FILL_PARENT

        self.render_time = 0
        self.refresh_rate = refresh_rate
        self.running = False

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
                for element in self.root_element.get_all_children():
                    element.on_key_event(input_event)
            elif isinstance(input_event, MouseEvent):
                # TODO: optimize by only sending to elements under the mouse cursor
                for element in self.root_element.get_all_children():
                    element.on_mouse_event(input_event)
            else:
                raise RuntimeError(f"Unknown input event type: {type(input_event)}")

    def run(self):
        self.running = True
        while self.running:
            self.renderer.clear_screen()
            self.root_element.render(self.renderer)
            current_time = time.time()
            time.sleep(max(0, self.refresh_rate - (current_time - self.render_time)))
            self.render_time = current_time
            self.renderer.blit()
            self.handle_input()

import time

from .renderer import Renderer
from .element import Element
from .input_capture import InputCapture


class PyTUI:
    def __init__(self, refresh_rate: float = 1):
        self.renderer = Renderer()
        self.input_capture = InputCapture()
        self.root_element = Element()

        self.render_time = 0
        self.refresh_rate = refresh_rate
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

    def run(self):
        self.running = True
        while self.running:
            self.renderer.clear_screen()
            self.root_element.render(self.renderer)
            current_time = time.time()
            time.sleep(max(0, 1 / self.refresh_rate - (current_time - self.render_time)))
            self.render_time = current_time
            self.renderer.blit()

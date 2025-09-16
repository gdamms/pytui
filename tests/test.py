import time

from pytui.pytui import PyTUI
from pytui.element import Element


def next_border(self, event):
    borders = [
        Element.BORDER_NONE,
        Element.BORDER_SINGLE,
        Element.BORDER_DOUBLE,
        Element.BORDER_ROUNDED,
        Element.BORDER_HEAVY,
    ]
    if self.border in borders:
        index = borders.index(self.border)
        self.border = borders[(index + 1) % len(borders)]
    else:
        self.border = Element.BORDER_NONE




def main():
    with PyTUI() as tui:
        def quit(self, event):
            if event.key == 'q' or event.key == 'ESCAPE':
                tui.quit()

        tui.root_element.text = "Hello, World!"
        tui.root_element.border = Element.BORDER_NONE
        tui.root_element.key_event_listeners.append(quit)

        el = Element()
        el.x = 10
        el.y = 3
        el.text = "This is a test"
        el.border = Element.BORDER_DOUBLE
        el.mouse_event_listeners.append(next_border)
        tui.root_element.add_child(el)

        el2 = Element()
        el2.x = 5
        el2.y = 6
        el2.text = "Another element"
        el2.border = Element.BORDER_ROUNDED
        tui.root_element.add_child(el2)

        el3 = Element()
        el3.x = 20
        el3.y = 8
        el3.text = "Element with heavy border"
        el3.border = Element.BORDER_HEAVY
        el2.add_child(el3)

        tui.main_loop()


if __name__ == "__main__":
    main()

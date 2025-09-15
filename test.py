import time

from src.pytui import PyTUI
from src.element import Element


def main():
    with PyTUI() as tui:
        tui.root_element.text = "Hello, World!"
        tui.root_element.border = Element.BORDER_SINGLE

        el = Element()
        el.x = 10
        el.y = 3
        el.text = "This is a test"
        el.border = Element.BORDER_DOUBLE
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

        while True:
            tui.render()
            time.sleep(0.1)


if __name__ == "__main__":
    main()

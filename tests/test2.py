from pytui.pytui import PyTUI
from pytui.element import Element
from pytui.style import Style


def main():
    with PyTUI() as tui:
        tui.root_element.text = "Hello, PyTUI!"

        el_1 = Element()
        el_1.text = "This is element 1."
        el_1.style.align_items = el_1.style.ALIGN_CENTER
        tui.root_element.add_child(el_1)

        el_2 = Element()
        el_2.style.direction = el_2.style.DIRECTION_HORIZONTAL
        el_2.style.border = Style.BORDER_NONE
        el_2.text = "This is element 2."
        tui.root_element.add_child(el_2)

        el_1_1 = Element()
        el_1_1.text = "This is a child of element 1."
        el_1.add_child(el_1_1)

        el_1_2 = Element()
        el_1_2.text = "This is another child of element 1."
        el_1.add_child(el_1_2)

        el_2_1 = Element()
        el_2_1.text = "This is a child of element 2."
        el_2.add_child(el_2_1)

        el_2_2 = Element()
        el_2_2.text = "This is another child of element 2."
        el_2.add_child(el_2_2)

        tui.run()


if __name__ == "__main__":
    main()

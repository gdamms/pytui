from pytui.pytui import PyTUI
from pytui.style import Style


def main():
    with PyTUI() as tui:
        list_container = tui.create_element()
        btn_container = tui.create_element()
        new_btn = tui.create_element()
        del_btn = tui.create_element()
        list_el = tui.create_element()
        list_title = tui.create_element()
        list_item = tui.create_element()
        editor_area = tui.create_element()
        editor_title = tui.create_element()

        tui.root_element.add_child(list_container)
        tui.root_element.add_child(editor_area)

        list_container.add_child(btn_container)
        list_container.add_child(list_el)

        btn_container.add_child(new_btn)
        btn_container.add_child(del_btn)

        list_el.add_child(list_title)
        list_el.add_child(list_item)

        editor_area.add_child(editor_title)

        new_btn.text = "New"
        del_btn.text = "Delete"
        list_title.text = "Files"
        editor_title.text = "Edit area"

        tui.root_element.set_style(
            border=Style.BORDER_NONE,
            width=Style.FILL_PARENT,
            height=Style.FILL_PARENT,
            direction=Style.DIRECTION_HORIZONTAL,
        )
        list_container.set_style(
            border=Style.BORDER_NONE,
            width=30,
            height=Style.FILL_PARENT,
            direction=Style.DIRECTION_VERTICAL,
        )
        btn_container.set_style(
            border=Style.BORDER_NONE,
            width=Style.FILL_PARENT,
            height=1,
            direction=Style.DIRECTION_HORIZONTAL,
        )
        new_btn.set_style(
            border=Style.BORDER_NONE,
            width=15,
            height=Style.FILL_PARENT
        )
        del_btn.set_style(
            border=Style.BORDER_NONE,
            width=15,
            height=Style.FILL_PARENT
        )
        list_el.set_style(
            border=Style.BORDER_SINGLE,
            width=Style.FILL_PARENT,
            height=Style.FILL_PARENT,
            direction=Style.DIRECTION_VERTICAL,
        )
        list_title.set_style(
            border=Style.BORDER_NONE,
            margin_top=-1,
        )
        list_item.set_style(
            border=Style.BORDER_NONE,
            width=Style.FILL_PARENT,
            height=1,
        )
        editor_area.set_style(
            border=Style.BORDER_SINGLE,
            width=60,
            height=Style.FILL_PARENT,
        )
        editor_title.set_style(
            border=Style.BORDER_NONE,
            margin_top=-1,
        )

        tui.run()


if __name__ == "__main__":
    main()

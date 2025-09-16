import os


BorderType = list[str] | None


class Element:

    WRAP_CONTENT = -1
    FILL_PARENT = -2

    BORDER_NONE: BorderType = None
    BORDER_SINGLE: BorderType = ['┌', '─', '┐', '│', '┘', '─', '└', '│']
    BORDER_DOUBLE: BorderType = ['╔', '═', '╗', '║', '╝', '═', '╚', '║']
    BORDER_ROUNDED: BorderType = ['╭', '─', '╮', '│', '╯', '─', '╰', '│']
    BORDER_HEAVY: BorderType = ['┏', '━', '┓', '┃', '┛', '━', '┗', '┃']

    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = Element.WRAP_CONTENT
        self.height = Element.WRAP_CONTENT
        self.parent = None
        self.children = []
        self.text = ""
        self.border: BorderType = Element.BORDER_NONE
        self.childs = []

        self.key_event_listeners = []
        self.mouse_event_listeners = []

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            return child
        return None

    @property
    def max_width(self):
        if self.parent is not None:
            return self.parent.max_content_width
        else:
            return os.get_terminal_size().columns

    @property
    def max_height(self):
        if self.parent is not None:
            return self.parent.max_content_height
        else:
            return os.get_terminal_size().lines

    @property
    def max_content_width(self):
        max_width = self.max_width
        if self.border is not None:
            max_width -= 2
        return max_width

    @property
    def max_content_height(self):
        max_height = self.max_height
        if self.border is not None:
            max_height -= 2
        return max_height

    @property
    def content_width(self):
        min_width = len(self.text)  # TODO: better calculate text width (wrap, ansi, newlines, etc)
        for child in self.children:
            min_width = max(min_width, child.x + child.border_width - 2)
        return min_width

    @property
    def content_height(self):
        min_height = 1 if self.text else 0  # TODO: better calculate text height (wrap, newlines, etc)
        for child in self.children:
            min_height = max(min_height, child.y + child.border_height - 2)
        return min_height

    @property
    def border_width(self):
        if self.width == Element.WRAP_CONTENT:
            width = self.content_width
            if self.border is not None:
                width += 2
            return width
        elif self.width == Element.FILL_PARENT:
            if self.parent is not None:
                return self.parent.max_content_width
            else:
                return os.get_terminal_size().columns
        else:
            return self.width

    @property
    def border_height(self):
        if self.height == Element.WRAP_CONTENT:
            height = self.content_height
            if self.border is not None:
                height += 2
            return height
        elif self.height == Element.FILL_PARENT:
            if self.parent is not None:
                return self.parent.max_content_height
            else:
                return os.get_terminal_size().lines
        else:
            return self.height

    @property
    def content_x(self):
        x = self.x
        if self.border is not None:
            x += 1
        return x

    @property
    def content_y(self):
        y = self.y
        if self.border is not None:
            y += 1
        return y

    def render(self, renderer):
        x = self.x
        y = self.y

        if self.parent is not None:
            x += self.parent.content_x
            y += self.parent.content_y

        if self.border is not None:
            renderer.move_cursor(x, y)
            renderer.write(self.border[0])  # top-left
            renderer.write(self.border[1] * (self.border_width - 2))  # top
            renderer.write(self.border[2])  # top-right

            for i in range(1, self.border_height - 1):
                renderer.move_cursor(x, y + i)
                renderer.write(self.border[3])  # left
                renderer.move_cursor(x + self.border_width - 1, y + i)
                renderer.write(self.border[7])  # right

            renderer.move_cursor(x, y + self.border_height - 1)
            renderer.write(self.border[6])  # bottom-left
            renderer.write(self.border[5] * (self.border_width - 2))  # bottom
            renderer.write(self.border[4])  # bottom-right

            x += 1
            y += 1

        renderer.move_cursor(x, y)
        renderer.write(self.text)

        for child in self.children:
            child.render(renderer)

    def get_all_children(self):
        yield self
        for child in self.children:
            yield from child.get_all_children()

    def on_key_event(self, event):
        for listener in self.key_event_listeners:
            listener(self, event)

    def on_mouse_event(self, event):
        for listener in self.mouse_event_listeners:
            listener(self, event)

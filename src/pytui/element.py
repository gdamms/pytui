import os
import sys


BorderType = list[str] | None


def log(x):
    print(f"LOG: {x}", file=sys.stderr)
    return x


class Element:

    WRAP_CONTENT = -1
    FILL_PARENT = -2

    BORDER_NONE: BorderType = None
    BORDER_SINGLE: BorderType = ['┌', '─', '┐', '│', '┘', '─', '└', '│']
    BORDER_DOUBLE: BorderType = ['╔', '═', '╗', '║', '╝', '═', '╚', '║']
    BORDER_ROUNDED: BorderType = ['╭', '─', '╮', '│', '╯', '─', '╰', '│']
    BORDER_HEAVY: BorderType = ['┏', '━', '┓', '┃', '┛', '━', '┗', '┃']

    STYLE_NORMAL = 0
    STYLE_INVERTED = 1
    STYLE_HIDDEN = 2

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
        self.style = Element.STYLE_NORMAL

        self.key_event_listeners = []
        self.mouse_event_listeners = []
        self.render_listeners = []

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

    def clear_children(self):
        for child in self.children:
            child.parent = None
        self.children = []

    @property
    def max_width(self):
        if self.width > 0:
            return self.width

        if self.parent is not None:
            return self.parent.max_content_width

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
    def text_width(self):
        # TODO: better calculate text width (wrap, ansi, etc)
        return max((len(line) for line in self.text.split('\n')), default=0) if self.text else 0

    @property
    def text_height(self):
        return self.text.count('\n') + 1 if self.text else 0  # TODO: better calculate text height (wrap, ansi, etc)

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

    @property
    def actual_width(self):
        if self.width > 0:
            return self.width
        if self.width == Element.FILL_PARENT:
            return self.max_width
        if self.width == Element.WRAP_CONTENT:
            width = self.content_width
            if self.border is not None:
                width += 2
            return width
        raise RuntimeError("Invalid width")

    @property
    def actual_height(self):
        if self.height > 0:
            return self.height
        if self.height == Element.FILL_PARENT:
            return self.max_height
        if self.height == Element.WRAP_CONTENT:
            height = self.content_height
            if self.border is not None:
                height += 2
            return height
        raise RuntimeError("Invalid height")

    @property
    def actual_content_width(self):
        width = self.actual_width
        if self.border is not None:
            width -= 2
        return width

    @property
    def actual_content_height(self):
        height = self.actual_height
        if self.border is not None:
            height -= 2
        return height

    def render(self, renderer):
        if self.style == Element.STYLE_HIDDEN:
            return

        for listener in self.render_listeners:
            listener(self)

        renderer.reset_colors()
        if self.style == Element.STYLE_INVERTED:
            renderer.invert_colors()

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

        self.render_text(renderer, x, y)

        for child in self.children:
            child.render(renderer)

    def render_text(self, renderer, x, y):
        for i, line in enumerate(self.text.split('\n')):
            if i >= self.actual_content_height:
                break
            renderer.move_cursor(x, y + i)
            renderer.write(line[:self.actual_content_width].ljust(self.actual_content_width))

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

from .style import Style
from .renderer import Renderer


class Element:
    def __init__(self):
        self.style = Style()
        self.text = ""

        self._parent: 'None | Element' = None
        self._children = []

    def add_child(self, child: 'Element'):
        child._parent = self
        self._children.append(child)

    def remove_child(self, child: 'Element'):
        if child in self._children:
            self._children.remove(child)
            child._parent = None

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, value: Style):
        self._style = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self._lines = value.splitlines()

    @property
    def outer_pos(self):
        if self.style.position == Style.POSITION_ABSOLUTE:
            x = self.style.left
            y = self.style.top
            return x, y

        if self._parent is None:
            return 0, 0

        x, y = self._parent.content_pos
        if self._parent.style.direction == Style.DIRECTION_VERTICAL:
            y_offset = 0
            for sibling in self._parent._children:
                if sibling is self:
                    break
                y_offset += sibling.outer_dim[1]
            y += y_offset

            if self._parent.style.align_items == Style.ALIGN_CENTER:
                x += (self._parent.content_width - self.outer_dim[0]) // 2
            elif self._parent.style.align_items == Style.ALIGN_START:
                x += 0
            else:
                raise NotImplementedError()
        elif self._parent.style.direction == Style.DIRECTION_HORIZONTAL:
            x_offset = 0
            for sibling in self._parent._children:
                if sibling is self:
                    break
                x_offset += sibling.outer_dim[0]
            x += x_offset

            if self._parent.style.align_items == Style.ALIGN_CENTER:
                y += (self._parent.content_height - self.outer_dim[1]) // 2
            elif self._parent.style.align_items == Style.ALIGN_START:
                y += 0
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        return x, y

    @property
    def border_pos(self):
        x, y = self.outer_pos
        x += self.style.margin_left
        y += self.style.margin_top
        return x, y

    @property
    def inner_pos(self):
        x, y = self.border_pos
        if self.style.border is not None:
            x += 1
            y += 1
        return x, y

    @property
    def content_pos(self):
        x, y = self.inner_pos
        x += self.style.padding_left
        y += self.style.padding_top
        return x, y

    @property
    def content_width(self):
        text_width = max((len(line) for line in self._lines), default=0)

        def agg(x):
            if self.style.direction == Style.DIRECTION_HORIZONTAL:
                return sum(x, start=0)
            elif self.style.direction == Style.DIRECTION_VERTICAL:
                return max(x, default=0)
            else:
                raise NotImplementedError()
        children_width = agg((child.outer_dim[0] for child in self._children))
        return max(text_width, children_width)

    @property
    def content_height(self):
        def agg(x):
            if self.style.direction == Style.DIRECTION_HORIZONTAL:
                return max(x, default=0)
            elif self.style.direction == Style.DIRECTION_VERTICAL:
                return sum(x, start=0)
            else:
                raise NotImplementedError()
        children_height = agg((child.outer_dim[1] for child in self._children))
        return max(len(self._lines), children_height)

    @property
    def inner_dim(self):
        width = self.content_width + self.style.padding_left + self.style.padding_right
        height = self.content_height + self.style.padding_top + self.style.padding_bottom
        return width, height

    @property
    def border_dim(self):
        width, height = self.inner_dim
        if self.style.border is not None:
            width += 2
            height += 2
        return width, height

    @property
    def outer_dim(self):
        width, height = self.border_dim
        width += self.style.margin_left + self.style.margin_right
        height += self.style.margin_top + self.style.margin_bottom
        return width, height

    def render_border(self, renderer: Renderer):
        border = self.style.border
        if border is None:
            return

        x, y = self.border_pos
        width, height = self.border_dim
        width -= 2
        height -= 2

        renderer.move_cursor(x, y)
        renderer.write(border[0])  # Top-left corner
        renderer.write(border[1] * width)  # Top border
        renderer.write(border[2])  # Top-right corner
        for i in range(height):
            renderer.move_cursor(x, y + 1 + i)
            renderer.write(border[3])  # Left border
            renderer.move_cursor(x + 1 + width, y + 1 + i)
            renderer.write(border[7])  # Right border
        renderer.move_cursor(x, y + 1 + height)
        renderer.write(border[6])  # Bottom-left corner
        renderer.write(border[5] * width)  # Bottom border
        renderer.write(border[4])  # Bottom-right corner

    def render(self, renderer: Renderer):
        if self.style.visibility == Style.VISIBILITY_NONE or self.style.visibility == Style.VISIBILITY_HIDDEN:
            return

        self.render_border(renderer)

        x, y = self.content_pos
        for i, line in enumerate(self._lines):
            renderer.move_cursor(x, y + i)
            renderer.write(line)

        for child in self._children:
            child.render(renderer)

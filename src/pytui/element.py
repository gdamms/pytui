import os

from .style import Style
from .renderer import Renderer
from .event import Event
from .mouse_event import MouseEvent
from .key_event import KeyEvent
from .computed_style import ComputedStyle

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .pytui import PyTUI


class Element:
    def __init__(self, pytui: 'PyTUI'):
        self._pytui = pytui

        self._style: Style = Style(self)
        self._focus_style: Style = Style(self)
        self._computed_style: None | ComputedStyle = None

        self._text = ""

        self._parent: 'None | Element' = None
        self._children = []

        self._focus = False

    def add_child(self, child: 'Element'):
        child._parent = self
        self._children.append(child)

    def remove_child(self, child: 'Element'):
        if child in self._children:
            self._children.remove(child)
            child._parent = None

    def set_style(self, style: None | Style = None, **kwargs):
        if style is not None:
            self._style = style
        for key, value in kwargs.items():
            setattr(self._style, key, value)

    def set_focus_style(self, style: None | Style = None, **kwargs):
        if style is not None:
            self._focus_style = style
        for key, value in kwargs.items():
            setattr(self._focus_style, key, value)

    @property
    def computed_style(self):
        if self._computed_style is not None:
            return self._computed_style
        current_style = self._focus_style if self._focus else self._style
        self._computed_style = ComputedStyle(current_style)
        return self._computed_style

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self._lines = value.splitlines()

    # @property
    # def outer_pos(self):
    #     if self.style.position == Style.POSITION_ABSOLUTE:
    #         x = self.style.left
    #         y = self.style.top
    #         return x, y

    #     if self._parent is None:
    #         return 0, 0

    #     x, y = self._parent.content_pos
    #     if self._parent.style.direction == Style.DIRECTION_VERTICAL:
    #         y_offset = 0
    #         for sibling in self._parent._children:
    #             if sibling is self:
    #                 break
    #             y_offset += sibling.outer_dim[1]
    #         y += y_offset

    #         if self._parent.style.align_items == Style.ALIGN_CENTER:
    #             x += (self._parent.content_width - self.outer_dim[0]) // 2
    #         elif self._parent.style.align_items == Style.ALIGN_START:
    #             x += 0
    #         else:
    #             raise NotImplementedError()
    #     elif self._parent.style.direction == Style.DIRECTION_HORIZONTAL:
    #         x_offset = 0
    #         for sibling in self._parent._children:
    #             if sibling is self:
    #                 break
    #             x_offset += sibling.outer_dim[0]
    #         x += x_offset

    #         if self._parent.style.align_items == Style.ALIGN_CENTER:
    #             y += (self._parent.content_height - self.outer_dim[1]) // 2
    #         elif self._parent.style.align_items == Style.ALIGN_START:
    #             y += 0
    #         else:
    #             raise NotImplementedError()
    #     else:
    #         raise NotImplementedError()

    #     return x, y

    # @property
    # def border_pos(self):
    #     x, y = self.outer_pos
    #     x += self.style.margin_left
    #     y += self.style.margin_top
    #     return x, y

    # @property
    # def inner_pos(self):
    #     x, y = self.border_pos
    #     if self.style.border != Style.BORDER_NONE:
    #         x += 1
    #         y += 1
    #     return x, y

    # @property
    # def content_pos(self):
    #     x, y = self.inner_pos
    #     x += self.style.padding_left
    #     y += self.style.padding_top
    #     return x, y

    # @property
    # def content_width(self):
    #     text_width = max((len(line) for line in self._lines), default=0)

    #     def agg(x):
    #         if self.style.direction == Style.DIRECTION_HORIZONTAL:
    #             return sum(x, start=0)
    #         elif self.style.direction == Style.DIRECTION_VERTICAL:
    #             return max(x, default=0)
    #         else:
    #             raise NotImplementedError()
    #     children_width = agg((child.outer_dim[0] for child in self._children))
    #     return max(text_width, children_width)

    # @property
    # def content_height(self):
    #     def agg(x):
    #         if self.style.direction == Style.DIRECTION_HORIZONTAL:
    #             return max(x, default=0)
    #         elif self.style.direction == Style.DIRECTION_VERTICAL:
    #             return sum(x, start=0)
    #         else:
    #             raise NotImplementedError()
    #     children_height = agg((child.outer_dim[1] for child in self._children))
    #     return max(len(self._lines), children_height)

    # @property
    # def content_dim(self):
    #     if self.style.sizing == Style.SIZING_CONTENT:
    #         if self.style.width == Style.WRAP_CONTENT:
    #             width = self.min_content_dim[0]
    #         elif self.style.width == Style.FILL_PARENT:
    #             width = self.max_content_dim[0]
    #         else:
    #             width = self.style.width

    #         if self.style.height == Style.WRAP_CONTENT:
    #             height = self.min_content_dim[1]
    #         elif self.style.height == Style.FILL_PARENT:
    #             height = self.max_content_dim[1]
    #         else:
    #             height = self.style.height

    #         return width, height

    #     width, height = self.inner_dim
    #     width -= self.style.padding_left + self.style.padding_right
    #     height -= self.style.padding_top + self.style.padding_bottom
    #     return width, height

    # @property
    # def inner_dim(self):
    #     if self.style.sizing == Style.SIZING_INNER:
    #         if self.style.width == Style.WRAP_CONTENT:
    #             width = self.min_inner_dim[0]
    #         elif self.style.width == Style.FILL_PARENT:
    #             width = self.max_inner_dim[0]
    #         else:
    #             width = self.style.width

    #         if self.style.height == Style.WRAP_CONTENT:
    #             height = self.min_inner_dim[1]
    #         elif self.style.height == Style.FILL_PARENT:
    #             height = self.max_inner_dim[1]
    #         else:
    #             height = self.style.height

    #         return width, height

    #     if self.style.sizing == Style.SIZING_CONTENT:
    #         width, height = self.content_dim
    #         width += self.style.padding_left + self.style.padding_right
    #         height += self.style.padding_top + self.style.padding_bottom
    #         return width, height
    #     elif self.style.sizing == Style.SIZING_BORDER or self.style.sizing == Style.SIZING_OUTER:
    #         width, height = self.border_dim
    #         if self.style.sizing == Style.SIZING_BORDER:
    #             width -= 2 if self.style.border != Style.BORDER_NONE else 0
    #             height -= 2 if self.style.border != Style.BORDER_NONE else 0
    #         return width, height
    #     else:
    #         raise NotImplementedError(f"Unknown sizing mode: {self.style.sizing}")

    # @property
    # def border_dim(self):
    #     if self.style.sizing == Style.SIZING_BORDER:
    #         if self.style.width == Style.WRAP_CONTENT:
    #             width = self.min_border_dim[0]
    #         elif self.style.width == Style.FILL_PARENT:
    #             width = self.max_border_dim[0]
    #         else:
    #             width = self.style.width

    #         if self.style.height == Style.WRAP_CONTENT:
    #             height = self.min_border_dim[1]
    #         elif self.style.height == Style.FILL_PARENT:
    #             height = self.max_border_dim[1]
    #         else:
    #             height = self.style.height

    #         return width, height

    #     if self.style.sizing == Style.SIZING_INNER or self.style.sizing == Style.SIZING_CONTENT:
    #         width, height = self.inner_dim
    #         if self.style.sizing == Style.SIZING_INNER:
    #             width += 2 if self.style.border != Style.BORDER_NONE else 0
    #             height += 2 if self.style.border != Style.BORDER_NONE else 0
    #         return width, height
    #     elif self.style.sizing == Style.SIZING_OUTER:
    #         width, height = self.outer_dim
    #         if self.style.sizing == Style.SIZING_OUTER:
    #             width -= self.style.margin_left + self.style.margin_right
    #             height -= self.style.margin_top + self.style.margin_bottom
    #         return width, height
    #     else:
    #         raise NotImplementedError(f"Unknown sizing mode: {self.style.sizing}")

    # @property
    # def outer_dim(self):
    #     if self.style.sizing == Style.SIZING_OUTER:
    #         if self.style.width == Style.WRAP_CONTENT:
    #             width = self.min_outer_dim[0]
    #         elif self.style.width == Style.FILL_PARENT:
    #             width = self.max_outer_dim[0]
    #         else:
    #             width = self.style.width

    #         if self.style.height == Style.WRAP_CONTENT:
    #             height = self.min_outer_dim[1]
    #         elif self.style.height == Style.FILL_PARENT:
    #             height = self.max_outer_dim[1]
    #         else:
    #             height = self.style.height

    #         return width, height

    #     width, height = self.border_dim
    #     width += self.style.margin_left + self.style.margin_right
    #     height += self.style.margin_top + self.style.margin_bottom
    #     return width, height

    # @property
    # def max_content_dim(self):
    #     width, height = self.max_inner_dim
    #     width -= self.style.padding_left + self.style.padding_right
    #     height -= self.style.padding_top + self.style.padding_bottom
    #     return width, height

    # @property
    # def max_inner_dim(self):
    #     width, height = self.max_border_dim
    #     if self.style.border != Style.BORDER_NONE:
    #         width -= 2
    #         height -= 2
    #     return width, height

    # @property
    # def max_border_dim(self):
    #     width, height = self.max_outer_dim
    #     width -= self.style.margin_left + self.style.margin_right
    #     height -= self.style.margin_top + self.style.margin_bottom
    #     return width, height

    # @property
    # def max_outer_dim(self):
    #     if self._parent is None:
    #         term_size = os.get_terminal_size()
    #         return term_size.columns, term_size.lines
    #     return self._parent.max_content_dim  # TODO: account for siblings? add weighting?

    # @property
    # def min_outer_dim(self):
    #     width, height = self.border_dim
    #     width += self.style.margin_left + self.style.margin_right
    #     height += self.style.margin_top + self.style.margin_bottom
    #     return width, height

    # @property
    # def min_border_dim(self):
    #     width, height = self.min_inner_dim
    #     width += self.style.margin_left + self.style.margin_right
    #     height += self.style.margin_top + self.style.margin_bottom
    #     return width, height

    # @property
    # def min_inner_dim(self):
    #     width, height = self.min_content_dim
    #     if self.style.border != Style.BORDER_NONE:
    #         width += 2
    #         height += 2
    #     return width, height

    # @property
    # def min_content_dim(self):
    #     return self.content_width, self.content_height

    def compute_min_content_width(self):
        text_width = max((len(line) for line in self._lines), default=0)

        def agg(x):
            if self.style.direction == Style.DIRECTION_HORIZONTAL:
                return sum(x, start=0)
            elif self.style.direction == Style.DIRECTION_VERTICAL:
                return max(x, default=0)
            else:
                raise NotImplementedError()
        children_width = agg((child.compute_min_content_width() for child in self._children))

        self._min_content_width = max(text_width, children_width)
        return self._min_content_width

    def compute_min_content_height(self):
        def agg(x):
            if self.style.direction == Style.DIRECTION_HORIZONTAL:
                return max(x, default=0)
            elif self.style.direction == Style.DIRECTION_VERTICAL:
                return sum(x, start=0)
            else:
                raise NotImplementedError()
        children_height = agg((child.compute_min_content_height() for child in self._children))

        self._min_content_height = max(len(self._lines), children_height)
        return self._min_content_height

    def render_border(self, renderer: Renderer):
        border = self.style.border
        if border == Style.BORDER_NONE:
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

    def focus(self):
        self.pytui.focus(self)

    def unfocus(self):
        self._focus = False

    def on_focus(self):
        self._focus = True

    def handle_event(self, event: Event):
        if isinstance(event, MouseEvent):
            self.handle_mouse_event(event)
            return

        if isinstance(event, KeyEvent):
            self.handle_key_event(event)
            return

        raise NotImplementedError()

    def handle_mouse_event(self, event: MouseEvent):
        x, y = self.outer_pos
        width, height = self.outer_dim
        if not (x <= event.x < x + width and y <= event.y < y + height):
            return  # event not in this element

        for child in self._children:
            if child.handle_event(event):
                return

        self.focus()

    def handle_key_event(self, event: KeyEvent):
        if not self._focus:
            return  # not focused, ignore key events
        pass  # to be implemented

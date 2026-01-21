from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .style import Style, DirectionType
    from .element import Element


class ComputedStyle:
    def __init__(self, style: Style):
        self._style = style
        self._element = style.element

    @property
    def style(self) -> Style:
        return self._style

    @property
    def element(self) -> Element:
        return self._element
    
    @property
    def direction(self) -> DirectionType:
        return self._style.direction

    @property
    def min_content_width(self):
        if hasattr(self, '_min_content_width'):
            return self._min_content_width
        self.compute_min_content_width()
        return self._min_content_width

    def compute_min_content_width(self):
        text_width = max((len(line) for line in self._element._lines), default=0)

        def agg(x):
            if self.direction == Style.DIRECTION_HORIZONTAL:
                return sum(x, start=0)
            elif self.direction == Style.DIRECTION_VERTICAL:
                return max(x, default=0)
            else:
                raise NotImplementedError()
        children_width = agg((child.computed_style for child in self._element._children))

        self._min_content_width = max(text_width, children_width)
        return self._min_content_width
    
    @property
    def min_content_height(self):
        if hasattr(self, '_min_content_height'):
            return self._min_content_height
        self.compute_min_content_height()
        return self._min_content_height

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
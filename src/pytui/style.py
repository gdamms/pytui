from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .element import Element


BorderType = list[str]
VisibleType = int
WrapType = int
PositionType = int
DirectionType = int
JustifyType = int
AlignType = int
SizingType = int


class Style:

    BORDER_NONE: BorderType = []
    BORDER_INVISIBLE: BorderType = [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']
    BORDER_SINGLE: BorderType = ['┌', '─', '┐', '│', '┘', '─', '└', '│']
    BORDER_DOUBLE: BorderType = ['╔', '═', '╗', '║', '╝', '═', '╚', '║']
    BORDER_ROUNDED: BorderType = ['╭', '─', '╮', '│', '╯', '─', '╰', '│']
    BORDER_HEAVY: BorderType = ['┏', '━', '┓', '┃', '┛', '━', '┗', '┃']

    VISIBILITY_VISIBLE: VisibleType = 0
    VISIBILITY_HIDDEN: VisibleType = 1
    VISIBILITY_NONE: VisibleType = 2

    WRAP_CONTENT: WrapType = -1
    FILL_PARENT: WrapType = -2

    POSITION_RELATIVE: PositionType = 0
    POSITION_ABSOLUTE: PositionType = 1

    DIRECTION_VERTICAL: DirectionType = 0
    DIRECTION_HORIZONTAL: DirectionType = 1

    JUSTIFY_START: JustifyType = 0

    ALIGN_START: AlignType = 0
    ALIGN_CENTER: AlignType = 1

    SIZING_CONTENT: SizingType = 0
    SIZING_INNER: SizingType = 1
    SIZING_BORDER: SizingType = 2
    SIZING_OUTER: SizingType = 3

    def __init__(self, element: Element, **kwargs):
        self._element = element
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def element(self) -> Element:
        return self._element

    @property
    def border(self) -> BorderType:
        if not hasattr(self, '_border'):
            return Style.BORDER_SINGLE
        return self._border

    @border.setter
    def border(self, value: BorderType):
        self._border = value

    @property
    def visibility(self) -> VisibleType:
        if not hasattr(self, '_visibility'):
            return Style.VISIBILITY_VISIBLE
        return self._visibility

    @visibility.setter
    def visibility(self, value: VisibleType):
        self._visibility = value

    @property
    def inverted(self) -> bool:
        if not hasattr(self, '_inverted'):
            return False
        return self._inverted

    @inverted.setter
    def inverted(self, value: bool):
        self._inverted = value

    @property
    def content_fg_color(self) -> str:
        if not hasattr(self, '_content_fg_color'):
            return 'white'
        return self._content_fg_color

    @content_fg_color.setter
    def content_fg_color(self, value: str):
        self._content_fg_color = value

    @property
    def content_bg_color(self) -> str:
        if not hasattr(self, '_content_bg_color'):
            return 'black'
        return self._content_bg_color

    @content_bg_color.setter
    def content_bg_color(self, value: str):
        self._content_bg_color = value

    @property
    def border_fg_color(self) -> str:
        if not hasattr(self, '_border_fg_color'):
            return 'white'
        return self._border_fg_color

    @border_fg_color.setter
    def border_fg_color(self, value: str):
        self._border_fg_color = value

    @property
    def border_bg_color(self) -> str:
        if not hasattr(self, '_border_bg_color'):
            return 'black'
        return self._border_bg_color

    @border_bg_color.setter
    def border_bg_color(self, value: str):
        self._border_bg_color = value

    @property
    def width(self) -> WrapType:
        if not hasattr(self, '_width'):
            return Style.WRAP_CONTENT
        return self._width

    @width.setter
    def width(self, value: WrapType):
        self._width = value

    @property
    def height(self) -> WrapType:
        if not hasattr(self, '_height'):
            return Style.WRAP_CONTENT
        return self._height

    @height.setter
    def height(self, value: WrapType):
        self._height = value

    @property
    def padding_top(self) -> int:
        if not hasattr(self, '_padding_top'):
            return 0
        return self._padding_top

    @padding_top.setter
    def padding_top(self, value: int):
        self._padding_top = value

    @property
    def padding_bottom(self) -> int:
        if not hasattr(self, '_padding_bottom'):
            return 0
        return self._padding_bottom

    @padding_bottom.setter
    def padding_bottom(self, value: int):
        self._padding_bottom = value

    @property
    def padding_left(self) -> int:
        if not hasattr(self, '_padding_left'):
            return 0
        return self._padding_left

    @padding_left.setter
    def padding_left(self, value: int):
        self._padding_left = value

    @property
    def padding_right(self) -> int:
        if not hasattr(self, '_padding_right'):
            return 0
        return self._padding_right

    @padding_right.setter
    def padding_right(self, value: int):
        self._padding_right = value

    @property
    def margin_top(self) -> int:
        if not hasattr(self, '_margin_top'):
            return 0
        return self._margin_top

    @margin_top.setter
    def margin_top(self, value: int):
        self._margin_top = value

    @property
    def margin_bottom(self) -> int:
        if not hasattr(self, '_margin_bottom'):
            return 0
        return self._margin_bottom

    @margin_bottom.setter
    def margin_bottom(self, value: int):
        self._margin_bottom = value

    @property
    def margin_left(self) -> int:
        if not hasattr(self, '_margin_left'):
            return 0
        return self._margin_left

    @margin_left.setter
    def margin_left(self, value: int):
        self._margin_left = value

    @property
    def margin_right(self) -> int:
        if not hasattr(self, '_margin_right'):
            return 0
        return self._margin_right

    @margin_right.setter
    def margin_right(self, value: int):
        self._margin_right = value

    @property
    def position(self) -> PositionType:
        if not hasattr(self, '_position'):
            return Style.POSITION_RELATIVE
        return self._position

    @position.setter
    def position(self, value: PositionType):
        self._position = value

    @property
    def top(self) -> int:
        if not hasattr(self, '_top'):
            return 0
        return self._top

    @top.setter
    def top(self, value: int):
        self._top = value

    @property
    def bottom(self) -> None | int:
        if not hasattr(self, '_bottom'):
            return None
        return self._bottom

    @bottom.setter
    def bottom(self, value: None | int):
        self._bottom = value

    @property
    def left(self) -> int:
        if not hasattr(self, '_left'):
            return 0
        return self._left

    @left.setter
    def left(self, value: int):
        self._left = value

    @property
    def right(self) -> None | int:
        if not hasattr(self, '_right'):
            return None
        return self._right

    @right.setter
    def right(self, value: None | int):
        self._right = value

    @property
    def direction(self) -> DirectionType:
        if not hasattr(self, '_direction'):
            return Style.DIRECTION_VERTICAL
        return self._direction

    @direction.setter
    def direction(self, value: DirectionType):
        self._direction = value

    @property
    def justify_content(self) -> JustifyType:
        if not hasattr(self, '_justify_content'):
            return Style.JUSTIFY_START
        return self._justify_content

    @justify_content.setter
    def justify_content(self, value: JustifyType):
        self._justify_content = value

    @property
    def align_items(self) -> AlignType:
        if not hasattr(self, '_align_items'):
            return Style.ALIGN_START
        return self._align_items

    @align_items.setter
    def align_items(self, value: AlignType):
        self._align_items = value

    @property
    def sizing(self) -> SizingType:
        if not hasattr(self, '_sizing'):
            return Style.SIZING_BORDER
        return self._sizing

    @sizing.setter
    def sizing(self, value: SizingType):
        self._sizing = value

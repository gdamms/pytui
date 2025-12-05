BorderType = list[str] | None
VisibleType = int
WrapType = int
PositionType = int
DirectionType = int
JustifyType = int
AlignType = int


class Style:

    BORDER_NONE: BorderType = None
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

    def __init__(self, **kwargs):
        self.border = Style.BORDER_SINGLE
        self.visibility = Style.VISIBILITY_VISIBLE
        self.inverted = False
        self.content_fg_color = 'white'
        self.content_bg_color = 'black'
        self.border_fg_color = 'white'
        self.border_bg_color = 'black'
        self.width = Style.WRAP_CONTENT
        self.height = Style.WRAP_CONTENT
        self.padding_top = 0
        self.padding_bottom = 0
        self.padding_left = 0
        self.padding_right = 0
        self.margin_top = 0
        self.margin_bottom = 0
        self.margin_left = 0
        self.margin_right = 0
        self.position = Style.POSITION_RELATIVE
        self.top = 0
        self.bottom = None
        self.left = 0
        self.right = None
        self.direction = Style.DIRECTION_VERTICAL
        self.justify_content = Style.JUSTIFY_START
        self.align_items = Style.ALIGN_START
        for k, v in kwargs.items():
            setattr(self, k, v)

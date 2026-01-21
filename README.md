# pytui
A python package to make TUIs.


## TODO

- Need a better dynamic sizing system:
    - split dim/pos into width-height and x-y (group is a bad idea as they are not always related)
    - max/min sizes need to account for fixed sizes of parent
    - siblings sizes concurrency
    - percentage sizes


Sizing hierarchy:
- OUTER: includes margin
- BORDER: includes border
- INNER: includes padding
- CONTENT: only content

Sizing modes:
- SIZING_OUTER: width/height refer to outer dimensions
- SIZING_BORDER: width/height refer to border dimensions
- SIZING_INNER: width/height refer to inner dimensions
- SIZING_CONTENT: width/height refer to content dimensions

Sizing values:
- WRAP_CONTENT: size to fit content
- FILL_PARENT: size to fill parent available space, weighted if multiple siblings use FILL_PARENT
- absolute size: int value
- relative size: float value (>0.0) as a fraction of parent content size

Sizing resolution:
- compute minimum content size: (from root to leaves)
    - compute childs minimum content sizes
    - add them along the layout direction, take max along cross direction
    - compute text size
    - take max of text size and children size
- iterate to compute actual sizes: (from root to leaves)
    - absolute sizes: use as-is
    - fit content depends on childs -> if child depends on parent (self) size, use minimum content size (of self)
    - relative sizes: depends on parent size
- on more iteration for fill parent: depends on parent and siblings (parent size - sum of absolute, relative, wrap_content sizes; distribute remaining space according to weights)
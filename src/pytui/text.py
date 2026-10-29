"""Text measurement and wrapping, in terminal cells."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

_ZERO_WIDTH = {"​", "‌", "‍", "⁠", "﻿"}
_TOKEN = re.compile(r"\s+|\S+")


@lru_cache(maxsize=8192)
def char_width(char: str) -> int:
    """Number of terminal cells used by a single character (0, 1 or 2)."""
    code = ord(char)
    if 32 <= code < 127:
        return 1
    if code < 32 or 0x7F <= code < 0xA0 or char in _ZERO_WIDTH:
        return 0
    if unicodedata.combining(char) or unicodedata.category(char) in ("Mn", "Me", "Cf"):
        return 0
    if 0xFE00 <= code <= 0xFE0F:  # variation selectors
        return 0
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return 2
    return 1


def text_width(text: str) -> int:
    """Number of terminal cells used by a single line of text."""
    if text.isascii() and text.isprintable():
        return len(text)
    return sum(char_width(char) for char in text)


def split_at_width(text: str, width: int) -> tuple[str, str]:
    """Split ``text`` so that the head fits in ``width`` cells.

    The head always contains at least one character so callers make progress.
    """
    used = 0
    for index, char in enumerate(text):
        w = char_width(char)
        if used + w > width and index > 0:
            return text[:index], text[index:]
        used += w
    return text, ""


def truncate(text: str, width: int) -> str:
    """Cut ``text`` to at most ``width`` cells."""
    if width <= 0:
        return ""
    if text_width(text) <= width:
        return text
    head, _ = split_at_width(text, width)
    if text_width(head) > width:  # a single wide char in a 1-cell space
        return ""
    return head


def slice_cells(text: str, start: int, width: int) -> str:
    """Return the part of ``text`` covering cells ``[start, start + width)``.

    Wide characters cut in half by either edge are replaced by spaces.
    """
    out: list[str] = []
    end = start + width
    pos = 0
    for char in text:
        if pos >= end:
            break
        w = char_width(char)
        if w == 0:
            if out and start <= pos <= end:
                out.append(char)
            continue
        if pos >= start and pos + w <= end:
            out.append(char)
        elif pos < end and pos + w > start:
            out.append(" " * (min(pos + w, end) - max(pos, start)))
        pos += w
    return "".join(out)


def index_at_cell(text: str, cell: int) -> int:
    """Index of the character displayed at ``cell`` (or ``len(text)`` past the end)."""
    pos = 0
    for index, char in enumerate(text):
        w = char_width(char)
        if pos + w > cell:
            return index
        pos += w
    return len(text)


def wrap(text: str, width: int) -> list[str]:
    """Word-wrap ``text`` into lines of at most ``width`` cells.

    Hard line breaks are kept, words longer than ``width`` are split and
    whitespace at wrap points is dropped. With ``width <= 0`` only hard line
    breaks are applied.
    """
    lines: list[str] = []
    for paragraph in text.expandtabs(4).split("\n"):
        if width <= 0:
            lines.append(paragraph)
            continue
        line, used = "", 0
        for token in _TOKEN.findall(paragraph):
            token_width = text_width(token)
            if token[0].isspace():
                if used + token_width <= width:
                    line, used = line + token, used + token_width
                else:
                    lines.append(line)
                    line, used = "", 0
                continue
            if used + token_width > width and line:
                lines.append(line.rstrip())
                line, used = "", 0
            while token_width > width:
                head, token = split_at_width(token, width)
                lines.append(head)
                token_width = text_width(token)
            line, used = line + token, used + token_width
        lines.append(line)
    return lines

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


def clean_text(text: str) -> str:
    """Normalize line breaks to ``\n`` and expand tabs, as text is stored in widgets."""
    return text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)


def wrap_spans(text: str, width: int) -> list[tuple[int, int]]:
    """Word-wrap ``text`` into lines of at most ``width`` cells, as ``(start, end)`` offsets.

    Hard line breaks are kept, words longer than ``width`` are split and
    whitespace at wrap points is left out of the lines. With ``width <= 0``
    only hard line breaks are applied. ``text`` must not contain tabs.
    """
    spans: list[tuple[int, int]] = []
    offset = 0
    for paragraph in text.split("\n"):
        base, offset = offset, offset + len(paragraph) + 1
        if width <= 0:
            spans.append((base, base + len(paragraph)))
            continue
        start = end = base
        used = 0
        for match in _TOKEN.finditer(paragraph):
            token = match.group()
            token_start, token_end = base + match.start(), base + match.end()
            token_width = text_width(token)
            if token[0].isspace():
                if used + token_width <= width:
                    end, used = token_end, used + token_width
                else:
                    spans.append((start, end))
                    start = end = token_end
                    used = 0
                continue
            if used + token_width > width and end > start:
                while end > start and text[end - 1].isspace():
                    end -= 1
                spans.append((start, end))
                start = end = token_start
                used = 0
            while token_width > width:
                head, token = split_at_width(token, width)
                spans.append((token_start, token_start + len(head)))
                token_start += len(head)
                start = token_start
                token_width = text_width(token)
            end, used = token_end, used + token_width
        spans.append((start, end))
    return spans


def wrap(text: str, width: int) -> list[str]:
    """Word-wrap ``text`` into lines of at most ``width`` cells (see :func:`wrap_spans`)."""
    text = text.expandtabs(4)
    return [text[start:end] for start, end in wrap_spans(text, width)]

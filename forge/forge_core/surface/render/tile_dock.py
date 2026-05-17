# -*- coding: utf-8 -*-
"""
forge_core.surface.render.tile_dock
====================================

Compact dynamic tile dock for reboot surface controls and navigation.
"""

from forge_core.surface.render.pills import pill_link
from forge_core.surface.render.primitives import colour, reset, spacer


WIDTH = 41
INNER = 37
BODY_INDENT = 3


def center(text, width=WIDTH):
    text = str(text or '')
    if len(text) >= width:
        return text
    left = (width - len(text)) // 2
    return (' ' * left) + text


def side_prefix():
    return '  '


def _safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _visible_width(icon, label):
    return len(str(icon or '')) + len(str(label or ''))


def tile_dock_height(tiles, cols=2, row_gap=1, header=True, leading_space=1, trailing_space=0):
    tiles = list(tiles or [])
    if not tiles:
        return 0

    cols = max(1, _safe_int(cols, 2))
    row_gap = max(0, _safe_int(row_gap, 1))
    leading_space = max(0, _safe_int(leading_space, 1))
    trailing_space = max(0, _safe_int(trailing_space, 0))

    rows = (len(tiles) + cols - 1) // cols

    total = leading_space
    if header:
        total += 4

    total += rows * 2

    if rows > 1:
        total += (rows - 1) * row_gap

    total += trailing_space
    return total


def render_tile_dock(
    title,
    tiles,
    cols=2,
    col_width=18,
    gap='   ',
    row_gap=1,
    leading_space=1,
    trailing_space=0,
    tone='surface_2',
):
    items = list(tiles or [])
    if not items:
        return False

    cols = max(1, _safe_int(cols, 2))
    col_width = max(8, _safe_int(col_width, 18))
    row_gap = max(0, _safe_int(row_gap, 1))
    leading_space = max(0, _safe_int(leading_space, 1))
    trailing_space = max(0, _safe_int(trailing_space, 0))

    if leading_space:
        spacer(leading_space)

    colour(tone)
    print(side_prefix() + '═' * INNER)
    reset()

    colour('text')
    print(center(str(title or '').upper(), WIDTH))
    reset()

    colour(tone)
    print(side_prefix() + '═' * INNER)
    reset()
    print('')

    for i in range(0, len(items), cols):
        row = items[i:i + cols]

        print(' ' * BODY_INDENT, end='')
        for j, item in enumerate(row):
            icon, label, _subtitle, args, item_tone = item
            pill_link(label, *args, tone=item_tone, icon=icon)

            visible = _visible_width(icon, label)
            pad = max(1, col_width - visible)
            print(' ' * pad, end='')

            if j < len(row) - 1:
                print(gap, end='')
        print('')

        print(' ' * BODY_INDENT, end='')
        for j, item in enumerate(row):
            _icon, _label, subtitle, _args, _tone = item
            colour('muted')
            cell = ('%-' + str(col_width) + 's') % (str(subtitle or '')[:col_width])
            print(cell, end='')
            reset()

            if j < len(row) - 1:
                print(gap, end='')
        print('')

        if i + cols < len(items):
            spacer(row_gap)

    if trailing_space:
        spacer(trailing_space)

    return True

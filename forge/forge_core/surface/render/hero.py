# -*- coding: utf-8 -*-
"""
forge_core.surface.render.hero
===============================

Branded section openers for surface pages.

* ``hero`` — full LinkOS-branded title block at the top of a route.
* ``big_section`` — heavy in-page section heading with underline.

Both are intentionally weighty. For lighter lists use
:func:`forge_core.surface.render.primitives.section_label`.
"""

from forge_core.surface.render.primitives import (
    band, colour, reset, say, spacer,
)


def hero(title_text, icon='🌅', subtitle=None):
    """Print the top-of-page LinkOS hero block.

    Renders as: blank line / heavy rule / ``icon  LINKOS ✦ title`` /
    softer rule / optional subtitle. Used once per page at the very top
    of console output.
    """
    spacer()
    band('━', 46, 'border')
    colour('text')
    print('%s  LINKOS' % icon, end='')
    colour('muted')
    print('   ✦   ', end='')
    colour('accent')
    print(title_text)
    reset()
    band('━', 46, 'surface_2')
    if subtitle:
        say('   ' + subtitle, 'muted')
        spacer()


def big_section(title_text, icon='◆', tone='accent'):
    """Print an in-page section heading with underline.

    Heavier than :func:`section_label` — for major page sections where
    the underline visually anchors a block of cards or actions below.
    """
    spacer(2)
    colour(tone)
    print('%s  %s' % (icon, title_text.upper()))
    reset()
    colour('surface_2')
    print('   ' + '▔' * 30)
    reset()

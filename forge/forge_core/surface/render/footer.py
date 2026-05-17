# -*- coding: utf-8 -*-
"""
forge_core.surface.render.footer
=================================

Bottom navigation rail.

Surface pages render bottom-up in the Pythonista console: the footer
is the last thing printed and the first thing the user sees. It
provides persistent navigation between top-level surfaces.

Overlaps with ``nav.render_global_nav`` — that's the tile-dock-based
modern path. Footer is the older hand-rolled rail kept for any page
that imports it directly. Prefer ``render_global_nav`` for new code.
"""

import time

try:
    import console as _console
except Exception:
    _console = None

from forge_core.surface.render.primitives import (
    band, colour, reset, say, spacer, url,
)


def bottom_action(label, target_args, icon='◆', tone='accent'):
    """Print one footer control where the whole icon+label is tappable."""
    href = url(*target_args)
    text = '%s%s' % (str(icon), str(label).upper())

    if _console and hasattr(_console, 'write_link'):
        try:
            colour(tone)
            _console.write_link(text, href)
            reset()
            print('   ', end='')
            return
        except Exception:
            reset()

    colour(tone)
    print(text, end='   ')
    reset()


def footer():
    """Render the bottom action rail as a boxed-off control area.

    Uses rule-only borders rather than vertical box sides so it stays
    visually solid in the Pythonista console.
    """
    spacer()
    spacer()

    colour('border')
    print('  ' + '═' * 38)
    reset()

    colour('muted')
    print('               NAVIGATION')
    reset()
    print('')

    print('   ', end='')
    bottom_action('Back', ('back',), icon='⬅️ ', tone='orange')
    bottom_action('Home', ('home',), icon='🏠 ', tone='success')
    bottom_action('Runs', ('runs',), icon='◎ ', tone='accent')
    bottom_action('Docs', ('docs',), icon='📖 ', tone='border')
    print('')

    print('   ', end='')
    bottom_action('Run Forge', ('run_forge',), icon='▶️ ', tone='warning')
    bottom_action('New here?', ('start',), icon='🏁 ', tone='success')
    print('')

    print('')
    colour('surface_2')
    print('  ' + '─' * 38)
    reset()

    spacer()
    spacer()

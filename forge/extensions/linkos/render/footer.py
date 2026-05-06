# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.render.footer
======================================

Bottom navigation rail for LinkOS.

LinkOS pages render bottom-up in the Pythonista console: the footer is
the last thing printed and the first thing the user sees. It provides
persistent navigation between top-level surfaces.
"""

import time

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.render.primitives import (
    band, colour, reset, say, spacer, url,
)


def bottom_action(label, target_args, icon='◆', tone='accent'):
    """Print one rail item — the whole emoji+label is the tap target.

    Does not emit a newline; the caller composes the rail row.
    """
    href = url(*target_args)
    text = str(icon) + str(label).upper()

    if _console and hasattr(_console, 'write_link'):
        try:
            colour(tone)
            _console.write_link(text, href)
            reset()
            return
        except Exception:
            reset()

    colour(tone)
    print('  ' + text, end='')
    reset()


def footer():
    """Print the compact LinkOS bottom rail.

    No label, no timestamp. The rail is persistent navigation, not content.
    Extra spacer keeps it clear of the Pythonista input bar.
    """
    spacer(2)

    bottom_action('Back', ('back',), icon='⬅️', tone='orange')
    bottom_action('Home', ('home',), icon='🏠', tone='success')
    bottom_action('Run', ('run_forge',), icon='▶️', tone='warning')
    bottom_action('Start', ('start',), icon='🏁', tone='success')
    bottom_action('Docs', ('docs',), icon='📖', tone='accent')
    print('')
    print('')

    spacer(4)

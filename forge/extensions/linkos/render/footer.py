# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.render.footer
======================================

Bottom navigation rail for LinkOS.

LinkOS pages render bottom-up in the Pythonista console: the footer is
the last thing printed and the first thing the user sees. It must always
offer a safe escape route.
"""

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.render.primitives import (
    colour, reset, spacer, url, root_router_installed,
)


def bottom_action(label, target_args, icon='◆ ', tone='accent'):
    """Print one footer control where the whole icon+label is tappable."""
    href = url(*target_args)
    text = '%s%s' % (str(icon), str(label).upper())

    links_active = root_router_installed() and bool(href)

    if links_active and _console and hasattr(_console, 'write_link'):
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
    """Render the bottom action rail as a boxed-off control area."""
    spacer(2)

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
    bottom_action('New here?', ('start-here',), icon='🏁 ', tone='success')
    print('')

    print('')
    colour('surface_2')
    print('  ' + '─' * 38)
    reset()

    spacer(2)

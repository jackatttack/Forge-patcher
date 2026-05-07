# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.unknown
======================================

Recovery page for unrecognised LinkOS routes.

Unknown routes should never dead-end the user. They should explain what
happened and offer safe exits.
"""

from forge.extensions.linkos.render.docpage import (
    doc_footer, doc_hero, doc_text, doc_tile_grid,
)


def unknown_page(cmd, rest=None):
    """Render the unknown-command recovery page."""
    rest = rest or []

    doc_hero('Unknown route', 'safe recovery')
    doc_text('LinkOS did not recognise this route: %s' % (cmd or '(empty)'), tone='warning')

    if rest:
        doc_text('Extra route arguments: %s' % ' '.join(str(x) for x in rest), tone='muted')

    doc_text(
        'This is not dangerous. It usually means a stale link, typo, or a route '
        'that has not been built yet. Use one of the safe exits below.',
        tone='muted',
    )

    doc_tile_grid('safe exits', [
        ('🧭 ', 'Start Here', 'orientation', ('start-here',), 'success'),
        ('🩺 ', 'Health', 'install check', ('install-health',), 'warning'),
        ('🏠 ', 'Home', 'LinkOS home', ('home',), 'success'),
        ('📖 ', 'Docs', 'browse docs', ('docs',), 'accent'),
        ('❔ ', 'Help', 'human help', ('help', 'HELP'), 'border'),
        ('▶️ ', 'Run Forge', 'clipboard loop', ('run_forge',), 'orange'),
    ])

    doc_footer()


# Backward compatibility for older imports.
def unknown(cmd):
    unknown_page(cmd, [])

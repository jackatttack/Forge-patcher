# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.unknown
======================================

Recovery page for unrecognised commands.

LinkOS pages should never dead-end the user. Any unknown route lands
here with a clear "what went wrong" message and a route home.
"""

from forge.extensions.linkos.render.cards import action_link, panel
from forge.extensions.linkos.render.footer import footer
from forge.extensions.linkos.render.hero import big_section, hero


def unknown(cmd):
    """Render the unknown-command recovery page."""
    hero('Unknown command', '⚠️', 'Bad links should fail into navigation, not dead ends.')
    panel(
        'Recovery',
        [
            'Unknown LinkOS command: %s' % cmd,
            'Route back to a useful starting point.',
        ],
        icon='⚠️',
        tone='danger',
    )

    big_section('Recovery', '🛟', 'danger')
    action_link('Home', 'home', icon='🏠', tone='success',
                note='Return to LinkOS home.')

    footer()

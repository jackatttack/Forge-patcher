# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.coming_soon
==========================================

Aspirational placeholder pages for unbuilt LinkOS destinations.

Home and other launchers can route to ``coming_soon <name>`` for
features that are designed but not yet built (docs index, shortcut
launcher, scratch composer). Each placeholder previews what the
destination will be, so users discovering LinkOS via the home grid
see the full vision rather than dead links.

Add or update entries in :data:`PLANS` to reflect new aspirational
destinations.
"""

from forge.extensions.linkos.render.docpage import (
    doc_bullets, doc_footer, doc_hero, doc_section, doc_text,
)


PLANS = {
    'docs': {
        'title': 'Docs',
        'subtitle': 'rendered ops + HELP + GUIDE',
        'intro': (
            'A browsable index of every Forge op with its rendered '
            'HELP page, plus GUIDE workflows once GUIDE rendering '
            'lands.'
        ),
        'features': [
            'Searchable list of all registered ops.',
            'Tap any op to open its rendered HELP page.',
            'Curated GUIDE pages for repeatable Forge workflows.',
            'Copy starter bundles directly from the doc page.',
        ],
    },
    'shortcuts': {
        'title': 'Shortcuts',
        'subtitle': 'iOS shortcut launchers',
        'intro': (
            'A page of tappable iOS Shortcut hooks for the things '
            'you launch from LinkOS most often.'
        ),
        'features': [
            'Open a configured AI/chat shortcut in one tap from any LinkOS page.',
            'Quick-launch Pythonista, Notes, Reminders, etc.',
            'Tappable shortcut links you can configure yourself.',
        ],
    },
    'scratch': {
        'title': 'Scratch',
        'subtitle': 'quick .py / .txt jot',
        'intro': (
            'A composer for fast notes and tiny scripts without '
            'leaving LinkOS.'
        ),
        'features': [
            'Compose plain text or Python in console input.',
            'Save to scratch/ with an auto-stamped filename.',
            'Reopen the most recent scratch from home.',
        ],
    },
}


def coming_soon_page(name):
    """Render a placeholder page for an aspirational destination.

    ``name`` is the entry key in :data:`PLANS`. Unknown names render a
    generic "coming soon" stub so the route never dead-ends.
    """
    plan = PLANS.get(str(name or '').lower())

    if not plan:
        doc_hero('Coming soon', str(name or 'unknown'))
        doc_text(
            'This destination is planned but not yet built. Check '
            'back as LinkOS grows.'
        )
        doc_footer()
        return

    doc_hero(plan['title'], plan.get('subtitle', 'coming soon'))
    doc_text(plan['intro'])

    features = plan.get('features') or []
    if features:
        doc_section('what this will be')
        doc_bullets(features)

    doc_footer()

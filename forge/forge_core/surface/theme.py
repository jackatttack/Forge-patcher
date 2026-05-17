# -*- coding: utf-8 -*-
"""
forge_core.surface.theme
========================

Semantic colour roles for the Forge Surface.

Renderers should prefer semantic roles for product surfaces:

    audit.target
    audit.packet
    action.copy
    run.hero.border

The low-level palette still lives in render/primitives.py. This module maps
surface roles onto those palette tones so the visual language can be tuned in
one place without rewriting every renderer.
"""


DEFAULT_THEME = {
    # Base text roles
    'body': 'text',
    'label': 'muted',
    'value': 'text',
    'path': 'accent',
    'target': 'accent',
    'metric': 'warning',

    # Run summary / home
    'run.hero.border': 'border',
    'run.hero.title': 'success',
    'run.hero.subtitle': 'muted',
    'run.metric.packet': 'muted',
    'run.outcome.applied': 'success',
    'run.outcome.skipped': 'warning',
    'run.outcome.failed': 'danger',

    # Audit launch page
    'audit.header': 'muted',
    'audit.card.border': 'border',
    'audit.card.ok': 'success',
    'audit.card.skip': 'warning',
    'audit.card.fail': 'danger',
    'audit.op': 'success',
    'audit.status.ok': 'success',
    'audit.status.skip': 'warning',
    'audit.status.fail': 'danger',
    'audit.label': 'muted',
    'audit.target': 'orange',
    'audit.note': 'muted',
    'audit.packet': 'warning',

    # Actions
    'action.primary': 'success',
    'action.detail': 'success',
    'action.edit': 'accent',
    'action.copy': 'warning',
    'action.nav': 'accent',
    'action.home': 'success',
    'action.raw': 'warning',

    # Generic status roles
    'status.ok': 'success',
    'status.skip': 'warning',
    'status.fail': 'danger',
}


def resolve_tone(name, default='text'):
    """Resolve a semantic role to a palette tone.

    Unknown palette tones are allowed to pass through. This keeps existing
    callers working and lets renderers still use raw tones where that is
    clearer.
    """
    name = str(name or default).strip()
    if not name:
        return default

    seen = set()
    current = name

    # Allow aliases to point to aliases, but guard against accidental cycles.
    for _ in range(8):
        if current in seen:
            return default
        seen.add(current)

        mapped = DEFAULT_THEME.get(current)
        if not mapped:
            return current
        current = str(mapped or default).strip() or default

    return current or default
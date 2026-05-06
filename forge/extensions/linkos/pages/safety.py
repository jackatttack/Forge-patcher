# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.safety
====================================

Public/minimal safety hub.
"""

from forge.extensions.linkos.data import branches as _branches
from forge.extensions.linkos.data import runs as _runs
from forge.extensions.linkos.render.docpage import (
    doc_footer, doc_hero, doc_section, doc_text, doc_tile_grid,
)
from forge.extensions.linkos.render.pills import pill_link
from forge.extensions.linkos.render.primitives import say, spacer


RECENT_BRANCH_COUNT = 5


def _render_branch_row(branch):
    name = branch.get('name', '')
    rel_time = _branches.relative_time(branch.get('mtime', 0))
    scope = _branches.scope_summary(name)

    print('   ', end='')
    pill_link(name, 'restore_branch', name, tone='warning', icon='📦 ')
    print('')

    bits = [x for x in (rel_time, scope) if x]
    if bits:
        say('       ' + ' · '.join(bits), 'muted')
    spacer()


def safety_page():
    """Render safety hub."""
    doc_hero('Safety', 'restore + revert')
    doc_text(
        'Recovery actions prepare Forge bundles on the clipboard. '
        'You still run them through the normal Forge loop.'
    )

    branches = _branches.list_branches(limit=200)
    doc_section('branches')
    if not branches:
        doc_text('No branches saved yet.', tone='muted')
    else:
        spacer()
        for branch in branches[:RECENT_BRANCH_COUNT]:
            _render_branch_row(branch)

    latest = _runs.latest_stamp()
    doc_tile_grid('revert', [
        ('⤺ ', 'Revert latest', latest or 'no runs yet',
         ('revert_run', latest) if latest else ('safety',), 'danger'),
        ('◎ ', 'Pick run', 'history', ('runs',), 'accent'),
    ])

    doc_text(
        'Revert is destructive: it restores files from the snapshot for one run.',
        tone='muted',
    )

    doc_tile_grid('docs', [
        ('🧯 ', 'Recovery tutorial', 'restore safely', ('doc', 'tutorial-recovery'), 'orange'),
        ('❌ ', 'Failure reading', 'bad packets', ('doc', 'tutorial-failure-reading'), 'danger'),
        ('🔒 ', 'Core edit', 'guard rails', ('doc', 'core-edit'), 'warning'),
    ])

    doc_footer()

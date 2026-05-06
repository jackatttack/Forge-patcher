# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.runs
==================================

Public/minimal run navigator.
"""

from forge.extensions.linkos.data import runs as _runs
from forge.extensions.linkos.render.docpage import (
    doc_footer, doc_hero, doc_run_card, doc_section, doc_text, doc_tile_grid,
)
from forge.extensions.linkos.render.pills import pill_link
from forge.extensions.linkos.render.primitives import colour, reset, say, spacer


RECENT_COUNT = 12


def _status_emoji_for(run):
    counts = run.get('counts') or {}
    if counts.get('failed', 0):
        return '❌'
    if counts.get('skipped', 0):
        return '⚠️'
    if counts.get('applied', 0):
        return '✅'
    return '•'


def _render_recent_row(stamp, active=False):
    run = _runs.load_run(stamp)
    emoji = _status_emoji_for(run)
    rel = _runs.relative_time(stamp)

    print(' ▸ ' if active else '   ', end='')
    print(emoji + '  ', end='')
    pill_link(stamp, 'run', stamp, tone='success' if active else 'accent')
    colour('muted')
    print('   ' + rel)
    reset()


def runs_page(stamp=None):
    """Render recent runs and navigation."""
    stamps = _runs.list_stamps(limit=500)

    if not stamps:
        doc_hero('Runs', 'navigator')
        doc_text('No Forge runs yet. Run a bundle and history will appear here.', tone='muted')
        doc_footer()
        return

    if not stamp or stamp == 'latest' or stamp not in stamps:
        active = stamps[0]
    else:
        active = stamp

    doc_hero('Runs', '%d run(s)' % len(stamps))
    doc_text('Viewing %s · %s' % (active, _runs.relative_time(active)), tone='muted')

    doc_section('active')
    doc_run_card(_runs.load_run(active), route=('run', active))

    doc_section('recent')
    spacer()
    for s in stamps[:RECENT_COUNT]:
        _render_recent_row(s, active=(s == active))

    if len(stamps) > RECENT_COUNT:
        say('   +%d more run(s)' % (len(stamps) - RECENT_COUNT), 'muted')

    doc_tile_grid('safety', [
        ('🛟 ', 'Safety', 'restore + revert', ('safety',), 'border'),
        ('⤺ ', 'Revert active', active, ('revert_run', active), 'danger'),
    ])

    doc_footer()

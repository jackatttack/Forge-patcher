# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.run
=================================

Public/minimal single-run page.
"""

from forge.extensions.linkos.data import runs as _runs
from forge.extensions.linkos.render.docpage import (
    doc_footer, doc_hero, doc_section, doc_text, doc_tile_grid,
)
from forge.extensions.linkos.render.pills import pill_link
from forge.extensions.linkos.render.primitives import colour, reset, say, spacer


def _tone_for_status(status):
    status = str(status or '').upper()
    if status.startswith('FAILED'):
        return 'danger'
    if status.startswith('SKIPPED'):
        return 'warning'
    if status == 'APPLIED':
        return 'success'
    return 'muted'


def _clean_target(value):
    text = str(value or '').strip()
    return '' if text in ('?', 'None', 'null') else text


def _render_op_row(result):
    status = result.get('status') or ''
    op = result.get('op') or '?'
    target = _clean_target(result.get('target')) or _clean_target(result.get('file')) or ''
    msg = str(result.get('message') or '').split('\n')[0]

    colour(_tone_for_status(status))
    print('   %s %s' % (result.get('status_emoji') or '•', op), end='')
    reset()

    if target:
        print('  ', end='')
        pill_link(target.rsplit('/', 1)[-1], 'files', target, tone='accent')

    print('  ', end='')
    pill_link('Help', 'help', str(op).upper(), tone='border')
    print('')

    if msg:
        say('      ' + msg, 'muted')


def _render_failures(run):
    failures = run.get('failed_results') or []
    skips = run.get('skipped_results') or []
    rows = failures + skips

    if not rows:
        return

    doc_section('attention')
    spacer()
    for r in rows[:6]:
        op = r.get('op') or '?'
        msg = str(r.get('message') or '').replace('\n', ' / ')
        say('   ❌ %s' % op, 'danger')
        if msg:
            say('      ' + msg[:180], 'text')
    spacer()


def run_page(stamp=None):
    """Render one run."""
    run = _runs.load_run(stamp if stamp and stamp != 'latest' else None)
    stamp = run.get('stamp') or '(no run)'
    counts = run.get('counts') or {}

    if run.get('missing'):
        doc_hero('Run', 'missing')
        doc_text('No run manifest found for %s.' % stamp, tone='muted')
        doc_footer()
        return

    failed = counts.get('failed', 0)
    skipped = counts.get('skipped', 0)
    applied = counts.get('applied', 0)

    if failed:
        subtitle = 'needs attention'
    elif skipped:
        subtitle = 'partial'
    elif applied:
        subtitle = 'clean'
    else:
        subtitle = 'empty'

    doc_hero('Run', subtitle)
    doc_text('%s · %s applied · %s skipped · %s failed' % (
        stamp, applied, skipped, failed
    ), tone='muted')

    doc_tile_grid('actions', [
        ('📋 ', 'Copy packet', 'full truth', ('copy_packet', stamp), 'warning'),
        ('🧠 ', 'Copy summary', 'AI handoff', ('copy_summary', stamp), 'success'),
        ('❌ ', 'Failure detail', 'if failed', ('copy_failure_detail', stamp), 'danger'),
        ('⤺ ', 'Revert run', 'copy bundle', ('revert_run', stamp), 'danger'),
        ('◎ ', 'All runs', 'history', ('runs', stamp), 'accent'),
        ('🛟 ', 'Safety', 'recovery', ('safety',), 'border'),
    ])

    _render_failures(run)

    doc_section('ops')
    spacer()
    for r in run.get('results') or []:
        _render_op_row(r)

    doc_footer()

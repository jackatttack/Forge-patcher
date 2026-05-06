# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.run
=================================

Public/minimal run-packet view.

This page intentionally renders bottom-up for Pythonista's console. The
last printed content is what the user lands on, so the final run summary
is printed after details/actions and just before the footer rail.

No forge_ui dependency: this uses the self-contained minimal run reader in
forge.extensions.linkos.data.runs.
"""

from forge.extensions.linkos.data import runs as _runs
from forge.extensions.linkos.render.docpage import (
    doc_section, doc_text, doc_tile_grid,
)
from forge.extensions.linkos.render.footer import footer
from forge.extensions.linkos.render.pills import pill_link
from forge.extensions.linkos.render.primitives import (
    colour, reset, say, section_label, spacer, thin_rule,
)


# -- small render helpers ----------------------------------------------------

def _split_target(target):
    """Split ``file.py::scope`` into ``(file, scope)``."""
    target = str(target or '')
    if '::' in target:
        file_part, _, scope_part = target.partition('::')
        return file_part, scope_part
    return target, ''


def _clean_target(value):
    """Return a display-safe target string."""
    text = str(value or '').strip()
    return '' if text in ('?', 'None', 'null') else text


def _compact_message(result):
    """Return the useful first-line result detail."""
    msg = str(result.get('message') or '').strip()
    if not msg:
        return ''

    op = str(result.get('op') or '').upper()
    low = msg.lower()
    line = msg.split('\n')[0]

    if op == 'LIST_FILES' and (' entries' in low or low.endswith(' entry')):
        return line
    if op == 'GREP' and ' hits' in low:
        return line
    if op in ('PREVIEW', 'READ_FILE', 'LIST_TARGETS'):
        return line
    if op in ('RUN_FILE', 'URL', 'PIP') and 'exit ' in low:
        return line

    return line


def _is_empty_search(result):
    """Return True when an applied GREP produced no matches."""
    op = str(result.get('op') or '').upper()
    msg = str(result.get('message') or '').lower()
    return op == 'GREP' and ('0 hits' in msg or '(no hits)' in msg)


def _op_tone(result):
    """Return display tone for one op row."""
    status = str(result.get('status') or '').upper()
    if 'FAIL' in status:
        return 'danger'
    if 'SKIP' in status:
        return 'warning'
    if _is_empty_search(result):
        return 'muted'
    return 'success'


def _detail_tone(result):
    """Return display tone for the result detail line."""
    status = str(result.get('status') or '').upper()
    if 'FAIL' in status:
        return 'danger'
    if 'SKIP' in status:
        return 'warning'
    return 'muted'


def _display_emoji(result):
    """Return row emoji, with neutral treatment for empty successful searches."""
    if _is_empty_search(result):
        return '○'
    return result.get('status_emoji') or '•'


def _render_op_row(result):
    """Render one compact two-line op row."""
    op = result.get('op') or '?'
    raw_target = _clean_target(result.get('target'))
    file_part, scope_part = _split_target(raw_target)
    file_text = file_part or _clean_target(result.get('file')) or ''
    detail = _compact_message(result)

    colour(_op_tone(result))
    print('   %s %s' % (_display_emoji(result), op), end='')
    reset()

    print('  ', end='')
    if file_text:
        pill_link(file_text.rsplit('/', 1)[-1], 'files', file_text, tone='accent')
    else:
        colour('muted')
        print('(no file)', end='')
        reset()

    print('  ', end='')
    pill_link('Help', 'help', str(op).upper(), tone='border')
    print('')

    if detail:
        colour(_detail_tone(result))
        print('      ' + detail, end='')
        reset()
    else:
        colour('muted')
        print('      No detail', end='')
        reset()

    if scope_part:
        colour('muted')
        print('  ·  ', end='')
        reset()
        colour('cyan')
        print(scope_part, end='')
        reset()

    print('')
    say('      ' + '─' * 34, 'surface_2')


def _doc_slug_for_failure(result):
    """Return a likely help doc slug for a failed/skipped result."""
    status = str(result.get('status') or '').upper()
    msg = str(result.get('message') or '').lower()
    op = str(result.get('op') or '').upper()

    if op == 'PARSE' or 'FAILED_PARSE' in status:
        return 'parse-errors'
    if 'anchor' in msg and ('matched' in msg or 'mismatch' in status.lower()):
        return 'anchor-disambiguation'
    if 'file not found' in msg:
        return 'file-not-found'
    if 'invalid directive' in msg or 'directive not allowed' in msg:
        return 'directives'
    return ''


def _render_attention(run):
    """Render failures and skips close to the action section."""
    rows = (run.get('failed_results') or []) + (run.get('skipped_results') or [])
    if not rows:
        return

    section_label('ATTENTION', icon='❌', tone='danger')
    spacer()

    for result in rows[:6]:
        op = result.get('op') or '?'
        target = _clean_target(result.get('target')) or _clean_target(result.get('file'))
        msg = str(result.get('message') or '').replace('\n', ' / ')

        colour('danger')
        print('   ❌ %s' % op, end='')
        reset()

        if target:
            print('  ', end='')
            pill_link(target.rsplit('/', 1)[-1], 'files', target, tone='accent')

        print('  ', end='')
        pill_link('Help', 'help', str(op).upper(), tone='border')
        print('')

        if msg:
            say('      ' + msg[:220], 'text')

        slug = _doc_slug_for_failure(result)
        if slug:
            print('      ', end='')
            pill_link('Related doc', 'doc', slug, tone='warning')
            print('')

    spacer()


def _render_actions(stamp):
    """Render the run action grid."""
    doc_tile_grid('actions', [
        ('📋 ', 'Copy packet', 'full truth', ('copy_packet', stamp), 'warning'),
        ('🧠 ', 'Copy summary', 'AI handoff', ('copy_summary', stamp), 'success'),
        ('❌ ', 'Failure detail', 'if failed', ('copy_failure_detail', stamp), 'danger'),
        ('⤺ ', 'Revert run', 'copy bundle', ('revert_run', stamp), 'danger'),
        ('◎ ', 'All runs', 'history', ('runs', stamp), 'accent'),
        ('🛟 ', 'Safety', 'recovery', ('safety',), 'border'),
    ])


def _render_summary(run):
    """Render the final bottom landing summary."""
    stamp = run.get('stamp') or '(no run)'
    counts = run.get('counts') or {}

    applied = counts.get('applied', 0)
    skipped = counts.get('skipped', 0)
    failed = counts.get('failed', 0)

    if failed:
        title = 'RUN FAILED'
        tone = 'danger'
        ready = 'Needs attention.'
    elif skipped:
        title = 'RUN PARTIAL'
        tone = 'warning'
        ready = 'Check skipped ops.'
    elif applied:
        title = 'RUN CLEAN'
        tone = 'success'
        ready = 'Ready.'
    else:
        title = 'RUN EMPTY'
        tone = 'muted'
        ready = 'No ops recorded.'

    spacer()
    thin_rule(46, 'border')
    spacer()

    colour(tone)
    print((' ' * 9) + ' '.join(title))
    reset()

    spacer()
    colour('muted')
    print((' ' * 10) + stamp)
    reset()

    spacer()
    thin_rule(46, 'border')
    spacer()

    def centered_count(emoji, count, label, count_tone):
        text = '%s  %s %s' % (emoji, count, label)
        pad = max(0, (41 - len(text)) // 2)
        colour(count_tone)
        print((' ' * pad) + text)
        reset()

    centered_count('✅', applied, 'applied', 'success')
    centered_count('⚠️', skipped, 'skipped', 'warning')
    centered_count('❌', failed, 'failed', 'danger')

    packet = ''
    try:
        packet = _runs.full_packet(run) or ''
    except Exception:
        packet = ''

    spacer()
    colour('muted')
    print((' ' * 11) + 'packet: %s chars' % len(packet))
    reset()

    spacer()
    colour(tone)
    print((' ' * 16) + ready)
    reset()

    spacer()
    thin_rule(46, 'border')


# -- page --------------------------------------------------------------------

def run_page(stamp=None):
    """Render one run."""
    run = _runs.load_run(stamp if stamp and stamp != 'latest' else None)
    stamp = run.get('stamp') or '(no run)'

    if run.get('missing'):
        spacer()
        thin_rule(46, 'border')
        spacer()
        colour('warning')
        print((' ' * 14) + 'RUN MISSING')
        reset()
        spacer()
        doc_text('No run manifest found for %s.' % stamp, tone='muted')
        footer()
        return

    # Print order is intentional: details first, summary last, footer final.
    doc_section('ops')
    spacer()
    for result in run.get('results') or []:
        _render_op_row(result)

    _render_attention(run)
    _render_actions(stamp)
    _render_summary(run)
    footer()

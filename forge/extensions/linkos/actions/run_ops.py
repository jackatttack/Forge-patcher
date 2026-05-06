# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.run_ops
=======================================

Public/minimal run clipboard actions.
"""

try:
    import clipboard as _clipboard
except Exception:
    _clipboard = None

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.data import runs as _runs
from forge.extensions.linkos.render.cards import panel
from forge.extensions.linkos.render.footer import footer
from forge.extensions.linkos.render.hero import big_section, hero
from forge.extensions.linkos.render.pills import pill_rows
from forge.extensions.linkos.render.primitives import small_note, spacer


def _set_clipboard(text):
    if _clipboard is None:
        return False
    try:
        _clipboard.set(text or '')
        if _console:
            try:
                _console.hud_alert('Copied', 'success', 0.8)
            except Exception:
                pass
        return True
    except Exception:
        return False


def _post_action_pills(stamp):
    pill_rows([
        ('RUN', ('run', stamp), 'success', '◎'),
        ('RUNS', ('runs', stamp), 'accent', '◎'),
        ('HOME', ('home',), 'success', '🏠'),
    ], cols=2)


def _failure_detail_text(run):
    stamp = run.get('stamp') or '(unknown run)'
    rows = (run.get('failed_results') or []) + (run.get('skipped_results') or [])

    lines = ['Forge run %s — needs attention.' % stamp, '']
    if not rows:
        lines.append('No failures or skipped ops.')
    else:
        for r in rows:
            lines.append('- %s %s' % (r.get('op') or '', r.get('target') or ''))
            msg = (r.get('message') or '').replace('\n', '\n  ')
            if msg:
                lines.append('  ' + msg)
    lines.append('')
    lines.append("What's the fix?")
    return '\n'.join(lines)


def copy_packet(stamp):
    run = _runs.load_run(stamp)
    text = _runs.full_packet(run) or ''
    ok = _set_clipboard(text)

    hero('Copied packet', '📋', stamp)
    panel('Clipboard', [
        'Full packet copied.' if ok else 'Clipboard unavailable.',
        '%d characters' % len(text),
    ], icon='📋', tone='warning')

    if not ok and text:
        spacer()
        for line in text.split('\n')[:20]:
            small_note(line, icon=' ', tone='muted')

    big_section('Next', '→', 'accent')
    _post_action_pills(stamp)
    footer()


def copy_summary(stamp):
    run = _runs.load_run(stamp)
    text = _runs.ai_summary(run)
    ok = _set_clipboard(text)

    hero('Copied summary', '🧠', stamp)
    panel('Clipboard', [
        'AI summary copied.' if ok else 'Clipboard unavailable.',
        '%d characters' % len(text),
    ], icon='🧠', tone='success')

    if not ok and text:
        spacer()
        for line in text.split('\n')[:20]:
            small_note(line, icon=' ', tone='muted')

    big_section('Next', '→', 'accent')
    _post_action_pills(stamp)
    footer()


def copy_failure_detail(stamp):
    run = _runs.load_run(stamp)
    text = _failure_detail_text(run)
    ok = _set_clipboard(text)

    hero('Copied failure detail', '❌', stamp)
    panel('Clipboard', [
        'Failure detail copied.' if ok else 'Clipboard unavailable.',
        '%d characters' % len(text),
    ], icon='❌', tone='danger')

    if not ok and text:
        spacer()
        for line in text.split('\n')[:30]:
            small_note(line, icon=' ', tone='muted')

    big_section('Next', '→', 'accent')
    _post_action_pills(stamp)
    footer()


def print_packet(stamp):
    run = _runs.load_run(stamp)
    text = _runs.full_packet(run) or ''

    hero('Packet', '🖨', stamp)
    if text:
        for line in text.split('\n')[:120]:
            small_note(line, icon=' ', tone='muted')
    else:
        panel('Packet', ['No packet available.'], icon='🖨', tone='muted')

    big_section('Next', '→', 'accent')
    _post_action_pills(stamp)
    footer()

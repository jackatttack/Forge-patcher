# -*- coding: utf-8 -*-
"""
run_packet.py
=============
Simple run-packet formatter for parser-lab engine.
"""

def format_run_packet(results, stamp=None, step=None, max_steps=None, normalise_notes=None):
    """Format engine context into a human-readable run packet string."""
    normalise_notes = normalise_notes or []

    # filter out silent results for packet display
    visible = [r for r in results if not r.get('silent')]

    # if all ops were silent and all applied, return empty string unless normalisation should be reported
    if not visible and not normalise_notes:
        all_applied = all(r.get('status') == 'APPLIED' for r in results)
        if all_applied:
            return ''

    applied = sum(1 for r in results if r.get('status') == 'APPLIED')
    failed  = sum(1 for r in results if (r.get('status') or '').startswith('FAILED'))
    skipped = len(results) - applied - failed

    lines = ['=== FORGE RUN ===']
    if stamp:
        lines.append('Run: ' + stamp)
    if step is not None and max_steps is not None:
        lines.append('Step: %d/%d' % (step, max_steps))

    if normalise_notes:
        lines += ['', 'Normalized:']
        for note in normalise_notes:
            lines.append('- ' + str(note))

    lines += ['', 'Ops:']

    for r in visible:
        line = '- %s | %s | %s' % (
            r.get('status') or 'UNKNOWN',
            r.get('op') or '?',
            r.get('target') or '?',
        )
        msg = r.get('message') or ''
        if msg:
            line += ' :: ' + msg
        lines.append(line)

    lines += ['', 'APPLIED=%d  SKIPPED=%d  FAILED=%d' % (applied, skipped, failed)]

    preview_blocks = []
    for r in visible:
        if r.get('preview'):
            preview_blocks.append(r.get('preview'))
            continue

        out_obj = r.get('out') or {}
        stdout_text = ''
        if isinstance(out_obj, dict):
            stdout_text = out_obj.get('stdout') or ''
        if not stdout_text:
            stdout_text = r.get('stdout') or ''

        if stdout_text:
            preview_blocks.append(stdout_text)

    if preview_blocks:
        lines.append('')
        lines.append('=== PREVIEW ===')
        for block in preview_blocks:
            lines.append(str(block).rstrip())

    return '\n'.join(lines).rstrip() + '\n'

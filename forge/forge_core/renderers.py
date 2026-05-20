# -*- coding: utf-8 -*-
"""
Renderers for the Forge.

Important split:
- packet: LLM-facing truth
- surface_text: user-facing LinkOS-style run landing

During the LinkOS runtime migration, ``build_pages`` remains the legacy page
builder for stored run metadata, but ``format_surface`` now captures the new
page-stack runtime so the shortcut clipboard return lands on the same surface
architecture as live LinkOS.
"""

import contextlib
import importlib
import io
import sys

from forge_core.surface.pages import build_pages


def _packet_line_count(text):
    return len((text or '').splitlines())


def _packet_changed_ranges(before, after):
    before_lines = (before or '').splitlines()
    after_lines = (after or '').splitlines()
    max_len = max(len(before_lines), len(after_lines))
    nums = []

    for i in range(max_len):
        b = before_lines[i] if i < len(before_lines) else None
        a = after_lines[i] if i < len(after_lines) else None
        if b != a:
            nums.append(i + 1)

    if not nums:
        return 'none'

    ranges = []
    start = nums[0]
    prev = nums[0]

    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        ranges.append((start, prev))
        start = prev = n

    ranges.append((start, prev))

    parts = []
    for a, b in ranges:
        if a == b:
            parts.append(str(a))
        else:
            parts.append('%d-%d' % (a, b))

    return ', '.join(parts)


def _packet_collect_touched(run):
    touched = []

    for item in (run or {}).get('touched_files') or []:
        if isinstance(item, dict):
            touched.append(dict(item))

    for res in (run or {}).get('results') or []:
        for item in res.get('touched') or []:
            if isinstance(item, dict):
                touched.append(dict(item))

    by_rel = {}
    order = []

    for item in touched:
        rel = str(item.get('rel') or item.get('file') or '').strip()
        if not rel:
            continue

        before = item.get('before') if item.get('before') is not None else ''
        after = item.get('after') if item.get('after') is not None else ''

        if rel not in by_rel:
            order.append(rel)
            by_rel[rel] = {
                'rel': rel,
                'kind': item.get('kind') or 'file',
                'existed_before': bool(item.get('existed_before')),
                'before': before,
                'after': after,
            }
        else:
            by_rel[rel]['after'] = after
            if item.get('kind'):
                by_rel[rel]['kind'] = item.get('kind')

    return [by_rel[rel] for rel in order]


def _format_changed_files(run):
    touched = _packet_collect_touched(run)
    if not touched:
        return []

    lines = []
    lines.append('')
    lines.append('Changed files:')

    for item in touched:
        rel = item.get('rel') or '?'
        existed_before = bool(item.get('existed_before'))
        before = item.get('before') or ''
        after = item.get('after') or ''

        if not existed_before:
            summary = 'created · %d lines' % _packet_line_count(after)
        elif before == after:
            summary = 'touched · %d lines · no content change' % _packet_line_count(after)
        else:
            summary = (
                'modified · %d -> %d lines · changed: %s'
                % (
                    _packet_line_count(before),
                    _packet_line_count(after),
                    _packet_changed_ranges(before, after),
                )
            )

        lines.append('- %s — %s' % (rel, summary))

    return lines


def format_packet(run):
    lines = []
    lines.append('=== FORGE RUN ===')
    if run.get('stamp'):
        lines.append('Run: ' + str(run.get('stamp')))
    lines.append('Mode: ' + str(run.get('mode') or 'dev'))
    lines.append('Status: ' + str(run.get('status') or 'UNKNOWN'))

    errors = run.get('errors') or []
    if errors:
        lines.append('')
        lines.append('Errors:')
        for err in errors:
            lines.append('- ' + str(err))

    lines.append('')
    lines.append('Ops:')

    results = run.get('results') or []
    if not results:
        lines.append('- none')
    else:
        for r in results:
            line = '- %s | %s | %s' % (
                r.get('status') or 'UNKNOWN',
                r.get('op') or '?',
                r.get('target') or '?',
            )
            if r.get('message'):
                line += ' :: ' + str(r.get('message'))
            lines.append(line)

    changed = _format_changed_files(run)
    if changed:
        lines.extend(changed)

    hinted = [r for r in results if r.get('hint')]
    if hinted:
        lines.append('')
        lines.append('=== HINTS ===')
        for r in hinted:
            lines.append('%s %s' % (r.get('op') or '?', r.get('target') or '?'))
            lines.append(str(r.get('hint')).rstrip())

    previews = [r for r in results if r.get('preview')]
    if previews:
        lines.append('')
        lines.append('=== PREVIEW ===')
        for r in previews:
            lines.append(str(r.get('preview')).rstrip())

    return '\n'.join(lines).rstrip() + '\n'


def _clear_render_cache():
    """Clear stale Pythonista imports from surface renderer/runtime edits.

    Pythonista keeps imported modules alive aggressively. During the reboot
    surface migration, render shape can change in render/, core_pages,
    page_runtime, page_model, and page_stack. Clear the surface layer before
    capturing ``surface_text`` so clipboard output reflects the latest files.
    """
    prefixes = (
        'forge_core.surface.render',
        'forge_core.surface.core_pages',
        'forge_core.surface.page_runtime',
        'forge_core.surface.page_model',
        'forge_core.surface.page_stack',
        'forge_core.surface.render_context',
        'forge_core.surface.control_model',
    )

    for name in list(sys.modules):
        if any(name == prefix or name.startswith(prefix + '.') for prefix in prefixes):
            del sys.modules[name]

    importlib.invalidate_caches()

def format_surface(run):
    """Return captured LinkOS-style surface text for the clipboard return.

    The useful landing/control dock should be the final thing printed, because
    Pythonista lands near the bottom of console output after a run.
    """
    run = run or {}

    try:
        _clear_render_cache()

        from forge_core.surface.page_stack import build_run_page_stack
        from forge_core.surface.page_runtime import render_landing

        stack = build_run_page_stack(run, registry={})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            render_landing(stack)

        text = buf.getvalue().rstrip()
        if text:
            return text + '\n'
    except Exception as e:
        try:
            from forge_core.surface.legacy_render import format_surface as legacy_format_surface
            legacy = legacy_format_surface(run)
            return (
                '[LinkOS runtime surface failed: %s]\n\n%s'
                % (e, legacy or '')
            ).rstrip() + '\n'
        except Exception as e2:
            return (
                '[LinkOS runtime surface failed: %s]\n'
                '[legacy surface failed: %s]\n'
                % (e, e2)
            )

    return ''

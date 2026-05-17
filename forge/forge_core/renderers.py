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

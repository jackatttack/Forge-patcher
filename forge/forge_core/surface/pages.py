# -*- coding: utf-8 -*-
"""
Build Surface V2 page objects from a Forge run.

Core owns the standard page stack and generic fallback pages.

Op-specific surface knowledge should live beside the op package, e.g.

    forge_packages/core_ops/run_file/pages.py

That keeps op data shape, help, hints, execution, and Surface pages together.
"""

import importlib.util
import os

from forge_core.surface.controls import run_copy_panel, run_nav_panel
from forge_core.surface.model import page


def _op_text(result):
    return str((result or {}).get('op') or '').upper()


def _package_name_for_op(op):
    return str(op or '').strip().lower()


def _has_preview(result):
    return bool(str((result or {}).get('preview') or '').strip())


def _list_files_pages(run):
    # LIST_FILES is now an op-owned surface. Its pages come from
    # forge_packages/core_ops/list_files/pages.py via the provider
    # dispatch in _provider_pages. This stub is kept to preserve the
    # build_pages call site; remove once that call site is cleaned up.
    return []

def _provider_path(run, op):
    from forge_core.surface.providers import provider_path
    return provider_path(run, op)

def _load_provider(run, op):
    from forge_core.surface.providers import load_provider
    return load_provider(run, op)

def _fallback_result_page(result, index):
    op = _op_text(result)
    if not _has_preview(result):
        return []

    kind = 'result'
    icon = '▣'
    title = op or 'Result'
    short = title[:12]
    tone = 'muted'

    if op == 'PREVIEW':
        kind, icon, title, short, tone = 'preview', '👁', 'Preview', 'Preview', 'accent'
    elif op == 'HELP':
        kind, icon, title, short, tone = 'help', '📖', 'Help', 'Help', 'warning'
    elif op == 'DIFF':
        kind, icon, title, short, tone = 'diff', '△', 'Diff', 'Diff', 'warning'
    elif op == 'AUDIT':
        kind, icon, title, short, tone = 'audit', '✓', 'Audit', 'Audit', 'success'

    return [page(
        '%s.%%N' % kind,
        title,
        kind=kind,
        icon=icon,
        short=short,
        tone=tone,
        mode='dense',
        size='compact',
        source='fallback:%s' % op,
        priority=50,
        data={
            'result': result,
            'result_index': index,
            'preview': result.get('preview') or '',
        },
    )]

def _provider_pages(run):
    out = []
    counters = {}

    for index, result in enumerate(run.get('results') or []):
        op = _op_text(result)
        if not op:
            continue

        provider = _load_provider(run, op)
        made = []

        if provider is not None:
            fn = getattr(provider, 'pages_for_result', None)
            if callable(fn):
                try:
                    made = fn(result, index, run) or []
                except Exception as e:
                    made = [page(
                        'surface.provider_error.%d' % index,
                        'Surface Provider Error',
                        kind='errors',
                        icon='!',
                        short='Provider',
                        tone='danger',
                        mode='dense',
                        size='compact',
                        source='provider:%s' % op,
                        data={
                            'result': result,
                            'result_index': index,
                            'error': '%s: %s' % (type(e).__name__, e),
                        },
                    )]

        if not made:
            made = _fallback_result_page(result, index)

        for p in made:
            pid = p.get('id') or ''
            if '%N' in pid:
                key = pid.split('%N')[0]
                n = counters.get(key, 0)
                counters[key] = n + 1
                p['id'] = pid.replace('%N', str(n))
            out.append(p)

    return out


def _stack_items(surface):
    stack = surface.get('stack') or ['summary', 'ops', 'files', 'results', 'raw']
    if isinstance(stack, str):
        stack = [s.strip() for s in stack.split(',') if s.strip()]
    return list(stack or [])


def _add_requested_pages(ordered, pages, requested, seen):
    for wanted in requested:
        for p in pages:
            pid = p.get('id')
            if pid == wanted and pid not in seen:
                ordered.append(p)
                seen.add(pid)


def build_pages(run):
    surface = run.get('surface') or {}
    title = surface.get('title') or 'Forge Run'
    hero = surface.get('hero') or 'compact'
    stamp = run.get('stamp') or 'latest'

    standard_pages = [
        page(
            'run.summary',
            title,
            kind='summary',
            icon='◆',
            short='Summary',
            tone='accent',
            mode=hero,
            size='full',
            priority=100,
            controls=[
                run_copy_panel(stamp),
                run_nav_panel(stamp),
            ],
        ),
        page(
            'run.ops',
            'Ops',
            kind='ops',
            icon='≡',
            short='Ops',
            tone='muted',
            mode='dense',
            size='full',
            priority=80,
            controls=[
                run_nav_panel(stamp),
            ],
        ),
        page(
            'packet.raw',
            'Raw Packet',
            kind='raw',
            icon='¶',
            short='Raw',
            tone='warning',
            mode='dense',
            size='full',
            priority=10,
            controls=[
                run_nav_panel(stamp),
            ],
        ),
    ]

    file_pages = _list_files_pages(run)
    result_pages = _provider_pages(run)

    pages = list(standard_pages)
    pages.extend(file_pages)
    pages.extend(result_pages)

    if run.get('errors'):
        pages.insert(0, page(
            'run.errors',
            'Errors',
            kind='errors',
            icon='!',
            short='Errors',
            tone='danger',
            mode='dense',
            size='full',
            priority=120,
            controls=[
                run_copy_panel(stamp),
                run_nav_panel(stamp),
            ],
        ))

    aliases = {
        'summary': 'run.summary',
        'home': 'run.summary',
        'ops': 'run.ops',
        'op': 'run.ops',
        'audit': 'run.ops',
        'raw': 'packet.raw',
        'packet': 'packet.raw',
        'errors': 'run.errors',
        'issue': 'run.errors',
        'files': 'files.tree.0',
        'tree': 'files.tree.0',
        'preview': 'preview.0',
        'run_file': 'run_file.0',
        'run-output': 'run_file.0',
        'url': 'url.0',
        'help': 'help.0',
        'diff': 'diff.0',
        'results': '__RESULTS__',
    }

    requested = [aliases.get(item, item) for item in _stack_items(surface)]

    ordered = []
    seen = set()
    expanded_requested = []

    for item in requested:
        if item == '__RESULTS__':
            expanded_requested.extend([p.get('id') for p in result_pages])
        else:
            expanded_requested.append(item)

    _add_requested_pages(ordered, pages, expanded_requested, seen)

    remaining = [
        p for p in pages
        if p.get('id') not in seen
    ]
    remaining = sorted(
        remaining,
        key=lambda p: int((p or {}).get('priority') or 0),
        reverse=True,
    )

    ordered.extend(remaining)

    return ordered

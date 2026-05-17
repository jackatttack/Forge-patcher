# -*- coding: utf-8 -*-
"""
Build LinkOS-style page stacks from Forge run packets.
"""

from forge_core.surface.page_model import (
    core_run_pages,
    describe_pages as _describe_pages,
    ensure_page_card,
    landing_page,
    sort_pages,
)


def _provider_pages(provider, run, registry=None):
    try:
        if callable(provider):
            try:
                pages = provider(run, registry)
            except TypeError:
                pages = provider(run)
        elif isinstance(provider, dict):
            fn = provider.get('build') or provider.get('provide')
            if not callable(fn):
                return [], 'provider is not callable'
            try:
                pages = fn(run, registry)
            except TypeError:
                pages = fn(run)
        else:
            return [], 'provider is not callable'
    except Exception as e:
        return [], str(e)

    if not pages:
        return [], None
    if isinstance(pages, dict):
        pages = [pages]
    return list(pages), None


def _attach_cards(pages, stamp):
    out = []
    for p in pages or []:
        if not isinstance(p, dict):
            continue
        p = dict(p)
        p['card'] = ensure_page_card(p, stamp=stamp)
        out.append(p)
    return out


def build_run_page_stack(run, registry=None):
    run = run or {}
    stamp = run.get('stamp') or 'latest'
    registry = registry or {}

    pages = []
    warnings = []

    pages.extend(core_run_pages(run))

    for entry in registry.get('run_page_providers') or []:
        provider_pages, warning = _provider_pages(entry, run, registry)
        if warning:
            source = entry.get('id') if isinstance(entry, dict) else 'provider'
            warnings.append('%s: %s' % (source, warning))
        pages.extend(provider_pages)

    pages = _attach_cards(sort_pages(pages), stamp)
    landing = landing_page(pages)

    return {
        'run': run,
        'stamp': stamp,
        'pages': pages,
        'landing': landing,
        'warnings': warnings + list(registry.get('warnings') or []),
        'registry': registry,
    }


def describe_stack(stack):
    stack = stack or {}
    lines = []
    lines.append('PAGES')
    lines.extend(_describe_pages(stack.get('pages') or []))

    lines.append('')
    lines.append('LANDING')
    landing = stack.get('landing')
    if landing:
        lines.append('%s | %s | mode=%s | size=%s' % (
            landing.get('id') or '?',
            landing.get('title') or '?',
            landing.get('mode') or '?',
            landing.get('size') or '?',
        ))
    else:
        lines.append('(none)')

    warnings = stack.get('warnings') or []
    if warnings:
        lines.append('')
        lines.append('WARNINGS')
        for w in warnings:
            lines.append('- ' + str(w))

    return lines

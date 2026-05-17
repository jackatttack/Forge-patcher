# -*- coding: utf-8 -*-
"""
forge_core.surface.surface_plan
===============================

Pure planning layer for SURFACE-controlled run presentation.

This module does not render. It turns:

    run['surface'] + page stack

into a plain dict describing:

- requested page ids
- inline pages
- navigation pages
- focus page
- missing-page warnings
- whether the run is in controlled stack mode

Keep this dependency-light and safe to import from tests, probes, and renderers.
"""

INLINE_EXCLUDED_IDS = frozenset({'packet.raw'})


CORE_ALIASES = {
    'summary': 'run.home',
    'home': 'run.home',
    'run.summary': 'run.home',
    'run': 'run.home',

    'audit': 'run.audit',
    'ops': 'op.list',
    'op': 'op.list',
    'commands': 'op.list',

    'docs': 'run.docs',
    'raw': 'packet.raw',
    'packet': 'packet.raw',
    'source': 'packet.raw',

    'files': 'files.tree.0',
    'tree': 'files.tree.0',

    'help': 'help.0',
    'preview': 'preview.0',
    'diff': 'diff.0',
}


def _text(value):
    return str(value or '').strip()


def _lower(value):
    return _text(value).lower()


def page_id(page):
    return _text((page or {}).get('id'))


def page_kind(page):
    return _text((page or {}).get('kind'))


def page_source(page):
    return _text((page or {}).get('source'))


def page_status(page):
    data = (page or {}).get('data') or {}
    result = data.get('result') or {}
    return _text(result.get('status')).upper()


def is_detail_page(page):
    return page_id(page).startswith('op.detail.')


def is_result_page(page):
    pid = page_id(page)
    if is_detail_page(page):
        return False
    source = page_source(page)
    if source and source != 'reboot':
        return True
    kind = page_kind(page)
    return kind in ('result', 'preview', 'help', 'diff', 'audit')


def is_preview_page(page):
    kind = page_kind(page)
    pid = page_id(page)
    return kind == 'preview' or pid.startswith('preview.')


def is_failure_detail_page(page):
    if not is_detail_page(page):
        return False
    status = page_status(page)
    return ('FAIL' in status) or ('SKIP' in status)


def is_read_like_detail_page(page):
    if not is_detail_page(page):
        return False
    data = (page or {}).get('data') or {}
    result = data.get('result') or {}
    op = _text(result.get('op')).upper()
    return op in ('READ', 'SEARCH', 'LIST_FILES', 'LIST_OPS', 'LIST_TARGETS', 'PREVIEW', 'HELP')


def is_write_like_detail_page(page):
    if not is_detail_page(page):
        return False
    data = (page or {}).get('data') or {}
    result = data.get('result') or {}
    op = _text(result.get('op')).upper()
    return op in ('CREATE_FILE', 'REPLACE_FILE', 'REPLACE', 'INSERT', 'DELETE', 'MOVE', 'COPY')


def page_map(pages):
    out = {}
    for p in pages or []:
        pid = page_id(p)
        if pid and pid not in out:
            out[pid] = p
    return out


def alias_page_id(value):
    raw = _text(value)
    lower = raw.lower()

    if lower.startswith('detail.'):
        suffix = lower.split('.', 1)[1]
        if suffix.isdigit():
            return 'op.detail.' + suffix

    if lower.startswith('op.') and lower[3:].isdigit():
        return 'op.detail.' + lower[3:]

    return CORE_ALIASES.get(lower, raw)


def parse_stack_tokens(raw):
    if raw is None or raw == '':
        return []

    if isinstance(raw, str):
        return [x.strip() for x in raw.replace(',', ' ').split() if x.strip()]

    out = []
    for item in raw or []:
        text = _text(item)
        if text:
            out.append(text)
    return out


def _ids_for_pages(pages):
    return [page_id(p) for p in pages or [] if page_id(p)]


ALIAS_TO_OP = {
    'help': 'HELP',
    'preview': 'PREVIEW',
    'diff': 'DIFF',
}


def _detail_op_name(page):
    data = (page or {}).get('data') or {}
    result = data.get('result') or {}
    return _text(result.get('op')).upper()


def _rich_detail_for_alias(lower, pages):
    op_name = ALIAS_TO_OP.get(lower)
    if not op_name:
        return ''
    for p in pages or []:
        if is_detail_page(p) and _detail_op_name(p) == op_name:
            return page_id(p)
    return ''

def expand_token(token, pages):
    lower = _lower(token)

    if lower in ('details', 'detail'):
        return _ids_for_pages([p for p in pages if is_detail_page(p)])

    if lower in ('results', 'result'):
        return _ids_for_pages([p for p in pages if is_result_page(p)])

    if lower in ('failures', 'failure', 'failed', 'issues', 'issue'):
        return _ids_for_pages([p for p in pages if is_failure_detail_page(p)])

    if lower in ('previews', 'preview-pages'):
        return _ids_for_pages([p for p in pages if is_preview_page(p)])

    if lower in ('reads', 'readers', 'inspection'):
        return _ids_for_pages([p for p in pages if is_read_like_detail_page(p)])

    if lower in ('writes', 'mutations', 'edits', 'patches'):
        return _ids_for_pages([p for p in pages if is_write_like_detail_page(p)])

    rich = _rich_detail_for_alias(lower, pages)
    if rich:
        return [rich]

    return [alias_page_id(token)]


def resolve_stack(raw_stack, pages):
    tokens = parse_stack_tokens(raw_stack)
    resolved = []
    seen = set()

    for token in tokens:
        for pid in expand_token(token, pages):
            pid = alias_page_id(pid)
            if pid and pid not in seen:
                resolved.append(pid)
                seen.add(pid)

    return resolved


def _default_nav_pages(pages):
    wanted = ['op.list', 'run.audit', 'run.docs', 'packet.raw']
    by_id = page_map(pages)
    out = []

    for pid in wanted:
        p = by_id.get(pid)
        if p:
            out.append(p)

    for p in pages or []:
        pid = page_id(p)
        if not pid:
            continue
        if p in out:
            continue
        if p.get('promote') is False:
            continue
        if pid == 'run.home':
            continue
        out.append(p)

    return out


def _default_inline_pages(pages):
    by_id = page_map(pages)
    audit = by_id.get('run.audit')
    return [audit] if audit else []


def _inline_from_selected(selected):
    out = []
    for p in selected or []:
        if page_id(p) in INLINE_EXCLUDED_IDS:
            continue
        out.append(p)
    return out


def _selected_pages(ids, pages):
    by_id = page_map(pages)
    selected = []
    missing = []

    for pid in ids or []:
        p = by_id.get(pid)
        if p:
            selected.append(p)
        else:
            missing.append(pid)

    return selected, missing


def plan_surface(run, pages):
    """Return a plain-dict surface plan.

    This is intentionally pure. It should not print, mutate run, mutate pages,
    or import render modules.

    Surface model:
    - STACK chooses content pages rendered inline.
    - FOCUS chooses one content page rendered first.
    - run.home / summary is just another selectable content page.
    - audit is just another selectable content page.
    - controls/navigation remain available by default.
    """
    run = run or {}
    pages = list(pages or [])
    surface = run.get('surface') or {}

    requested_ids = resolve_stack(surface.get('stack'), pages)

    focus_raw = surface.get('focus') or ''
    focus_id = alias_page_id(focus_raw) if focus_raw else ''
    focus_page = page_map(pages).get(focus_id) if focus_id else None

    controlled = bool(requested_ids or focus_id)

    selected, missing = _selected_pages(requested_ids, pages)

    if focus_id and not focus_page and focus_id not in missing:
        missing.append(focus_id)

    # Content is selected by STACK/FOCUS. Navigation controls stay useful by
    # default, so a focused help/detail page can still expose Ops/Audit/Raw/Home
    # without forcing audit or summary to render inline.
    if controlled:
        nav_pages = _default_nav_pages(pages)
        inline_pages = _inline_from_selected(selected)
    else:
        nav_pages = _default_nav_pages(pages)
        inline_pages = _default_inline_pages(pages)

    return {
        'controlled': controlled,
        'title': _text(surface.get('title')),
        'mode': _text(surface.get('mode') or 'default'),
        'hero': _text(surface.get('hero') or 'compact'),
        'focus_id': focus_id,
        'focus_page': focus_page,
        'requested_ids': requested_ids,
        'inline_pages': inline_pages,
        'nav_pages': nav_pages,
        'missing_ids': missing,
        'warnings': ['missing page: ' + pid for pid in missing],
        'utility': {
            'copy_packet': True,
            'raw': True,
            'home': True,
            'back': True,
        },
    }


def describe_plan(plan):
    plan = plan or {}
    lines = []

    lines.append('SURFACE PLAN')
    lines.append('controlled: %s' % bool(plan.get('controlled')))
    lines.append('title: %s' % (plan.get('title') or '-'))
    lines.append('mode: %s' % (plan.get('mode') or '-'))
    lines.append('hero: %s' % (plan.get('hero') or '-'))
    lines.append('focus: %s' % (plan.get('focus_id') or '-'))

    lines.append('')
    lines.append('REQUESTED')
    requested = plan.get('requested_ids') or []
    if requested:
        for pid in requested:
            lines.append('- ' + str(pid))
    else:
        lines.append('- default')

    lines.append('')
    lines.append('INLINE')
    inline = plan.get('inline_pages') or []
    if inline:
        for p in inline:
            lines.append('- %s [%s/%s]' % (page_id(p), page_kind(p), page_source(p)))
    else:
        lines.append('- default renderer policy')

    lines.append('')
    lines.append('NAV')
    nav = plan.get('nav_pages') or []
    if nav:
        for p in nav:
            lines.append('- %s [%s/%s]' % (page_id(p), page_kind(p), page_source(p)))
    else:
        lines.append('- none')

    warnings = plan.get('warnings') or []
    if warnings:
        lines.append('')
        lines.append('WARNINGS')
        for w in warnings:
            lines.append('- ' + str(w))

    return '\n'.join(lines)
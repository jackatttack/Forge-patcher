# -*- coding: utf-8 -*-
"""
Surface V2 renderer.

This intentionally renders plain text only. Colour belongs to the live console
theme later; this layer owns structure, spacing, page behaviour, and concise
user-readable summaries.
"""

WIDTH = 41
INNER = 37


def _line(char='═', width=WIDTH):
    return char * width


def _center(text, width=WIDTH):
    text = str(text or '')
    if len(text) >= width:
        return text
    left = (width - len(text)) // 2
    return (' ' * left) + text


def _spaced(text):
    return ' '.join(str(text or '').upper())


def _wrap(text, width=INNER):
    words = str(text or '').split()
    if not words:
        return ['']
    out = []
    cur = ''
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += ' ' + word
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def _section(lines, title):
    lines.append('')
    lines.append('  ' + _line('═', 37))
    lines.append(_center(str(title or '').upper()))
    lines.append('  ' + _line('═', 37))
    lines.append('')


def _status_counts(run):
    applied = 0
    skipped = 0
    failed = 0
    for r in run.get('results') or []:
        status = str(r.get('status') or '').upper()
        if status == 'APPLIED':
            applied += 1
        elif 'SKIP' in status:
            skipped += 1
        else:
            failed += 1
    return applied, skipped, failed


def _status_title(run):
    status = str(run.get('status') or 'UNKNOWN').upper()
    if status == 'APPLIED':
        return 'RUN CLEAN'
    if status == 'FAILED_PARSE':
        return 'RUN PARSE FAILED'
    if status == 'FAILED':
        return 'RUN FAILED'
    if status == 'EMPTY':
        return 'RUN EMPTY'
    return 'RUN ' + status


def _summary_sentence(run):
    applied, skipped, failed = _status_counts(run)
    if failed:
        return 'This run needs attention: %d failed op%s. Read the issue detail before retrying.' % (
            failed,
            '' if failed == 1 else 's',
        )
    if skipped:
        return 'Run completed with %d skipped op%s. Check whether the skip was intentional.' % (
            skipped,
            '' if skipped == 1 else 's',
        )
    if applied:
        return 'Run clean. %d op%s applied with no visible errors.' % (
            applied,
            '' if applied == 1 else 's',
        )
    return 'No executable ops were applied.'


def _outcome_chart(lines, applied, skipped, failed):
    values = [
        ('applied', applied),
        ('skipped', skipped),
        ('failed', failed),
    ]
    max_value = max([v for _label, v in values] + [1])
    bar_width = 22
    lines.append('   Outcome')
    for label, value in values:
        if value > 0:
            filled = max(1, int(round((float(value) / float(max_value)) * bar_width)))
        else:
            filled = 0
        empty = max(0, bar_width - filled)
        bar = ('█' * filled) + ('░' * empty)
        lines.append('   %-8s  %s  %s' % (label, bar, value))


def _page_card(page):
    size = str((page or {}).get('size') or 'full')
    suffix = ''
    if size and size != 'full':
        suffix = ' · ' + size

    return '%s  %-12s  [%s]%s' % (
        page.get('icon') or '▣',
        page.get('short') or page.get('title') or '?',
        page.get('id') or '?',
        suffix,
    )

def _render_page_stack(lines, pages, focus):
    _section(lines, 'Pages')
    for p in pages:
        marker = '→' if p.get('id') == focus else ' '
        lines.append('%s %s' % (marker, _page_card(p)))


def _compact_message(result):
    msg = str(result.get('message') or '').strip()
    if not msg:
        return ''
    return msg.splitlines()[0]


def _result_icon(status):
    status = str(status or '').upper()
    if status == 'APPLIED':
        return '✅'
    if 'SKIP' in status:
        return '⚠️'
    if 'FAIL' in status:
        return '❌'
    return '•'


def _page_result(page):
    data = page.get('data') or {}
    result = data.get('result') or {}
    return result if isinstance(result, dict) else {}


def _page_preview_text(page):
    data = page.get('data') or {}
    preview = data.get('preview')
    if preview:
        return str(preview)
    result = _page_result(page)
    return str(result.get('preview') or '')


def _result_page_summary_lines(page):
    kind = str(page.get('kind') or '')
    data = page.get('data') or {}
    result = _page_result(page)
    out = []

    if kind == 'run_file':
        path = data.get('path') or result.get('target') or ''
        exit_code = data.get('exit_code')
        stdout = data.get('stdout') or ''
        stderr = data.get('stderr') or ''
        if path:
            out.append(path)
        if exit_code is not None:
            out.append('exit %s' % exit_code)
        flags = []
        if stdout:
            flags.append('stdout')
        if stderr:
            flags.append('stderr')
        if flags:
            out.append('%s available' % ' + '.join(flags))

    elif kind == 'url':
        url = data.get('url') or result.get('target') or ''
        mode = str(data.get('mode') or '').strip()
        msg = str(result.get('message') or '').strip()
        if url:
            out.append(url)
        if msg:
            out.append(msg)
        elif mode:
            out.append(mode)

    elif kind in ('help', 'preview', 'diff', 'audit', 'result'):
        preview = _page_preview_text(page)
        first = ''
        for raw in preview.splitlines():
            if raw.strip():
                first = raw.strip()
                break
        if first:
            out.append(first)

    return out[:3]


def _render_result_page_summaries(lines, pages, limit=6):
    result_pages = []
    for p in pages:
        kind = str(p.get('kind') or '')
        if kind in ('summary', 'ops', 'raw', 'files', 'errors'):
            continue
        if p.get('data'):
            result_pages.append(p)

    if not result_pages:
        return

    _section(lines, 'Result Pages')

    for p in result_pages[:limit]:
        icon = p.get('icon') or '▣'
        title = p.get('short') or p.get('title') or p.get('id') or 'Page'
        pid = p.get('id') or '?'
        lines.append('   %s  %s  [%s]' % (icon, title, pid))

        for detail in _result_page_summary_lines(p):
            for wrapped in _wrap(detail, 32):
                lines.append('      ' + wrapped)

    remaining = len(result_pages) - limit
    if remaining > 0:
        lines.append('   … %d more result page%s' % (remaining, '' if remaining == 1 else 's'))


def _render_ops(lines, run, limit=8):
    results = run.get('results') or []
    _section(lines, 'Ops')

    if not results:
        lines.append('   none')
        return

    for i, r in enumerate(results[:limit]):
        op = str(r.get('op') or '?')
        status = str(r.get('status') or 'UNKNOWN')
        target = str(r.get('target') or '').strip()
        msg = _compact_message(r)
        icon = _result_icon(status)

        left = '   %s #%02d  %-14s' % (icon, i + 1, op)
        lines.append(left.rstrip())

        detail_parts = []
        if status and status != 'APPLIED':
            detail_parts.append(status)
        if target and target not in ('?', 'None', 'null'):
            detail_parts.append(target)
        if msg:
            detail_parts.append(msg)

        if detail_parts:
            for wrapped in _wrap(' · '.join(detail_parts), 34):
                lines.append('      ' + wrapped)

    remaining = len(results) - limit
    if remaining > 0:
        lines.append('   … %d more op%s in packet.raw' % (remaining, '' if remaining == 1 else 's'))


def _render_errors(lines, run):
    errors = run.get('errors') or []
    hinted = [r for r in (run.get('results') or []) if r.get('hint')]

    if not errors and not hinted:
        return

    _section(lines, 'Issues')

    for err in errors[:5]:
        for wrapped in _wrap(str(err), 35):
            lines.append('   ❌ ' + wrapped if wrapped == _wrap(str(err), 35)[0] else '      ' + wrapped)

    for r in hinted[:3]:
        hint = str(r.get('hint') or '').splitlines()
        first = hint[0] if hint else ''
        if first:
            lines.append('')
            lines.append('   Hint · %s' % (r.get('op') or '?'))
            for wrapped in _wrap(first, 35):
                lines.append('      ' + wrapped)


def _render_files(lines, run):
    results = [
        r for r in (run.get('results') or [])
        if str(r.get('op') or '').upper() == 'LIST_FILES'
    ]
    if not results:
        return

    _section(lines, 'Files')

    for r in results:
        data = r.get('data') or {}
        meta = data.get('meta') or {}
        path = data.get('path') or r.get('target') or '.'
        lines.append('   %s' % path)
        lines.append('   %s dirs · %s files · %s entries' % (
            meta.get('dirs', 0),
            meta.get('files', 0),
            meta.get('entries', 0),
        ))

        shown = 0
        for node in data.get('tree') or []:
            if shown >= 8:
                remaining = max(0, len(data.get('tree') or []) - shown)
                if remaining:
                    lines.append('   … %d more' % remaining)
                break

            level = int(node.get('level') or 0)
            prefix = '   ' + ('  ' * level)
            if node.get('kind') == 'dir':
                lines.append(prefix + '▸ ' + str(node.get('name') or '') + '/')
            else:
                lines.append(prefix + '· ' + str(node.get('name') or ''))
            shown += 1


def _recommendation(run):
    status = str(run.get('status') or '').upper()
    if status == 'APPLIED':
        return '🧠 Summary enough'
    if status == 'FAILED_PARSE':
        return '❌ Send parse error'
    if status == 'FAILED':
        return '❌ Send issue detail'
    return '📋 Send packet'


def _control_label(control):
    icon = str((control or {}).get('icon') or '')
    label = str((control or {}).get('label') or '')
    return (icon + label).strip()


def _control_route_text(control):
    route = (control or {}).get('route') or ()
    if isinstance(route, (list, tuple)):
        return ' '.join(str(x) for x in route if str(x))
    return str(route or '')


def _collect_action_panels(run):
    pages = run.get('pages') or []
    panels = []

    # Prefer the summary page controls as the run-level action deck.
    for p in pages:
        if (p or {}).get('id') == 'run.summary':
            panels.extend((p or {}).get('controls') or [])
            break

    if not panels:
        # Fallback for partially-built runs.
        try:
            from forge_core.surface.controls import run_copy_panel, run_nav_panel
            stamp = run.get('stamp') or 'latest'
            panels = [run_copy_panel(stamp), run_nav_panel(stamp)]
        except Exception:
            panels = []

    try:
        from forge_core.surface.controls import sort_panels
        return sort_panels(panels)
    except Exception:
        return list(panels or [])

def _render_control_panel(lines, panel):
    controls = (panel or {}).get('controls') or []
    if not controls:
        return

    title = (panel or {}).get('title') or 'Actions'
    _section(lines, title)

    for i in range(0, len(controls), 2):
        row = controls[i:i + 2]
        parts = []
        for c in row:
            label = _control_label(c)
            parts.append(label[:18].ljust(18))
        lines.append('   ' + '  '.join(parts).rstrip())

        notes = []
        for c in row:
            note = str((c or {}).get('note') or (c or {}).get('kind') or '')
            notes.append(note[:18].ljust(18))
        if any(x.strip() for x in notes):
            lines.append('   ' + '  '.join(notes).rstrip())

    route_bits = []
    for c in controls:
        route_text = _control_route_text(c)
        if not route_text:
            continue
        label = str((c or {}).get('label') or 'Action')
        first = route_text.split()[0] if route_text.split() else route_text
        if first:
            route_bits.append('%s:%s' % (label, first))

    if route_bits:
        compact = ' · '.join(route_bits[:4])
        if len(route_bits) > 4:
            compact += ' · +%d' % (len(route_bits) - 4)
        for wrapped in _wrap('routes: ' + compact, 35):
            lines.append('   ' + wrapped)

def _render_actions(lines, run):
    for panel in _collect_action_panels(run):
        _render_control_panel(lines, panel)

    stamp = str(run.get('stamp') or 'latest')
    lines.append('')
    lines.append('   inspect: RUNS show %s' % stamp)


def format_surface(run):
    pages = run.get('pages') or []
    surface = run.get('surface') or {}
    focus = surface.get('focus') or ('run.errors' if run.get('errors') else (pages[0].get('id') if pages else 'run.summary'))

    applied, skipped, failed = _status_counts(run)
    packet = run.get('packet') or ''
    stamp = str(run.get('stamp') or 'latest')

    lines = []
    lines.append('')
    lines.append(_line('═'))
    lines.append('')
    lines.append(_center(_spaced(_status_title(run))))

    if run.get('stamp'):
        lines.append('')
        lines.append(_center(str(run.get('stamp'))))

    lines.append('')
    lines.append(_center('focus: %s' % focus))
    lines.append('')
    lines.append(_line('═'))
    lines.append('')

    for wrapped in _wrap(_summary_sentence(run), 35):
        lines.append('   ' + wrapped)

    lines.append('')
    _outcome_chart(lines, applied, skipped, failed)

    lines.append('')
    lines.append(_center('packet: %d chars' % len(packet)))
    lines.append('')
    lines.append(_center(_recommendation(run)))

    _render_actions(lines, run)
    _render_errors(lines, run)
    _render_page_stack(lines, pages, focus)
    _render_result_page_summaries(lines, pages)
    _render_ops(lines, run)
    _render_files(lines, run)

    lines.append('')
    lines.append(_line('─', 37))
    lines.append(_center('Raw packet available as page: packet.raw', 37))
    lines.append('')
    lines.append('   🏠 Home        ◎ Runs')
    lines.append('   📚 Docs        ¶ Raw')
    lines.append('   run: %s' % stamp)

    return '\n'.join(lines).rstrip() + '\n'

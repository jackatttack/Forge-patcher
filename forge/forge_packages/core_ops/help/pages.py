# -*- coding: utf-8 -*-
"""
Surface pages for HELP.

HELP is the teaching surface for Forge ops. The packet preview remains
stable LLM-facing truth; this page turns the same result into a calmer,
actionable, user-facing explanation.
"""

from forge_core.surface.model import page


def pages_for_result(result, index, run):
    data = result.get('data') or {}
    op_name = data.get('op') or _extract_help_op(result) or result.get('target') or '?'
    mode = data.get('mode') or 'full'
    issues = data.get('contract_issues') or []

    status = str(result.get('status') or '').upper()
    if status != 'APPLIED':
        tone = 'danger'
    elif issues:
        tone = 'warning'
    else:
        tone = 'accent'

    return [page(
        'help.%N',
        'Help: %s' % op_name,
        kind='help',
        icon='📖',
        short='Help',
        tone=tone,
        mode='standard',
        size='full',
        source='op:HELP',
        priority=78,
        data={
            'result': result,
            'result_index': index,
            'op': op_name,
            'mode': mode,
            'contract_issues': issues,
            'preview': result.get('preview') or '',
        },
    )]


def render_detail(page, context=None):
    """Full HELP detail surface."""
    context = context or {}
    data = (page or {}).get('data') or {}
    run = data.get('run') or {}
    idx = int(data.get('index') or data.get('result_index') or 0)
    results = run.get('results') or []
    stamp = run.get('stamp') or context.get('run_stamp') or 'latest'

    try:
        result = results[idx]
    except Exception:
        result = data.get('result') or {}

    result_data = result.get('data') or data
    op_name = result_data.get('op') or data.get('op') or _extract_help_op(result) or '?'
    mode = result_data.get('mode') or data.get('mode') or 'full'
    issues = result_data.get('contract_issues') or data.get('contract_issues') or []
    manifest = result_data.get('manifest') or {}
    preview = result.get('preview') or data.get('preview') or ''
    status = str(result.get('status') or 'unknown')

    try:
        from forge_core.surface.render.docpage import doc_hero
    except Exception:
        doc_hero = None
    try:
        from forge_core.surface.render.cards import panel
    except Exception:
        panel = None
    try:
        from forge_core.surface.render.hero import big_section
    except Exception:
        big_section = None
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
    except Exception:
        render_tile_dock = None
    try:
        from forge_core.surface.render.primitives import say
    except Exception:
        say = None

    if doc_hero:
        doc_hero('HELP %s' % op_name, 'mode %s · %s · #%02d' % (mode, status.lower(), idx + 1))
    else:
        print('=== HELP %s ===' % op_name)
        print('mode %s · %s · #%02d' % (mode, status.lower(), idx + 1))

    summary = _first_summary_line(preview, manifest)
    meta_lines = [
        'op:       %s' % op_name,
        'mode:     %s' % mode,
        'status:   %s' % status,
        'contract: %s' % ('FAIL' if issues else 'PASS'),
    ]
    if manifest:
        meta_lines.append('package:  %s' % (manifest.get('name') or '-'))
        meta_lines.append('version:  %s' % (manifest.get('version') or '-'))
        if manifest.get('risk'):
            meta_lines.append('risk:     %s' % manifest.get('risk'))

    _help_section_header('Summary', icon='◆')
    _help_body_line(summary)

    _help_section_header('Help Target', icon='▣')
    for line in meta_lines:
        _help_body_line(line)

    sections = _split_sections(preview)

    for title in ('USAGE', 'SPEC', 'DIRECTIVES', 'SAFE USAGE', 'EXAMPLE', 'COMMON FAILURES', 'RELATED', 'CONTRACT'):
        body = sections.get(title)
        if body:
            _render_section(title, body, panel, big_section, say)

    readme = sections.get('README')
    if readme:
        _render_readme_excerpt(readme, panel, big_section, say)

    if issues:
        _render_section('CONTRACT ISSUES', ['- ' + str(x) for x in issues], panel, big_section, say)

    _render_controls(stamp, op_name, render_tile_dock, context)


def _extract_help_op(result):
    message = str((result or {}).get('message') or '')
    prefix = 'Help for '
    if message.startswith(prefix):
        return message[len(prefix):].strip().upper()

    preview = str((result or {}).get('preview') or '')
    first = preview.splitlines()[0].strip() if preview.splitlines() else ''
    if first.startswith('HELP '):
        parts = first.split()
        if len(parts) >= 2:
            return parts[1].strip().upper()
    return ''


def _first_summary_line(preview, manifest):
    if manifest and manifest.get('summary'):
        return str(manifest.get('summary'))

    lines = [x.rstrip() for x in str(preview or '').splitlines()]
    for i, line in enumerate(lines):
        if line.startswith('HELP '):
            for candidate in lines[i + 1:]:
                candidate = candidate.strip()
                if candidate:
                    return candidate
    return 'Forge op help.'


def _split_sections(text):
    known = set([
        'README',
        'PACKAGE',
        'SPEC',
        'SUBJECT',
        'USAGE',
        'DIRECTIVES',
        'SAFE USAGE',
        'COMMON FAILURES',
        'EXAMPLE',
        'RELATED',
        'CONTRACT',
        'CHECKS',
        'MANIFEST',
    ])

    sections = {}
    current = None
    body = []

    for raw in str(text or '').splitlines():
        line = raw.rstrip()
        key = line.strip()
        if key in known:
            if current:
                sections[current] = body
            current = key
            body = []
        elif current:
            body.append(line)

    if current:
        sections[current] = body

    return sections


def _clean_lines(lines, limit=None):
    out = []
    for line in lines or []:
        text = str(line or '').rstrip()
        out.append(text)

    # Trim only the empty padding around a section. Preserve internal blank
    # lines so README/example blocks keep their intended breathing room.
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()

    if limit and len(out) > limit:
        return out[:limit] + ['… %d more lines' % (len(out) - limit)]
    return out


def _help_colour(tone):
    try:
        from forge_core.surface.render.primitives import colour
        colour(tone)
        return True
    except Exception:
        return False


def _help_reset():
    try:
        from forge_core.surface.render.primitives import reset
        reset()
    except Exception:
        pass


def _help_section_header(title, icon='▣'):
    title = str(title or 'Section').strip().upper()

    print('')
    print('  ' + '═' * 36)

    # Warning reads as warm/high-contrast in the current console theme.
    used_colour = _help_colour('warning')
    print('   %s  %s' % (icon, title))
    if used_colour:
        _help_reset()

    print('  ' + '─' * 36)


def _help_body_line(line, section=None):
    text = str(line or '').rstrip()
    section = str(section or '').upper()

    # Keep total printed width conservative for iPhone Pythonista console.
    # The console may hard-wrap much earlier than expected because of font,
    # scrollbar, safe-area, and current view width.
    indent = '   '
    width = 32

    if not text:
        print('')
        return

    if section == 'EXAMPLE':
        if text.startswith('    '):
            print(indent + text[4:])
        else:
            print(indent + text)
        return

    if text.startswith('#'):
        print('')
        used_colour = _help_colour('warning')
        _help_wrapped(text, indent=indent, width=width, hanging='  ')
        if used_colour:
            _help_reset()
        return

    if text.startswith('    '):
        print(indent + text[4:])
        return

    if text.startswith('- '):
        _help_wrapped('• ' + text[2:], indent=indent, width=width, hanging='  ')
        return

    if _looks_like_field_line(text):
        key, value = text.split(':', 1)
        key = key.strip()
        value = value.strip()

        if value:
            _help_wrapped('%s: %s' % (key, value), indent=indent, width=width, hanging='  ')
        else:
            print(indent + key + ':')
        return

    if _looks_like_command_line(text):
        print(indent + text)
        return

    _help_wrapped(text, indent=indent, width=width, hanging='  ')


def _looks_like_field_line(text):
    if ':' not in str(text or ''):
        return False
    key = str(text).split(':', 1)[0].strip()
    if not key:
        return False
    if ' ' in key:
        return False
    return key.replace('_', '').replace('-', '').isalnum()


def _looks_like_command_line(text):
    text = str(text or '').strip()
    if not text:
        return False
    first = text.split(None, 1)[0]
    if first.endswith(':'):
        return False
    return first.isupper() and first.replace('_', '').replace('-', '').isalnum()


def _help_wrapped(text, indent='   ', width=32, hanging='  '):
    text = str(text or '').strip()
    if not text:
        print('')
        return

    words = text.split()
    lines = []
    current = ''

    for word in words:
        candidate = word if not current else current + ' ' + word
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    if not lines:
        print(indent)
        return

    print(indent + lines[0])
    for line in lines[1:]:
        print(indent + str(hanging or '') + line)


def _render_section(title, lines, panel, big_section, say):
    body = _clean_lines(lines, limit=None)
    if not body:
        return

    section = str(title or '').upper()
    _help_section_header(_title_case(title), icon='▣')

    for line in body:
        _help_body_line(line, section=section)


def _render_readme_excerpt(lines, panel, big_section, say):
    body = _clean_lines(lines, limit=None)
    if not body:
        return

    _help_section_header('README', icon='📖')

    for line in body:
        _help_body_line(line, section='README')


def _render_controls(stamp, op_name, render_tile_dock, context=None):
    lower = str(op_name or '').lower()
    context = context or {}

    try:
        from forge_core.surface.actions import (
            back, copy_packet, help_for, home, op_readme, raw, runs, tile,
        )
        back_label = str(context.get('back_page') or 'audit').replace('run.', '').replace('op.', '')
        tiles = [
            tile('Back', back(context, stamp), icon='⬅️ ', subtitle=back_label, tone='warning'),
            tile('Quick', help_for(op_name, 'quick'), icon='⚡ ', subtitle='syntax', tone='accent'),
            tile('Full', help_for(op_name, 'full'), icon='📖 ', subtitle='docs', tone='accent'),
            tile('Contract', help_for(op_name, 'contract'), icon='✅ ', subtitle='checks', tone='accent'),
            tile('README', op_readme(stamp, lower), icon='📘 ', subtitle=lower, tone='accent'),
            tile('Raw', raw(stamp), icon='📦 ', subtitle='packet', tone='warning'),
            tile('Copy', copy_packet(stamp), icon='📋 ', subtitle='packet', tone='warning'),
            tile('Runs', runs(), icon='◎ ', subtitle='history', tone='accent'),
            tile('Home', home(), icon='🏠 ', subtitle='workbench', tone='success'),
        ]
    except Exception:
        tiles = [
            ('⬅️ ', 'Back',     'audit',      ('run_page', stamp, 'run.audit'),                  'warning'),
            ('⚡ ', 'Quick',    'syntax',     ('run_bundle', 'HELP %s quick' % op_name),          'accent'),
            ('📖 ', 'Full',     'docs',       ('run_bundle', 'HELP %s full' % op_name),           'accent'),
            ('✅ ', 'Contract', 'checks',     ('run_bundle', 'HELP %s contract' % op_name),       'accent'),
            ('📘 ', 'README',   lower,        ('run_page', stamp, 'op.readme', lower),            'accent'),
            ('📦 ', 'Raw',      'packet',     ('run_page', stamp, 'packet.raw'),                  'warning'),
            ('📋 ', 'Copy',     'packet',     ('copy_packet', stamp),                             'warning'),
            ('◎ ', 'Runs',     'history',    ('runs',),                                         'accent'),
            ('🏠 ', 'Home',     'workbench',  ('home',),                                          'success'),
        ]

    if render_tile_dock:
        render_tile_dock('Controls', tiles, cols=2, col_width=18, leading_space=1, trailing_space=2)
    else:
        print('')
        print('-- Controls --')
        for icon, label, subtitle, _route, _tone in tiles:
            print('  %s%s — %s' % (icon, label, subtitle))


def _title_case(text):
    return str(text or '').replace('_', ' ').title()
# -*- coding: utf-8 -*-
"""
Surface pages for READ.

READ is the inspect-first surface. It should make the important question obvious:
what was read, what mode was used, how much of the object is visible, and what
the next safe action is.
"""

def render_detail(page, context=None):
    """Render READ as a visual inspection dashboard.

    Console UX rule:
    the inspected content is useful, but the bottom landing zone should be the
    dashboard + controls because Pythonista prints top-to-bottom and leaves the
    latest output nearest the input bar.
    """
    context = context or {}
    data = (page or {}).get('data') or {}
    run = data.get('run') or {}
    idx = int(data.get('index') or 0)
    results = run.get('results') or []
    stamp = run.get('stamp') or context.get('run_stamp') or 'latest'

    try:
        result = results[idx]
    except Exception:
        result = data.get('result') or {}

    result_data = result.get('data') or {}
    status = str(result.get('status') or 'unknown')
    mode = str(result_data.get('mode') or 'file')
    path = str(result_data.get('path') or result.get('file') or result.get('target') or '')
    ast_target = str(result_data.get('ast_target') or '')
    kind = str(result_data.get('kind') or '')
    start = result_data.get('start')
    end = result_data.get('end')
    total = result_data.get('total')
    lines = list(result_data.get('lines') or [])
    preview_lines = list(result_data.get('preview_lines') or [])
    targets = list(result_data.get('targets') or [])
    tree = list(result_data.get('tree') or [])
    meta = result_data.get('meta') or {}

    try:
        from forge_core.surface.render.docpage import doc_hero
    except Exception:
        doc_hero = None

    tone = 'success' if status.upper() == 'APPLIED' else ('danger' if 'FAIL' in status.upper() else 'warning')

    subtitle_bits = [status.lower(), mode]
    if start and end:
        subtitle_bits.append('lines %s-%s' % (start, end))
    elif mode == 'targets':
        subtitle_bits.append('%d target%s' % (len(targets), '' if len(targets) == 1 else 's'))
    elif mode == 'directory':
        subtitle_bits.append('%d entr%s' % (len(tree), 'y' if len(tree) == 1 else 'ies'))

    if doc_hero:
        doc_hero('READ', ' · '.join([str(x) for x in subtitle_bits if str(x)]))
    else:
        print('')
        print('READ')
        print(' · '.join([str(x) for x in subtitle_bits if str(x)]))

    # Content first: useful to read, but not the bottom landing zone.
    if mode in ('file', 'ast') and lines:
        _section('Source', icon='👁')
        _render_code(lines)
    elif mode == 'targets':
        _section('Targets', icon='◎')
        _render_targets(targets, preview_lines)
    elif mode == 'directory':
        _section('Directory', icon='📁')
        _render_plain(preview_lines, max_lines=90)
    else:
        _section('Output', icon='▣')
        _render_plain(preview_lines or str(result.get('preview') or '').splitlines(), max_lines=None)

    # Bottom dashboard: this is what should be visible after the content.
    overview_rows = [
        ('status', status.lower(), tone),
        ('path', _compact_path(path), 'audit.target'),
    ]
    if ast_target:
        overview_rows.append(('target', _compact_path(ast_target), 'audit.target'))
    if kind:
        overview_rows.append(('kind', kind, 'text'))
    if start and end:
        if total:
            overview_rows.append(('range', '%s-%s of %s' % (start, end, total), 'audit.packet'))
        else:
            overview_rows.append(('range', '%s-%s' % (start, end), 'audit.packet'))

    _card('READ OVERVIEW', overview_rows, status='OK' if status.upper() == 'APPLIED' else status.upper())

    shape_rows = []
    if mode in ('file', 'ast'):
        shown = len(lines)
        span = _span(start, end, shown)
        shape_rows.extend([
            ('shown', '%s lines' % shown, 'success' if shown else 'muted'),
            ('span', '%s lines' % span, 'accent' if span else 'muted'),
        ])
        if total:
            shape_rows.append(('total', '%s lines' % total, 'audit.packet'))
    elif mode == 'targets':
        funcs, classes, assigns = _target_counts(targets)
        shape_rows.extend([
            ('targets', len(targets), 'success' if targets else 'muted'),
            ('funcs', funcs, 'accent' if funcs else 'muted'),
            ('classes', classes, 'audit.packet' if classes else 'muted'),
            ('assigns', assigns, 'muted'),
        ])
    elif mode == 'directory':
        dirs = int(meta.get('dirs') or 0)
        files = int(meta.get('files') or 0)
        shape_rows.extend([
            ('dirs', dirs, 'accent' if dirs else 'muted'),
            ('files', files, 'success' if files else 'muted'),
            ('entries', len(tree), 'audit.packet' if tree else 'muted'),
        ])
    else:
        shape_rows.append(('output', '%s lines' % len(preview_lines), 'accent'))

    _card('READ SHAPE', shape_rows)

    signal_rows = [
        ('mode', mode, 'text'),
        ('path', _compact_path(path), 'audit.target'),
        ('target', _compact_path(ast_target), 'audit.target'),
        ('kind', kind, 'text'),
        ('start', start, 'audit.packet'),
        ('end', end, 'audit.packet'),
        ('total', total, 'audit.packet'),
    ]
    if mode == 'directory':
        signal_rows.extend([
            ('depth', meta.get('depth'), 'audit.packet'),
            ('readme', 'yes' if meta.get('readme') else 'no', 'text'),
            ('docs', 'yes' if meta.get('docs') else 'no', 'text'),
        ])
    signal_rows = [row for row in signal_rows if row[1] not in (None, '')]
    if not signal_rows:
        signal_rows = [('signals', '(none)', 'muted')]

    _card('SIGNALS', signal_rows)

    _controls(stamp, idx, path, context)


def _compact_path(value, max_len=34):
    """Compact long paths/targets for boxed console rows."""
    text = str(value or '').strip()
    if not text:
        return ''
    if len(text) <= max_len:
        return text

    if '::' in text:
        path, _, target = text.partition('::')
        filename = path.replace('\\', '/').split('/')[-1]
        compact = '…/%s::%s' % (filename, target)
        if len(compact) <= max_len:
            return compact

    parts = text.replace('\\', '/').split('/')
    if len(parts) >= 2:
        compact = '…/' + '/'.join(parts[-2:])
        if len(compact) <= max_len:
            return compact

    return '…' + text[-max(1, max_len - 1):]


def _card(title, rows=None, status=''):
    """Render a compact boxed dashboard card using the audit card grammar."""
    import textwrap

    width = 40
    inner = width - 4
    label_width = 8
    value_width = inner - label_width

    def use_colour(tone):
        try:
            from forge_core.surface.render.primitives import colour
            colour(tone)
        except Exception:
            pass

    def clear_colour():
        try:
            from forge_core.surface.render.primitives import reset
            reset()
        except Exception:
            pass

    def frame(text):
        use_colour('audit.card.border')
        print(text)
        clear_colour()

    def content_line(text='', tone='text'):
        text = str(text or '')
        if len(text) > inner:
            text = text[:inner]

        use_colour('audit.card.border')
        print('│ ', end='')
        clear_colour()

        use_colour(tone)
        print(text.ljust(inner), end='')
        clear_colour()

        use_colour('audit.card.border')
        print(' │')
        clear_colour()

    def wrapped_rows(label, value, tone):
        label = str(label or '').strip()
        value = str(value or '').strip()
        if not value:
            return []

        wrapped = textwrap.wrap(value, width=max(10, value_width)) or ['']
        out = []
        for i, part in enumerate(wrapped):
            prefix = ('%-7s ' % (label + ':')) if i == 0 else ' ' * label_width
            out.append((prefix + part, tone))
        return out

    title = str(title or '').upper()
    status = str(status or '').upper()
    if status:
        header = ('%-24s %10s' % (title[:24], status[:10]))
    else:
        header = title[:inner]

    print('')
    frame('╭' + '─' * (width - 2) + '╮')
    content_line(header, 'success' if status in ('OK', 'APPLIED') else 'text')
    frame('├' + '─' * (width - 2) + '┤')

    printed = 0
    for row in rows or []:
        if len(row) == 2:
            label, value = row
            tone = 'text'
        else:
            label, value, tone = row
        for line, line_tone in wrapped_rows(label, value, tone):
            content_line(line, line_tone)
            printed += 1

    if not printed:
        content_line('(none)', 'muted')

    frame('╰' + '─' * (width - 2) + '╯')

def _span(start, end, fallback=0):
    try:
        s = int(start)
        e = int(end)
        if e >= s:
            return e - s + 1
    except Exception:
        pass
    return int(fallback or 0)


def _target_counts(targets):
    funcs = 0
    classes = 0
    assigns = 0

    for row in targets or []:
        if not isinstance(row, dict):
            continue
        kind = str(row.get('kind') or row.get('type') or '').lower()
        target = str(row.get('target') or '')
        if 'class' in kind:
            classes += 1
        elif 'function' in kind or 'method' in kind or '(' in target:
            funcs += 1
        elif '@' in target or 'assign' in kind:
            assigns += 1
        elif 'def ' in target:
            funcs += 1

    return funcs, classes, assigns


def _section(title, icon='▣'):
    title = str(title or '').upper()
    print('')
    try:
        from forge_core.surface.render.primitives import colour, reset
        colour('warning')
        print('  ' + '═' * 36)
        print('   %s  %s' % (icon, title))
        print('  ' + '─' * 36)
        reset()
    except Exception:
        print('  ' + '═' * 36)
        print('   %s  %s' % (icon, title))
        print('  ' + '─' * 36)


def _say(text, tone='text'):
    try:
        from forge_core.surface.render.primitives import say
        say(str(text), tone=tone)
    except Exception:
        print(str(text))


def _line(label, value, tone='text'):
    if value is None or str(value) == '':
        return
    _say('   %s: %s' % (label, value), tone=tone)


def _bar(label, value, max_value, tone='accent', width=16):
    try:
        value = int(value or 0)
    except Exception:
        value = 0
    try:
        max_value = int(max_value or 1)
    except Exception:
        max_value = 1

    max_value = max(max_value, 1)
    filled = max(1, int(round((float(value) / float(max_value)) * width))) if value else 0
    glyphs = ('█' * filled) + ('░' * max(0, width - filled))
    _say('   %-8s %s  %s' % (str(label or '')[:8], glyphs, value), tone=tone if value else 'muted')


def _wrapped(prefix, text=None, width=31, tone='text', indent='   ', hanging='  '):
    if text is None:
        raw = str(prefix or '').strip()
        prefix = indent
    else:
        raw = str(text or '').strip()
        prefix = str(prefix or '')

    if not raw:
        return

    words = raw.split()
    line = ''
    first = True

    for word in words:
        candidate = word if not line else line + ' ' + word
        if len(candidate) <= width:
            line = candidate
            continue
        if line:
            _say((prefix if first else ' ' * len(prefix) + str(hanging or '')) + line, tone=tone)
            first = False
        line = word

    if line:
        _say((prefix if first else ' ' * len(prefix) + str(hanging or '')) + line, tone=tone)


def _render_code(lines):
    try:
        from forge_core.surface.render.console_code import render_code_lines
        render_code_lines(lines, max_lines=None, indent='   ')
        return
    except Exception as e:
        print('   [code render unavailable: %s]' % e)

    for line in lines:
        print('   ' + str(line))


def _render_plain(lines, max_lines=None):
    rows = list(lines or [])
    original_len = len(rows)

    if max_lines is not None and len(rows) > max_lines:
        rows = rows[:max_lines]

    for line in rows:
        print('   ' + str(line))

    if max_lines is not None and original_len > max_lines:
        _say('   ... truncated: %d more line(s) ...' % (original_len - max_lines), tone='muted')


def _render_targets(targets, preview_lines):
    if targets:
        for row in targets[:80]:
            if not isinstance(row, dict):
                print('   ' + str(row))
                continue
            target = str(row.get('target') or '').strip()
            rng = str(row.get('range') or '').strip()
            doc = str(row.get('doc') or '').strip()
            indent = '  ' * int(row.get('indent') or 0)
            line = indent + target
            if rng:
                line += '  ' + rng
            print('   ' + line)
            if doc and doc != '∅':
                _wrapped('     · ', doc, width=30, tone='muted')
        if len(targets) > 80:
            _say('   ... %d more target(s) ...' % (len(targets) - 80), tone='muted')
        return

    _render_plain(preview_lines, max_lines=None)


def _controls(stamp, idx, path, context=None):
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
    except Exception:
        render_tile_dock = None

    try:
        from forge_core.surface.actions import (
            back, copy_packet, file_tiles, home, raw, runs, tile,
        )
        context = context or {}
        back_label = str(context.get('back_page') or 'audit').replace('run.', '').replace('op.', '')
        tiles = [
            tile('Back', back(context, stamp), icon='⬅️ ', subtitle=back_label, tone='warning'),
            tile('Raw', raw(stamp), icon='📦 ', subtitle='packet', tone='warning'),
            tile('Copy', copy_packet(stamp), icon='📋 ', subtitle='packet', tone='warning'),
            tile('Runs', runs(), icon='◎ ', subtitle='history', tone='accent'),
            tile('Home', home(), icon='🏠 ', subtitle='workbench', tone='success'),
        ]

        if path:
            for item in reversed(file_tiles(path, include_read=True, include_editor=True)):
                tiles.insert(1, item)

    except Exception:
        tiles = [
            ('⬅️ ', 'Back', 'audit', ('run_page', stamp, 'run.audit'), 'warning'),
            ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
            ('📋 ', 'Copy', 'packet', ('copy_packet', stamp), 'warning'),
            ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ]
        if path:
            tiles.insert(1, ('📄 ', 'Read', 'again', ('run_bundle', 'READ %s' % path), 'accent'))
            tiles.insert(2, ('🐍 ', 'Editor', 'Pythonista', ('open_pythonista', path), 'success'))
            tiles.insert(3, ('📋 ', 'Copy path', 'path', ('copy_path', path), 'warning'))

    if render_tile_dock:
        render_tile_dock('Controls', tiles, cols=2, col_width=18, leading_space=1, trailing_space=2)
    else:
        print('')
        print('-- Controls --')
        for icon, label, subtitle, _route, _tone in tiles:
            print('  %s%s — %s' % (icon, label, subtitle))
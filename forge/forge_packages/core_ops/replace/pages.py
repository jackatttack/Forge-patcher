# -*- coding: utf-8 -*-
"""
Surface pages for REPLACE.

REPLACE is a surgical edit surface. The detail page should make it obvious:
- what replacement mode was used
- what target was changed
- what body/block shape was supplied
- what Forge reported back
"""

def pages_for_result(run, result, index, registry=None):
    run = run or {}
    result = result or {}
    stamp = run.get('stamp') or 'latest'
    status = str(result.get('status') or '').upper()
    tone = 'success' if status == 'APPLIED' else ('danger' if 'FAIL' in status else 'warning')
    mode = _detect_mode(result)

    return [{
        'id': 'op.detail.%d' % int(index or 0),
        'title': 'REPLACE',
        'kind': 'op_detail',
        'source': 'op:REPLACE',
        'priority': -100 - int(index or 0),
        'mode': 'dense',
        'size': 'full',
        'footer': ['run.home', 'op.list'],
        'data': {
            'stamp': stamp,
            'run': run,
            'index': int(index or 0),
            'result': result,
            'back_page': 'run.audit',
            'runtime_controls': False,
            'runtime_grid': False,
        },
        'target': 'run:%s/replace/%d' % (stamp, int(index or 0)),
        'card': {
            'title': 'REPLACE',
            'subtitle': '%s · %s' % (status.lower() or 'unknown', mode),
            'icon': '✂',
            'tone': tone,
            'route': ('run_page', stamp, 'op.detail.%d' % int(index or 0)),
            'page_id': 'op.detail.%d' % int(index or 0),
            'body': [],
        },
        'emoji': '✂',
        'short': 'Replace',
        'tone': tone,
        'promote': False,
        'render_in_stack': False,
        'render': render_detail,
    }]


def render_detail(page, context=None):
    context = context or {}
    data = (page or {}).get('data') or {}
    run = data.get('run') or {}
    idx = int(data.get('index') or 0)
    results = run.get('results') or []
    stamp = run.get('stamp') or data.get('stamp') or context.get('run_stamp') or 'latest'

    try:
        result = results[idx]
    except Exception:
        result = data.get('result') or {}

    result_data = result.get('data') or {}
    status = str(result.get('status') or 'unknown')
    mode = _detect_mode(result)
    target = str(result_data.get('target') or result.get('target') or result.get('file') or '').strip()
    file_path = str(result_data.get('path') or result_data.get('file') or result.get('file') or '').strip()
    message = str(result.get('message') or '').strip()
    preview = str(result.get('preview') or result.get('stdout') or result.get('output') or '').strip()
    tone = 'success' if status.upper() == 'APPLIED' else ('danger' if 'FAIL' in status.upper() else 'warning')

    try:
        from forge_core.surface.render.docpage import doc_hero
    except Exception:
        doc_hero = None

    if doc_hero:
        doc_hero('REPLACE', '%s · %s · #%02d' % (status.lower(), mode, idx + 1))
    else:
        print('')
        print('REPLACE')
        print('%s · %s · #%02d' % (status.lower(), mode, idx + 1))

    overview_rows = [
        ('status', status.lower(), tone),
        ('target', _compact_path(target or file_path), 'audit.target'),
    ]
    if message:
        overview_rows.append(('message', message, 'audit.note'))
    _card('REPLACE OVERVIEW', overview_rows, status='OK' if status.upper() == 'APPLIED' else status.upper())

    stats = _preview_stats(result, preview)
    shape_rows = [
        ('mode', mode, 'accent'),
        ('span', '%s lines' % stats.get('span', 0), 'accent' if stats.get('span', 0) else 'muted'),
        ('changed', '%s lines' % stats.get('replaced', 0), 'success' if status.upper() == 'APPLIED' else 'warning'),
    ]
    _card('EDIT SHAPE', shape_rows)

    start = result_data.get('start')
    end = result_data.get('end')
    line_span = ''
    if start not in (None, '') and end not in (None, ''):
        line_span = '%s-%s' % (start, end)

    signal_rows = [
        ('file', _compact_path(file_path), 'audit.target'),
        ('kind', result_data.get('kind'), 'text'),
        ('mode', result_data.get('mode') or mode, 'accent'),
        ('lines', line_span, 'audit.packet'),
        ('matches', result_data.get('matches'), 'audit.packet'),
        ('replaced', result_data.get('replaced'), 'audit.packet'),
    ]
    signal_rows = [row for row in signal_rows if row[1] not in (None, '')]
    if not signal_rows:
        signal_rows = [('signals', '(none)', 'muted')]
    _card('SIGNALS', signal_rows)

    if preview:
        _section('Result preview', icon='👁')
        _render_output(preview.splitlines(), max_lines=80)
    else:
        _section('Result preview', icon='👁')
        _line('preview', '(none)', tone='muted')

    _controls(stamp, file_path or target, context)


def _compact_path(value, max_len=34):
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

def _detect_mode(result):
    result = result or {}
    data = result.get('data') or {}
    mode = str(data.get('mode') or '').strip().lower()
    if mode:
        return mode

    preview = str(result.get('preview') or '').lower()
    target = str(data.get('target') or result.get('target') or result.get('file') or '')
    msg = str(result.get('message') or '').lower()

    if '::' in target:
        return 'ast'
    if 'mode: ast' in preview:
        return 'ast'
    if 'mode: lines' in preview or 'lines:' in preview:
        return 'lines'
    if 'mode: block' in preview or 'old block' in msg:
        return 'block'
    if 'replaced file' in msg:
        return 'file'
    return 'replace'


def _preview_stats(result, text):
    result = result or {}
    data = result.get('data') or {}
    lines = str(text or '').splitlines()

    signals = 0
    for key in ('mode', 'path', 'file', 'target', 'kind', 'start', 'end', 'matches', 'replaced'):
        if data.get(key) not in (None, ''):
            signals += 1

    if not signals:
        for line in lines:
            s = line.strip().lower()
            if s.startswith(('replaced:', 'matches:', 'lines:', 'mode:', 'file:', 'kind:')):
                signals += 1

    span = 0
    try:
        start = int(data.get('start') or 0)
        end = int(data.get('end') or 0)
        if start and end >= start:
            span = end - start + 1
    except Exception:
        span = 0

    replaced = 0
    try:
        replaced = int(data.get('replaced') or 0)
    except Exception:
        replaced = 0

    if not replaced and span:
        replaced = span

    return {
        'lines': len(lines),
        'signals': signals,
        'span': span,
        'replaced': replaced,
    }


def _section(title, icon='▣'):
    print('')
    try:
        from forge_core.surface.render.primitives import colour, reset
        colour('warning')
        print('  ' + '═' * 36)
        print('   %s  %s' % (icon, str(title or '').upper()))
        print('  ' + '─' * 36)
        reset()
    except Exception:
        print('  ' + '═' * 36)
        print('   %s  %s' % (icon, str(title or '').upper()))
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


def _wrapped(prefix, text, width=31, tone='text'):
    text = str(text or '').strip()
    prefix = str(prefix or '')
    if not text:
        return

    words = text.split()
    line = ''
    first = True

    for word in words:
        candidate = word if not line else line + ' ' + word
        if len(candidate) <= width:
            line = candidate
            continue
        if line:
            _say((prefix if first else ' ' * len(prefix)) + line, tone=tone)
            first = False
        line = word

    if line:
        _say((prefix if first else ' ' * len(prefix)) + line, tone=tone)


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
    _say('   %-8s %s  %s' % (label, glyphs, value), tone=tone if value else 'muted')


def _render_output(lines, max_lines=80):
    rows = list(lines or [])
    try:
        from forge_core.surface.render.console_code import render_code_lines
        render_code_lines(rows[:max_lines], max_lines=max_lines, indent='   ')
    except Exception:
        for line in rows[:max_lines]:
            print('   ' + str(line))

    if len(rows) > max_lines:
        _say('   ... %d more line(s) ...' % (len(rows) - max_lines), tone='muted')


def _controls(stamp, target, context=None):
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

        if target and '::' not in target:
            for item in reversed(file_tiles(target, include_read=True, include_editor=True)):
                tiles.insert(1, item)

    except Exception:
        tiles = [
            ('⬅️ ', 'Back', 'audit', ('run_page', stamp, 'run.audit'), 'warning'),
            ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
            ('📋 ', 'Copy', 'packet', ('copy_packet', stamp), 'warning'),
            ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ]

    if render_tile_dock:
        render_tile_dock('Controls', tiles, cols=2, col_width=18, leading_space=1, trailing_space=2)
    else:
        for icon, label, subtitle, _route, _tone in tiles:
            print('  %s%s — %s' % (icon, label, subtitle))
# -*- coding: utf-8 -*-
"""
Surface pages for RUN_FILE.

RUN_FILE is a validation surface. It should make test output, smoke probes,
and tracebacks easier to scan than raw packet text.
"""

def pages_for_result(run, result, index, registry=None):
    run = run or {}
    result = result or {}
    data = result.get('data') or {}
    stamp = run.get('stamp') or 'latest'
    path = data.get('path') or result.get('target') or ''
    exit_code = data.get('exit_code')

    status = str(result.get('status') or '').upper()
    tone = 'success' if status == 'APPLIED' else 'danger'
    subtitle = 'exit %s' % exit_code if exit_code is not None else status.lower()

    return [{
        'id': 'op.detail.%d' % int(index or 0),
        'title': 'RUN_FILE',
        'kind': 'op_detail',
        'source': 'op:RUN_FILE',
        'priority': -100 - int(index or 0),
        'mode': 'dense',
        'size': 'full',
        'footer': ['run.home', 'op.list'],
        'data': {
            'stamp': stamp,
            'run': run,
            'index': int(index or 0),
            'result': result,
            'path': path,
            'exit_code': exit_code,
            'stdout': data.get('stdout') or '',
            'stderr': data.get('stderr') or '',
            'preview': result.get('preview') or '',
            'back_page': 'run.audit',
            'runtime_controls': False,
            'runtime_grid': False,
        },
        'target': 'run:%s/run_file/%d' % (stamp, int(index or 0)),
        'card': {
            'title': 'RUN_FILE',
            'subtitle': subtitle,
            'icon': '▶',
            'tone': tone,
            'route': ('run_page', stamp, 'op.detail.%d' % int(index or 0)),
            'page_id': 'op.detail.%d' % int(index or 0),
            'body': [],
        },
        'emoji': '▶',
        'short': 'Run',
        'tone': tone,
        'promote': False,
        'render_in_stack': False,
        'render': render_detail,
    }]


def render_detail(page, context=None):
    """Render a rich RUN_FILE detail surface."""
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

    result_data = result.get('data') or data
    status = str(result.get('status') or 'unknown')
    path = str(result_data.get('path') or result.get('target') or '').strip()
    exit_code = result_data.get('exit_code')
    stdout = str(result_data.get('stdout') or '')
    stderr = str(result_data.get('stderr') or '')

    try:
        from forge_core.surface.render.docpage import doc_hero
    except Exception:
        doc_hero = None

    subtitle_bits = [status.lower()]
    if exit_code is not None:
        subtitle_bits.append('exit %s' % exit_code)
    if path:
        subtitle_bits.append(_short_path(path))

    if doc_hero:
        doc_hero('RUN_FILE', ' · '.join(subtitle_bits))
    else:
        print('')
        print('RUN_FILE')
        print(' · '.join(subtitle_bits))

    _section('TARGET', icon='◆')
    _line('path', path)
    if exit_code is not None:
        _line('exit', exit_code)
    _line('status', status)

    if stdout.strip():
        _section('STDOUT', icon='▶')
        _render_output(stdout.splitlines(), tone='text')
    else:
        _section('STDOUT', icon='▶')
        _wrapped('(no stdout)', tone='muted')

    if stderr.strip():
        _section('STDERR / TRACEBACK', icon='⚠')
        _render_output(stderr.splitlines(), tone='danger')
    elif str(status).upper() != 'APPLIED':
        _section('STDERR / TRACEBACK', icon='⚠')
        _wrapped('(no stderr captured)', tone='warning')

    _controls(stamp, path, context)


def _short_path(path):
    path = str(path or '').strip()
    if len(path) <= 28:
        return path
    return '…' + path[-27:]


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


def _line(label, value):
    if value is None or str(value) == '':
        return
    label = str(label or '').strip()
    value = str(value)
    if label.lower() in ('path', 'file', 'target') and len(value) > 34:
        print('   %s:' % label)
        _wrapped(value, indent='     ', width=33, hanging='  ')
        return
    _wrapped('%s: %s' % (label, value), indent='   ', width=36, hanging='  ')


def _wrapped(text, indent='   ', width=36, hanging='  ', tone='text'):
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

    for i, line in enumerate(lines):
        prefix = indent if i == 0 else indent + str(hanging or '')
        _say(prefix + line, tone=tone)


def _say(text, tone='text'):
    try:
        from forge_core.surface.render.primitives import say
        say(str(text), tone=tone)
    except Exception:
        print(str(text))


def _render_output(lines, tone='text'):
    rows = list(lines or [])
    if not rows:
        return

    # Most RUN_FILE output is plain test/probe output, not Python source.
    # Still use the console code renderer where available because it gives
    # consistent monospace output and highlights tracebacks/code-ish lines.
    try:
        from forge_core.surface.render.console_code import render_code_lines
        render_code_lines(rows, max_lines=120, indent='   ')
        return
    except Exception:
        pass

    max_lines = 120
    for line in rows[:max_lines]:
        _say('   ' + str(line), tone=tone)
    if len(rows) > max_lines:
        _say('   ... %d more line(s) ...' % (len(rows) - max_lines), tone='muted')


def _controls(stamp, path, context=None):
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
    except Exception:
        render_tile_dock = None

    try:
        from forge_core.surface.actions import (
            back, copy_packet, file_tiles, home, raw, runs, run_bundle, tile,
        )
        context = context or {}
        back_label = str(context.get('back_page') or 'audit').replace('run.', '').replace('op.', '')
        tiles = [
            tile('Back', back(context, stamp), icon='⬅️ ', subtitle=back_label, tone='warning'),
            tile('Run again', run_bundle('RUN_FILE %s' % path), icon='▶ ', subtitle='rerun', tone='success'),
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
            ('▶ ', 'Run again', 'rerun', ('run_bundle', 'RUN_FILE %s' % path), 'success'),
            ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
            ('📋 ', 'Copy', 'packet', ('copy_packet', stamp), 'warning'),
            ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ]
        if path:
            tiles.insert(1, ('📁 ', 'File', 'inspect', ('run_page', stamp, 'file.view', 'path=' + path), 'accent'))
            tiles.insert(2, ('🐍 ', 'Editor', 'Pythonista', ('open_pythonista', path), 'success'))
            tiles.insert(3, ('📋 ', 'Copy path', 'path', ('copy_path', path), 'warning'))

    if render_tile_dock:
        render_tile_dock('Controls', tiles, cols=2, col_width=18, leading_space=1, trailing_space=2)
    else:
        print('')
        print('-- Controls --')
        for icon, label, subtitle, _route, _tone in tiles:
            print('  %s%s — %s' % (icon, label, subtitle))
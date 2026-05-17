# -*- coding: utf-8 -*-
"""
Surface pages for PIP.
"""


def pages_for_result(result, index, run):
    result = result or {}
    data = result.get('data') or {}
    status = str(result.get('status') or '').upper()
    tone = 'success' if status in ('APPLIED', 'SKIPPED_ALREADY_PRESENT') else 'danger'
    package = data.get('package') or result.get('target') or '?'
    action = data.get('action') or 'pip'
    stamp = (run or {}).get('stamp') or 'latest'

    return [{
        'id': 'op.detail.%d' % int(index or 0),
        'title': 'PIP',
        'kind': 'op_detail',
        'source': 'op:PIP',
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
        'target': 'run:%s/pip/%d' % (stamp, int(index or 0)),
        'card': {
            'title': 'PIP',
            'subtitle': '%s · %s · %s' % (status.lower(), action, package),
            'icon': '📦',
            'tone': tone,
            'route': ('run_page', stamp, 'op.detail.%d' % int(index or 0)),
            'page_id': 'op.detail.%d' % int(index or 0),
            'body': [],
        },
        'emoji': '📦',
        'short': 'PIP',
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

    info = result.get('data') or {}
    status = str(result.get('status') or 'unknown')
    tone = 'success' if status.upper() in ('APPLIED', 'SKIPPED_ALREADY_PRESENT') else 'danger'

    _hero('PIP', '%s · %s · %s' % (
        status.lower(),
        info.get('action') or 'pip',
        info.get('package') or result.get('target') or '?',
    ))

    _section('Package', icon='📦')
    _line('status', status, tone=tone)
    _line('package', info.get('package') or result.get('target'))
    _line('import', info.get('import_name'))
    _line('action', info.get('action'))
    _line('version', info.get('version'))
    _line('summary', info.get('summary'))
    _line('wheel', info.get('wheel'))
    _line('installed files', info.get('installed_count'))
    _line('removed items', info.get('removed_count'))

    msg = result.get('message')
    if msg:
        _section('Message', icon='◇')
        _wrapped(msg, tone=tone)

    _section('Verify', icon='✓')
    _wrapped('After install, create a tiny RUN_FILE import check before relying on the package.', tone='warning')

    _controls(stamp)


def _hero(title, subtitle):
    try:
        from forge_core.surface.render.docpage import doc_hero
        doc_hero(title, subtitle)
    except Exception:
        print('')
        print(title)
        print(subtitle)


def _section(title, icon='▣'):
    print('')
    try:
        from forge_core.surface.render.primitives import colour, reset
        colour('warning')
        print('  ' + '═' * 36)
        print('   %s  %s' % (icon, str(title).upper()))
        print('  ' + '─' * 36)
        reset()
    except Exception:
        print('  ' + '═' * 36)
        print('   %s  %s' % (icon, str(title).upper()))
        print('  ' + '─' * 36)


def _say(text, tone='text'):
    try:
        from forge_core.surface.render.primitives import say
        say(str(text), tone=tone)
    except Exception:
        print(str(text))


def _wrapped(text, indent='   ', width=36, hanging='  ', tone='text'):
    text = str(text or '').strip()
    if not text:
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

    for i, line in enumerate(lines):
        prefix = indent if i == 0 else indent + str(hanging or '')
        _say(prefix + line, tone=tone)


def _line(label, value, tone='text'):
    if value is None or str(value) == '':
        return
    _wrapped('%s: %s' % (label, value), tone=tone)


def _controls(stamp):
    try:
        from forge_core.surface.render.docpage import doc_tile_grid
        tiles = [
            ('⬅️ ', 'Back', 'audit', ('run_page', stamp, 'run.audit'), 'warning'),
            ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
            ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
        ]
        doc_tile_grid('Controls', tiles)
    except Exception:
        print('')
        print('Controls: Back | Raw | Runs')
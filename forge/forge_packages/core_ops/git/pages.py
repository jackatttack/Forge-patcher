# -*- coding: utf-8 -*-
"""
Surface pages for GIT.
"""

def pages_for_result(*args, **kwargs):
    run, result, index = _normalise_args(args)
    result = result or {}
    data = result.get('data') or {}
    stamp = (run or {}).get('stamp') or 'latest'
    sub = str(data.get('subcommand') or result.get('target') or 'status').strip() or 'status'
    status = str(result.get('status') or '').upper()
    tone = 'success' if status == 'APPLIED' else 'danger'

    return [{
        'id': 'op.detail.%d' % int(index or 0),
        'title': 'GIT',
        'kind': 'op_detail',
        'source': 'op:GIT',
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
        'target': 'run:%s/git/%d' % (stamp, int(index or 0)),
        'card': {
            'title': 'GIT',
            'subtitle': '%s · %s' % (status.lower(), sub),
            'icon': '⑂',
            'tone': tone,
            'route': ('run_page', stamp, 'op.detail.%d' % int(index or 0)),
            'page_id': 'op.detail.%d' % int(index or 0),
            'body': [],
        },
        'emoji': '⑂',
        'short': 'Git',
        'tone': tone,
        'promote': False,
        'render_in_stack': False,
        'render': render_detail,
    }]


def _normalise_args(args):
    if len(args) >= 3 and isinstance(args[0], dict) and 'results' in args[0]:
        return args[0], args[1], args[2]
    if len(args) >= 3:
        return args[2], args[0], args[1]
    return {}, {}, 0


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
    sub = str(info.get('subcommand') or 'status')
    repo = str(info.get('repo_full') or '')
    branch = str(info.get('branch') or '')
    tone = 'success' if status.upper() == 'APPLIED' else 'danger'

    _hero('GIT', '%s · %s · %s@%s' % (status.lower(), sub, repo or '?', branch or '?'))

    _section('Repo', icon='⑂')
    _line('repo', repo)
    _line('branch', branch)
    _line('command', sub)
    _line('token', 'loaded' if info.get('token_loaded') else 'not loaded', tone='success' if info.get('token_loaded') else 'warning')

    if sub in ('status', 'repo', 'branch'):
        _section('Status', icon='◇')
        _line('visibility', info.get('visibility'))
        _line('private', info.get('private'))
        _line('default', info.get('default_branch'))
        _line('url', info.get('html_url'))
        _line('latest', info.get('latest_sha_short'))
        _line('author', info.get('latest_author'))
        _line('date', info.get('latest_date'))
        _wrapped(str(info.get('latest_message') or ''), tone='text')

    elif sub == 'branches':
        _section('Branches', icon='⑂')
        for item in info.get('branches') or []:
            _wrapped('%s  %s  protected=%s' % (
                item.get('name'),
                item.get('sha_short'),
                item.get('protected'),
            ))

    elif sub == 'commits':
        _section('Commits', icon='◎')
        for item in info.get('commits') or []:
            _wrapped('%s  %s  %s' % (
                item.get('sha_short'),
                item.get('date'),
                item.get('message_short'),
            ))

    elif sub == 'files':
        _section('Files', icon='▦')
        _line('path', info.get('path'))
        for item in info.get('items') or []:
            size = item.get('size')
            size_text = '' if size is None else str(size) + ' B'
            _wrapped('%s  %-9s  %s' % (item.get('type'), size_text, item.get('path')))

    elif sub == 'file':
        _section('File', icon='📄')
        _line('path', info.get('path'))
        _line('sha', info.get('sha_short'))
        _line('size', info.get('size'))
        _section('Preview', icon='▣')
        _output(str(info.get('content_preview') or '').splitlines(), max_lines=120)

    elif sub == 'diff':
        _section('Diff', icon='▵')
        _line('local', info.get('local'))
        _line('remote', info.get('remote'))
        _line('remote exists', info.get('remote_exists'))
        _line('same', info.get('same'), tone='success' if info.get('same') else 'warning')
        _line('local size', info.get('local_size'))
        _line('remote size', info.get('remote_size'))
        diff_lines = info.get('diff_lines') or []
        if diff_lines:
            _section('Unified diff', icon='≠')
            _output(diff_lines, max_lines=160)
        elif info.get('same'):
            _wrapped('No content difference.', tone='success')
        else:
            _wrapped('No text diff shown.', tone='warning')

    elif sub in ('upload', 'delete'):
        _section(sub.capitalize(), icon='⇧' if sub == 'upload' else '⌫')
        _line('dry run', info.get('dry_run'), tone='warning' if info.get('dry_run') else 'text')
        _line('wrote', info.get('wrote'), tone='success' if info.get('wrote') else 'warning')
        _line('local', info.get('local'))
        _line('remote', info.get('remote'))
        _line('size', info.get('size'))
        _line('commit', str(info.get('commit_sha') or '')[:12])
        _line('commit url', info.get('commit_url'))
        _wrapped(str(info.get('message') or ''), tone='text')

    if status.upper() != 'APPLIED':
        _section('Failure', icon='⚠')
        _wrapped(str(result.get('message') or info.get('error') or 'GIT failed'), tone='danger')

    _controls(stamp, context)


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


def _output(lines, max_lines=120):
    rows = list(lines or [])
    try:
        from forge_core.surface.render.console_code import render_code_lines
        render_code_lines(rows, max_lines=max_lines, indent='   ')
        return
    except Exception:
        pass

    for line in rows[:max_lines]:
        _say('   ' + str(line))
    if len(rows) > max_lines:
        _say('   ... %d more line(s) ...' % (len(rows) - max_lines), tone='muted')


def _controls(stamp, context):
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
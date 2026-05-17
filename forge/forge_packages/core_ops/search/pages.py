# -*- coding: utf-8 -*-
"""
Surface pages for SEARCH.

SEARCH is an orientation surface: it should quickly show what matched, where,
and what action to take next. It deliberately follows the visual language used
by READ and HELP:
- doc hero
- section headers
- code-style hit rendering
- tile controls for file/navigation actions
"""

def pages_for_result(run, result, index, registry=None):
    run = run or {}
    result = result or {}
    data = result.get('data') or {}
    stamp = run.get('stamp') or 'latest'
    query = data.get('query') or ''
    hits = data.get('hits') or []

    title = 'SEARCH'
    subtitle = '%d hit%s' % (len(hits), '' if len(hits) == 1 else 's')

    return [{
        'id': 'op.detail.%d' % int(index or 0),
        'title': title,
        'kind': 'op_detail',
        'source': 'op:SEARCH',
        'priority': -100 - int(index or 0),
        'mode': 'dense',
        'size': 'full',
        'footer': ['run.home', 'op.list'],
        'data': {
            'stamp': stamp,
            'run': run,
            'index': int(index or 0),
            'result': result,
            'query': query,
            'hits': hits,
            'back_page': 'run.audit',
            'runtime_controls': False,
            'runtime_grid': False,
        },
        'target': 'run:%s/search/%d' % (stamp, int(index or 0)),
        'card': {
            'title': 'SEARCH',
            'subtitle': subtitle,
            'icon': '⌕',
            'tone': 'accent',
            'route': ('run_page', stamp, 'op.detail.%d' % int(index or 0)),
            'page_id': 'op.detail.%d' % int(index or 0),
            'body': [],
        },
        'emoji': '⌕',
        'short': 'Search',
        'tone': 'accent',
        'promote': False,
        'render_in_stack': False,
        'render': render_detail,
    }]


def render_detail(page, context=None):
    """Render SEARCH as a boxed visual result dashboard."""
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
    query = str(result_data.get('query') or '').strip()
    target = str(result_data.get('target') or result.get('target') or '').strip()
    hits = list(result_data.get('hits') or [])
    searched = int(result_data.get('searched') or 0)
    files_hit = int(result_data.get('files_hit') or 0)
    match_mode = str(result_data.get('match_mode') or 'exact')
    limit = int(result_data.get('limit') or 0)
    limit_reached = bool(result_data.get('limit_reached'))
    context_lines = int(result_data.get('context') or 0)
    path_filter = str(result_data.get('path_filter') or '').strip()
    exts = result_data.get('exts') or []
    case_sensitive = bool(result_data.get('case_sensitive'))

    try:
        from forge_core.surface.render.docpage import doc_hero
    except Exception:
        doc_hero = None

    tone = 'success' if status.upper() == 'APPLIED' else ('danger' if 'FAIL' in status.upper() else 'warning')

    if doc_hero:
        doc_hero('SEARCH', '%s · %d hit%s · %s' % (
            status.lower(),
            len(hits),
            '' if len(hits) == 1 else 's',
            match_mode,
        ))
    else:
        print('')
        print('SEARCH')
        print('%s · %d hit(s) · %s' % (status, len(hits), match_mode))

    grouped = _group_hits(hits)

    _summary_card(
        'SEARCH',
        status,
        tone,
        [
            ('query', query or '(empty)', 'text'),
            ('target', target or '.', 'path'),
            ('mode', match_mode, 'text'),
            ('hits', '%d across %d file%s' % (
                len(hits),
                files_hit,
                '' if files_hit == 1 else 's',
            ), 'metric'),
        ],
    )

    _metric_box(
        'Search shape',
        [
            ('hits', len(hits), 'success' if hits else 'muted'),
            ('files', files_hit, 'accent' if files_hit else 'muted'),
            ('scanned', searched, 'warning' if searched else 'muted'),
        ],
    )

    signal_rows = [
        ('match', match_mode, 'text'),
        ('case', 'sensitive' if case_sensitive else 'insensitive', 'text'),
    ]
    if limit:
        signal_rows.append(('limit', str(limit) + (' reached' if limit_reached else ''), 'warning' if limit_reached else 'text'))
    if context_lines:
        signal_rows.append(('context', context_lines, 'text'))
    if path_filter:
        signal_rows.append(('filter', path_filter, 'path'))
    if exts:
        signal_rows.append(('ext', ', '.join(str(x) for x in exts), 'text'))

    _summary_card('SIGNALS', 'search settings', 'border', signal_rows, icon='◇')

    if not hits:
        _summary_card(
            'NO HITS',
            'widen or fuzz',
            'warning',
            [
                ('next', 'try MATCH: fuzzy', 'text'),
                ('scope', 'widen EXT or remove FILTER', 'text'),
                ('target', 'search a broader directory', 'path'),
            ],
            icon='◇',
        )
        _controls(stamp, context)
        return

    _section('Hit map', icon='▦')
    top_counts = _top_file_counts(grouped)
    max_hits = max([count for _path, count in top_counts] + [1])
    for file_path, count in top_counts:
        label = _compact_path_label(file_path)
        _bar(label, count, max_hits, 'accent', width=14)
    if len(grouped) > len(top_counts):
        _say('   ... %d more file(s) ...' % (len(grouped) - len(top_counts)), tone='muted')

    _section('Results', icon='⌕')
    for file_path in sorted(grouped):
        _file_block(file_path, grouped[file_path])

    _controls(stamp, context)


def _tone(name, default='text'):
    try:
        from forge_core.surface.theme import resolve_tone
        return resolve_tone(name, default)
    except Exception:
        return default


def _colour(name):
    try:
        from forge_core.surface.render.primitives import colour
        colour(_tone(name, name))
    except Exception:
        pass


def _reset():
    try:
        from forge_core.surface.render.primitives import reset
        reset()
    except Exception:
        pass


def _box_print(text='', tone='text', end='\n'):
    _colour(tone)
    print(str(text), end=end)
    _reset()


def _clip(text, width):
    text = str(text or '')
    if len(text) > width:
        return text[:max(0, width - 1)] + '…'
    return text


def _box_top(tone='border', width=40):
    _box_print('╭' + '─' * (width - 2) + '╮', tone)


def _box_mid(tone='border', width=40):
    _box_print('├' + '─' * (width - 2) + '┤', tone)


def _box_bottom(tone='border', width=40):
    _box_print('╰' + '─' * (width - 2) + '╯', tone)


def _box_line(text='', tone='text', width=40):
    inner = width - 4
    text = _clip(text, inner)
    _colour(tone)
    print('│ ' + text.ljust(inner) + ' │')
    _reset()


def _box_wrapped(label, value, tone='text', width=40):
    import textwrap

    label = str(label or '').strip()
    value = str(value or '').strip()
    if not value:
        return

    inner = width - 4
    prefix = ('%-7s ' % (label + ':'))[:8]
    rows = textwrap.wrap(value, width=max(8, inner - len(prefix))) or ['']

    for i, row in enumerate(rows):
        if i == 0:
            _box_line(prefix + row, tone, width)
        else:
            _box_line((' ' * len(prefix)) + row, tone, width)


def _summary_card(title, subtitle, tone, rows, icon='◆'):
    width = 40
    print('')
    _box_top(tone, width)
    _box_line('%s  %-20s %10s' % (icon, str(title or '').upper()[:20], str(subtitle or '')[:10]), tone, width)
    _box_mid(tone, width)

    for row in rows or []:
        if len(row) == 3:
            label, value, row_tone = row
        else:
            label, value = row
            row_tone = 'text'
        _box_wrapped(label, value, row_tone, width)

    _box_bottom(tone, width)


def _metric_box(title, rows):
    rows = list(rows or [])
    max_value = max([int(value or 0) for _label, value, _tone in rows] + [1])
    width = 40

    print('')
    _box_top('border', width)
    _box_line('▥  ' + str(title or '').upper(), 'border', width)
    _box_mid('border', width)

    for label, value, tone in rows:
        try:
            value = int(value or 0)
        except Exception:
            value = 0
        bar_width = 14
        filled = max(1, int(round((float(value) / float(max_value)) * bar_width))) if value else 0
        glyphs = ('█' * filled) + ('░' * max(0, bar_width - filled))
        _box_line('%-8s %s  %s' % (str(label or '')[:8], glyphs, value), tone if value else 'muted', width)

    _box_bottom('border', width)

def _group_hits(hits):
    grouped = {}
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        file_path = str(hit.get('file') or hit.get('path') or '').strip()
        if not file_path:
            file_path = '?'
        grouped.setdefault(file_path, []).append(hit)
    return grouped


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
    row = '%s: %s' % (label, value)
    _wrapped(row, indent='   ', width=36, hanging='  ')

def _say(text, tone='text'):
    try:
        from forge_core.surface.render.primitives import say
        say(str(text), tone=tone)
    except Exception:
        print(str(text))


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


def _top_file_counts(grouped, limit=6):
    rows = []
    for path, hits in (grouped or {}).items():
        rows.append((path, len(hits or [])))
    rows.sort(key=lambda item: (-item[1], item[0]))
    return rows[:int(limit or 6)]


def _compact_path_label(path):
    """Return a short but less ambiguous label for hit-map bars."""
    path = str(path or '').replace('\\', '/').strip()
    if not path:
        return '?'

    parts = [p for p in path.split('/') if p]
    if not parts:
        return path[:8]

    name = parts[-1]
    if len(parts) >= 2:
        parent = parts[-2]
        label = parent[:3] + '/' + name
    else:
        label = name

    if len(label) <= 8:
        return label

    if '.' in name:
        stem, dot, ext = name.rpartition('.')
        compact = stem[:4] + dot + ext[:2]
        if len(parts) >= 2:
            compact = parts[-2][:2] + '/' + compact
        return compact[:8]

    return label[:8]


def _wrapped(text, indent='   ', width=36, hanging='  '):
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


def _file_block(path, hits):
    print('')
    try:
        from forge_core.surface.render.primitives import colour, reset
        colour('accent')
        print('   ' + str(path))
        reset()
    except Exception:
        print('   ' + str(path))

    for hit in hits[:12]:
        try:
            lineno = int(hit.get('line') or 0)
        except Exception:
            lineno = 0

        text = str(hit.get('text') or '')

        if lineno:
            try:
                from forge_core.surface.render.primitives import say
                say('   line %d' % lineno, tone='muted')
            except Exception:
                print('   line %d' % lineno)

        _render_code([text])

    if len(hits) > 12:
        print('   ... %d more hit(s) ...' % (len(hits) - 12))

    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
        from forge_core.surface.actions import file_tiles
        tiles = file_tiles(path, include_read=True, include_editor=True)
        if tiles:
            render_tile_dock('File actions', tiles, cols=2, col_width=18, leading_space=1, trailing_space=1)
    except Exception:
        pass


def _render_code(lines):
    try:
        from forge_core.surface.render.console_code import render_code_lines
        render_code_lines(lines, max_lines=12, indent='   ')
        return
    except Exception as e:
        print('   [code render unavailable: %s]' % e)

    for line in lines[:12]:
        print('   ' + str(line))
    if len(lines) > 12:
        print('   ... %d more hit(s) ...' % (len(lines) - 12))


def _controls(stamp, context=None):
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
    except Exception:
        render_tile_dock = None

    try:
        from forge_core.surface.actions import back, copy_packet, home, raw, runs, tile
        context = context or {}
        back_label = str(context.get('back_page') or 'audit').replace('run.', '').replace('op.', '')
        tiles = [
            tile('Back', back(context, stamp), icon='⬅️ ', subtitle=back_label, tone='warning'),
            tile('Raw', raw(stamp), icon='📦 ', subtitle='packet', tone='warning'),
            tile('Copy', copy_packet(stamp), icon='📋 ', subtitle='packet', tone='warning'),
            tile('Runs', runs(), icon='◎ ', subtitle='history', tone='accent'),
            tile('Home', home(), icon='🏠 ', subtitle='workbench', tone='success'),
        ]
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
        print('')
        print('-- Controls --')
        for icon, label, subtitle, _route, _tone in tiles:
            print('  %s%s — %s' % (icon, label, subtitle))
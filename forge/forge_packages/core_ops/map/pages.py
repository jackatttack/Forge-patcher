# -*- coding: utf-8 -*-
"""
Surface pages for MAP.

MAP is an orientation surface. It should make structure easier to scan than raw
packet text while preserving the useful command-oriented output.
"""


def _normalise_args(args):
    """Support both provider call shapes used during the reboot migration."""
    if len(args) >= 3:
        a, b, c = args[:3]

        # Newer custom pages often use (run, result, index).
        if isinstance(a, dict) and isinstance(b, dict):
            return a or {}, b or {}, int(c or 0)

        # Older provider loader uses (result, index, run).
        return c or {}, a or {}, int(b or 0)

    return {}, {}, 0


def pages_for_result(*args, **kwargs):
    run, result, index = _normalise_args(args)
    data = result.get('data') or {}
    stamp = run.get('stamp') or 'latest'

    target = data.get('target') or result.get('target') or '?'
    kind = data.get('kind') or 'map'
    mode = data.get('mode') or 'auto'

    subtitle = '%s · %s' % (kind, mode)

    return [{
        'id': 'op.detail.%d' % int(index or 0),
        'title': 'MAP',
        'kind': 'op_detail',
        'source': 'op:MAP',
        'priority': -100 - int(index or 0),
        'mode': 'dense',
        'size': 'full',
        'footer': ['run.home', 'op.list'],
        'data': {
            'stamp': stamp,
            'run': run,
            'index': int(index or 0),
            'result': result,
            'target': target,
            'kind': kind,
            'mode': mode,
            'back_page': 'run.audit',
            'runtime_controls': False,
            'runtime_grid': False,
        },
        'target': 'run:%s/map/%d' % (stamp, int(index or 0)),
        'card': {
            'title': 'MAP',
            'subtitle': subtitle,
            'icon': '🗺️',
            'tone': 'accent',
            'route': ('run_page', stamp, 'op.detail.%d' % int(index or 0)),
            'page_id': 'op.detail.%d' % int(index or 0),
            'body': [str(target)],
        },
        'emoji': '🗺️',
        'short': 'Map',
        'tone': 'accent',
        'promote': False,
        'render_in_stack': False,
        'render': render_detail,
    }]


def render_detail(page, context=None):
    """Render MAP as a visual structure dashboard."""
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
    target = str(result_data.get('target') or result.get('target') or '').strip()
    kind = str(result_data.get('kind') or '').strip()
    mode = str(result_data.get('mode') or 'auto').strip()
    depth = result_data.get('depth')
    limit = result_data.get('limit')
    docs = result_data.get('docs')

    preview = str(result.get('preview') or '').rstrip()
    parsed = {
        'target': result_data.get('map_target') or '',
        'type': result_data.get('map_type') or '',
        'fields': result_data.get('fields') or {},
        'sections': result_data.get('sections') or {},
    }

    if not parsed.get('sections') and preview:
        parsed = _parse_map_preview(preview)

    sections = parsed.get('sections') or {}
    title_target = parsed.get('target') or target or '?'
    title_kind = parsed.get('type') or kind or 'map'

    _hero(status, title_kind, title_target, mode)

    _summary_card(
        'MAP',
        status.lower(),
        _status_tone(status),
        [
            ('target', title_target, 'path'),
            ('type', title_kind, 'text'),
            ('mode', mode or 'auto', 'text'),
            ('depth', depth if depth is not None else parsed.get('depth'), 'metric'),
            ('limit', limit if limit is not None else '', 'metric'),
            ('docs', _yes_no(docs), 'text'),
        ],
        icon='🗺️',
    )

    metrics = _metric_rows(parsed)
    if metrics:
        _metric_box('Shape', metrics)

    section_specs = [
        ('README', 'list'),
        ('Project hints', 'list'),
        ('Likely entrypoints', 'list'),
        ('Import summary', 'list'),
        ('Imports', 'imports'),
        ('Target summary', 'list'),
        ('Target highlights', 'targets'),
        ('Targets', 'targets'),
        ('Structure', 'tree'),
        ('Suggested next reads', 'commands'),
        ('Suggested next steps', 'commands'),
        ('Suggested dependency maps', 'commands'),
    ]

    for section, kind_name in section_specs:
        rows = sections.get(section) or []
        if not rows:
            continue

        if kind_name == 'tree':
            _tree_section(section, rows)
        elif kind_name == 'targets':
            _target_section(section, rows)
        elif kind_name == 'imports':
            _import_section(rows)
        elif kind_name == 'commands':
            _command_section(section, rows)
        else:
            _list_section(section, rows)

    rendered = set(name for name, _kind in section_specs)
    extra_sections = [name for name in sections if name not in rendered]
    for section in extra_sections:
        rows = sections.get(section) or []
        if rows:
            _list_section(section, rows)

    if not sections and preview:
        _section('Raw map', icon='▤')
        _render_code(preview.splitlines()[:80])

    _controls(stamp, context)


def _parse_map_preview(preview):
    try:
        from forge_packages.core_ops.map.op import _preview_sections
        data = _preview_sections(str(preview or '').splitlines())
        return {
            'target': data.get('map_target') or '',
            'type': data.get('map_type') or '',
            'fields': data.get('fields') or {},
            'sections': data.get('sections') or {},
        }
    except Exception:
        pass
    # Inline fallback if import fails.
    out = {'target': '', 'type': '', 'fields': {}, 'sections': {}}
    current = None
    for raw in str(preview or '').splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('MAP '):
            out['target'] = stripped[4:].strip()
            current = None
            continue
        if stripped.startswith('TYPE='):
            out['type'] = stripped.split('=', 1)[1].strip()
            current = None
            continue
        if stripped.endswith(':') and not stripped.startswith('-'):
            current = stripped[:-1]
            out['sections'].setdefault(current, [])
            continue
        if current:
            out['sections'].setdefault(current, []).append(line)
            continue
        if ':' in stripped:
            key, value = stripped.split(':', 1)
            out['fields'][key.strip().lower()] = value.strip()
    return out


def _metric_rows(parsed):
    fields = parsed.get('fields') or {}
    rows = []

    for key, tone in (
        ('files', 'accent'),
        ('dirs', 'warning'),
        ('python files', 'success'),
        ('lines', 'accent'),
        ('imports', 'warning'),
        ('targets', 'success'),
    ):
        value = fields.get(key)
        if value is None or value == '':
            continue
        try:
            n = int(str(value).strip())
        except Exception:
            continue
        rows.append((key, n, tone if n else 'muted'))

    return rows


def _hero(status, kind, target, mode):
    try:
        from forge_core.surface.render.docpage import doc_hero
        doc_hero('MAP', '%s · %s · %s' % (
            str(status or '').lower(),
            str(kind or 'map'),
            str(mode or 'auto'),
        ))
        return
    except Exception:
        pass

    print('')
    print('MAP')
    print('%s · %s · %s' % (status, kind, mode))
    print(target)


def _status_tone(status):
    status = str(status or '').upper()
    if status == 'APPLIED':
        return 'success'
    if 'FAIL' in status:
        return 'danger'
    return 'warning'


def _yes_no(value):
    if value is True:
        return 'yes'
    if value is False:
        return 'no'
    if value in (None, ''):
        return ''
    return str(value)


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
    prefix = ('%-8s ' % (label + ':'))[:9]
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
    if not rows:
        return

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
        _box_line('%-10s %s %s' % (str(label or '')[:10], glyphs, value), tone if value else 'muted', width)

    _box_bottom('border', width)


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


def _list_section(title, rows):
    _section(title, icon='◇')
    for row in rows[:40]:
        _say('   ' + str(row).strip(), tone='text')
    if len(rows) > 40:
        _say('   ... %d more row(s) ...' % (len(rows) - 40), tone='muted')


def _tree_section(title, rows):
    _section(title, icon='▦')
    for row in rows[:80]:
        text = str(row)
        tone = 'accent' if text.rstrip().endswith('/') else 'text'
        if '· readme' in text:
            tone = 'success'
        elif '· py' in text:
            tone = 'warning'
        _say('   ' + text, tone=tone)
    if len(rows) > 80:
        _say('   ... %d more row(s) ...' % (len(rows) - 80), tone='muted')


def _target_section(title, rows=None):
    if rows is None:
        rows = title
        title = 'Targets'

    _section(str(title or 'Targets'), icon='◎')
    for row in rows[:50]:
        text = str(row).strip()
        tone = 'accent'
        if 'assignment' in text:
            tone = 'warning'
        elif 'function' in text or 'method' in text:
            tone = 'success'
        elif 'class' in text:
            tone = 'accent'
        if 'huge class' in text:
            tone = 'warning'
        _say('   ' + text, tone=tone)
    if len(rows) > 50:
        _say('   ... %d more target(s) ...' % (len(rows) - 50), tone='muted')


def _import_section(rows):
    _section('Imports', icon='⇄')
    local_count = 0
    external_count = 0
    stdlib_count = 0

    for row in rows:
        text = str(row)
        if '· local' in text:
            local_count += 1
        elif '· stdlib' in text:
            stdlib_count += 1
        else:
            external_count += 1

    _summary_card(
        'IMPORTS',
        'coupling',
        'border',
        [
            ('local', local_count, 'success'),
            ('stdlib', stdlib_count, 'accent'),
            ('other', external_count, 'warning'),
        ],
        icon='⇄',
    )

    for row in rows[:50]:
        text = str(row).strip()
        tone = 'success' if '· local' in text else ('accent' if '· stdlib' in text else 'warning')
        _say('   ' + text, tone=tone)

    if len(rows) > 50:
        _say('   ... %d more import(s) ...' % (len(rows) - 50), tone='muted')


def _command_section(title, rows):
    _section(title, icon='▶')
    commands = []
    for row in rows:
        text = str(row).strip()
        if text.startswith('- '):
            text = text[2:].strip()
        if text:
            commands.append(text)

    for command in commands[:30]:
        tone = 'text'
        if command.startswith('READ '):
            tone = 'success'
        elif command.startswith('MAP '):
            tone = 'accent'
        elif command.startswith('...'):
            tone = 'muted'
        _say('   ' + command, tone=tone)

    if len(commands) > 30:
        _say('   ... %d more command(s) ...' % (len(commands) - 30), tone='muted')


def _render_code(lines):
    try:
        from forge_core.surface.render.console_code import render_code_lines
        render_code_lines(lines, max_lines=80, indent='   ')
        return
    except Exception:
        pass

    for line in lines[:80]:
        print('   ' + str(line))
    if len(lines) > 80:
        print('   ... %d more line(s) ...' % (len(lines) - 80))


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
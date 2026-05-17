# -*- coding: utf-8 -*-
"""
Minimal reboot-native LinkOS core pages.

This file intentionally does not port the full live LinkOS core_pages.py yet.
It provides enough page renderers to prove the page-stack runtime inside the
Forge without dragging in live package data/router dependencies.
"""


def _rule(width=42, char='─'):
    print(str(char) * int(width))


def _counts(run):
    counts = (run or {}).get('counts') or {}
    results = (run or {}).get('results') or []

    applied = counts.get('applied')
    skipped = counts.get('skipped')
    failed = counts.get('failed')

    if applied is None:
        applied = sum(1 for r in results if str(r.get('status') or '').upper() == 'APPLIED')
    if skipped is None:
        skipped = sum(1 for r in results if 'SKIP' in str(r.get('status') or '').upper())
    if failed is None:
        failed = sum(1 for r in results if 'FAIL' in str(r.get('status') or '').upper())

    return applied or 0, skipped or 0, failed or 0


def _status(run):
    applied, skipped, failed = _counts(run)
    if failed:
        return 'RUN FAILED'
    if skipped:
        return 'RUN PARTIAL'
    if applied:
        return 'RUN CLEAN'
    return 'RUN'


def _result_text(result):
    result = result or {}
    for key in ('preview', 'stdout', 'output', 'text'):
        value = result.get(key)
        if value:
            return str(value)
    return str(result.get('message') or '')


def _is_stack_mode(context):
    return bool(isinstance(context, dict) and context.get('stack_mode'))


def _compact_stack_header(title, subtitle=''):
    title = str(title or 'Page').strip()
    subtitle = str(subtitle or '').strip()
    label = title
    if subtitle:
        label += ' · ' + subtitle
    print('')
    print('──────── %s ────────' % label)


def _doc_helpers():
    try:
        from forge_core.surface.render.docpage import doc_hero, doc_text, doc_output, doc_tile_grid, doc_actions
        return doc_hero, doc_text, doc_output, doc_tile_grid, doc_actions
    except Exception:
        return None, None, None, None, None


def _tile_dock(title, tiles):
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
        render_tile_dock(title, tiles, cols=2, col_width=18, row_gap=1, leading_space=1, trailing_space=1)
        return True
    except Exception:
        print('')
        print(title)
        _rule()
        for icon, label, subtitle, _route, _tone in tiles:
            print('- %s%s  %s' % (icon, label, subtitle))
        return False


def render_page_grid(stack_pages, stamp='latest', current_id=None, title='Run pages'):
    pages = []
    for p in stack_pages or []:
        if not isinstance(p, dict):
            continue
        if current_id and p.get('id') == current_id:
            continue
        if p.get('promote') is False and not str(p.get('id') or '').startswith(('op.list', 'packet.raw')):
            continue
        pages.append(p)

    if not pages:
        return False

    tiles = []
    for p in pages:
        page_id = p.get('id') or ''
        card = p.get('card') or {}
        icon = p.get('emoji') or card.get('icon') or '▣'
        label = p.get('short') or card.get('title') or p.get('title') or page_id or 'Page'
        subtitle = card.get('subtitle') or p.get('kind') or 'page'
        tone = p.get('tone') or card.get('tone') or 'muted'
        route = card.get('route') or ('run_page', stamp, page_id)
        tiles.append((str(icon) + ' ', str(label), str(subtitle), route, tone))

    return _tile_dock(title, tiles)


def render_home_controls(run, stamp, pages=None):
    failed = _counts(run)[2]
    tiles = []

    if failed:
        tiles.append(('❌ ', 'Issue', 'copy failure', ('copy_failure', stamp), 'danger'))

    tiles.append(('◎ ', 'Runs', 'history', ('runs',), 'accent'))
    seen = set()

    def add_page_tile(p, subtitle=None):
        if not isinstance(p, dict):
            return
        page_id = str(p.get('id') or '')
        if not page_id or page_id in seen or page_id == 'run.home':
            return
        if page_id.startswith('op.detail.'):
            return
        if p.get('promote') is False and page_id not in ('op.list', 'packet.raw'):
            return

        card = p.get('card') or {}
        icon = p.get('emoji') or card.get('icon') or '▣'
        label = p.get('short') or card.get('title') or p.get('title') or 'Page'
        tone = p.get('tone') or card.get('tone') or 'muted'
        route = card.get('route') or ('run_page', stamp, page_id)
        tiles.append((str(icon) + ' ', str(label), str(subtitle or card.get('subtitle') or p.get('kind') or 'page'), route, tone))
        seen.add(page_id)

    for p in pages or []:
        if isinstance(p, dict) and p.get('id') == 'op.list':
            add_page_tile(p, 'op list')

    for p in pages or []:
        add_page_tile(p)

    tiles.append(('🏠 ', 'Home', 'workbench', ('home',), 'success'))
    _tile_dock('run controls', tiles)


def render_run_hero(run):
    """Old-LinkOS-style run hero."""
    run = run or {}
    stamp = run.get('stamp') or 'latest'
    applied, skipped, failed = _counts(run)
    title = _status(run)
    surface = run.get('surface') or {}
    focus = str(surface.get('focus') or '').strip()

    tone = 'success'
    if failed:
        tone = 'danger'
    elif skipped:
        tone = 'warning'

    def center(text, width=46):
        text = str(text or '')
        if len(text) >= width:
            return text
        left = (width - len(text)) // 2
        return (' ' * left) + text

    def spaced(text):
        return ' '.join(str(text or '').upper())

    try:
        from forge_core.surface.render.primitives import colour, reset, spacer
    except Exception:
        colour = reset = None
        spacer = lambda n=1: [print('') for _ in range(n)]

    spacer()

    if colour:
        colour('border')
    print('═' * 46)
    reset and reset()

    print('')

    if colour:
        colour(tone)
    print(center(spaced(title), 46))
    reset and reset()

    print('')

    if colour:
        colour('muted')
    print(center(stamp, 46))
    reset and reset()

    if focus:
        print('')
        if colour:
            colour('muted')
        print(center('focus: ' + focus, 46))
        reset and reset()

    print('')

    if colour:
        colour('border')
    print('═' * 46)
    reset and reset()

    return True


def _summary_sentence(run):
    applied, skipped, failed = _counts(run)
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


def _recommendation(run):
    status = str((run or {}).get('status') or '').upper()
    if status == 'APPLIED':
        return '🧠 Summary enough'
    if status == 'FAILED_PARSE':
        return '❌ Send parse error'
    if status == 'FAILED':
        return '❌ Send issue detail'
    return '📋 Send packet'


def render_run_summary_block(run, stamp):
    """Render the old LinkOS-style run summary between hero and controls."""
    run = run or {}
    applied, skipped, failed = _counts(run)

    try:
        from forge_core.surface.render.primitives import colour, reset, spacer
        from forge_core.surface.render.pills import pill_link
    except Exception:
        colour = reset = None
        spacer = lambda n=1: [print('') for _ in range(n)]
        pill_link = None

    def say_line(text, tone='text', indent='   '):
        if colour:
            colour(tone)
        print(indent + str(text))
        if reset:
            reset()

    def wrapped(text, width=37):
        words = str(text or '').split()
        rows = []
        cur = ''
        for word in words:
            if not cur:
                cur = word
            elif len(cur) + 1 + len(word) <= width:
                cur += ' ' + word
            else:
                rows.append(cur)
                cur = word
        if cur:
            rows.append(cur)
        return rows or ['']

    spacer()
    for row in wrapped(_summary_sentence(run), 37):
        say_line(row, 'text')

    spacer()
    say_line('Outcome', 'muted')

    values = [
        ('applied', applied, 'success'),
        ('skipped', skipped, 'warning'),
        ('failed', failed, 'danger'),
    ]
    max_value = max([v for _label, v, _tone in values] + [1])
    bar_width = 22

    for label, value, tone in values:
        if value > 0:
            filled = max(1, int(round((float(value) / float(max_value)) * bar_width)))
        else:
            filled = 0
        empty = max(0, bar_width - filled)
        bar = ('█' * filled) + ('░' * empty)
        say_line('%-8s  %s  %s' % (label, bar, value), tone)

    spacer()
    packet = str(run.get('packet') or '')
    if packet:
        say_line('packet: %s chars' % len(packet), 'muted', indent='           ')

    spacer()
    say_line(_recommendation(run), 'success' if not failed else 'danger', indent='           ')

    spacer()
    if pill_link:
        print('   ', end='')
        pill_link('Copy packet', 'copy_packet', stamp, tone='warning', icon='📋 ')
        print('      ', end='')
        pill_link('AI handoff', 'continue_ai', stamp, tone='success', icon='🤖 ')
        print('')
    else:
        print('   📋 Copy packet      🤖 AI handoff')

def render_list_ops_page(page, context=None):
    data = (page or {}).get('data') or {}
    result = data.get('result') or {}
    text = _result_text(result)
    mode = data.get('mode') or 'Ops'
    doc_hero, _doc_text, _doc_output, _doc_tile_grid, _doc_actions = _doc_helpers()

    catalog_title = 'Catalog' if mode == 'Ops' else ('%s Catalog' % mode)

    if _is_stack_mode(context):
        _compact_stack_header(catalog_title, 'commands')
    elif doc_hero:
        doc_hero(catalog_title, 'Forge command catalog')
    else:
        _rule()
        print(str(catalog_title).upper())
        _rule()

    count = 0
    spacer()
    if pill_link:
        print('   ', end='')
        pill_link('Copy packet', 'copy_packet', stamp, tone='warning', icon='📋 ')
        print('      ', end='')
        pill_link('AI handoff', 'continue_ai', stamp, tone='success', icon='🤖 ')
        print('')
    else:
        print('   📋 Copy packet      🤖 AI handoff')

def render_run_home_page(page, context=None):
    context = context or {}
    run = ((page or {}).get('data') or {}).get('run') or context.get('run') or {}
    pages = context.get('page_stack') or []
    stamp = run.get('stamp') or context.get('run_stamp') or 'latest'

    plan = context.get('surface_plan') or {}
    if plan.get('controlled'):
        nav_pages = plan.get('nav_pages') or pages
    else:
        nav_pages = pages

    # The run home page has two useful roles:
    # 1. Content page: run hero + run summary.
    # 2. Navigation dock: bottom controls only.
    #
    # SURFACE-controlled runs can now render summary/audit as selectable
    # content pages, while still keeping controls available at the bottom.
    if context.get('controls_only') or context.get('navigation_only'):
        render_home_controls(run, stamp, nav_pages)
        return

    render_run_hero(run)
    render_run_summary_block(run, stamp)

    if not context.get('content_only') and not context.get('stack_mode'):
        render_home_controls(run, stamp, nav_pages)

def render_list_ops_page(page, context=None):
    data = (page or {}).get('data') or {}
    result = data.get('result') or {}
    text = _result_text(result)
    mode = data.get('mode') or 'Ops'
    doc_hero, _doc_text, _doc_output, _doc_tile_grid, _doc_actions = _doc_helpers()

    ops_title = 'Ops' if mode == 'Ops' else ('%s Ops' % mode)

    if _is_stack_mode(context):
        _compact_stack_header(ops_title, 'catalog')
    elif doc_hero:
        doc_hero(ops_title, 'Forge command catalog')
    else:
        _rule()
        print(str(ops_title).upper())
        _rule()

    count = 0
    for raw in str(text or '').splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith('==='):
            continue
        if not stripped.startswith('- '):
            print('')
            print('   ' + stripped.upper())
            print('   ' + '═' * 30)
            continue
        body = stripped[2:].strip()
        parts = body.split(None, 1)
        op = parts[0].strip() if parts else ''
        desc = parts[1].strip() if len(parts) > 1 else ''
        if not op:
            continue
        count += 1
        print('')
        print('   ⚙  ' + op)
        if desc:
            print('      ' + desc[:88])

    print('')
    print('   %d op%s listed' % (count, '' if count == 1 else 's'))


def render_list_files_page(page, context=None):
    data = (page or {}).get('data') or {}
    result = data.get('result') or {}
    text = data.get('text') or _result_text(result)
    target = data.get('target') or result.get('file') or result.get('target') or '.'
    doc_hero, doc_text, doc_output, _doc_tile_grid, _doc_actions = _doc_helpers()

    if _is_stack_mode(context):
        _compact_stack_header('Files', target)
    elif doc_hero:
        doc_hero('Files', target)
    else:
        _rule()
        print('FILES')
        print(target)
        _rule()

    lines = str(text or '').splitlines()
    if doc_output:
        doc_output(lines, tone='text', max_lines=80)
    else:
        for line in lines[:80]:
            print(line)

    if doc_text and len(lines) > 80:
        doc_text('Output truncated to 80 lines in this minimal reboot renderer.', tone='muted')


def _status_emoji(result):
    status = str((result or {}).get('status') or '').upper()
    if 'FAIL' in status:
        return '❌'
    if 'SKIP' in status:
        return '⚠️'
    return '✅'


def _status_tone(result):
    status = str((result or {}).get('status') or '').upper()
    if 'FAIL' in status:
        return 'danger'
    if 'SKIP' in status:
        return 'warning'
    return 'success'


def _fit_line(text, budget=50):
    text = str(text or '').strip()
    if len(text) <= budget:
        return text
    cut = text[:budget].rsplit(' ', 1)[0]
    if len(cut) < budget - 12:
        cut = text[:budget]
    return cut.rstrip(' ,;:·') + '…'


def _audit_meta(result):
    result = result or {}
    status = str(result.get('status') or '').upper()
    target = str(result.get('target') or result.get('file') or '').strip()
    if target in ('?', 'None', 'null'):
        target = ''

    message = str(result.get('message') or '').strip()
    first_line = message.split('\n', 1)[0] if message else ''
    detail = target or first_line

    if 'FAIL' in status or 'SKIP' in status:
        if detail:
            return '%s · %s' % (status, _fit_line(detail, 46))
        return status

    return _fit_line(detail, 50) if detail else ''


def render_audit_page(page, context=None):
    """Render the run audit trail as scannable op action cards.

    Audit is the launch pad for run actions:
    - identify what happened
    - show the acted-on target
    - show packet/output weight
    - offer concrete per-op actions

    Important console UX rule:
    - when rendered inside a stack, audit is content only
    - stack/landing owns the final controls
    - standalone audit still gets its own controls
    """
    import textwrap

    data = (page or {}).get('data') or {}
    context = context or {}
    run = data.get('run') or (context.get('run') if isinstance(context, dict) else {}) or {}
    results = list((run or {}).get('results') or [])
    stamp = data.get('stamp') or run.get('stamp') or context.get('run_stamp') or 'latest'

    try:
        from forge_core.surface.render.docpage import doc_hero, doc_text
        from forge_core.surface.render.pills import pill_link
        from forge_core.surface.render.primitives import colour, reset, say
    except Exception:
        doc_hero = None
        doc_text = None
        pill_link = None
        colour = reset = None
        say = None

    WIDTH = 40
    INNER = WIDTH - 4

    def say_line(text, tone='text'):
        if say:
            say(str(text), tone=tone)
        else:
            print(str(text))

    def use_colour(tone):
        if colour:
            colour(tone)

    def clear_colour():
        if reset:
            reset()

    def status_short(result):
        status = str((result or {}).get('status') or '').upper()
        if status == 'APPLIED':
            return 'OK'
        if 'FAIL' in status:
            return 'FAIL'
        if 'SKIP' in status:
            return 'SKIP'
        return status[:8] if status else '?'

    def tone_for_result(result):
        status = str((result or {}).get('status') or '').upper()
        if 'FAIL' in status:
            return 'audit.card.fail'
        if 'SKIP' in status:
            return 'audit.card.skip'
        return 'audit.card.border'

    def wrap_text(text, width):
        return textwrap.wrap(str(text or ''), width=width) or ['']

    def result_text(result):
        result = result or {}
        parts = []
        op = str(result.get('op') or 'OP').upper()
        status = str(result.get('status') or '?').upper()
        target = str(result.get('target') or result.get('file') or '').strip()

        parts.append('%s | %s' % (op, status))
        if target and target not in ('?', 'None', 'null'):
            parts.append('target: %s' % target)

        message = str(result.get('message') or '').strip()
        if message:
            parts.append('message: %s' % message)

        for key in ('preview', 'stdout', 'stderr', 'output', 'text'):
            value = result.get(key)
            if value:
                parts.append('')
                parts.append(key.upper())
                parts.append(str(value).rstrip())

        return '\n'.join(parts).strip()

    def packet_chars(result):
        return len(result_text(result))

    def fmt_chars(n):
        try:
            n = int(n)
        except Exception:
            n = 0
        return format(n, ',')

    def clean_target(result):
        result = result or {}
        target = str(result.get('target') or result.get('file') or '').strip()
        if target in ('?', 'None', 'null'):
            target = ''
        if not target:
            target = _audit_meta(result) or 'no target'
        return target

    def editor_path(target):
        target = str(target or '').strip()
        if not target:
            return ''

        # Strip AST suffixes such as file.py::function_name.
        if '::' in target:
            target = target.split('::', 1)[0].strip()

        # Strip obvious command/query tails from SEARCH-style targets.
        if ' FOR ' in target:
            target = target.split(' FOR ', 1)[0].strip()

        if target.endswith('.py') and ' ' not in target:
            return target
        return ''

    def box_top(tone):
        frame = 'audit.card.border' if tone == 'audit.card.border' else tone
        use_colour(frame)
        print('╭' + '─' * (WIDTH - 2) + '╮')
        clear_colour()

    def box_mid(tone):
        frame = 'audit.card.border' if tone == 'audit.card.border' else tone
        use_colour(frame)
        print('├' + '─' * (WIDTH - 2) + '┤')
        clear_colour()

    def box_bottom(tone):
        frame = 'audit.card.border' if tone == 'audit.card.border' else tone
        use_colour(frame)
        print('╰' + '─' * (WIDTH - 2) + '╯')
        clear_colour()

    def box_line(text='', tone='text', frame_tone='audit.card.border'):
        text = str(text or '')
        if len(text) > INNER:
            text = text[:INNER]

        use_colour(frame_tone)
        print('│ ', end='')
        clear_colour()

        use_colour(tone)
        print(text.ljust(INNER), end='')
        clear_colour()

        use_colour(frame_tone)
        print(' │')
        clear_colour()

    def action_link(label, icon, route_parts, tone):
        if pill_link:
            pill_link(label, *route_parts, tone=tone, icon=icon)
        else:
            use_colour(tone)
            print(icon + label, end='')
            clear_colour()

    def action_row(index, result, target, tone, back_target):
        text = result_text(result)
        path = editor_path(target)

        print('', end='')
        action_link('DETAIL', '🔎 ', ('run_page', stamp, 'op.detail.%d' % index, back_target), 'action.detail')

        if path:
            print('   ', end='')
            action_link('EDIT', '✏️ ', ('open_pythonista', path, stamp, back_target), 'action.edit')

        if text:
            print('   ', end='')
            action_link('COPY', '📋 ', ('copy_text', 'op-%02d' % (index + 1), text), 'action.copy')

        print('')

    def render_card(index, result, back_target):
        result = result or {}
        op = str(result.get('op') or 'OP').upper()
        status = status_short(result)
        tone = tone_for_result(result)
        target = clean_target(result)

        msg = str(result.get('message') or '').strip().split('\n')[0]
        meta = _audit_meta(result)
        note = msg or meta or status.lower()

        print('')
        box_top(tone)

        header = '#%02d  %-13s %9s' % (index + 1, op, status)
        box_line(header, 'audit.op' if status == 'OK' else tone)
        box_mid(tone)

        target_rows = wrap_text(target, INNER - 8)
        for i, part in enumerate(target_rows):
            prefix = 'target: ' if i == 0 else '        '
            box_line(prefix + part, 'audit.target')

        note_rows = wrap_text(note, INNER - 8)
        for i, part in enumerate(note_rows):
            prefix = 'note:   ' if i == 0 else '        '
            box_line(prefix + part, 'audit.note')

        box_line('pkt:    %s chars' % fmt_chars(packet_chars(result)), 'audit.packet')

        box_bottom(tone)
        action_row(index, result, target, tone, back_target)

    stack_mode = _is_stack_mode(context)

    if stack_mode:
        back_target = 'landing'
        _compact_stack_header('Audit Trail', '%d op%s' % (len(results), '' if len(results) == 1 else 's'))
    else:
        back_target = 'run.audit'
        applied, skipped, failed = _counts(run)
        if doc_hero:
            doc_hero('AUDIT TRAIL', '%s · %d ok · %d skip · %d fail' % (stamp, applied, skipped, failed))
        else:
            _rule()
            print('AUDIT TRAIL')
            print('%s · %d ok · %d skip · %d fail' % (stamp, applied, skipped, failed))
            _rule()

    if not results:
        if doc_text:
            doc_text('No ops recorded in this run.', tone='muted')
        else:
            print('   No ops recorded in this run.')
        return

    for i, result in enumerate(results):
        render_card(i, result, back_target)

    if stack_mode:
        return

    try:
        from forge_core.surface.actions import copy_packet, home, raw, runs, tile
        tiles = [
            tile('Runs', runs(), icon='◎ ', subtitle='history', tone='accent'),
            tile('Raw', raw(stamp), icon='📦 ', subtitle='packet', tone='warning'),
            tile('Copy', copy_packet(stamp), icon='📋 ', subtitle='packet', tone='warning'),
            tile('Home', home(), icon='🏠 ', subtitle='workbench', tone='success'),
        ]
    except Exception:
        tiles = [
            ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
            ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
            ('📋 ', 'Copy', 'packet', ('copy_packet', stamp), 'warning'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ]

    _tile_dock('Controls', tiles)

def render_ops_page(page, context=None):
    run = ((page or {}).get('data') or {}).get('run') or {}
    results = run.get('results') or []
    stamp = run.get('stamp') or 'latest'
    doc_hero, _doc_text, _doc_output, _doc_tile_grid, _doc_actions = _doc_helpers()

    if _is_stack_mode(context):
        _compact_stack_header('Ops', stamp)
    elif doc_hero:
        doc_hero('Ops', stamp)
    else:
        _rule()
        print('OPS')
        print(stamp)
        _rule()

    if not results:
        print('   No ops recorded.')
        return

    for i, r in enumerate(results, 1):
        status = str(r.get('status') or '?')
        op = str(r.get('op') or '?').upper()
        target = str(r.get('target') or r.get('file') or '').strip()
        msg = str(r.get('message') or '').strip().split('\n')[0]
        print('')
        print('   %02d  %s  %s' % (i, status, op))
        if target and target not in ('?', 'None', 'null'):
            print('       ' + target[:72])
        if msg:
            print('       ' + msg[:88])


def render_file_view_page(page, context=None):
    """Render a first-class file/object surface for a project-relative path."""
    import os

    data = (page or {}).get('data') or {}
    context = context or {}
    params = context.get('params') or {}
    run = data.get('run') or {}
    stamp = run.get('stamp') or data.get('stamp') or context.get('run_stamp') or 'latest'
    path = str(params.get('path') or data.get('path') or '').strip()

    root = str(run.get('project_root') or os.getcwd())
    abs_path = path if os.path.isabs(path) else os.path.join(root, path)
    if not os.path.exists(abs_path) and os.path.exists(path):
        abs_path = path

    doc_hero, doc_text, _doc_output, _doc_tile_grid, _doc_actions = _doc_helpers()

    if doc_hero:
        doc_hero('FILE', path or 'no path')
    else:
        _rule()
        print('FILE')
        print(path or 'no path')
        _rule()

    def say_line(text, tone='text'):
        try:
            from forge_core.surface.render.primitives import say
            say(str(text), tone=tone)
        except Exception:
            print(str(text))

    def section(title, icon='▣'):
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

    def wrapped(prefix, text, width=31, tone='text'):
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
                say_line((prefix if first else ' ' * len(prefix)) + line, tone)
                first = False
            line = word
        if line:
            say_line((prefix if first else ' ' * len(prefix)) + line, tone)

    def stat_bar(label, value, max_value, tone='accent'):
        try:
            value = int(value or 0)
        except Exception:
            value = 0
        max_value = max(int(max_value or 1), 1)
        filled = max(1, int(round((float(value) / float(max_value)) * 14))) if value else 0
        glyphs = ('█' * filled) + ('░' * max(0, 14 - filled))
        say_line('   %-8s %s  %s' % (label, glyphs, value), tone if value else 'muted')

    if not path:
        if doc_text:
            doc_text('No path was supplied to file.view.', tone='warning')
        else:
            print('No path was supplied to file.view.')
        return

    exists = os.path.exists(abs_path)
    is_dir = os.path.isdir(abs_path)
    is_file = os.path.isfile(abs_path)

    section('Overview', icon='◆')
    wrapped('   path: ', path, width=31)
    say_line('   exists: %s' % ('yes' if exists else 'no'), 'success' if exists else 'danger')
    say_line('   kind: %s' % ('directory' if is_dir else ('file' if is_file else 'unknown')), 'text')

    parent = os.path.dirname(path) or '.'
    wrapped('   parent: ', parent, width=31, tone='muted')

    text = ''
    lines = []
    ext = os.path.splitext(path)[1].lower()

    if exists and is_file:
        try:
            size = os.path.getsize(abs_path)
            say_line('   size: %d bytes' % size, 'muted')
        except Exception:
            pass

        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            lines = text.splitlines()
            say_line('   lines: %d' % len(lines), 'muted')
        except Exception as e:
            say_line('   read: %s: %s' % (type(e).__name__, e), 'danger')

    if exists and is_file and text:
        funcs = 0
        classes = 0
        imports = 0

        if ext == '.py':
            try:
                import ast
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        funcs += 1
                    elif isinstance(node, ast.ClassDef):
                        classes += 1
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        imports += 1
            except Exception:
                pass

        section('Shape', icon='▥')
        say_line('   lines: %d source line%s' % (len(lines), '' if len(lines) == 1 else 's'), 'accent')
        if ext == '.py':
            max_structure = max(funcs, classes, imports, 1)
            say_line('   structure:', 'muted')
            stat_bar('funcs', funcs, max_structure, tone='success')
            stat_bar('classes', classes, max_structure, tone='warning')
            stat_bar('imports', imports, max_structure, tone='muted')

        section('Preview', icon='👁')
        preview = lines[:18]
        try:
            from forge_core.surface.render.console_code import render_code_lines
            render_code_lines(preview, max_lines=18, indent='   ')
        except Exception:
            for line in preview:
                print('   ' + str(line))
        if len(lines) > len(preview):
            say_line('   ... %d more line(s) ...' % (len(lines) - len(preview)), 'muted')

    elif exists and is_dir:
        section('Directory', icon='📁')
        try:
            names = sorted(os.listdir(abs_path))
        except Exception:
            names = []

        dirs = 0
        files = 0
        for name in names:
            full = os.path.join(abs_path, name)
            if os.path.isdir(full):
                dirs += 1
            elif os.path.isfile(full):
                files += 1

        max_value = max(dirs, files, 1)
        stat_bar('dirs', dirs, max_value, tone='accent')
        stat_bar('files', files, max_value, tone='success')

        for name in names[:12]:
            full = os.path.join(abs_path, name)
            icon = '📁' if os.path.isdir(full) else '📄'
            say_line('   %s %s' % (icon, name), 'text')
        if len(names) > 12:
            say_line('   ... %d more item(s) ...' % (len(names) - 12), 'muted')

    try:
        from forge_core.surface.actions import copy_path, home, open_editor, read_again, raw, runs, tile
        tiles = [
            tile('Read', read_again(path), icon='📄 ', subtitle='open text', tone='accent'),
            tile('Editor', open_editor(path), icon='🐍 ', subtitle='Pythonista', tone='success'),
            tile('Copy path', copy_path(path), icon='📋 ', subtitle='clipboard', tone='warning'),
            tile('Raw', raw(stamp), icon='📦 ', subtitle='packet', tone='warning'),
            tile('Runs', runs(), icon='◎ ', subtitle='history', tone='accent'),
            tile('Home', home(), icon='🏠 ', subtitle='workbench', tone='success'),
        ]
        if is_dir:
            tiles[0] = tile('List', ('run_bundle', 'LIST_FILES %s\nDEPTH: 2\nFILES: yes' % path), icon='📁 ', subtitle='directory', tone='accent')
    except Exception:
        tiles = [
            ('📄 ', 'Read', 'open text', ('run_bundle', 'READ %s' % path), 'accent'),
            ('🐍 ', 'Editor', 'Pythonista', ('open_pythonista', path), 'success'),
            ('📋 ', 'Copy path', 'clipboard', ('copy_path', path), 'warning'),
            ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
            ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ]

    _tile_dock('Controls', tiles)
def render_op_detail_page(page, context=None):
    data = (page or {}).get('data') or {}
    context = context or {}
    run = data.get('run') or {}
    idx = int(data.get('index') or 0)
    results = run.get('results') or []
    stamp = run.get('stamp') or data.get('stamp') or context.get('run_stamp') or 'latest'

    try:
        result = results[idx]
    except Exception:
        result = data.get('result') or {}

    op = str(result.get('op') or 'OP').upper()

    # Try op-owned render_detail first. Falls through on any failure
    # so a buggy provider can never break the audit→detail route.
    try:
        from forge_core.surface.providers import load_provider
        provider = load_provider(run, op)
        if provider is not None:
            custom = getattr(provider, 'render_detail', None)
            if callable(custom):
                try:
                    custom(page, context)
                    return
                except Exception as e:
                    print('[render_detail failed for %s: %s: %s]' % (op, type(e).__name__, e))
    except Exception:
        pass

    status = str(result.get('status') or 'unknown')

    # Context wins. Static page data is only a fallback.
    back_page = str(context.get('back_page') or data.get('back_page') or 'landing').strip()
    if not back_page:
        back_page = 'landing'

    if back_page in ('landing', 'default', 'home', 'run.home'):
        back_route = ('run', stamp)
        back_hint = 'landing'
    else:
        back_route = ('run_page', stamp, back_page)
        back_hint = 'previous page'

    doc_hero, _doc_text, doc_output, _doc_tile_grid, _doc_actions = _doc_helpers()

    if doc_hero:
        doc_hero(op, '%s · #%02d' % (status.lower(), idx + 1))
    else:
        _rule()
        print(op)
        print(status)
        _rule()

    rows = []
    for key in ('message', 'target', 'file'):
        if result.get(key):
            rows.append('%s: %s' % (key, result.get(key)))

    text = _result_text(result)
    if text:
        rows.append('')
        rows.extend(str(text).splitlines())

    if doc_output:
        doc_output(rows, tone='text', max_lines=None)
    else:
        for row in rows:
            print(row)

    tiles = [
        ('⬅️ ', 'Back', back_hint, back_route, 'warning'),
        ('📦 ', 'Raw', 'packet', ('run_page', stamp, 'packet.raw'), 'warning'),
        ('📋 ', 'Copy', 'packet', ('copy_packet', stamp), 'warning'),
        ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
    ]
    _tile_dock('controls', tiles)

def _run_doc_slugs(run):
    slugs = []

    def add(value):
        value = str(value or '').strip()
        if value and value not in slugs:
            slugs.append(value)

    def add_many(value):
        if not value:
            return
        if isinstance(value, str):
            for part in value.replace(',', ' ').split():
                add(part)
            return
        for item in value:
            if isinstance(item, dict):
                add(item.get('slug') or item.get('name') or item.get('id'))
            else:
                add(item)

    for result in (run or {}).get('results') or []:
        if str((result or {}).get('op') or '').upper() != 'DOCS':
            continue
        add_many(result.get('opened') or result.get('open'))
        add_many(result.get('suggested') or result.get('suggestions'))
        add_many(result.get('requested') or result.get('requests'))

        msg = str(result.get('message') or '')
        if 'suggested' in msg.lower():
            banned = set(['suggested', 'requested', 'docs', 'doc', 'and'])
            for token in msg.replace(',', ' ').replace(':', ' ').split():
                clean = token.strip().strip('.;')
                if clean and clean.lower() not in banned and clean.replace('-', '').replace('_', '').isalnum():
                    add(clean)

    if not slugs:
        add('the_loop')
        add('safe_patch')
        add('run_packet')

    return slugs[:8]


def render_run_docs_nav_page(page, context=None):
    data = (page or {}).get('data') or {}
    run = data.get('run') or ((context or {}).get('run') if isinstance(context, dict) else {}) or {}
    stamp = data.get('stamp') or run.get('stamp') or ((context or {}).get('run_stamp') if isinstance(context, dict) else 'latest')
    slugs = _run_doc_slugs(run)
    doc_hero, doc_text, _doc_output, _doc_tile_grid, _doc_actions = _doc_helpers()

    if _is_stack_mode(context):
        _compact_stack_header('Docs', 'run guidance')
    elif doc_hero:
        doc_hero('Docs', 'run guidance')
    else:
        _rule()
        print('DOCS')
        print(stamp)
        _rule()

    if doc_text and not _is_stack_mode(context):
        doc_text('Useful docs for understanding or continuing from this run.', tone='muted')

    tiles = [('📖 ', slug, 'guide', ('doc', slug), 'accent') for slug in slugs]
    tiles.append(('📚 ', 'Hub', 'all docs', ('docs',), 'border'))
    _tile_dock('docs', tiles)


def render_page_index_page(page, context=None):
    context = context or {}
    pages = context.get('page_stack') or []

    _rule()
    print('Page index')
    _rule()

    for i, p in enumerate(pages, 1):
        marker = '*' if (p or {}).get('id') == 'run.home' else ' '
        nav = (p.get('emoji') or '') + ' ' + (p.get('short') or p.get('title') or '')
        print('%s%02d. %-18s %-8s %-8s %-8s %s' % (
            marker,
            i,
            p.get('id') or '?',
            p.get('kind') or '?',
            p.get('mode') or '?',
            p.get('size') or '?',
            nav.strip(),
        ))


def render_raw_packet_page(page, context=None):
    run = ((page or {}).get('data') or {}).get('run') or {}
    stamp = run.get('stamp') or 'latest'
    doc_hero, _doc_text, doc_output, doc_tile_grid, _doc_actions = _doc_helpers()

    if doc_hero:
        doc_hero('Raw Packet', stamp)
    else:
        _rule()
        print('RAW PACKET')
        print(stamp)
        _rule()

    packet = run.get('packet') or ''
    if not packet:
        lines = ['=== FORGE RUN ===', 'Run: %s' % stamp, '', 'Ops:']
        for r in run.get('results') or []:
            lines.append('- %s | %s | %s :: %s' % (
                r.get('status') or '?',
                r.get('op') or '?',
                r.get('target') or r.get('file') or '?',
                r.get('message') or '',
            ))
        packet = '\n'.join(lines)

    if doc_tile_grid:
        doc_tile_grid('packet actions', [
            ('📋 ', 'Copy Packet', 'to clipboard', ('copy_packet', stamp), 'warning'),
        ])

    if doc_output:
        doc_output(packet.splitlines(), tone='text', max_lines=None)
    else:
        print(packet)

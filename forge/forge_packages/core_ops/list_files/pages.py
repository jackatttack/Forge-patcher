# -*- coding: utf-8 -*-
"""
Surface pages for LIST_FILES.

This is the reference implementation of the reboot op page contract.

Exports:
    pages_for_result(result, index, run) -> list[page]
        Inline result card shown in the run stack (replaces the old
        core-built files.tree.N page).

    render_detail(page, context) -> None
        Full detail surface reached by tapping the op in run audit.
        Information-dense tree with depth and filter pills.

See docs/OP_DEVELOPMENT.txt for the full contract.
"""

from forge_core.surface.model import page


# Truncate caps. Override per-page via expand=1 param.
INLINE_TREE_LIMIT = 10
DETAIL_TREE_LIMIT = 50
DEPTH_OPTIONS = [1, 2, 3, 4]
FILTER_TOP_N = 4


# -- public providers -------------------------------------------------------

def pages_for_result(result, index, run):
    data = result.get('data') or {}
    path = data.get('path') or result.get('target') or '.'
    meta = data.get('meta') or {}

    status = str(result.get('status') or '').upper()
    tone = 'accent' if status == 'APPLIED' else 'danger'

    subtitle = '%d dirs · %d files · depth %d' % (
        int(meta.get('dirs') or 0),
        int(meta.get('files') or 0),
        int(meta.get('depth') or 1),
    )

    return [page(
        'files.tree.%N',
        'Files: %s' % path,
        kind='files',
        icon='▥',
        short='Files',
        tone=tone,
        mode='dense',
        size='full',
        source='op:LIST_FILES',
        priority=75,
        data={
            'result': result,
            'result_index': index,
            'path': path,
            'subtitle': subtitle,
            'tree': data.get('tree') or [],
            'lines': data.get('lines') or [],
            'meta': meta,
        },
    )]


def render_detail(page, context=None):
    """Full LIST_FILES detail surface as a visual directory dashboard."""
    context = context or {}
    params = context.get('params') or {}

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
    meta = result_data.get('meta') or {}
    tree = result_data.get('tree') or []
    path = result_data.get('path') or result.get('target') or '.'
    status = str(result.get('status') or 'unknown')

    captured_depth = int(meta.get('depth') or 1)
    active_depth = _safe_int(params.get('depth'), captured_depth)
    active_filter = (params.get('filter') or '').strip()
    expanded = params.get('expand') in ('1', 'yes', 'true')

    page_id = 'op.detail.%d' % idx

    try:
        from forge_core.surface.render.docpage import doc_hero
    except Exception:
        doc_hero = None
    try:
        from forge_core.surface.render.primitives import say, colour, reset, spacer
    except Exception:
        say = None
        colour = reset = None
        spacer = None
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
    except Exception:
        render_tile_dock = None

    def say_line(text, tone='text'):
        if say:
            say(str(text), tone=tone)
        else:
            print(str(text))

    def section(title, icon='▣'):
        print('')
        if colour:
            colour('warning')
        print('  ' + '═' * 36)
        print('   %s  %s' % (icon, str(title or '').upper()))
        print('  ' + '─' * 36)
        if reset:
            reset()

    def wrapped(prefix, text, width=30, tone='text'):
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

    def bar(label, value, max_value, tone='accent', width=18):
        try:
            value = int(value or 0)
        except Exception:
            value = 0
        max_value = max(int(max_value or 1), 1)
        filled = max(1, int(round((float(value) / float(max_value)) * width))) if value else 0
        glyphs = ('█' * filled) + ('░' * max(0, width - filled))
        say_line('   %-7s %s  %s' % (label, glyphs, value), tone if value else 'muted')

    def badge(label, yes, true_tone='success'):
        icon = '✅' if yes else '·'
        tone = true_tone if yes else 'muted'
        say_line('   %s %s' % (icon, label), tone)

    dirs = int(meta.get('dirs') or 0)
    files = int(meta.get('files') or 0)
    readme = bool(meta.get('readme'))
    docs = bool(meta.get('docs'))

    if doc_hero:
        doc_hero('LIST_FILES', '%s · %s · #%02d' % (path, status.lower(), idx + 1))
    else:
        print('')
        print('LIST_FILES')
        print('%s · %s · #%02d' % (path, status.lower(), idx + 1))

    section('Overview', icon='◆')
    wrapped('   path: ', path, width=30)
    say_line('   status: %s' % status.lower(), 'success' if status.upper() == 'APPLIED' else 'danger')
    say_line('   depth: %d captured / %d active' % (captured_depth, active_depth), 'muted')
    if active_filter:
        say_line('   filter: %s' % active_filter, 'accent')

    section('Directory shape', icon='▥')
    max_shape = max(dirs, files, 1)
    bar('dirs', dirs, max_shape, tone='accent')
    bar('files', files, max_shape, tone='success')

    section('Signals', icon='◇')
    badge('README present', readme, true_tone='success')
    badge('docs/docstrings present', docs, true_tone='accent')

    extensions = _top_extensions(tree, FILTER_TOP_N)
    if extensions:
        section('File mix', icon='▤')
        max_ext = max([count for _ext, count in extensions] + [1])
        for ext, count in extensions:
            label = ext or '(none)'
            bar(label[:7], count, max_ext, tone='accent', width=16)

    visible = _filter_tree(tree, active_depth, active_filter)
    truncated = False
    if not expanded and len(visible) > DETAIL_TREE_LIMIT:
        shown = visible[:DETAIL_TREE_LIMIT]
        truncated = True
    else:
        shown = visible

    section('Tree map', icon='🌲')
    say_line('   showing %d of %d entr%s' % (
        len(shown),
        len(visible),
        'y' if len(visible) == 1 else 'ies',
    ), 'muted')

    if not shown:
        say_line('   (no entries match)', tone='muted')
    else:
        for node in shown:
            _print_node_styled(node, say)

    if truncated:
        say_line('   … %d more' % (len(visible) - DETAIL_TREE_LIMIT), tone='muted')
        if render_tile_dock:
            render_tile_dock('Expand', [
                ('⤢ ', 'Expand all', 'show full tree', ('run_page', stamp, page_id, 'expand=1'), 'accent'),
            ], cols=1, col_width=30, leading_space=1, trailing_space=0)

    depth_tiles = []
    for d in DEPTH_OPTIONS:
        tone = 'success' if d == active_depth else 'accent'
        subtitle = 'active' if d == active_depth else ('captured' if d <= captured_depth else 'rerun')
        depth_tiles.append((
            '',
            str(d),
            subtitle,
            ('run_page', stamp, page_id, 'depth=%d' % d),
            tone,
        ))
    if render_tile_dock and depth_tiles:
        render_tile_dock('Depth', depth_tiles, cols=4, col_width=8, leading_space=1, trailing_space=0)

    if extensions and render_tile_dock:
        all_tone = 'success' if not active_filter else 'accent'
        filter_tiles = [('', 'all', '%d files' % sum(c for _, c in extensions),
                         ('run_page', stamp, page_id), all_tone)]
        for ext, count in extensions:
            tone = 'success' if ext == active_filter else 'accent'
            filter_tiles.append((
                '',
                ext,
                '%d' % count,
                ('run_page', stamp, page_id, 'filter=%s' % ext),
                tone,
            ))
        render_tile_dock('Filter', filter_tiles, cols=5, col_width=8, leading_space=1, trailing_space=0)

    back_page = (context.get('back_page') or data.get('back_page') or 'run.audit').strip() or 'run.audit'
    if back_page in ('landing', 'default', 'home', 'run.home'):
        back_route = ('run', stamp)
    else:
        back_route = ('run_page', stamp, back_page)

    try:
        from forge_core.surface.actions import (
            back, copy_packet, file_page, home, op_readme, raw, runs, tile,
        )
        back_label = str(back_page or 'audit').replace('run.', '').replace('op.', '')
        tiles = [
            tile('Back', back(context, stamp), icon='⬅️ ', subtitle=back_label, tone='warning'),
            tile('File', file_page(path, stamp), icon='📁 ', subtitle='inspect', tone='accent'),
            tile('Raw', raw(stamp), icon='📦 ', subtitle='packet', tone='warning'),
            tile('Copy', copy_packet(stamp), icon='📋 ', subtitle='packet', tone='warning'),
            tile('README', op_readme(stamp, 'list_files'), icon='📖 ', subtitle='list_files', tone='accent'),
            tile('Runs', runs(), icon='◎ ', subtitle='history', tone='accent'),
            tile('Home', home(), icon='🏠 ', subtitle='workbench', tone='success'),
        ]
    except Exception:
        tiles = [
            ('⬅️ ', 'Back',   'audit',      back_route,                                    'warning'),
            ('📁 ', 'File',   'inspect',    ('run_page', stamp, 'file.view', 'path=' + path), 'accent'),
            ('📦 ', 'Raw',    'packet',     ('run_page', stamp, 'packet.raw'),             'warning'),
            ('📋 ', 'Copy',   'packet',     ('copy_packet', stamp),                        'warning'),
            ('📖 ', 'README', 'list_files', ('run_page', stamp, 'op.readme', 'list_files'), 'accent'),
            ('◎ ', 'Runs',   'history',    ('runs',),                                     'accent'),
            ('🏠 ', 'Home',   'workbench',  ('home',),                                     'success'),
        ]

    if render_tile_dock:
        render_tile_dock('Controls', tiles, cols=2, col_width=18, leading_space=1, trailing_space=2)
    else:
        for icon, label, _subtitle, _route, _tone in tiles:
            print('  %s%s' % (icon, label))

def _safe_int(value, default):
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _filter_tree(tree, max_depth, ext_filter):
    out = []
    for node in tree or []:
        level = int(node.get('level') or 0)
        if level >= max_depth:
            continue
        if ext_filter and node.get('kind') == 'file':
            if not str(node.get('name') or '').endswith(ext_filter):
                continue
        out.append(node)
    return out


def _top_extensions(tree, top_n):
    counts = {}
    for node in tree or []:
        if node.get('kind') != 'file':
            continue
        name = str(node.get('name') or '')
        dot = name.rfind('.')
        if dot <= 0:
            continue
        ext = name[dot:].lower()
        if not ext or len(ext) > 8:
            continue
        counts[ext] = counts.get(ext, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:top_n]


def _print_node(primitives, node):
    indent = '  ' * int(node.get('level') or 0)
    name = str(node.get('name') or '')
    if node.get('kind') == 'dir':
        line = indent + name + '/'
        _say(primitives, line, tone='accent')
        summary = node.get('summary')
        if summary:
            _say(primitives, indent + '  · ' + summary, tone='muted')
    else:
        size = node.get('size')
        if size is not None:
            line = indent + '%s (%d bytes)' % (name, size)
        else:
            line = indent + name
        _say(primitives, line, tone='text')
        doc = node.get('doc')
        if doc:
            _say(primitives, indent + '  · ' + doc, tone='muted')

def _print_node_styled(node, say):
    """Print a tree node with dir/file/summary tone hierarchy."""
    indent = '  ' * int(node.get('level') or 0)
    name = str(node.get('name') or '')

    if node.get('kind') == 'dir':
        line = indent + name + '/'
        if say:
            say(line, tone='accent')
        else:
            print(line)
        summary = node.get('summary')
        if summary:
            sub = indent + '  · ' + summary
            if say:
                say(sub, tone='muted')
            else:
                print(sub)
        return

    size = node.get('size')
    if size is not None:
        line = indent + '%s (%d bytes)' % (name, size)
    else:
        line = indent + name
    if say:
        say(line, tone='text')
    else:
        print(line)
    doc = node.get('doc')
    if doc:
        sub = indent + '  · ' + doc
        if say:
            say(sub, tone='muted')
        else:
            print(sub)


# -- primitive shims --------------------------------------------------------

def _load_primitives():
    out = {
        'doc_hero': None,
        'doc_section': None,
        'doc_text': None,
        'pill_rows': None,
        'tile_dock': None,
        'say': None,
        'colour': None,
        'reset': None,
    }
    try:
        from forge_core.surface.render.docpage import doc_hero, doc_section, doc_text
        out['doc_hero'] = doc_hero
        out['doc_section'] = doc_section
        out['doc_text'] = doc_text
    except Exception:
        pass
    try:
        from forge_core.surface.render.pills import pill_rows
        out['pill_rows'] = pill_rows
    except Exception:
        pass
    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
        out['tile_dock'] = render_tile_dock
    except Exception:
        pass
    try:
        from forge_core.surface.render.primitives import say, colour, reset
        out['say'] = say
        out['colour'] = colour
        out['reset'] = reset
    except Exception:
        pass
    return out


def _doc_section(primitives, title):
    if primitives['doc_section']:
        primitives['doc_section'](title)
    else:
        print('')
        print('-- %s --' % title)


def _say(primitives, text, tone=None):
    if primitives['say']:
        primitives['say'](text, tone=tone)
    else:
        print(text)


def _kv(primitives, key, value):
    _say(primitives, '  %-9s %s' % (key + ':', value), tone='text')


def _rule(width=42, char='─'):
    print(str(char) * int(width))


def _tile_dock(primitives, name, tiles):
    if primitives['tile_dock']:
        primitives['tile_dock'](name, tiles, cols=2, col_width=18, row_gap=1, leading_space=1, trailing_space=2)
        return
    for icon, label, _subtitle, _route, _tone in tiles:
        print('  %s%s' % (icon, label))

# -*- coding: utf-8 -*-
"""
forge_core.surface.actions
==========================

Central route/action helpers for the user-facing Surface.

Surface pages should describe intent:

    open_editor(path)
    file_page(path)
    copy_text(text)
    back(context, stamp)
    op_detail(stamp, index)
    tile('Raw', raw(stamp), icon='📦 ', subtitle='packet')

rather than hand-writing route tuples everywhere.

This keeps op-owned pages local while making links consistent across the
whole printed-page system.
"""


# -- small normalisation helpers -------------------------------------------

def _text(value, default=''):
    value = str(value or '').strip()
    return value if value else default


def _page_id(value, default='run.home'):
    value = _text(value, default)
    aliases = {
        'home': 'run.home',
        'summary': 'run.home',
        'run': 'run.home',
        'audit': 'run.audit',
        'ops': 'op.list',
        'raw': 'packet.raw',
        'packet': 'packet.raw',
        'docs': 'run.docs',
    }
    return aliases.get(value, value)


def route(*parts):
    """Return a route tuple suitable for pill/tile renderers."""
    out = []
    for part in parts:
        if part is None:
            continue
        text = str(part)
        if text == '':
            continue
        out.append(text)
    return tuple(out)


# -- run/page navigation ----------------------------------------------------

def page(stamp, page_id, back_page=''):
    """Route to a page in a stored run."""
    stamp = _text(stamp, 'latest')
    page_id = _page_id(page_id)
    if back_page:
        return route('run_page', stamp, page_id, _page_id(back_page))
    return route('run_page', stamp, page_id)


def run(stamp='latest'):
    """Route to a run landing page."""
    return route('run', _text(stamp, 'latest'))


def latest_run():
    """Route to the latest stored run."""
    return run('latest')

def runs():
    """Route to the stored runs index."""
    return route('runs')


def audit(stamp):
    return page(stamp, 'run.audit')


def summary(stamp):
    return page(stamp, 'run.home')


def raw(stamp):
    return page(stamp, 'packet.raw')


def docs(stamp):
    return page(stamp, 'run.docs')


def ops(stamp):
    return page(stamp, 'op.list')


def home():
    return route('home')


def op_detail(stamp, index, back_page='run.audit'):
    """Route to an op detail page."""
    try:
        idx = int(index)
    except Exception:
        idx = 0
    return page(stamp, 'op.detail.%d' % idx, back_page=back_page)

def op_readme(stamp, op_name):
    """Route to an op README page."""
    return route('run_page', _text(stamp, 'latest'), 'op.readme', _text(op_name).lower())


def back(context=None, stamp='latest', default_page='run.audit'):
    """Return a consistent Back route for page controls.

    Contextual back is one of the key Surface concepts. If a route supplied a
    back_page, use it. Otherwise fall back to audit, because audit is the normal
    parent for op details.
    """
    context = context or {}
    target = _text(context.get('back_page') or default_page, default_page)

    if target in ('landing', 'default', 'home'):
        return run(stamp)
    if target == 'run.home':
        return run(stamp)

    return page(stamp, target)


def refresh(context=None, stamp='latest', default_page='landing'):
    """Route back to the current page when the context exposes one.

    This gives pages a standard way to look "live": run a small action, then
    return to the same page or re-render the current page.
    """
    context = context or {}
    current = _text(context.get('page_id') or context.get('current_page') or default_page, default_page)
    if current in ('landing', 'default', 'home'):
        return run(stamp)
    return page(stamp, current, back_page=context.get('back_page') or '')


# -- file/object actions ----------------------------------------------------

def file_page(path, stamp='latest'):
    """Route to the first-class file/object page for a project-relative path."""
    return route('run_page', _text(stamp, 'latest'), 'file.view', 'path=' + _text(path, '.'))


def open_editor(path, stamp='', return_page=''):
    """Open a project-relative file in the Pythonista editor.

    Optional stamp/return_page keep the console navigable after the editor opens.
    """
    parts = ['open_pythonista', _text(path)]
    if stamp:
        parts.append(_text(stamp, 'latest'))
    if return_page:
        parts.append(_page_id(return_page))
    return route(*parts)


def quicklook(path):
    return route('quicklook', _text(path))


def open_in(path):
    return route('open_in', _text(path))


def copy_path(path):
    return route('copy_path', _text(path))


# -- clipboard / bundle actions -------------------------------------------

def copy_packet(stamp):
    return route('copy_packet', _text(stamp, 'latest'))


def copy_text(text, label='text'):
    """Copy arbitrary useful text to clipboard."""
    return route('copy_text', _text(label, 'text'), str(text or ''))


def copy_bundle(bundle_text, label='bundle'):
    """Copy/stage a Forge bundle without running it."""
    return route('copy_text', _text(label, 'bundle'), str(bundle_text or '').strip())


def run_bundle(bundle_text):
    """Route that runs a small Forge bundle.

    Best for short one-command bundles. For multi-line bundles, prefer
    copy_bundle() so URL quoting/newline handling does not become fragile.
    """
    return route('run_bundle', str(bundle_text or '').strip())


def read_again(path):
    path = _text(path)
    return run_bundle('READ %s' % path) if path else run_bundle('READ')


def help_for(op_name, mode='full'):
    op_name = _text(op_name, 'HELP').upper()
    mode = _text(mode)
    if mode:
        return run_bundle('HELP %s %s' % (op_name, mode))
    return run_bundle('HELP %s' % op_name)


# -- render-shape helpers ---------------------------------------------------

def tile(label, target, icon='', subtitle='', tone='accent'):
    """Return the tile tuple used by render_tile_dock.

    Shape:
        (icon, label, subtitle, route, tone)
    """
    return (
        str(icon or ''),
        str(label or ''),
        str(subtitle or ''),
        tuple(target or ()),
        str(tone or 'accent'),
    )


def file_tiles(path, include_read=True, include_editor=True):
    """Standard file-related action tiles."""
    path = _text(path)
    if not path:
        return []

    tiles = [
        tile('File', file_page(path), icon='📁 ', subtitle='inspect', tone='accent'),
    ]
    if include_read:
        tiles.append(tile('Read', read_again(path), icon='📄 ', subtitle='again', tone='accent'))
    if include_editor:
        tiles.append(tile('Editor', open_editor(path), icon='🐍 ', subtitle='Pythonista', tone='success'))
    tiles.append(tile('Copy path', copy_path(path), icon='📋 ', subtitle='path', tone='warning'))
    return tiles


def standard_run_tiles(stamp):
    """Common run-level controls."""
    return [
        tile('Runs', runs(), icon='◎ ', subtitle='history', tone='accent'),
        tile('Ops', ops(stamp), icon='⚙ ', subtitle='op list', tone='accent'),
        tile('Audit', audit(stamp), icon='📋 ', subtitle='trail', tone='warning'),
        tile('Raw', raw(stamp), icon='📦 ', subtitle='packet', tone='warning'),
        tile('Copy', copy_packet(stamp), icon='📋 ', subtitle='packet', tone='warning'),
        tile('Home', home(), icon='🏠 ', subtitle='workbench', tone='success'),
    ]
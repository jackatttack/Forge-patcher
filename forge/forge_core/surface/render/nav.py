# -*- coding: utf-8 -*-
"""
forge_core.surface.render.nav
==============================

Reusable compact navigation docks for surface pages.

Console-native bottom navigation. Gives global pages a consistent way
out without relying on the older doc_footer rail.
"""

from forge_core.surface.render.tile_dock import render_tile_dock


def render_global_nav(current='', include_back=True, include_runs=True, include_docs=True):
    """Render a compact bottom navigation dock for global pages.

    ``current`` can be one of:
        home, docs, runs, files, safety, ops, start

    The current destination is omitted where useful, keeping the dock
    compact.
    """
    current = str(current or '').strip().lower()
    tiles = []

    if include_back:
        tiles.append(('⬅️ ', 'Back', 'previous', ('back',), 'orange'))

    if current != 'home':
        tiles.append(('🏠 ', 'Home', 'workbench', ('home',), 'success'))

    if include_runs and current != 'runs':
        tiles.append(('◎ ', 'Runs', 'history', ('runs',), 'success'))

    if include_docs and current != 'docs':
        tiles.append(('📚 ', 'Docs', 'learn Forge', ('docs',), 'border'))

    if current != 'ops':
        tiles.append(('⚙ ', 'Ops', 'commands', ('ops', 'core'), 'accent'))

    if current != 'files':
        tiles.append(('📁 ', 'Files', 'browse', ('files', '.'), 'accent'))

    if current != 'safety':
        tiles.append(('🛟 ', 'Safety', 'restore', ('safety',), 'danger'))

    if not tiles:
        return False

    return render_tile_dock(
        'navigation',
        tiles,
        cols=2,
        col_width=18,
        row_gap=1,
        leading_space=1,
        trailing_space=0,
    )

# -*- coding: utf-8 -*-
"""
forge_core.surface.live
========================

Live Surface renderer for Forge.

Prints directly to the Pythonista console using the LinkOS visual
grammar: palette, pills, tile docks, hero bands. Tappable controls
route back into ``forge_entry.py`` via ``pythonista3://`` URLs built
by ``primitives.url``.

The same code path renders cleanly under Forge ``RUN_FILE`` capture
because ``pill_link`` falls back to plain coloured text when stdout
is a captured StringIO. There is no separate "packet" mode here —
``surface/render.py`` remains the explicit plain-text packet
renderer; ``live.py`` is the one renderer that adapts to the host.
"""

from forge_core.surface.pills import pill_link
from forge_core.surface.primitives import (
    band, center, colour, font, reset, say, spacer, thin_rule,
)
from forge_core.surface.tile_dock import render_tile_dock


# -- font -------------------------------------------------------------------

def set_live_font():
    """Set the Pythonista console to the standard reboot monospace.

    Pulled from ``primitives.font`` so the live surface and any other
    consumer (e.g. doc pages) share one baseline.
    """
    font('Menlo', 15)


# -- helpers ----------------------------------------------------------------

def spaced(text):
    """Letter-space a label: ``RUN CLEAN`` becomes ``R U N   C L E A N``.

    Used for hero titles where extra horizontal weight matters more
    than character economy.
    """
    return ' '.join(str(text or '').upper())


# -- run inspection ---------------------------------------------------------

def status_title(run):
    """Pick the hero title and tone for a run.

    Returns ``(title, tone)``. ``tone`` is a palette key from
    ``primitives.HEX``.
    """
    status = str((run or {}).get('status') or 'UNKNOWN').upper()
    if status == 'APPLIED':
        return 'RUN CLEAN', 'success'
    if status == 'FAILED_PARSE':
        return 'RUN PARSE FAILED', 'danger'
    if status == 'FAILED':
        return 'RUN FAILED', 'danger'
    return 'RUN ' + status, 'warning'


def status_counts(run):
    """Tally applied / skipped / failed counts across a run's results."""
    applied = skipped = failed = 0
    for r in (run or {}).get('results') or []:
        status = str((r or {}).get('status') or '').upper()
        if status == 'APPLIED':
            applied += 1
        elif 'SKIP' in status:
            skipped += 1
        else:
            failed += 1
    return applied, skipped, failed


# -- hero -------------------------------------------------------------------

def render_hero(run):
    """Print the run hero band: status title, stamp, summary counts."""
    title, tone = status_title(run)
    stamp = str((run or {}).get('stamp') or 'latest')
    applied, skipped, failed = status_counts(run)

    band('═', width=41, tone='border')
    spacer()
    say(center(spaced(title), 41), tone)
    spacer()
    say(center(stamp, 41), 'muted')
    spacer()
    say(
        center(
            '%s applied · %s skipped · %s failed' % (applied, skipped, failed),
            41,
        ),
        'text',
    )
    spacer()
    band('═', width=41, tone='border')


# -- tile items -------------------------------------------------------------

def page_tiles(run):
    """Build tile-dock items for every renderable page in the run.

    Each tile becomes ``(icon, label, subtitle, args, tone)`` for
    ``render_tile_dock``. Tapping a page tile routes to
    ``run_page <stamp> <page_id>``.
    """
    stamp = str((run or {}).get('stamp') or 'latest')
    tiles = []
    for p in (run or {}).get('pages') or []:
        if not isinstance(p, dict):
            continue
        if not p.get('render_in_stack', True):
            continue
        label = p.get('short') or p.get('title') or p.get('id') or 'Page'
        icon = p.get('icon') or '▣'
        icon = str(icon)
        if not icon.endswith(' '):
            icon = icon + ' '
        subtitle = p.get('kind') or ''
        tiles.append((
            icon,
            label,
            subtitle,
            ('run_page', stamp, p.get('id') or ''),
            p.get('tone') or 'accent',
        ))
    return tiles


def control_tiles(run):
    """Standard control dock for a run: copy, handoff, raw, navigation."""
    stamp = str((run or {}).get('stamp') or 'latest')
    return [
        ('📋 ', 'Copy packet', 'clipboard',   ('copy_packet', stamp),              'warning'),
        ('🤖 ', 'AI handoff',  'next turn',   ('continue_ai', stamp),              'success'),
        ('📦 ', 'Raw packet',  'source text', ('run_page', stamp, 'packet.raw'),   'warning'),
        ('◎ ',  'Runs',         'history',     ('runs',),                           'accent'),
        ('📚 ', 'Docs',         'reference',   ('docs',),                           'accent'),
        ('🏠 ', 'Home',         'workbench',   ('home',),                           'success'),
    ]


# -- main entry -------------------------------------------------------------

def render_live_surface(run):
    """Render the full live surface for a run dict.

    Print order is bottom-first conscious: hero at top, then page
    stack, then the control dock last so it lands at the bottom of
    the Pythonista viewport where it is most tappable.
    """
    set_live_font()
    run = run or {}

    spacer()
    render_hero(run)

    pages = page_tiles(run)
    if pages:
        render_tile_dock(
            'Pages',
            pages,
            cols=2,
            col_width=18,
            row_gap=1,
            leading_space=1,
            trailing_space=0,
            tone='surface_2',
        )

    render_tile_dock(
        'Actions',
        control_tiles(run),
        cols=2,
        col_width=18,
        row_gap=1,
        leading_space=1,
        trailing_space=1,
        tone='surface_2',
    )

    thin_rule(width=41, tone='surface_2')
    say('  Tap labels above. Packet text remains truth.', 'muted')
    spacer()

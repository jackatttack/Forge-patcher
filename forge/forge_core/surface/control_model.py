# -*- coding: utf-8 -*-
"""
LinkOS-style control model for Forge.

This is deliberately plain-dict and dependency-free. It sits beside the older
surface/controls.py during the migration; do not wire entry.py to it until the
page runtime has passed smoke tests.
"""

VALID_CONTROL_KINDS = set([
    'nav',
    'copy',
    'action',
    'danger',
    'docs',
    'page',
    'package',
    'custom',
])


def control(control_id,
            label,
            route=None,
            action=None,
            value=None,
            icon='',
            tone='accent',
            kind='action',
            note='',
            payload=None):
    kind = str(kind or 'action')
    if kind not in VALID_CONTROL_KINDS:
        kind = 'custom'

    return {
        'id': str(control_id or ''),
        'label': str(label or ''),
        'route': route,
        'action': action,
        'value': value,
        'icon': str(icon or ''),
        'tone': str(tone or 'accent'),
        'kind': kind,
        'note': str(note or ''),
        'payload': payload if payload is not None else {},
    }


def panel(panel_id,
          title,
          controls=None,
          kind='action',
          placement='body',
          priority=0,
          collapsed=False,
          source='reboot'):
    return {
        'id': str(panel_id or ''),
        'title': str(title or ''),
        'kind': str(kind or 'action'),
        'placement': str(placement or 'body'),
        'priority': int(priority or 0),
        'collapsed': bool(collapsed),
        'source': str(source or 'reboot'),
        'controls': list(controls or []),
    }


def sort_panels(panels):
    order = {
        'top': 0,
        'body': 1,
        'bottom': 2,
        'footer': 3,
    }
    return sorted(
        list(panels or []),
        key=lambda p: (
            order.get(str((p or {}).get('placement')), 9),
            -int((p or {}).get('priority') or 0),
        ),
    )


def run_copy_panel(stamp):
    stamp = stamp or 'latest'
    return panel(
        'run.copy',
        'Copy controls',
        [
            control('copy.packet', 'Copy packet', route=('copy_packet', stamp), icon='📋 ', tone='warning', kind='copy'),
            control('copy.handoff', 'AI handoff', route=('continue_ai', stamp), icon='🤖 ', tone='success', kind='copy'),
            control('copy.summary', 'Copy summary', route=('copy_summary', stamp), icon='🧠 ', tone='accent', kind='copy'),
            control('print.packet', 'Print packet', route=('print_packet', stamp), icon='🖨 ', tone='border', kind='action'),
        ],
        kind='copy',
        placement='bottom',
        priority=50,
    )


def run_nav_panel(stamp):
    stamp = stamp or 'latest'
    return panel(
        'run.nav',
        'Navigation',
        [
            control('page.home', 'Run home', route=('run_page', stamp, 'run.home'), icon='🏠 ', tone='success', kind='nav'),
            control('page.index', 'Pages', route=('run_page', stamp, 'page.index'), icon='▦ ', tone='accent', kind='nav'),
            control('packet.raw', 'Raw', route=('run_page', stamp, 'packet.raw'), icon='▤ ', tone='warning', kind='nav'),
        ],
        kind='nav',
        placement='footer',
        priority=10,
    )


def describe_panels(panels):
    out = []
    for p in sort_panels(panels):
        out.append('%s | %s | placement=%s | controls=%d | source=%s' % (
            p.get('id') or '?',
            p.get('kind') or '?',
            p.get('placement') or '?',
            len(p.get('controls') or []),
            p.get('source') or '',
        ))
    return out

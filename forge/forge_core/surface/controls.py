# -*- coding: utf-8 -*-
"""
Surface control model.

Controls are structured action data. The renderer may show them as plain text,
Pythonista tappable links, WebView buttons, or future UI widgets.

Keep this module dependency-free.
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


def _route_tuple(value):
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return tuple(str(value).split())


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
        'route': _route_tuple(route),
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
        'Actions',
        [
            control('copy.packet', 'Copy packet', route=('copy_packet', stamp), icon='📋 ', tone='warning', kind='copy', note='full packet'),
            control('copy.handoff', 'AI handoff', route=('continue_ai', stamp), icon='🤖 ', tone='success', kind='copy', note='send to chat'),
            control('packet.raw', 'Raw packet', route=('run_page', stamp, 'packet.raw'), icon='📦 ', tone='warning', kind='page', note='source packet'),
            control('runs', 'Runs', route=('runs',), icon='◎ ', tone='accent', kind='nav', note='history'),
            control('docs', 'Docs', route=('docs',), icon='📚 ', tone='accent', kind='docs', note='guidance'),
            control('home', 'Home', route=('home',), icon='🏠 ', tone='success', kind='nav', note='workbench'),
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
            control('page.summary', 'Summary', route=('run_page', stamp, 'run.summary'), icon='◆ ', tone='accent', kind='page'),
            control('page.ops', 'Ops', route=('run_page', stamp, 'run.ops'), icon='≡ ', tone='accent', kind='page'),
            control('packet.raw', 'Raw', route=('run_page', stamp, 'packet.raw'), icon='¶ ', tone='warning', kind='page'),
        ],
        kind='nav',
        placement='footer',
        priority=10,
    )

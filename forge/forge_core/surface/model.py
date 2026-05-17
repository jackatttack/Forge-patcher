# -*- coding: utf-8 -*-
"""
Small page/action helpers for Forge Surface pages.

Kept plain-dict and dependency-free for Pythonista compatibility.
"""

KIND_DEFAULTS = {
    'summary': ('◆', 'Summary', 'accent'),
    'ops': ('≡', 'Ops', 'muted'),
    'raw': ('¶', 'Raw', 'warning'),
    'errors': ('!', 'Errors', 'danger'),
    'files': ('▥', 'Files', 'accent'),
    'help': ('📖', 'Docs', 'warning'),
}


def _short(value, fallback='Page', limit=12):
    text = str(value or fallback or 'Page').strip()
    if not text:
        text = str(fallback or 'Page')
    return text[:limit]


def page(
    page_id,
    title,
    kind='detail',
    icon=None,
    short=None,
    tone=None,
    mode='dense',
    size='full',
    source='reboot',
    priority=0,
    data=None,
    controls=None,
    promote=True,
    render_in_stack=True,
):
    default_icon, default_short, default_tone = KIND_DEFAULTS.get(
        str(kind or 'detail'),
        ('▣', 'Page', 'muted'),
    )

    size = str(size or 'full')
    if size not in ('compact', 'card', 'full', 'wide', 'dashboard'):
        size = 'full'

    return {
        'id': str(page_id or ''),
        'title': str(title or page_id or 'Page'),
        'kind': str(kind or 'detail'),
        'icon': str(icon or default_icon),
        'short': _short(short or title or default_short, default_short),
        'tone': str(tone or default_tone),
        'mode': str(mode or 'dense'),
        'size': size,
        'source': str(source or 'reboot'),
        'priority': int(priority or 0),
        'data': data if data is not None else {},
        'controls': list(controls or []),
        'promote': bool(promote),
        'render_in_stack': bool(render_in_stack),
    }

def action(label, target='', icon='•', tone='accent', note=''):
    return {
        'label': str(label or ''),
        'target': str(target or ''),
        'icon': str(icon or '•'),
        'tone': str(tone or 'accent'),
        'note': str(note or ''),
    }

# -*- coding: utf-8 -*-
"""
Surface pages for URL.
"""

from forge_core.surface.model import page


def pages_for_result(result, index, run):
    data = result.get('data') or {}
    status = str(result.get('status') or '').upper()
    tone = 'accent' if status == 'APPLIED' else 'danger'

    mode = str(data.get('mode') or '').strip()
    if not mode:
        msg = str(result.get('message') or '')
        if 'probe' in msg:
            mode = 'probe'
        elif 'json' in msg:
            mode = 'json'
        elif 'download' in msg:
            mode = 'download'
        else:
            mode = 'fetch'

    title = 'URL'
    short = 'URL'
    if mode:
        short = ('URL ' + mode)[:12]

    return [page(
        'url.%N',
        title,
        kind='url',
        icon='🌐',
        short=short,
        tone=tone,
        mode='dense',
        size='compact',
        source='op:URL',
        priority=70,
        data={
            'result': result,
            'result_index': index,
            'url': result.get('target') or '',
            'mode': mode,
            'preview': result.get('preview') or '',
            'data': data,
        },
    )]

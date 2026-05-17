# -*- coding: utf-8 -*-
"""
LinkOS-style page model for Forge.

This is the new page-with-render-callable model. It intentionally lives beside
the older surface/model.py until the reboot entry point is switched over.
"""

VALID_MODES = set(['dense', 'standard', 'hero'])
VALID_SIZES = set(['compact', 'card', 'full', 'wide', 'dashboard'])

_KIND_NAV = {
    'home':    ('🏠', 'Home', 'success'),
    'result':  ('▣', 'Result', 'accent'),
    'summary': ('✦', 'Story', 'accent'),
    'detail':  ('▦', 'Stack', 'accent'),
    'raw':     ('▤', 'Raw', 'warning'),
    'docs':    ('📚', 'Docs', 'border'),
    'help':    ('📖', 'Help', 'info'),
    'preview': ('👁', 'Preview', 'info'),
    'op':      ('⚙', 'Ops', 'muted'),
    'op_detail': ('⚙', 'Op', 'muted'),
    'run':     ('▶', 'Run', 'success'),
    'issue':   ('⚠', 'Issue', 'danger'),
}


def _mode(value):
    value = str(value or 'standard')
    return value if value in VALID_MODES else 'standard'


def _size(value):
    value = str(value or 'full')
    return value if value in VALID_SIZES else 'full'


def _nav_defaults(kind):
    kind = str(kind or 'detail')
    return _KIND_NAV.get(kind, ('▣', 'Page', 'muted'))


def _short(value, fallback='Page'):
    value = str(value or fallback or 'Page').strip()
    if not value:
        value = str(fallback or 'Page')
    return value[:12]


def card(title, subtitle='', body=None, icon='▣', tone='muted', route=None, page_id=''):
    return {
        'title': str(title or ''),
        'subtitle': str(subtitle or ''),
        'body': list(body or []),
        'icon': str(icon or '▣'),
        'tone': str(tone or 'muted'),
        'route': route,
        'page_id': str(page_id or ''),
    }


def page(page_id,
         title,
         kind,
         render=None,
         source='reboot',
         priority=0,
         landing=False,
         mode='standard',
         size='full',
         footer=None,
         controls=None,
         data=None,
         target=None,
         card=None,
         emoji=None,
         short=None,
         tone=None,
         promote=True,
         render_in_stack=True):
    default_emoji, default_short, default_tone = _nav_defaults(kind)
    page_id = str(page_id or '')
    title = str(title or page_id or 'Page')

    return {
        'id': page_id,
        'title': title,
        'kind': str(kind or 'detail'),
        'source': str(source or 'reboot'),
        'priority': int(priority or 0),
        'landing': bool(landing),
        'mode': _mode(mode),
        'size': _size(size),
        'footer': list(footer or []),
        'controls': list(controls or []),
        'data': data if data is not None else {},
        'target': target,
        'card': card,
        'emoji': str(emoji or default_emoji),
        'short': _short(short or title or default_short, default_short),
        'tone': str(tone or default_tone),
        'promote': bool(promote),
        'render_in_stack': bool(render_in_stack),
        'render': render,
    }


def ensure_page_card(page_obj, stamp='latest'):
    page_obj = page_obj or {}
    existing = page_obj.get('card')
    page_id = page_obj.get('id') or ''
    route = ('run_page', stamp, page_id)

    if isinstance(existing, dict):
        if not existing.get('page_id'):
            existing['page_id'] = page_id
        if not existing.get('route'):
            existing['route'] = route
        if not existing.get('icon'):
            existing['icon'] = page_obj.get('emoji') or '▣'
        if not existing.get('tone'):
            existing['tone'] = page_obj.get('tone') or 'muted'
        return existing

    title = page_obj.get('short') or page_obj.get('title') or page_id or 'Page'
    subtitle = '%s / %s' % (
        page_obj.get('kind') or 'detail',
        page_obj.get('source') or 'reboot',
    )

    return card(
        title,
        subtitle=subtitle,
        body=[],
        icon=page_obj.get('emoji') or '▣',
        tone=page_obj.get('tone') or 'muted',
        route=route,
        page_id=page_id,
    )


def sort_pages(pages):
    return sorted(
        list(pages or []),
        key=lambda p: int((p or {}).get('priority') or 0),
        reverse=True,
    )


def landing_page(pages):
    pages = list(pages or [])

    for p in pages:
        if (p or {}).get('id') == 'run.home':
            return p

    landing = [p for p in pages if (p or {}).get('landing')]
    if landing:
        return sort_pages(landing)[0]

    sorted_pages = sort_pages(pages)
    return sorted_pages[0] if sorted_pages else None


def core_run_pages(run):
    """Build the reboot-native page stack for a structured run."""
    run = run or {}
    stamp = run.get('stamp') or 'latest'

    from forge_core.surface.core_pages import (
        render_audit_page,
        render_file_view_page,
        render_list_files_page,
        render_list_ops_page,
        render_op_detail_page,
        render_ops_page,
        render_raw_packet_page,
        render_run_docs_nav_page,
        render_run_home_page,
    )

    pages = [
        page(
            'packet.raw',
            'Raw Packet',
            'raw',
            render=render_raw_packet_page,
            source='reboot',
            priority=950,
            landing=False,
            mode='dense',
            size='full',
            footer=['run.home'],
            data={'stamp': stamp, 'run': run, 'runtime_controls': False, 'runtime_grid': False},
            target='run:%s/raw' % stamp,
            card=card('Raw', 'source packet', icon='📦', tone='warning', route=('run_page', stamp, 'packet.raw'), page_id='packet.raw'),
            emoji='📦',
            short='Raw',
            tone='warning',
            promote=False,
            render_in_stack=False,
        ),
        page(
            'run.home',
            'Run',
            'home',
            render=render_run_home_page,
            source='reboot',
            priority=100,
            landing=True,
            mode='hero',
            size='full',
            footer=[],
            data={'stamp': stamp, 'run': run, 'runtime_controls': False, 'runtime_grid': True},
            target='run:%s' % stamp,
            card=card('Run', 'workbench', icon='🏠', tone='success', route=('run', stamp), page_id='run.home'),
            emoji='🏠',
            short='Run',
            tone='success',
            promote=True,
            render_in_stack=True,
        ),
        page(
            'file.view',
            'File',
            'preview',
            render=render_file_view_page,
            source='reboot',
            priority=30,
            landing=False,
            mode='dense',
            size='full',
            footer=['run.home', 'op.list'],
            data={'stamp': stamp, 'run': run, 'runtime_controls': False, 'runtime_grid': False},
            target='run:%s/file' % stamp,
            card=card('File', 'inspect path', icon='📁', tone='accent', route=('run_page', stamp, 'file.view'), page_id='file.view'),
            emoji='📁',
            short='File',
            tone='accent',
            promote=False,
            render_in_stack=False,
        ),
        page(
            'run.docs',
            'Docs',
            'docs',
            render=render_run_docs_nav_page,
            source='reboot',
            priority=35,
            landing=False,
            mode='dense',
            size='compact',
            footer=['run.home', 'op.list'],
            data={'stamp': stamp, 'run': run, 'runtime_controls': False, 'runtime_grid': True},
            target='run:%s/docs' % stamp,
            card=card('Docs', 'run guidance', icon='📚', tone='border', route=('run_page', stamp, 'run.docs'), page_id='run.docs'),
            emoji='📚',
            short='Docs',
            tone='border',
            promote=True,
            render_in_stack=True,
        ),
        page(
            'op.list',
            'Ops',
            'op',
            render=render_ops_page,
            source='reboot',
            priority=20,
            landing=False,
            mode='dense',
            size='full',
            footer=['run.home'],
            data={'stamp': stamp, 'run': run, 'runtime_controls': False, 'runtime_grid': True},
            target='run:%s/ops' % stamp,
            card=card('Ops', 'op list', icon='⚙', tone='cyan', route=('run_page', stamp, 'op.list'), page_id='op.list'),
            emoji='⚙',
            short='Ops',
            tone='cyan',
            promote=True,
            render_in_stack=False,
        ),
    ]

    if run.get('results'):
        pages.append(page(
            'run.audit',
            'Audit Trail',
            'audit',
            render=render_audit_page,
            source='reboot',
            priority=60,
            landing=False,
            mode='dense',
            size='full',
            footer=['run.home', 'op.list'],
            data={'stamp': stamp, 'run': run, 'runtime_controls': False, 'runtime_grid': True},
            target='run:%s/audit' % stamp,
            card=card(
                'Audit',
                '%d op%s' % (len(run.get('results') or []), '' if len(run.get('results') or []) == 1 else 's'),
                icon='📋',
                tone='accent',
                route=('run_page', stamp, 'run.audit'),
                page_id='run.audit',
            ),
            emoji='📋',
            short='Audit',
            tone='accent',
            promote=True,
            render_in_stack=True,
        ))

    list_files_index = 0
    list_ops_index = 0

    for result in run.get('results') or []:
        result = result or {}
        op = str(result.get('op') or '').upper()
        text = ''
        for key in ('preview', 'stdout', 'output', 'text', 'message'):
            if result.get(key):
                text = str(result.get(key))
                break

        if op == 'LIST_FILES':
            target = str(result.get('file') or result.get('target') or '.').strip() or '.'
            page_id = 'files.tree.%d' % list_files_index
            pages.append(page(
                page_id,
                'Files',
                'preview',
                render=render_list_files_page,
                source='reboot',
                priority=75 - list_files_index,
                mode='dense',
                size='full',
                footer=['run.home', 'op.list'],
                data={
                    'stamp': stamp,
                    'run': run,
                    'result': result,
                    'text': text,
                    'target': target,
                    'runtime_controls': False,
                    'runtime_grid': True,
                },
                target='run:%s/files/%s' % (stamp, target),
                card=card('Files', target[:18] if target else 'directory map', icon='📁', tone='accent', route=('run_page', stamp, page_id), page_id=page_id),
                emoji='📁',
                short='Files',
                tone='accent',
                promote=True,
                render_in_stack=False,
            ))
            list_files_index += 1

        if op == 'LIST_OPS':
            mode = 'Ops'
            upper = text.upper()
            if '[CORE]' in upper:
                mode = 'Core'
            elif '[CUSTOM]' in upper:
                mode = 'Custom'
            elif '[ALL]' in upper:
                mode = 'All'

            catalog_label = 'Catalog' if mode == 'Ops' else ('%s Catalog' % mode)
            page_id = 'ops.catalog.%d' % list_ops_index
            pages.append(page(
                page_id,
                catalog_label,
                'detail',
                render=render_list_ops_page,
                source='reboot',
                priority=80 - list_ops_index,
                mode='dense',
                size='full',
                footer=['run.home', 'op.list'],
                data={
                    'stamp': stamp,
                    'run': run,
                    'result': result,
                    'mode': mode,
                    'runtime_controls': False,
                    'runtime_grid': True,
                },
                target='run:%s/%s' % (stamp, page_id),
                card=card(catalog_label, 'command catalog', icon='📚', tone='border', route=('run_page', stamp, page_id), page_id=page_id),
                emoji='📚',
                short=catalog_label,
                tone='border',
                promote=True,
                render_in_stack=False,
            ))
            list_ops_index += 1

    for index, result in enumerate(run.get('results') or []):
        result = result or {}
        op_name = str(result.get('op') or 'OP').upper()
        status = str(result.get('status') or '').upper()
        page_id = 'op.detail.%d' % index
        pages.append(page(
            page_id,
            op_name,
            'op_detail',
            render=render_op_detail_page,
            source='reboot',
            priority=-100 - index,
            mode='dense',
            size='full',
            footer=['run.home', 'op.list'],
            data={
                'stamp': stamp,
                'run': run,
                'index': index,
                'result': result,
                'back_page': 'run.audit',
                'runtime_controls': False,
                'runtime_grid': False,
            },
            target='run:%s/op/%d' % (stamp, index),
            card=card('#%02d %s' % (index + 1, op_name[:8]), status or 'op detail', icon='⚙', tone='muted', route=('run_page', stamp, page_id), page_id=page_id),
            emoji='⚙',
            short='#%02d' % (index + 1),
            tone='muted',
            promote=False,
            render_in_stack=False,
        ))

    return pages


def describe_pages(pages):
    out = []
    for p in sort_pages(pages):
        bits = [
            str(p.get('id') or '?'),
            'kind=' + str(p.get('kind') or '?'),
            'priority=' + str(p.get('priority') or 0),
            'landing=' + str(bool(p.get('landing'))),
            'mode=' + str(p.get('mode') or ''),
            'size=' + str(p.get('size') or ''),
            'source=' + str(p.get('source') or ''),
            'nav=' + str(p.get('emoji') or '') + ' ' + str(p.get('short') or ''),
        ]
        controls = p.get('controls') or []
        if controls:
            bits.append('controls=' + str(len(controls)))
        if p.get('card'):
            bits.append('card=yes')
        out.append(' | '.join(bits))
    return out

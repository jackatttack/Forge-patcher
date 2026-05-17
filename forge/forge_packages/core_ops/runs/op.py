# -*- coding: utf-8 -*-
"""
RUNS reboot op.

Inspect durable reboot run artifacts.

This proves the new Forge data layer is visible through the same package-shaped
op system as everything else.
"""

import os

from forge_core.run_storage import list_runs, read_text, runs_root


SPEC = {
    'name': 'RUNS',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS', 'LIMIT']),
    'required_directives': set(),
}

HELP = {
    'summary': 'List or inspect stored Forge runs.',
    'minimal_example': [
        'RUNS',
        '',
        'RUNS',
        'ARGS: latest',
        '',
        'RUNS',
        'ARGS: show 20260511_122038 packet',
    ],
}


HINTS = {
    '_max_hints': 1,
    'usage': {
        'message': 'RUNS lists or shows stored reboot runs.',
        'why': 'Stored run ids are used by DIFF and REVERT_RUN.',
        'example': [
            'RUNS latest',
            '',
            'RUNS list',
        ],
        'next': [
            'Use RUNS latest to find the newest stamp.',
            'Use DIFF <stamp> before reverting if unsure.',
        ],
    },
}

def validate(parsed_op):
    return []


def _limit(value, default=10):
    try:
        return max(1, int(str(value).strip()))
    except Exception:
        return default


def execute(ctx, parsed_op, result):
    project_root = ctx.get('project_root') or os.getcwd()
    directives = parsed_op.get('directives') or {}
    args = (directives.get('ARGS') or '').strip()
    limit = _limit(directives.get('LIMIT'), 10)

    run_mode = str((ctx.get('run') or {}).get('mode') or ctx.get('mode') or 'dev')
    names = list_runs(project_root, limit=limit, mode=run_mode)

    if not args:
        lines = []
        lines.append('RUNS')
        lines.append('root: ' + runs_root(project_root))
        if not names:
            lines.append('(none)')
        else:
            for stamp in names:
                lines.append('- ' + stamp)

        result['status'] = 'APPLIED'
        result['message'] = '%d stored run(s)' % len(names)
        result['preview'] = '\n'.join(lines)
        result['data'] = {'runs': names}
        return

    parts = args.split()

    if parts[0] == 'latest':
        if not names:
            result['status'] = 'FAILED_NOT_FOUND'
            result['message'] = 'No stored runs'
            return
        stamp = names[0]
        packet = read_text(project_root, stamp, 'packet.txt') or ''
        surface = read_text(project_root, stamp, 'surface.txt') or ''

        lines = []
        lines.append('RUNS latest ' + stamp)
        lines.append('')
        lines.append('PACKET')
        lines.append(packet.rstrip())
        lines.append('')
        lines.append('SURFACE')
        lines.append(surface.rstrip())

        result['status'] = 'APPLIED'
        result['message'] = 'Latest run: ' + stamp
        result['preview'] = '\n'.join(lines).rstrip()
        result['data'] = {'stamp': stamp}
        return

    if parts[0] == 'show':
        if len(parts) < 2:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'RUNS show requires a stamp'
            return

        stamp = parts[1]
        kind = parts[2] if len(parts) > 2 else 'packet'
        file_map = {
            'packet': 'packet.txt',
            'surface': 'surface.txt',
            'bundle': 'bundle.txt',
            'json': 'run.json',
            'run': 'run.json',
        }
        filename = file_map.get(kind)
        if not filename:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'Unknown RUNS show kind: ' + kind
            return

        text = read_text(project_root, stamp, filename)
        if text is None:
            result['status'] = 'FAILED_NOT_FOUND'
            result['message'] = 'Run artifact not found: %s %s' % (stamp, filename)
            return

        result['status'] = 'APPLIED'
        result['message'] = 'Run %s %s' % (stamp, kind)
        result['preview'] = text.rstrip()
        result['data'] = {'stamp': stamp, 'kind': kind}
        return

    result['status'] = 'FAILED_PARSE'
    result['message'] = 'Unknown RUNS args: ' + args

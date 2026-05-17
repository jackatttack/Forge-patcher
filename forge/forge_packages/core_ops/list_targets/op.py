# -*- coding: utf-8 -*-
"""
LIST_TARGETS reboot op.

Enumerate patchable AST targets in a Python file.
"""

import os


SPEC = {
    'name': 'LIST_TARGETS',
    'target_kind': 'path',
    'body_mode': 'forbidden',
    'allowed_directives': set(['DOCS']),
    'required_directives': set(),
}

HELP = {
    'summary': 'List patchable AST targets found in a Python file.',
    'minimal_example': [
        'LIST_TARGETS forge/smoke.py',
        '',
        'LIST_TARGETS forge/smoke.py',
        'DOCS: no',
    ],
}


HINTS = {
    '_max_hints': 1,
    'file': {
        'message': 'LIST_TARGETS needs a Python file path.',
        'why': 'AST targets can only be discovered from parseable Python source.',
        'example': [
            'LIST_TARGETS forge/smoke.py',
        ],
        'next': [
            'Use LIST_FILES to locate the file.',
            'Use PREVIEW first if the file may not be valid Python.',
        ],
    },
}

def validate(parsed_op):
    if not (parsed_op.get('target') or '').strip():
        return ['LIST_TARGETS requires a Python file path']
    return []


def execute(ctx, parsed_op, result):
    from forge_core.ast_tools import list_targets

    root = os.path.abspath(ctx.get('project_root') or os.getcwd())
    target = (parsed_op.get('target') or '').strip()
    directives = parsed_op.get('directives') or {}
    docs_mode = str(directives.get('DOCS') or 'yes').strip().lower() or 'yes'

    rows, err = list_targets(root, target, docs_mode=docs_mode)
    if err:
        if 'not found' in err.lower():
            result['status'] = 'FAILED_NOT_FOUND'
        elif 'escapes' in err.lower():
            result['status'] = 'FAILED_IO'
        else:
            result['status'] = 'FAILED_PARSE'
        result['message'] = err
        return

    lines = []
    lines.append('LIST_TARGETS %s [%d targets]' % (target, len(rows or [])))

    for row in rows or []:
        pad = '  ' * int(row.get('indent') or 0)
        line = '%-58s %s' % (pad + row.get('target', ''), row.get('range') or '')
        if docs_mode != 'no':
            doc = row.get('doc') or '∅'
            line += '  # ' + doc[:80]
        lines.append(line.rstrip())

    result['status'] = 'APPLIED'
    result['message'] = '%d targets' % len(rows or [])
    result['preview'] = '\n'.join(lines).rstrip()
    result['file'] = target
    result['data'] = {
        'path': target,
        'targets': rows or [],
    }

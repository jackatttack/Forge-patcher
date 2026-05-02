# -*- coding: utf-8 -*-
"""
ops.list_ops
============
List active forge ops.
"""

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'LIST_OPS',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS']),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP LIST_OPS.
HELP = {
    'summary': 'List all currently registered forge ops grouped by category.',
    'subject': ['No target.'],
    'common_failures': [],
    'safe_usage': [
        'Use this to discover active ops instead of relying on old docs.',
        'Use HELP <OP_NAME> for syntax and pain points.',
    ],
    'minimal_example': [
        'LIST_OPS',
    ],
    'related_ops': ['HELP'],
}

HINTS = {
    '_max_hints': 1,
    'arg must be': {
        'message': 'LIST_OPS only accepts core, custom, or all.',
        'why': 'LIST_OPS filters registered ops by layer. Unknown filters are rejected to avoid misleading output.',
        'priority': 120,
        'example': [
            'LIST_OPS',
            '',
            'LIST_OPS custom',
            '',
            'LIST_OPS all',
        ],
        'next': ['Use LIST_OPS all when unsure', 'Use HELP <OP> after finding the op name'],
    },
    'stale': {
        'message': 'Registered ops may be stale after edits.',
        'why': 'Pythonista can cache modules after op edits, so LIST_OPS/HELP may lag behind disk.',
        'priority': 100,
        'example': [
            'REFRESH',
            '',
            'LIST_OPS all',
        ],
        'next': ['Run REFRESH', 'Restart Pythonista after new op files or parser/engine changes'],
    },
}


def validate(parsed_op):
    """Check optional filter argument is valid. Returns list of error strings."""
    errors = []

    subject = (parsed_op.directives.get('ARGS') or '').strip().lower()
    if subject and subject not in ('core', 'custom', 'all'):
        errors.append('LIST_OPS arg must be core, custom, or all (or omit for core)')
    return errors

def execute(ctx, parsed_op, result):
    """Emit all registered ops grouped by category."""
    from forge.op_help import render_ops_list

    subject = (parsed_op.directives.get('ARGS') or '').strip().lower()
    if subject in ('all', 'custom', 'core'):
        layer = subject
    else:
        layer = 'core'

    text = render_ops_list(layer=layer)
    count = len([line for line in text.splitlines() if line.startswith('- ')])
    result['status'] = 'APPLIED'
    result['message'] = '%d ops' % count
    result['preview'] = text

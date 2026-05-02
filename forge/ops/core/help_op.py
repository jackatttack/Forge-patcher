# -*- coding: utf-8 -*-
"""
ops.help_op
===========
Show syntax and guidance for one registered forge op.
"""

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'HELP',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS']),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP HELP.
HELP = {
    'summary': 'Show syntax, required directives, common failures, and examples for one op.',
    'subject': ['Registered op name, for example READ_FILE.'],
    'common_failures': [
        'Unknown op name.',
    ],
    'safe_usage': [
        'Use uppercase op names for clarity.',
        'Pair with LIST_OPS when exploring the system.',
    ],
    'minimal_example': [
        'HELP REPLACE_FILE_RANGE',
    ],
    'related_ops': ['LIST_OPS'],
}

HINTS = {
    '_max_hints': 1,
    'op name': {
        'message': 'HELP needs an op name or file path.',
        'why': 'Forge needs to know which op or module you want guidance for.',
        'priority': 100,
        'example': [
            'HELP REPLACE_LINES',
            '',
            'HELP forge/ops/core/grep_ast.py',
        ],
        'next': ['Run LIST_OPS all to discover registered ops'],
    },
    'unknown op': {
        'message': 'Unknown op.',
        'why': 'The requested op is not currently registered in this Forge entry point.',
        'priority': 120,
        'example': [
            'LIST_OPS all',
            '',
            'HELP REPLACE_LINES',
        ],
        'next': ['Run LIST_OPS all', 'Run REFRESH if an edited existing op looks stale'],
    },
    'file not found': {
        'message': 'Help target file was not found.',
        'why': 'HELP can show module docstrings for files, but the path must exist under project root.',
        'priority': 120,
        'example': [
            'LIST_FILES forge/ops/core',
            '',
            'HELP forge/ops/core/grep_ast.py',
        ],
        'next': ['Check the path with LIST_FILES'],
    },
}


def validate(parsed_op):
    """Check op name is present. Returns list of error strings."""
    errors = []

    name = (parsed_op.target or '').strip() or (parsed_op.directives.get('ARGS') or '').strip()
    if not name:
        errors.append('HELP requires an op name target')
    return errors

def execute(ctx, parsed_op, result):
    """Look up op by name and emit its HELP block."""
    from forge.op_help import render_op_help

    name = (parsed_op.target or '').strip() or (parsed_op.directives.get('ARGS') or '').strip()

    # File path — resolve against project root
    if '/' in name or name.endswith('.py'):
        from forge.op_help import _render_file_help
        import os
        rel = name
        text = _render_file_help(rel)
        if text is None:
            result['status'] = 'FAILED_NOT_FOUND'
            result['message'] = 'File not found: ' + rel
            return
        result['status'] = 'APPLIED'
        result['message'] = 'Help for ' + rel
        result['preview'] = text
        return

    text = render_op_help(name)
    if text is None:
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'Unknown op: ' + name
        return

    result['status'] = 'APPLIED'
    result['message'] = 'Help for ' + name.upper()
    result['preview'] = text

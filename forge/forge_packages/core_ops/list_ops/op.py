# -*- coding: utf-8 -*-
"""
LIST_OPS reboot op.

List package-shaped reboot ops discovered by forge_core.registry.
"""

from forge_core.registry import OP_MODULES, OPS_BY_NAME, discover_ops


SPEC = {
    'name': 'LIST_OPS',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(),
    'required_directives': set(),
}

HELP = {
    'summary': 'List reboot ops discovered from package-shaped op folders.',
    'minimal_example': [
        'LIST_OPS',
    ],
}


HINTS = {
    '_max_hints': 1,
    'usage': {
        'message': 'LIST_OPS shows registered reboot ops.',
        'why': 'It is the safest way to discover what this entry point currently knows about.',
        'example': [
            'LIST_OPS',
            '',
            'HELP INSERT',
        ],
        'next': [
            'Use HELP <OP> after finding the op name.',
            'Run AUDIT if an expected op is missing or malformed.',
        ],
    },
}

def validate(parsed_op):
    return []


def execute(ctx, parsed_op, result):
    discover_ops()

    lines = []
    lines.append('REBOOT OPS')
    lines.append('')

    for name in sorted(OPS_BY_NAME.keys()):
        mod = OPS_BY_NAME.get(name)
        help_data = getattr(mod, 'HELP', {}) or {}
        summary = help_data.get('summary') or '(no summary)'
        lines.append('- %-12s %s' % (name, summary))

    result['status'] = 'APPLIED'
    result['message'] = '%d op(s)' % len(OPS_BY_NAME)
    result['preview'] = '\n'.join(lines)
    result['data'] = {
        'ops': sorted(OPS_BY_NAME.keys()),
    }

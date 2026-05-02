# -*- coding: utf-8 -*-
"""
ops.read_file
=============
READ_FILE op — read and return the full contents of a text file.

Returns all lines with line numbers. Prefer PREVIEW with LINES or ANCHOR
for large files where only a slice is needed.
"""

import os

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'READ_FILE',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP READ_FILE.
HELP = {
    'summary': 'Read a full text file and return numbered lines.',
    'subject': ['Relative file path inside project root.'],
    'common_failures': [
        'File not found.',
        'Target escapes project root.',
    ],
    'safe_usage': [
        'Use PREVIEW when you only need a line range.',
        'Prefer this for small files or when full context matters.',
    ],
    'minimal_example': [
        'READ_FILE forge/registry.py',
    ],
    'related_ops': ['PREVIEW', 'LIST_FILES', 'GREP'],
}


def validate(parsed_op):
    """Check path is present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('READ_FILE requires a target path')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve path, read contents, return numbered lines in result preview."""
    file_abs = ctx.resolve_file(parsed_op.target)
    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isfile(file_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'File not found: ' + parsed_op.target
        return

    with open(file_abs, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    numbered = ['%04d: %s' % (i + 1, ln) for i, ln in enumerate(content.splitlines())]

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = '%d lines' % len(numbered)
    result['preview'] = parsed_op.target + ' [%d lines]\n' % len(numbered) + '\n'.join(numbered)

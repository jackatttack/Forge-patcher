# -*- coding: utf-8 -*-
"""
ops.replace_file_range
======================
REPLACE_FILE_RANGE op — replace an explicit line range in a plain text file.

Takes a LINES: start-end directive and overwrites exactly those lines.
Use PREVIEW with LINES first to confirm the range before patching.
"""

import os

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'REPLACE_FILE_RANGE',
    'target_kind': 'file',
    'body_mode': 'optional',

    'allowed_directives': set(['LINES']),
    'required_directives': set(['LINES']),
}

# HELP doc block — surfaces via HELP REPLACE_FILE_RANGE.
HELP = {
    'summary': 'Replace an explicit line range in a text file.',
    'subject': ['Relative file path inside project root.'],
    'common_failures': [
        'Use LINES: start-end, not START_LINE / END_LINE.',
        'LINES out of range for the current file.',
        'Omit body content (empty BEGIN_BODY / END_BODY) to delete the matched range.',

    ],
    'safe_usage': [
        'PREVIEW the target range first.',
        'Verify the result after patching.',
        'Use this for text files or exact top-of-file cleanup when AST patching is not appropriate.',
    ],
    'minimal_example': [
        'REPLACE_FILE_RANGE forge_app.py',
        'LINES: 12-23',
        'BEGIN_BODY',
        "DOCUMENTS_ROOT = '/path/to/Documents'",
        'END_BODY',
    ],
    'related_ops': ['PREVIEW', 'REPLACE_FILE', 'REPLACE_FILE_LINES'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    '_max_hints': 1,
    'lines': {
        'message': 'REPLACE_FILE_RANGE needs LINES: start-end.',
        'why': 'Forge needs an explicit line range to replace in the target file.',
        'priority': 100,
        'example': [
            'PREVIEW docs/example.txt',
            'LINES: 10-25',
            '',
            'REPLACE_FILE_RANGE docs/example.txt',
            'LINES: 12-18',
            'BEGIN_BODY',
            'replacement text',
            'END_BODY',
        ],
        'next': ['PREVIEW the file first to find line numbers', 'HELP REPLACE_FILE_RANGE'],
    },
    'invalid lines range': {
        'message': 'The LINES range is invalid.',
        'why': 'Line ranges must be positive and ordered as start-end.',
        'priority': 100,
        'example': [
            'REPLACE_FILE_RANGE docs/example.txt',
            'LINES: 12-18',
            'BEGIN_BODY',
            'replacement text',
            'END_BODY',
        ],
        'next': ['Use LINES: start-end with start >= 1 and end >= start'],
    },
    'target path': {
        'message': 'REPLACE_FILE_RANGE needs a target file path.',
        'why': 'This op patches a flat text file by explicit line numbers.',
        'priority': 90,
        'example': [
            'REPLACE_FILE_RANGE docs/example.txt',
            'LINES: 12-18',
            'BEGIN_BODY',
            'replacement text',
            'END_BODY',
        ],
        'next': ['LIST_FILES on the parent directory', 'HELP REPLACE_FILE_RANGE'],
    },
    'not found': {
        'message': 'File not found.',
        'why': 'The target path must be an existing file under project root.',
        'priority': 100,
        'example': [
            'LIST_FILES docs',
            '',
            'REPLACE_FILE_RANGE docs/example.txt',
            'LINES: 12-18',
            'BEGIN_BODY',
            'replacement text',
            'END_BODY',
        ],
        'next': ['Check the path with LIST_FILES', 'Use CREATE_FILE if this should be a new file'],
    },
    'escapes project root': {
        'message': 'Target path escapes project root.',
        'why': 'Forge only patches files inside the Pythonista project root.',
        'priority': 100,
        'example': [
            'REPLACE_FILE_RANGE docs/example.txt',
            'LINES: 12-18',
            'BEGIN_BODY',
            'replacement text',
            'END_BODY',
        ],
        'next': ['Use a relative path under project root'],
    },
}


def validate(parsed_op):
    """Check path and LINES directive are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('REPLACE_FILE_RANGE requires a target path')
    lines_range = parsed_op.directives.get('LINES')
    if not isinstance(lines_range, tuple) or len(lines_range) != 2:
        errors.append('REPLACE_FILE_RANGE requires LINES: start-end')
    else:
        a, b = lines_range
        if a < 1 or b < a:
            errors.append('Invalid LINES range')
    return errors

def execute(ctx, parsed_op, result):
    """Resolve path, parse LINES range, replace that range with body content."""
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
        before = f.read()

    src_lines = before.splitlines()
    total = len(src_lines)

    start, end = parsed_op.directives.get('LINES')
    if end > total:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'LINES out of range: file has %d lines' % total
        return

    new_lines = parsed_op.body.splitlines()
    out_lines = src_lines[:start - 1] + new_lines + src_lines[end:]
    after = '\n'.join(out_lines)
    if before.endswith('\n') or parsed_op.body.endswith('\n'):
        after += '\n'

    with open(file_abs, 'w', encoding='utf-8') as f:
        f.write(after)

    ctx.file_cache[file_abs] = after
    ctx.touched_files[file_abs] = {
        'before': before,
        'after': after,
    }

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = 'Replaced lines %d-%d' % (start, end)

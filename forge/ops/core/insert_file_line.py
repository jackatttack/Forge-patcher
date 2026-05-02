# -*- coding: utf-8 -*-
"""
ops.insert_file_line
====================
Insert lines into a plain text file at a given line number.
No anchors needed. Body is spliced in before or after LINE: N.
"""

import os

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'INSERT_FILE_LINE',
    'target_kind': 'file',
    'body_mode': 'required',
    'allowed_directives': set(['LINE', 'POSITION']),
    'required_directives': set(['LINE']),
}

# HELP doc block — surfaces via HELP INSERT_FILE_LINE.
HELP = {
    'summary': 'Insert lines into a plain text file at a given line number.',
    'subject': ['Relative file path inside project root.'],
    'optional_directives': [
        'POSITION: before|after (default after)',
    ],
    'common_failures': [
        'LINE out of range for the current file.',
        'Missing BEGIN_BODY / END_BODY.',
        'POSITION must be before or after.',
    ],
    'safe_usage': [
        'PREVIEW the target area first to confirm the line number.',
        'Use POSITION: before to insert above a section heading.',
        'Use POSITION: after to append below a line.',
        'Prefer this over REPLACE_FILE_RANGE when you only want to insert without replacing.',
    ],
    'minimal_example': [
        'INSERT_FILE_LINE journal/prompt.md',
        'LINE: 40',
        'POSITION: after',
        'BEGIN_BODY',
        '## New Section',
        '',
        'Content here.',
        'END_BODY',
    ],
    'related_ops': ['PREVIEW', 'REPLACE_FILE_RANGE', 'REPLACE_FILE_LINES'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    'line': 'Add LINE: N — the line number to insert at',
    'body required': 'Provide the content to insert as the body',
}


def validate(parsed_op):
    """Check path and LINE directive are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('INSERT_FILE_LINE requires a target path')
    if not parsed_op.body:
        errors.append('INSERT_FILE_LINE requires body content')

    line_val = parsed_op.directives.get('LINE')
    if not isinstance(line_val, int) or line_val < 1:
        errors.append('INSERT_FILE_LINE requires LINE: N (integer >= 1)')

    position = parsed_op.directives.get('POSITION', 'after')
    if position not in ('before', 'after'):
        errors.append('POSITION must be before or after')

    return errors


def execute(ctx, parsed_op, result):
    """Resolve path, find line number, insert body before or after it."""
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
    total     = len(src_lines)

    line_n   = parsed_op.directives.get('LINE')
    position = parsed_op.directives.get('POSITION', 'after')

    if line_n > total:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'LINE out of range: file has %d lines' % total
        return

    new_lines = parsed_op.body.splitlines()

    if position == 'before':
        insert_at = line_n - 1
    else:
        insert_at = line_n

    out_lines = src_lines[:insert_at] + new_lines + src_lines[insert_at:]
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

    result['file']    = parsed_op.target
    result['status']  = 'APPLIED'
    result['message'] = 'Inserted %d lines %s line %d' % (len(new_lines), position, line_n)

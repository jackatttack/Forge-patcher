# -*- coding: utf-8 -*-
"""
ops.clipboard
=============
Copy the raw contents of a file to the iOS clipboard.
No packet output - just the file content.

Usage:
    CLIPBOARD path/to/file.py
"""

import os

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'CLIPBOARD',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(),
    'required_directives': set(),
    "summary": 'Copy the raw contents of a file to the iOS clipboard.',
}


def validate(parsed_op):
    """Check path is present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('CLIPBOARD requires a file path')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve path, read file, copy raw contents to iOS clipboard."""
    from forge.file_ops import resolve_under_root, in_root

    src_abs = resolve_under_root(ctx.project_root, parsed_op.target)

    if not in_root(ctx.project_root, src_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Path escapes project root'
        return

    if not os.path.isfile(src_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'File not found: ' + parsed_op.target
        return

    try:
        with open(src_abs, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = 'Read error: ' + str(e)
        return

    try:
        import clipboard as _cb
        _cb.set(content)
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = 'Clipboard error: ' + str(e)
        return

    result['file']    = parsed_op.target
    result['status']  = 'APPLIED'
    result['silent']  = True
    result['message'] = 'Copied to clipboard: %s (%d chars)' % (
        parsed_op.target, len(content)
    )

# -*- coding: utf-8 -*-
"""
ops.replace_file
================
REPLACE_FILE op — replace the entire contents of an existing text file.

Overwrites the file with the supplied body. Use for config files, flat
data files, or any non-Python file that needs a full rewrite.
"""

import os

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'REPLACE_FILE',
    'target_kind': 'file',
    'body_mode': 'required',
    'allowed_directives': set(),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP REPLACE_FILE.
HELP = {
    'summary': 'Replace the full contents of an existing text file.',
    'subject': ['Relative file path inside project root.'],
    'common_failures': [
        'File not found.',
        'Target escapes project root.',
        'Missing BEGIN_BODY / END_BODY.',
    ],
    'safe_usage': [
        'Use this for full rewrites of docs, JSON, Markdown, or other plain text files.',
        'Prefer AST ops for Python when you only need to change a specific target.',
        'Preview or read the file first if you are not intentionally overwriting everything.',
    ],
    'minimal_example': [
        'REPLACE_FILE docs/example.txt',
        'BEGIN_BODY',
        'hello world',
        'END_BODY',
    ],
    'related_ops': ['READ_FILE', 'PREVIEW', 'REPLACE_FILE_LINES', 'REPLACE_FILE_RANGE'],
}

HINTS = {
    '_max_hints': 1,
    'body content': {
        'message': 'REPLACE_FILE needs body content.',
        'why': 'Forge overwrites the whole file with the supplied body.',
        'priority': 100,
        'example': [
            'REPLACE_FILE docs/example.txt',
            'BEGIN_BODY',
            'new full file contents',
            'END_BODY',
        ],
        'next': ['Add BEGIN_BODY / END_BODY', 'Use PREVIEW first unless full overwrite is intentional'],
    },
    'target path': {
        'message': 'REPLACE_FILE needs a target path.',
        'why': 'Forge needs to know which existing file to overwrite.',
        'priority': 100,
        'example': [
            'REPLACE_FILE docs/example.txt',
            'BEGIN_BODY',
            'new full file contents',
            'END_BODY',
        ],
        'next': ['Use LIST_FILES to check the path', 'HELP REPLACE_FILE'],
    },
    'file not found': {
        'message': 'File not found.',
        'why': 'REPLACE_FILE only overwrites existing files. Use CREATE_FILE for new files.',
        'priority': 120,
        'example': [
            'LIST_FILES docs',
            '',
            'CREATE_FILE docs/example.txt',
            'BEGIN_BODY',
            'contents',
            'END_BODY',
        ],
        'next': ['Check the path with LIST_FILES', 'Use CREATE_FILE if this should be new'],
    },
    'escapes project root': {
        'message': 'Target path escapes project root.',
        'why': 'Forge only patches files inside the Pythonista project root.',
        'priority': 100,
        'example': [
            'REPLACE_FILE docs/example.txt',
            'BEGIN_BODY',
            'new full file contents',
            'END_BODY',
        ],
        'next': ['Use a relative path under project root'],
    },
}


def validate(parsed_op):
    """Check path and body are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('REPLACE_FILE requires a target path')
    if not parsed_op.body:
        errors.append('REPLACE_FILE requires body content')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve path, check file exists, overwrite with body content."""
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

    after = parsed_op.body

    with open(file_abs, 'w', encoding='utf-8') as f:
        f.write(after)

    ctx.file_cache[file_abs] = after
    ctx.touched_files[file_abs] = {
        'before': before,
        'after': after,
    }

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = 'Replaced file: ' + parsed_op.target

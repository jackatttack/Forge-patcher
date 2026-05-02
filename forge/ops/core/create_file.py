# -*- coding: utf-8 -*-
"""
ops.create_file
===============
CREATE_FILE op — create a new file at a given path with provided content.

Writes the body to a new file under project root. Fails if the path
escapes root. Use for scaffolding new modules, configs, or data files.
"""

import os

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'CREATE_FILE',
    'target_kind': 'file',
    'body_mode': 'required',
    'allowed_directives': set(),
    'required_directives': set(),
    "summary": 'Create a new file at a given path with the provided body content.',
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.

HELP = {
    'summary': 'Create a new file at a relative path under the project root.',
    'subject': [
        'Required. Relative path for the new file.',
        'Example: CREATE_FILE utils/new_tool.py',
    ],
    'required_directives': [],
    'optional_directives': [],
    'body': [
        'Required. File contents to write.',
        'Use BEGIN_BODY / END_BODY for anything more than one short line.',
    ],
    'common_failures': [
        'Missing target path.',
        'Missing body content.',
        'File already exists — use REPLACE_FILE if you intend to overwrite.',
        'Target escapes project root.',
    ],
    'safe_usage': [
        'Use for scaffolding new files only.',
        'Prefer REPLACE_FILE for deliberate overwrites.',
        'Parent directories are created automatically.',
        'Keep paths relative to project root.',
    ],
    'related_ops': ['REPLACE_FILE', 'PREVIEW', 'DELETE_FILE', 'LIST_FILES'],
    'minimal_example': [
        'CREATE_FILE scratch/hello.py',
        'BEGIN_BODY',
        'print("hello")',
        'END_BODY',
    ],
}

HINTS = {
    '_max_hints': 1,
    'body content': {
        'message': 'CREATE_FILE needs body content.',
        'why': 'Forge needs the exact contents to write into the new file.',
        'priority': 100,
        'example': [
            'CREATE_FILE scratch/hello.py',
            'BEGIN_BODY',
            'print("hello")',
            'END_BODY',
        ],
        'next': ['Add BEGIN_BODY / END_BODY', 'HELP CREATE_FILE'],
    },
    'target path': {
        'message': 'CREATE_FILE needs a target path.',
        'why': 'Forge needs to know where to create the new file under project root.',
        'priority': 100,
        'example': [
            'CREATE_FILE scratch/hello.py',
            'BEGIN_BODY',
            'print("hello")',
            'END_BODY',
        ],
        'next': ['Use a relative path under project root', 'HELP CREATE_FILE'],
    },
    'already exists': {
        'message': 'File already exists.',
        'why': 'CREATE_FILE will not overwrite existing files.',
        'priority': 100,
        'example': [
            'REPLACE_FILE scratch/hello.py',
            'BEGIN_BODY',
            'new contents',
            'END_BODY',
        ],
        'next': ['Use REPLACE_FILE if overwriting is intentional', 'Use a different path'],
    },
    'escapes project root': {
        'message': 'Target path escapes project root.',
        'why': 'Forge only creates files inside the Pythonista project root.',
        'priority': 100,
        'example': [
            'CREATE_FILE scratch/hello.py',
            'BEGIN_BODY',
            'print("hello")',
            'END_BODY',
        ],
        'next': ['Use a relative path under project root'],
    },
}


def validate(parsed_op):
    """Check path and body are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('CREATE_FILE requires a target path')
    if not parsed_op.body:
        errors.append('CREATE_FILE requires body content')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve path, check for conflicts, create parent dirs, write file to disk."""
    file_abs = ctx.resolve_file(parsed_op.target)
    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if os.path.exists(file_abs):
        result['status'] = 'SKIPPED_ALREADY_PRESENT'
        result['message'] = 'File already exists: ' + parsed_op.target
        return

    parent = os.path.dirname(file_abs)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)

    body = parsed_op.body
    with open(file_abs, 'w', encoding='utf-8') as f:

        f.write(body)

    ctx.file_cache[file_abs] = body
    ctx.touched_files[file_abs] = {
        'before': None,
        'after': body,
    }

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = 'Created: ' + parsed_op.target

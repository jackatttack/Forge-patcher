# -*- coding: utf-8 -*-
"""
ops.delete_file
===============
Delete-file op.
"""

import os

from forge.file_ops import resolve_under_root, in_root

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'DELETE_FILE',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['CONFIRM']),
    'required_directives': set(['CONFIRM']),
}

# HELP doc block — surfaces via HELP DELETE_FILE.
HELP = {
    'summary': 'Delete a file under project root.',
    'subject': ['Relative file path inside project root.'],
    'common_failures': [
        'Missing CONFIRM: yes.',
        'File not found.',
        'Target escapes project root.',
    ],
    'safe_usage': [
        'Use this only when you intend to remove the file entirely.',
        'Consider COPY_FILE first if you may want a backup.',
    ],
    'minimal_example': [
        'DELETE_FILE docs/tmp.txt',
        'CONFIRM: yes',
    ],
    'related_ops': ['COPY_FILE', 'MOVE_FILE', 'LIST_FILES'],
}

HINTS = {
    '_max_hints': 1,
    'confirm': {
        'message': 'DELETE_FILE requires CONFIRM: yes.',
        'why': 'Deleting files is destructive, so Forge requires explicit confirmation.',
        'priority': 100,
        'example': [
            'DELETE_FILE scratch/tmp.txt',
            'CONFIRM: yes',
        ],
        'next': ['Use LIST_FILES first if unsure', 'Consider MOVE_FILE or COPY_FILE before deleting'],
    },
    'target path': {
        'message': 'DELETE_FILE needs a target file path.',
        'why': 'Forge needs to know which file to delete under project root.',
        'priority': 100,
        'example': [
            'DELETE_FILE scratch/tmp.txt',
            'CONFIRM: yes',
        ],
        'next': ['Use LIST_FILES to check the path', 'HELP DELETE_FILE'],
    },
    'file not found': {
        'message': 'File not found.',
        'why': 'DELETE_FILE only deletes existing files.',
        'priority': 120,
        'example': [
            'LIST_FILES scratch',
            '',
            'DELETE_FILE scratch/tmp.txt',
            'CONFIRM: yes',
        ],
        'next': ['Check the path with LIST_FILES'],
    },
    'escapes project root': {
        'message': 'Target path escapes project root.',
        'why': 'Forge only deletes files inside the Pythonista project root.',
        'priority': 100,
        'example': [
            'DELETE_FILE scratch/tmp.txt',
            'CONFIRM: yes',
        ],
        'next': ['Use a relative path under project root'],
    },
}


def validate(parsed_op):
    """Check path is present and CONFIRM: yes is set. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('DELETE_FILE requires a target path')
    if (parsed_op.directives.get('CONFIRM') or '').lower() != 'yes':
        errors.append('DELETE_FILE requires CONFIRM: yes')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve path, confirm file exists, delete from disk."""
    file_abs = resolve_under_root(ctx.project_root, parsed_op.target)

    if not in_root(ctx.project_root, file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isfile(file_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'File not found: ' + parsed_op.target
        return

    os.remove(file_abs)

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = 'Deleted: ' + parsed_op.target

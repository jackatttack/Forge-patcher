# -*- coding: utf-8 -*-
"""
ops.delete_dir
==============
Delete-directory op for quick cleanup.
"""

import os
import shutil

from forge.file_ops import resolve_under_root, in_root

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'DELETE_DIR',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['CONFIRM']),
    'required_directives': set(['CONFIRM']),
    "summary": 'Permanently delete a directory and all its contents. Requires CONFIRM: yes.',
}

HELP = {
    'summary': 'Permanently delete a directory under project root. Requires explicit confirmation.',
    'subject': [
        'Required. Relative path to the directory to delete.',
        'Example: DELETE_DIR scratch/old_lab',
    ],
    'required_directives': [
        'CONFIRM: yes',
    ],
    'optional_directives': [],
    'body': [
        'Forbidden. DELETE_DIR does not accept body content.',
    ],
    'common_failures': [
        'Missing target path.',
        'Missing CONFIRM: yes.',
        'Target does not exist or is not a directory.',
        'Target escapes project root.',
    ],
    'safe_usage': [
        'Use LIST_FILES first if unsure what the directory contains.',
        'Prefer MOVE_DIR to archive important work instead of deleting it.',
        'Never use on broad project directories unless Jack explicitly asked.',
        'Deletion is permanent unless a branch/run snapshot exists.',
    ],
    'related_ops': ['LIST_FILES', 'MOVE_DIR', 'DELETE_FILE', 'BRANCH'],
    'minimal_example': [
        'DELETE_DIR scratch/old_lab',
        'CONFIRM: yes',
    ],
}

HINTS = {
    '_max_hints': 1,
    'confirm': {
        'message': 'DELETE_DIR requires CONFIRM: yes.',
        'why': 'Deleting directories is destructive, so Forge requires explicit confirmation.',
        'priority': 100,
        'example': [
            'DELETE_DIR scratch/old_lab',
            'CONFIRM: yes',
        ],
        'next': ['Use LIST_FILES first if unsure', 'Prefer MOVE_DIR when preserving work'],
    },
    'target path': {
        'message': 'DELETE_DIR needs a target directory path.',
        'why': 'Forge needs to know which directory to delete under project root.',
        'priority': 100,
        'example': [
            'DELETE_DIR scratch/old_lab',
            'CONFIRM: yes',
        ],
        'next': ['Use LIST_FILES to check the path', 'HELP DELETE_DIR'],
    },
    'directory not found': {
        'message': 'Directory not found.',
        'why': 'DELETE_DIR only deletes existing directories.',
        'priority': 120,
        'example': [
            'LIST_FILES scratch',
            '',
            'DELETE_DIR scratch/old_lab',
            'CONFIRM: yes',
        ],
        'next': ['Check the path with LIST_FILES'],
    },
    'not a directory': {
        'message': 'Target is not a directory.',
        'why': 'DELETE_DIR only removes directories. Use DELETE_FILE for files.',
        'priority': 120,
        'example': [
            'DELETE_FILE scratch/tmp.txt',
            'CONFIRM: yes',
        ],
        'next': ['Use DELETE_FILE for files', 'Use LIST_FILES to inspect the path'],
    },
    'escapes project root': {
        'message': 'Target path escapes project root.',
        'why': 'Forge only deletes directories inside the Pythonista project root.',
        'priority': 100,
        'example': [
            'DELETE_DIR scratch/old_lab',
            'CONFIRM: yes',
        ],
        'next': ['Use a relative path under project root'],
    },
}


def validate(parsed_op):
    """Check path is present and CONFIRM: yes is set. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('DELETE_DIR requires a target path')
    if (parsed_op.directives.get('CONFIRM') or '').lower() != 'yes':
        errors.append('DELETE_DIR requires CONFIRM: yes')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve path and recursively delete directory from disk."""
    dir_abs = resolve_under_root(ctx.project_root, parsed_op.target)

    if not in_root(ctx.project_root, dir_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isdir(dir_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Directory not found: ' + parsed_op.target
        return

    shutil.rmtree(dir_abs)

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = 'Deleted dir: ' + parsed_op.target

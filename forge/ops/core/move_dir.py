# -*- coding: utf-8 -*-
"""
ops.move_dir
============
Move/rename a directory within the project root.
"""

import os
import shutil

from forge.file_ops import resolve_under_root, in_root, ensure_parent_dir

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'MOVE_DIR',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': {'DEST'},
    'required_directives': {'DEST'},
    "summary": 'Move or rename a directory to a new path inside project root.',
}

HELP = {
    'summary': 'Move or rename a directory to a new path inside project root.',
    'subject': [
        'Required. Relative source directory path inside project root.',
        'Example: MOVE_DIR labs/old_name',
    ],
    'required_directives': [
        'DEST: relative destination directory path',
    ],
    'optional_directives': [],
    'body': [
        'Forbidden. MOVE_DIR does not accept body content.',
    ],
    'common_failures': [
        'Missing source path.',
        'Missing DEST directive.',
        'Source directory not found.',
        'Destination already exists.',
        'Source or destination escapes project root.',
    ],
    'safe_usage': [
        'Use LIST_FILES first when reorganising project folders.',
        'Use BRANCH before moving important directories.',
        'Prefer MOVE_DIR over DELETE_DIR when preserving work.',
        'Keep both source and destination paths relative to project root.',
    ],
    'related_ops': ['LIST_FILES', 'BRANCH', 'MOVE_FILE', 'COPY_FILE', 'DELETE_DIR'],
    'minimal_example': [
        'MOVE_DIR labs/old_lab',
        'DEST: archive/2026/old_lab',
    ],
}

HINTS = {
    '_max_hints': 1,
    'dest': {
        'message': 'MOVE_DIR needs DEST.',
        'why': 'Forge needs to know the new relative path for the directory.',
        'priority': 100,
        'example': [
            'MOVE_DIR labs/old_lab',
            'DEST: archive/2026/old_lab',
        ],
        'next': ['Add DEST: <relative destination directory path>', 'HELP MOVE_DIR'],
    },
    'target path': {
        'message': 'MOVE_DIR needs a source directory path.',
        'why': 'Forge needs to know which existing directory to move.',
        'priority': 100,
        'example': [
            'MOVE_DIR labs/old_lab',
            'DEST: archive/2026/old_lab',
        ],
        'next': ['Use LIST_FILES to check the source path', 'HELP MOVE_DIR'],
    },
    'source directory not found': {
        'message': 'Source directory not found.',
        'why': 'MOVE_DIR only moves existing directories.',
        'priority': 120,
        'example': [
            'LIST_FILES labs',
            '',
            'MOVE_DIR labs/old_lab',
            'DEST: archive/2026/old_lab',
        ],
        'next': ['Check the source path with LIST_FILES'],
    },
    'destination already exists': {
        'message': 'Destination already exists.',
        'why': 'MOVE_DIR will not overwrite an existing destination directory.',
        'priority': 120,
        'example': [
            'MOVE_DIR labs/old_lab',
            'DEST: archive/2026/old_lab_v2',
        ],
        'next': ['Choose a new DEST', 'Move/delete the existing destination only if safe'],
    },
    'path escapes project root': {
        'message': 'Source or destination escapes project root.',
        'why': 'Forge only moves directories inside the Pythonista project root.',
        'priority': 100,
        'example': [
            'MOVE_DIR labs/old_lab',
            'DEST: archive/2026/old_lab',
        ],
        'next': ['Use relative paths under project root'],
    },
}


def validate(parsed_op):
    """Check source and destination paths are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('MOVE_DIR requires a target path')
    if not (parsed_op.directives.get('DEST') or '').strip():
        errors.append('Missing required directive for MOVE_DIR: DEST')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve source and dest paths, move directory, optionally overwrite."""
    src_abs = resolve_under_root(ctx.project_root, parsed_op.target)
    dst_abs = resolve_under_root(ctx.project_root, parsed_op.directives.get('DEST'))

    if not (in_root(ctx.project_root, src_abs) and in_root(ctx.project_root, dst_abs)):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Path escapes project root'
        return

    if not os.path.isdir(src_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Source directory not found: ' + parsed_op.target
        return

    if os.path.exists(dst_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Destination already exists: ' + parsed_op.directives.get('DEST')
        return

    ensure_parent_dir(dst_abs)
    shutil.move(src_abs, dst_abs)

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = '%s -> %s' % (parsed_op.target, parsed_op.directives.get('DEST'))

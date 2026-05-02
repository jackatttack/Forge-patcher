# -*- coding: utf-8 -*-
"""
ops.move_file
=============
Move/rename-file op.
"""

import os

from forge.file_ops import resolve_under_root, in_root, ensure_parent_dir

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'MOVE_FILE',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['DEST']),
    'required_directives': set(['DEST']),
}

# HELP doc block — surfaces via HELP MOVE_FILE.
HELP = {
    'summary': 'Move or rename a file to a new path under project root.',
    'subject': ['Relative source file path inside project root.'],
    'common_failures': [
        'Missing DEST directive.',
        'Source not found.',
        'Destination already exists.',
        'Source or destination escapes project root.',
    ],
    'safe_usage': [
        'Use this for renames and path cleanups after confirming the new destination.',
        'Unlike COPY_FILE, this removes the original source path.',
    ],
    'minimal_example': [
        'MOVE_FILE old_name.txt',
        'DEST: archive/new_name.txt',
    ],
    'related_ops': ['COPY_FILE', 'LIST_FILES', 'DELETE_FILE'],
}

HINTS = {
    '_max_hints': 1,
    'dest': {
        'message': 'MOVE_FILE needs DEST.',
        'why': 'Forge needs to know the new relative path for the file.',
        'priority': 100,
        'example': [
            'MOVE_FILE docs/old.txt',
            'DEST: archive/old.txt',
        ],
        'next': ['Add DEST: <relative destination file path>', 'HELP MOVE_FILE'],
    },
    'target path': {
        'message': 'MOVE_FILE needs a source file path.',
        'why': 'Forge needs to know which existing file to move.',
        'priority': 100,
        'example': [
            'MOVE_FILE docs/old.txt',
            'DEST: archive/old.txt',
        ],
        'next': ['Use LIST_FILES to check the source path', 'HELP MOVE_FILE'],
    },
    'source not found': {
        'message': 'Source file not found.',
        'why': 'MOVE_FILE only moves existing files.',
        'priority': 120,
        'example': [
            'LIST_FILES docs',
            '',
            'MOVE_FILE docs/old.txt',
            'DEST: archive/old.txt',
        ],
        'next': ['Check the source path with LIST_FILES'],
    },
    'destination already exists': {
        'message': 'Destination already exists.',
        'why': 'MOVE_FILE will not overwrite an existing destination.',
        'priority': 120,
        'example': [
            'MOVE_FILE docs/old.txt',
            'DEST: archive/old_v2.txt',
        ],
        'next': ['Choose a new DEST', 'Delete or move the existing destination only if safe'],
    },
    'path escapes project root': {
        'message': 'Source or destination escapes project root.',
        'why': 'Forge only moves files inside the Pythonista project root.',
        'priority': 100,
        'example': [
            'MOVE_FILE docs/old.txt',
            'DEST: archive/old.txt',
        ],
        'next': ['Use relative paths under project root'],
    },
}


def validate(parsed_op):
    """Check source and destination paths are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('MOVE_FILE requires a target path')
    if not (parsed_op.directives.get('DEST') or '').strip():
        errors.append('Missing required directive for MOVE_FILE: DEST')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve source and dest paths, move file, optionally overwrite."""
    src_abs = resolve_under_root(ctx.project_root, parsed_op.target)
    dst_abs = resolve_under_root(ctx.project_root, parsed_op.directives.get('DEST'))

    if not (in_root(ctx.project_root, src_abs) and in_root(ctx.project_root, dst_abs)):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Path escapes project root'
        return

    if not os.path.isfile(src_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Source not found: ' + parsed_op.target
        return

    if os.path.exists(dst_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Destination already exists: ' + parsed_op.directives.get('DEST')
        return

    ensure_parent_dir(dst_abs)
    os.rename(src_abs, dst_abs)

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = '%s -> %s' % (parsed_op.target, parsed_op.directives.get('DEST'))

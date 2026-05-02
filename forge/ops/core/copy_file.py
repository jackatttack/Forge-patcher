# -*- coding: utf-8 -*-
"""
ops.copy_file
=============
Copy-file op.
"""

import os
import shutil

from forge.file_ops import resolve_under_root, in_root, ensure_parent_dir

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'COPY_FILE',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['DEST', 'OVERWRITE']),
    'required_directives': set(['DEST']),
}

# HELP doc block — surfaces via HELP COPY_FILE.
HELP = {
    'summary': 'Copy one file to a new destination under project root.',
    'subject': ['Relative source file path inside project root.'],
    'common_failures': [
        'Missing DEST directive.',
        'Source not found.',
        'Destination already exists (use OVERWRITE: yes to force).',
        'Source or destination escapes project root.',
        'Missing or invalid target.',
        'Absolute or escaping paths are rejected.',
    ],
    'safe_usage': [
        'Use this when you want a backup or duplicate before riskier edits.',
        'DEST should normally include the full new file path, not just a folder.',
        'Use OVERWRITE: yes to replace an existing destination — useful for promoting dev files.',
        'Use relative paths only.',
    ],
    'minimal_example': [
        'COPY_FILE docs/old.txt',
        'DEST: docs/old_backup.txt',
        '',
        'COPY_FILE forge/engine_dev.py',
        'DEST: forge/engine.py',
        'OVERWRITE: yes',
    ],
    'related_ops': ['MOVE_FILE', 'READ_FILE', 'LIST_FILES'],
}

HINTS = {
    '_max_hints': 1,
    'dest': {
        'message': 'COPY_FILE needs DEST.',
        'why': 'Forge needs to know where to copy the source file.',
        'priority': 100,
        'example': [
            'COPY_FILE docs/source.txt',
            'DEST: docs/source_backup.txt',
        ],
        'next': ['Add DEST: <relative destination path>', 'HELP COPY_FILE'],
    },
    'target path': {
        'message': 'COPY_FILE needs a source file path.',
        'why': 'Forge needs to know which existing file to copy.',
        'priority': 100,
        'example': [
            'COPY_FILE docs/source.txt',
            'DEST: docs/source_backup.txt',
        ],
        'next': ['Use LIST_FILES to check the source path', 'HELP COPY_FILE'],
    },
    'source not found': {
        'message': 'Source file not found.',
        'why': 'COPY_FILE only copies existing files.',
        'priority': 120,
        'example': [
            'LIST_FILES docs',
            '',
            'COPY_FILE docs/source.txt',
            'DEST: docs/source_backup.txt',
        ],
        'next': ['Check the source path with LIST_FILES'],
    },
    'destination already exists': {
        'message': 'Destination already exists.',
        'why': 'COPY_FILE avoids overwriting unless OVERWRITE: yes is provided.',
        'priority': 120,
        'example': [
            'COPY_FILE docs/source.txt',
            'DEST: docs/source_backup.txt',
            'OVERWRITE: yes',
        ],
        'next': ['Choose a new DEST', 'Use OVERWRITE: yes only when intentional'],
    },
    'path escapes project root': {
        'message': 'Source or destination escapes project root.',
        'why': 'Forge only copies files inside the Pythonista project root.',
        'priority': 100,
        'example': [
            'COPY_FILE docs/source.txt',
            'DEST: docs/source_backup.txt',
        ],
        'next': ['Use relative paths under project root'],
    },
}


def validate(parsed_op):
    """Check source and destination paths are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('COPY_FILE requires a target path')
    if not (parsed_op.directives.get('DEST') or '').strip():
        errors.append('Missing required directive for COPY_FILE: DEST')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve source and dest paths, copy file, optionally overwrite."""
    src_abs   = resolve_under_root(ctx.project_root, parsed_op.target)
    dst_abs   = resolve_under_root(ctx.project_root, parsed_op.directives.get('DEST'))
    overwrite = (parsed_op.directives.get('OVERWRITE') or '').strip().lower() == 'yes'

    if not (in_root(ctx.project_root, src_abs) and in_root(ctx.project_root, dst_abs)):
        result['status']  = 'FAILED_INVALID_PATH'
        result['message'] = 'Path escapes project root'
        return

    if not os.path.isfile(src_abs):
        result['status']  = 'FAILED_IO'
        result['message'] = 'Source not found: ' + parsed_op.target
        return

    if os.path.exists(dst_abs) and not overwrite:
        result['status']  = 'SKIPPED_ALREADY_PRESENT'
        result['message'] = 'Destination already exists: ' + parsed_op.directives.get('DEST')
        return

    ensure_parent_dir(dst_abs)
    shutil.copy2(src_abs, dst_abs)

    result['file']    = parsed_op.target
    result['status']  = 'APPLIED'
    result['message'] = '%s -> %s' % (parsed_op.target, parsed_op.directives.get('DEST'))

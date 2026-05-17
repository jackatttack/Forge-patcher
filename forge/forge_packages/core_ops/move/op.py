# -*- coding: utf-8 -*-
"""
MOVE reboot op.

Move a project-relative text file from one path to another.

Contract:

MOVE source/path.txt
TO: destination/path.txt
OVERWRITE: no|yes

Recovery model:
- source is recorded as existed_before=True with after=''
- destination is recorded with its real previous state
- REVERT_RUN can restore the source and either restore/delete the destination
"""

import os

from forge_core.file_safety import safe_target, read_text, write_text


SPEC = {
    'name': 'MOVE',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['CONFIRM', 'TO', 'OVERWRITE']),
    'required_directives': set(['TO']),
}


HELP = {
    'summary': 'Move a project-relative file and record recovery metadata for both paths.',
    'minimal_example': [
        'MOVE scratch/old_name.py',
        'TO: scratch/new_name.py',
        '',
        'MOVE scratch/source.py',
        'TO: scratch/existing.py',
        'OVERWRITE: yes',
    ],
}


HINTS = {
    '_max_hints': 1,
    'requires to': {
        'message': 'MOVE needs TO.',
        'why': 'MOVE needs to know the destination path before it can safely rename or relocate a file.',
        'example': [
            'MOVE scratch/old_name.py',
            'TO: scratch/new_name.py',
        ],
        'next': [
            'Add TO: destination/path under the MOVE line.',
            'Run HELP MOVE if unsure of the shape.',
        ],
    },
    'destination exists': {
        'message': 'Destination already exists.',
        'why': 'MOVE will not overwrite an existing file unless the bundle says so explicitly.',
        'example': [
            'MOVE scratch/source.py',
            'TO: scratch/existing.py',
            'OVERWRITE: yes',
        ],
        'next': [
            'Use a different destination path, or add OVERWRITE: yes deliberately.',
            'PREVIEW the destination first if you are not sure what it contains.',
        ],
    },
    'source file not found': {
        'message': 'MOVE source was not found.',
        'why': 'The source path must point to an existing project-relative file.',
        'example': [
            'LIST_FILES scratch',
            'MOVE scratch/old_name.py',
            'TO: scratch/new_name.py',
        ],
        'next': [
            'Check the source path with LIST_FILES or SEARCH.',
            'Use project-relative paths only.',
        ],
    },
    'source and destination must be different': {
        'message': 'MOVE source and destination are the same.',
        'why': 'A move must change the file path.',
        'example': [
            'MOVE scratch/name.py',
            'TO: scratch/new_name.py',
        ],
        'next': [
            'Change TO: to a different path.',
        ],
    },
}


def _truthy(value):
    return str(value or '').strip().lower() in ('1', 'yes', 'y', 'true', 'on')


def validate(parsed_op):
    errors = []
    target = (parsed_op.get('target') or '').strip()
    directives = parsed_op.get('directives') or {}

    if not target:
        errors.append('MOVE requires a source path')

    dest = str(directives.get('TO') or '').strip()
    if not dest:
        errors.append('MOVE requires TO: destination/path')

    overwrite = str(directives.get('OVERWRITE') or 'no').strip().lower()
    if overwrite not in ('', '0', '1', 'no', 'yes', 'n', 'y', 'false', 'true', 'off', 'on'):
        errors.append('MOVE OVERWRITE must be yes or no')

    if target and dest and target == dest:
        errors.append('MOVE source and destination must be different')

    return errors


def _record_touched_pair(ctx, result, source_touch, dest_touch):
    touched = [source_touch, dest_touch]
    result['touched'] = touched

    run = (ctx or {}).get('run') or {}
    run.setdefault('touched_files', []).extend(touched)


def execute(ctx, parsed_op, result):
    source = (parsed_op.get('target') or '').strip()
    directives = parsed_op.get('directives') or {}
    dest = str(directives.get('TO') or '').strip()
    overwrite = _truthy(directives.get('OVERWRITE'))

    root, src_abs, src_err = safe_target(ctx, source)
    if src_err:
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = src_err
        return

    root, dest_abs, dest_err = safe_target(ctx, dest)
    if dest_err:
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = dest_err
        return

    if not os.path.isfile(src_abs):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'Source file not found: ' + source
        return

    dest_existed = os.path.exists(dest_abs)
    if dest_existed and not os.path.isfile(dest_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Destination exists but is not a file: ' + dest
        return

    if dest_existed and not overwrite:
        result['status'] = 'FAILED_EXISTS'
        result['message'] = 'Destination exists; use OVERWRITE: yes'
        return

    try:
        before_src = read_text(src_abs)
        before_dest = read_text(dest_abs) if dest_existed else ''
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = '%s: %s' % (type(e).__name__, e)
        return

    try:
        write_text(dest_abs, before_src)
        os.remove(src_abs)
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = '%s: %s' % (type(e).__name__, e)
        return

    source_touch = {
        'rel': source,
        'before': before_src,
        'after': '',
        'existed_before': True,
        'kind': 'file',
    }
    dest_touch = {
        'rel': dest,
        'before': before_dest,
        'after': before_src,
        'existed_before': bool(dest_existed),
        'kind': 'file',
    }
    _record_touched_pair(ctx, result, source_touch, dest_touch)

    result['status'] = 'APPLIED'
    result['message'] = 'Moved %s -> %s' % (source, dest)
    result['file'] = source
    result['preview'] = result['message']
    result['data'] = {
        'source': source,
        'destination': dest,
        'overwrite': bool(overwrite),
        'destination_existed': bool(dest_existed),
    }

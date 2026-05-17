# -*- coding: utf-8 -*-
"""
REPLACE_FILE reboot op.

Replace an existing text file and record recovery metadata so DIFF and
REVERT_RUN can inspect and restore the previous state.
"""

import os

from forge_core.file_safety import read_text, record_touched, safe_target, touched_file, write_text


SPEC = {
    'name': 'REPLACE_FILE',
    'target_kind': 'path',
    'body_mode': 'required',
    'allowed_directives': set(['CONFIRM']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Replace an existing text file under the project root and track it for recovery.',
    'minimal_example': [
        'REPLACE_FILE scratch/example.txt',
        'BEGIN_BODY',
        'new contents',
        'END_BODY',
    ],
}


HINTS = {
    '_max_hints': 1,
    'body': {
        'message': 'REPLACE_FILE needs body content.',
        'why': 'Full-file replacement needs the complete new file text.',
        'example': [
            'REPLACE_FILE scratch/example.txt',
            'BEGIN_BODY',
            'new full contents',
            'END_BODY',
        ],
        'next': [
            'PREVIEW the file first.',
            'Use REPLACE for narrower AST, line-range, or exact-block edits.',
        ],
    },
    'not found': {
        'message': 'REPLACE_FILE target was not found.',
        'why': 'REPLACE_FILE is for existing files; CREATE_FILE creates new files.',
        'example': [
            'CREATE_FILE scratch/example.txt',
            'BEGIN_BODY',
            'contents',
            'END_BODY',
        ],
        'next': [
            'Use CREATE_FILE for new files.',
            'Check the path with LIST_FILES.',
        ],
    },
}

def validate(parsed_op):
    errors = []
    if not (parsed_op.get('target') or '').strip():
        errors.append('REPLACE_FILE requires a target path')
    if not parsed_op.get('body'):
        errors.append('REPLACE_FILE requires body content')
    return errors


def execute(ctx, parsed_op, result):
    target = (parsed_op.get('target') or '').strip()
    body = parsed_op.get('body') or ''

    root, abs_path, err = safe_target(ctx, target)
    if err:
        result['status'] = 'FAILED_IO'
        result['message'] = err
        return

    if not os.path.exists(abs_path):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'File not found: ' + target
        return

    if not os.path.isfile(abs_path):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Target exists but is not a file: ' + target
        return

    before = read_text(abs_path)

    if before == body:
        result['status'] = 'SKIPPED_ALREADY_APPLIED'
        result['message'] = 'File already has requested content: ' + target
        result['file'] = target
        result['data'] = {
            'path': target,
            'bytes': len(body),
            'changed': False,
        }
        return

    write_text(abs_path, body)

    touched = touched_file(target, before, body, existed_before=True)
    record_touched(ctx, result, touched)

    result['status'] = 'APPLIED'
    result['message'] = 'Replaced file: ' + target
    result['preview'] = 'REPLACE_FILE %s\n%d bytes written' % (target, len(body))
    result['file'] = target
    result['data'] = {
        'path': target,
        'bytes': len(body),
        'changed': True,
    }

# -*- coding: utf-8 -*-
"""
CREATE_FILE reboot op.

Creates a project-relative text file and records enough recovery metadata for
DIFF / REVERT_RUN to know whether the file existed before the run.
"""

import os


SPEC = {
    'name': 'CREATE_FILE',
    'target_kind': 'path',
    'body_mode': 'required',
    'allowed_directives': set(['CONFIRM']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Create or replace a text file under the project root and track it for recovery.',
    'minimal_example': [
        'CREATE_FILE scratch/example.txt',
        'BEGIN_BODY',
        'hello',
        'END_BODY',
    ],
}


HINTS = {
    '_max_hints': 1,
    'body': {
        'message': 'CREATE_FILE needs body content.',
        'why': 'Forge needs the text that should be written to the new file.',
        'example': [
            'CREATE_FILE scratch/example.txt',
            'BEGIN_BODY',
            'hello',
            'END_BODY',
        ],
        'next': [
            'Add BEGIN_BODY / END_BODY.',
            'Use REPLACE_FILE if the file already exists and you mean to overwrite it.',
        ],
    },
    'exists': {
        'message': 'CREATE_FILE is for new files.',
        'why': 'Existing files are protected from accidental overwrite.',
        'example': [
            'REPLACE_FILE scratch/example.txt',
            'BEGIN_BODY',
            'replacement',
            'END_BODY',
        ],
        'next': [
            'Use REPLACE_FILE for deliberate full-file replacement.',
            'Use PREVIEW first if unsure.',
        ],
    },
}

def validate(parsed_op):
    errors = []
    if not (parsed_op.get('target') or '').strip():
        errors.append('CREATE_FILE requires a target path')
    if not parsed_op.get('body'):
        errors.append('CREATE_FILE requires body content')
    return errors


def _in_root(root, path):
    root_real = os.path.realpath(os.path.abspath(root))
    path_real = os.path.realpath(os.path.abspath(path))
    return path_real == root_real or path_real.startswith(root_real + os.sep)


def execute(ctx, parsed_op, result):
    root = os.path.abspath(ctx.get('project_root') or os.getcwd())
    target = (parsed_op.get('target') or '').strip()
    body = parsed_op.get('body') or ''

    abs_path = os.path.abspath(os.path.join(root, target))
    if not _in_root(root, abs_path):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Path escapes project root'
        return

    existed_before = os.path.exists(abs_path)
    before = ''
    if existed_before and os.path.isfile(abs_path):
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            before = f.read()
    elif existed_before:
        result['status'] = 'FAILED_IO'
        result['message'] = 'Target exists but is not a file: ' + target
        return

    parent = os.path.dirname(abs_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)

    with open(abs_path, 'w', encoding='utf-8') as f:
        f.write(body)

    touched = {
        'rel': target,
        'before': before,
        'after': body,
        'existed_before': bool(existed_before),
        'kind': 'file',
    }

    result['status'] = 'APPLIED'
    result['message'] = 'Created file: ' + target
    result['preview'] = 'CREATE_FILE %s\n%d bytes written' % (target, len(body))
    result['file'] = target
    result['touched'] = [touched]
    result['data'] = {
        'path': target,
        'bytes': len(body),
        'existed_before': bool(existed_before),
    }

    run = ctx.get('run') or {}
    run.setdefault('touched_files', []).append(touched)

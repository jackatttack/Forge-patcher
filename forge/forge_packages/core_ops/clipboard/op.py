# -*- coding: utf-8 -*-
"""
CLIPBOARD reboot op.

Copy a project-relative text file to the iOS clipboard.

Contract:

CLIPBOARD path/to/file.txt
"""

import os

from forge_core.file_safety import safe_target, read_text


SPEC = {
    'name': 'CLIPBOARD',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['CONFIRM']),
    'required_directives': set([]),
}


HELP = {
    'summary': 'Copy a project-relative text file to the iOS clipboard.',
    'minimal_example': [
        'CLIPBOARD forge/docs/MILESTONE_002_CORE_OPS_AND_HINTS.txt',
    ],
    'common_failures': [
        'Missing target file path.',
        'Target file does not exist.',
        'Target escapes the project root.',
        'Pythonista clipboard module unavailable.',
    ],
    'safe_usage': [
        'Use for generated handoff files, starter bundles, and export text.',
        'Use PREVIEW if you only need to inspect the file.',
    ],
}


HINTS = {
    '_max_hints': 1,
    'target': {
        'message': 'CLIPBOARD needs a file path on the op line.',
        'why': 'The reboot clipboard bridge copies exactly one existing project file.',
        'example': [
            'CLIPBOARD forge/docs/MILESTONE_002_CORE_OPS_AND_HINTS.txt',
        ],
        'next': [
            'Put the file path directly after CLIPBOARD.',
            'Use PREVIEW first if you are unsure whether the file exists.',
        ],
    },
    'not found': {
        'message': 'The file to copy was not found.',
        'why': 'CLIPBOARD only copies existing text files inside the project root.',
        'example': [
            'LIST_FILES forge/docs',
            'CLIPBOARD forge/docs/MILESTONE_002_CORE_OPS_AND_HINTS.txt',
        ],
        'next': [
            'Check the path with LIST_FILES.',
            'Create the file first if this was meant to copy generated output.',
        ],
    },
    'clipboard module': {
        'message': 'Pythonista clipboard support was not available.',
        'why': 'This op depends on Pythonista/iOS clipboard access.',
        'next': [
            'Run inside Pythonista.',
            'Use PREVIEW as a fallback to inspect the file content.',
        ],
    },
}


def validate(parsed_op):
    errors = []
    target = (parsed_op.get('target') or '').strip()

    if not target:
        errors.append('CLIPBOARD requires target file path')

    if parsed_op.get('body'):
        errors.append('CLIPBOARD does not accept body content')

    if parsed_op.get('directives'):
        errors.append('CLIPBOARD does not accept directives')

    return errors


def execute(ctx, parsed_op, result):
    target = (parsed_op.get('target') or '').strip()

    root, abs_path, err = safe_target(ctx, target)
    if err:
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = err
        return

    if not os.path.isfile(abs_path):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'File not found: ' + target
        return

    try:
        text = read_text(abs_path)
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = '%s: %s' % (type(e).__name__, e)
        return

    try:
        import clipboard
        clipboard.set(text)
    except Exception as e:
        result['status'] = 'FAILED_RUNTIME'
        result['message'] = 'Pythonista clipboard module unavailable: %s: %s' % (
            type(e).__name__,
            e,
        )
        return

    result['status'] = 'APPLIED'
    result['message'] = 'Copied %s to clipboard' % target
    result['file'] = target
    result['preview'] = 'CLIPBOARD %s\ncopied: %d chars' % (target, len(text))
    result['data'] = {
        'path': target,
        'chars': len(text),
    }

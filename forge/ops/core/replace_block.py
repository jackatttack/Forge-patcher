# -*- coding: utf-8 -*-
"""
ops.replace_block
=================
Exact flat-file block replacement using OLD/NEW markers inside BEGIN_BODY.

Use this when directive-line anchors are awkward, especially for blocks with
blank lines, duplicate lines, or repeated simple anchors.
"""

import os


SPEC = {
    'name': 'REPLACE_BLOCK',
    'target_kind': 'file',
    'body_mode': 'required',
    'allowed_directives': set(['OCCURRENCE', 'ALL']),
    'required_directives': set(),
}


HELP = {
    'summary': 'Replace an exact block of text in a flat file using BEGIN_OLD / BEGIN_NEW markers inside the body.',
    'body': [
        'Body must contain BEGIN_OLD / END_OLD and BEGIN_NEW / END_NEW.',
        'The OLD block may contain blank lines and repeated lines.',
        'By default the OLD block must occur exactly once.',
        'Use OCCURRENCE: N to replace the Nth occurrence.',
        'Use ALL: yes to replace all occurrences.',
    ],
    'subject': ['Relative file path inside project root.'],
    'common_failures': [
        'Missing BEGIN_OLD / END_OLD or BEGIN_NEW / END_NEW markers inside BEGIN_BODY.',
        'OLD block matched zero times.',
        'OLD block matched more than once without OCCURRENCE or ALL: yes.',
        'OCCURRENCE is out of range.',
        'Target file not found.',
    ],
    'safe_usage': [
        'Use for exact flat-file replacements where line anchors are fragile.',
        'Excellent for duplicate bottom blocks, markdown sections, config snippets, and blank-line-sensitive edits.',
        'Prefer REPLACE_FILE_LINES when simple single-line anchors are unique.',
        'Prefer REPLACE_FILE_RANGE after PREVIEW when exact line numbers are already confirmed.',
    ],
    'minimal_example': [
        'REPLACE_BLOCK docs/example.txt',
        'BEGIN_BODY',
        'BEGIN_OLD',
        'alpha',
        '',
        'alpha',
        'END_OLD',
        'BEGIN_NEW',
        'alpha',
        'END_NEW',
        'END_BODY',
    ],
    'related_ops': ['PREVIEW', 'REPLACE_FILE_LINES', 'REPLACE_FILE_RANGE', 'REPLACE_FILE'],
}


HINTS = {
    '_max_hints': 1,
    'old marker': {
        'message': 'REPLACE_BLOCK needs BEGIN_OLD / END_OLD inside BEGIN_BODY.',
        'why': 'The op needs to know the exact existing block to find.',
        'priority': 100,
        'example': [
            'REPLACE_BLOCK docs/example.txt',
            'BEGIN_BODY',
            'BEGIN_OLD',
            'old text',
            'END_OLD',
            'BEGIN_NEW',
            'new text',
            'END_NEW',
            'END_BODY',
        ],
        'next': ['Put the existing text between BEGIN_OLD and END_OLD'],
    },
    'new marker': {
        'message': 'REPLACE_BLOCK needs BEGIN_NEW / END_NEW inside BEGIN_BODY.',
        'why': 'The op needs to know the replacement block.',
        'priority': 100,
        'example': [
            'REPLACE_BLOCK docs/example.txt',
            'BEGIN_BODY',
            'BEGIN_OLD',
            'old text',
            'END_OLD',
            'BEGIN_NEW',
            'new text',
            'END_NEW',
            'END_BODY',
        ],
        'next': ['Put replacement text between BEGIN_NEW and END_NEW'],
    },
    'matched 0': {
        'message': 'OLD block was not found.',
        'why': 'The file may have drifted or the copied OLD block does not exactly match.',
        'priority': 120,
        'example': [
            'PREVIEW docs/example.txt',
            '',
            'Then copy the exact block into BEGIN_OLD / END_OLD.',
        ],
        'next': ['PREVIEW the file and copy the exact block'],
    },
    'matched more than once': {
        'message': 'OLD block matched more than once.',
        'why': 'Forge will not guess which occurrence to replace.',
        'priority': 120,
        'example': [
            'REPLACE_BLOCK docs/example.txt',
            'OCCURRENCE: 2',
            'BEGIN_BODY',
            'BEGIN_OLD',
            'repeated text',
            'END_OLD',
            'BEGIN_NEW',
            'replacement',
            'END_NEW',
            'END_BODY',
        ],
        'next': ['Use OCCURRENCE: N or ALL: yes'],
    },
}


def _extract_between(body, start_marker, end_marker):
    lines = body.splitlines()
    start = None
    end = None

    for i, line in enumerate(lines):
        if line.strip() == start_marker:
            start = i + 1
            break

    if start is None:
        return None

    for i in range(start, len(lines)):
        if lines[i].strip() == end_marker:
            end = i
            break

    if end is None:
        return None

    return '\n'.join(lines[start:end])


def _parse_bool(value):
    return str(value or '').strip().lower() in ('1', 'yes', 'y', 'true', 'on', 'all')


def validate(parsed_op):
    """Check target and marker presence."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('REPLACE_BLOCK requires a target path')

    body = parsed_op.body or ''
    if _extract_between(body, 'BEGIN_OLD', 'END_OLD') is None:
        errors.append('REPLACE_BLOCK requires BEGIN_OLD / END_OLD')
    if _extract_between(body, 'BEGIN_NEW', 'END_NEW') is None:
        errors.append('REPLACE_BLOCK requires BEGIN_NEW / END_NEW')

    return errors


def execute(ctx, parsed_op, result):
    """Replace exact OLD block with NEW block."""
    file_abs = ctx.resolve_file(parsed_op.target)
    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isfile(file_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'File not found: ' + parsed_op.target
        return

    body = parsed_op.body or ''
    old = _extract_between(body, 'BEGIN_OLD', 'END_OLD')
    new = _extract_between(body, 'BEGIN_NEW', 'END_NEW')

    if old is None:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'Missing BEGIN_OLD / END_OLD markers'
        return
    if new is None:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'Missing BEGIN_NEW / END_NEW markers'
        return

    with open(file_abs, 'r', encoding='utf-8', errors='replace') as f:
        before = f.read()

    hits = []
    pos = 0
    while True:
        idx = before.find(old, pos)
        if idx == -1:
            break
        hits.append(idx)
        pos = idx + max(1, len(old))

    if not hits:
        result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
        result['message'] = 'OLD block matched 0 times, expected 1'
        return

    replace_all = _parse_bool(parsed_op.directives.get('ALL'))
    occurrence_raw = parsed_op.directives.get('OCCURRENCE')

    if replace_all:
        after = before.replace(old, new)
        replaced = len(hits)
    else:
        if occurrence_raw is not None:
            try:
                occurrence = int(str(occurrence_raw).strip())
            except Exception:
                result['status'] = 'FAILED_PARSE'
                result['message'] = 'OCCURRENCE must be an integer'
                return
            if occurrence < 1 or occurrence > len(hits):
                result['status'] = 'FAILED_PARSE'
                result['message'] = 'OCCURRENCE out of range: %s found %d time(s)' % (occurrence, len(hits))
                return
            target_idx = hits[occurrence - 1]
        else:
            if len(hits) != 1:
                result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
                result['message'] = 'OLD block matched more than once (%d). Use OCCURRENCE: N or ALL: yes.' % len(hits)
                return
            target_idx = hits[0]

        after = before[:target_idx] + new + before[target_idx + len(old):]
        replaced = 1

    with open(file_abs, 'w', encoding='utf-8') as f:
        f.write(after)

    ctx.file_cache[file_abs] = after
    ctx.touched_files[file_abs] = {
        'before': before,
        'after': after,
    }

    result['file'] = parsed_op.target
    result['status'] = 'APPLIED'
    result['message'] = 'Replaced %d block%s' % (replaced, '' if replaced == 1 else 's')

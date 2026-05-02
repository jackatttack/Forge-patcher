# -*- coding: utf-8 -*-
"""
ops.replace_lines_ast
=====================
Anchor-based AST range replacement.
"""

from forge.target_resolver import resolve_ast_target
from forge.source_ops import replace_line_range
from forge.anchor_tools import resolve_single_anchor

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'REPLACE_LINES',
    'target_kind': 'ast',
    'body_mode': 'optional',

    'allowed_directives': set(['ANCHOR_START', 'ANCHOR_END', 'MATCH', 'OCCURRENCE', 'EXPECT']),
    'required_directives': set(['ANCHOR_START', 'ANCHOR_END']),
    "summary": 'Replace a range of lines inside an AST target between ANCHOR_START and ANCHOR_END.',
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.

HELP = {
    'summary': 'Replace a range of lines inside a resolved Python AST target using start and end anchors.',
    'subject': [
        'Required. AST target such as file.py::function_name or file.py::Class.method.',
    ],
    'required_directives': [
        'ANCHOR_START: substring marking the first line of the range',
        'ANCHOR_END: substring marking the last line of the range',
    ],
    'optional_directives': [
        'MATCH: exact | fuzzy | regex',
        'OCCURRENCE: N',
        'EXPECT: expected text or count, depending on resolver support',
    ],
    'body': [
        'Optional. Replacement lines.',
        'Empty BEGIN_BODY / END_BODY deletes the matched range.',
        'Use BEGIN_BODY / END_BODY whenever replacing multiple lines.',
    ],
    'common_failures': [
        'ANCHOR_START missing.',
        'ANCHOR_END missing.',
        'Anchor not found because target content drifted.',
        'Anchor matched more than once.',
        'ANCHOR_END appears before ANCHOR_START.',
        'Target not found — run LIST_TARGETS on the file.',
    ],
    'safe_usage': [
        'Run PREVIEW on the target before patching.',
        'Use tight anchors copied from PREVIEW output.',
        'Prefer REPLACE_LINES over REPLACE when only a small block changes.',
        'Prefer REPLACE when a target is messy and anchors would be fragile.',
    ],
    'related_ops': ['PREVIEW', 'LIST_TARGETS', 'REPLACE_LINE', 'REPLACE', 'REPLACE_FILE_LINES'],
    'minimal_example': [
        'REPLACE_LINES app.py::main',
        'ANCHOR_START: old_first_line',
        'ANCHOR_END: old_last_line',
        'BEGIN_BODY',
        'new_first_line',
        'new_last_line',
        'END_BODY',
    ],
}

HINTS = {
    '_max_hints': 1,
    'anchor_start': {
        'message': 'REPLACE_LINES needs ANCHOR_START.',
        'why': 'Forge needs a start anchor to know where the replacement range begins inside the AST target.',
        'priority': 100,
        'example': [
            'REPLACE_LINES app.py::main',
            'ANCHOR_START: old_first_line',
            'ANCHOR_END: old_last_line',
            'BEGIN_BODY',
            'new_first_line',
            'new_last_line',
            'END_BODY',
        ],
        'next': ['PREVIEW the target and copy the exact start/end lines', 'HELP REPLACE_LINES'],
    },
    'anchor_end': {
        'message': 'REPLACE_LINES needs ANCHOR_END.',
        'why': 'Forge needs an end anchor to know where the replacement range stops.',
        'priority': 100,
        'example': [
            'REPLACE_LINES app.py::main',
            'ANCHOR_START: old_first_line',
            'ANCHOR_END: old_last_line',
            'BEGIN_BODY',
            'new_first_line',
            'new_last_line',
            'END_BODY',
        ],
        'next': ['PREVIEW the target and copy the exact start/end lines', 'HELP REPLACE_LINES'],
    },
    'target': {
        'message': 'REPLACE_LINES needs a real AST target.',
        'why': 'This op works inside a Python function, method, class, or assignment target.',
        'priority': 90,
        'example': [
            'LIST_TARGETS app.py',
            '',
            'REPLACE_LINES app.py::main',
            'ANCHOR_START: old_first_line',
            'ANCHOR_END: old_last_line',
            'BEGIN_BODY',
            'new_first_line',
            'END_BODY',
        ],
        'next': ['LIST_TARGETS <file.py>', 'HELP REPLACE_LINES'],
    },
    'anchor_end appears before': {
        'message': 'ANCHOR_END was found before ANCHOR_START.',
        'why': 'The replacement range must move downward through the target from start to end.',
        'priority': 110,
        'example': [
            'PREVIEW app.py::main',
            '',
            'Then copy anchors in the same order they appear in the preview.',
        ],
        'next': ['PREVIEW the target', 'Swap or tighten the anchors'],
    },
    'matched 0': {
        'message': 'Anchor text was not found.',
        'why': 'The file probably drifted, whitespace differs, or the anchor was copied inaccurately.',
        'priority': 120,
        'example': [
            'PREVIEW app.py::main',
            '',
            'REPLACE_LINES app.py::main',
            'ANCHOR_START: exact line copied from preview',
            'ANCHOR_END: exact later line copied from preview',
            'BEGIN_BODY',
            'replacement',
            'END_BODY',
        ],
        'next': ['PREVIEW the target', 'Try MATCH: fuzzy if whitespace is the issue'],
    },
    'matched 2': {
        'message': 'Anchor text matched more than once.',
        'why': 'Forge cannot safely choose which repeated line to patch.',
        'priority': 120,
        'example': [
            'REPLACE_LINES app.py::main',
            'ANCHOR_START: more distinctive start text',
            'ANCHOR_END: more distinctive end text',
            'BEGIN_BODY',
            'replacement',
            'END_BODY',
        ],
        'next': ['Use more specific anchors', 'Use OCCURRENCE: N only if the repeated match is intentional'],
    },
    'skipped_anchor_mismatch': {
        'message': 'Anchor mismatch: patch against the live target text.',
        'why': 'The target content likely drifted since the bundle was written.',
        'priority': 80,
        'example': [
            'PREVIEW app.py::main',
            '',
            'Then retry with anchors copied from the preview output.',
        ],
        'next': ['PREVIEW the target', 'Tighten anchors or switch to REPLACE for messy targets'],
    },
}


def validate(parsed_op):
    """Check target and both anchor directives are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('REPLACE_LINES requires a target')
    if not parsed_op.body:
        pass  # empty body allowed — BEGIN_BODY/END_BODY with no content deletes the range

    if 'ANCHOR_START' not in parsed_op.directives:
        errors.append('Missing required directive for REPLACE_LINES: ANCHOR_START')
    if 'ANCHOR_END' not in parsed_op.directives:
        errors.append('Missing required directive for REPLACE_LINES: ANCHOR_END')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve AST target, find anchor range, and replace lines between them."""
    resolved = resolve_ast_target(

        ctx.project_root,
        parsed_op.target,
        default_file=parsed_op.default_file,
    )

    if not resolved.get('ok'):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = resolved.get('error') or 'Target not found'
        return

    file_abs = resolved['file_abs']
    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    before = resolved['source_text']
    all_lines = before.splitlines()
    start = resolved['start']
    end = resolved['end']

    target_lines = all_lines[start - 1:end]

    match_mode = parsed_op.directives.get('MATCH', 'exact')
    occurrence = parsed_op.directives.get('OCCURRENCE', 1)
    expect = parsed_op.directives.get('EXPECT', 1)

    try:
        occurrence = int(occurrence)
    except Exception:
        occurrence = 1
    try:
        expect = int(expect)
    except Exception:
        expect = 1

    start_idx, err = resolve_single_anchor(
        target_lines,
        parsed_op.directives.get('ANCHOR_START', ''),
        match_mode=match_mode,
        occurrence=occurrence,
        expect=expect,
    )
    if err:
        result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
        result['message'] = 'ANCHOR_START: ' + err
        return

    end_idx, err = resolve_single_anchor(
        target_lines,
        parsed_op.directives.get('ANCHOR_END', ''),
        match_mode=match_mode,
        occurrence=occurrence,
        expect=expect,
    )
    if err:
        result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
        result['message'] = 'ANCHOR_END: ' + err
        return

    if end_idx < start_idx:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'ANCHOR_END occurs before ANCHOR_START'
        return

    abs_start = start + start_idx
    abs_end = start + end_idx

    after = replace_line_range(
        before,
        abs_start,
        abs_end,
        parsed_op.body,
    )

    with open(file_abs, 'w', encoding='utf-8') as f:

        f.write(after)

    ctx.file_cache[file_abs] = after
    ctx.touched_files[file_abs] = {
        'before': before,
        'after': after,
    }

    result['file'] = resolved['file_ref']
    result['status'] = 'APPLIED'
    result['message'] = 'lines %d-%d replaced inside %s' % (abs_start, abs_end, resolved['kind'])

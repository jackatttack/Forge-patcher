# -*- coding: utf-8 -*-
"""
ops.replace_line_ast
====================
Single-line AST replacement.
"""

from forge.target_resolver import resolve_ast_target
from forge.source_ops import replace_line_range
from forge.anchor_tools import resolve_single_anchor

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'REPLACE_LINE',
    'target_kind': 'ast',
    'body_mode': 'optional',

    'allowed_directives': set(['ANCHOR', 'MATCH', 'OCCURRENCE', 'EXPECT']),
    'required_directives': set(['ANCHOR']),
    "summary": 'Replace a single line inside an AST target matched by an ANCHOR substring.',
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.

HELP = {
    'summary': 'Replace one line inside a resolved Python AST target using an anchor substring.',
    'subject': [
        'Required. AST target such as file.py::function_name or file.py::Class.method.',
    ],
    'required_directives': [
        'ANCHOR: unique substring on the line to replace',
    ],
    'optional_directives': [
        'MATCH: exact | fuzzy | regex',
        'OCCURRENCE: N',
        'EXPECT: expected text or count, depending on resolver support',
    ],
    'body': [
        'Optional. Replacement line.',
        'Empty BEGIN_BODY / END_BODY deletes the matched line.',
    ],
    'common_failures': [
        'ANCHOR missing.',
        'Anchor not found because target content drifted.',
        'Anchor matched more than once.',
        'Target not found — run LIST_TARGETS on the file.',
    ],
    'safe_usage': [
        'Run PREVIEW on the target before patching.',
        'Use a distinctive substring from the exact line.',
        'Use OCCURRENCE: N only when repeated lines are intentional and understood.',
        'Use REPLACE_LINES if more than one line is changing.',
    ],
    'related_ops': ['PREVIEW', 'LIST_TARGETS', 'REPLACE_LINES', 'REPLACE'],
    'minimal_example': [
        'REPLACE_LINE app.py::main',
        'ANCHOR: old_value = 1',
        'BEGIN_BODY',
        'old_value = 2',
        'END_BODY',
    ],
}

HINTS = {
    '_max_hints': 1,
    'anchor': {
        'message': 'REPLACE_LINE needs ANCHOR.',
        'why': 'Forge uses ANCHOR to find the exact line to replace inside the AST target.',
        'priority': 100,
        'example': [
            'REPLACE_LINE app.py::main',
            'ANCHOR: old_value = 1',
            'BEGIN_BODY',
            'old_value = 2',
            'END_BODY',
        ],
        'next': ['PREVIEW the target and copy a distinctive substring', 'HELP REPLACE_LINE'],
    },
    'target': {
        'message': 'REPLACE_LINE needs a real AST target.',
        'why': 'This op replaces one line inside a Python function, method, class, or assignment target.',
        'priority': 90,
        'example': [
            'LIST_TARGETS app.py',
            '',
            'REPLACE_LINE app.py::main',
            'ANCHOR: old_value = 1',
            'BEGIN_BODY',
            'old_value = 2',
            'END_BODY',
        ],
        'next': ['LIST_TARGETS <file.py>', 'HELP REPLACE_LINE'],
    },
    'matched 0': {
        'message': 'Anchor text was not found.',
        'why': 'The target may have changed, or the anchor text does not exactly appear on a line.',
        'priority': 120,
        'example': [
            'PREVIEW app.py::main',
            '',
            'REPLACE_LINE app.py::main',
            'ANCHOR: exact text copied from preview',
            'BEGIN_BODY',
            'replacement_line',
            'END_BODY',
        ],
        'next': ['PREVIEW the target', 'Try MATCH: fuzzy if whitespace differs'],
    },
    'matched 2': {
        'message': 'Anchor text matched more than once.',
        'why': 'Forge will not guess which repeated line to replace.',
        'priority': 120,
        'example': [
            'REPLACE_LINE app.py::main',
            'ANCHOR: repeated_text',
            'OCCURRENCE: 2',
            'BEGIN_BODY',
            'replacement_line',
            'END_BODY',
        ],
        'next': ['Use a more specific anchor', 'Use OCCURRENCE: N only when deliberate'],
    },
    'skipped_anchor_mismatch': {
        'message': 'Anchor mismatch: patch against the live target text.',
        'why': 'The target content likely drifted since the bundle was written.',
        'priority': 80,
        'example': [
            'PREVIEW app.py::main',
            '',
            'Then retry with ANCHOR copied from the preview.',
        ],
        'next': ['PREVIEW the target', 'Use REPLACE_LINES if more context is needed'],
    },
}


def validate(parsed_op):
    """Check target and ANCHOR directive are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('REPLACE_LINE requires a target')
    if not parsed_op.body:
        pass  # empty body allowed — BEGIN_BODY/END_BODY with no content deletes the line

    if 'ANCHOR' not in parsed_op.directives:
        errors.append('Missing required directive for REPLACE_LINE: ANCHOR')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve AST target, find anchor line, and replace it with body."""
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

    rel_idx, err = resolve_single_anchor(
        target_lines,
        parsed_op.directives.get('ANCHOR', ''),
        match_mode=match_mode,
        occurrence=occurrence,
        expect=expect,
    )
    if err:
        result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
        result['message'] = 'ANCHOR: ' + err
        return

    abs_line = start + rel_idx

    after = replace_line_range(
        before,
        abs_line,
        abs_line,
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
    result['message'] = 'line %d replaced inside %s' % (abs_line, resolved['kind'])

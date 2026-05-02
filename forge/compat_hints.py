# -*- coding: utf-8 -*-
"""
compat_hints.py
===============

Compatibility diagnostics for common LLM near-misses.

This module does not normalise or execute anything. It only explains cases
where the model's intent is clear but the Forge dialect is slightly wrong.
"""


def hint_for_invalid_directive(op_name, bad_key, spec=None):
    """Return lines of compatibility guidance for an unsupported directive."""
    op = (op_name or '').upper()
    key = (bad_key or '').upper()

    if key == 'ARG':
        return [
            'COMPAT:',
            '- ARG is close, but Forge uses ARGS.',
            'EXAMPLE:',
            'ARGS: today',
        ]

    if key == 'FILE':
        return [
            'COMPAT:',
            '- FILE is close, but this op expects the file/path in the op header target.',
            'EXAMPLE:',
            op + ' path/to/file.py',
        ]

    if key == 'CONTEXT' and op == 'GREP':
        return [
            'COMPAT:',
            '- GREP supports CONTEXT after the updated op has been refreshed.',
            'EXAMPLE:',
            'GREP',
            'PATTERN: def main',
            'FILTER: forge',
            'CONTEXT: 5',
            'NEXT:',
            '- Run REFRESH if HELP GREP still does not show CONTEXT.',
        ]

    if key in ('START', 'END') and op == 'REPLACE_FILE_RANGE':
        return [
            'COMPAT:',
            '- START/END is clear intent. Forge normalises START + END into LINES when both are present.',
            '- If normalisation did not happen, use LINES directly.',
            'EXAMPLE:',
            'REPLACE_FILE_RANGE path/to/file.py',
            'LINES: 10-20',
            'BEGIN_BODY',
            'replacement',
            'END_BODY',
        ]

    if key in ('OLD', 'NEW') and op in ('REPLACE_LINES', 'REPLACE_FILE_LINES'):
        return [
            'COMPAT:',
            '- OLD/NEW patch style is not Forge syntax for this op.',
            '- Forge needs explicit anchors so the replacement range is inspectable.',
            'EXAMPLE:',
            op + ' target',
            'ANCHOR_START: exact first line',
            'ANCHOR_END: exact last line',
            'BEGIN_BODY',
            'replacement',
            'END_BODY',
            'NEXT:',
            '- PREVIEW the target first and copy exact anchor lines.',
            '- Use REPLACE for a whole function/method if anchor range editing feels fragile.',
        ]

    if key == 'ANCHOR' and op in ('INSERT_AFTER', 'INSERT_BEFORE'):
        position = 'after' if op == 'INSERT_AFTER' else 'before'
        return [
            'COMPAT:',
            '- ANCHOR beside ' + op + ' is a known near-miss.',
            '- Forge now safely normalises this into INSERT_INTO with POSITION: ' + position + '.',
            '- If this still appears as an invalid directive, the compatibility normaliser may not have run or Python may need a module reload/restart.',
            'NORMALISED SHAPE:',
            'INSERT_INTO file.py::Class.method',
            'ANCHOR: exact line inside target',
            'POSITION: ' + position,
            'BEGIN_BODY',
            'new code',
            'END_BODY',
            'WHY:',
            '- INSERT_AFTER/INSERT_BEFORE add sibling AST targets.',
            '- INSERT_INTO is the correct op for anchored insertion inside an existing target.',
            'NEXT:',
            '- Prefer writing INSERT_INTO directly when using ANCHOR.',
            '- Use INSERT_AFTER/INSERT_BEFORE only for sibling functions or methods.',
        ]

    if key == 'ANCHOR' and op in ('REPLACE_LINES', 'REPLACE_FILE_LINES'):
        return [
            'COMPAT:',
            '- ANCHOR is close, but this op needs both ANCHOR_START and ANCHOR_END.',
            'EXAMPLE:',
            op + ' target',
            'ANCHOR_START: first matched line',
            'ANCHOR_END: last matched line',
            'BEGIN_BODY',
            'replacement',
            'END_BODY',
        ]

    if key == 'LINE' and op in ('PREVIEW',):
        return [
            'COMPAT:',
            '- LINE is close, but PREVIEW uses LINES.',
            'EXAMPLE:',
            'LINES: 1-40',
        ]

    if key == 'BODY':
        return [
            'COMPAT:',
            '- BODY is close, but multiline content must use BEGIN_BODY / END_BODY fences.',
            'EXAMPLE:',
            'BEGIN_BODY',
            'content here',
            'END_BODY',
        ]

    return []

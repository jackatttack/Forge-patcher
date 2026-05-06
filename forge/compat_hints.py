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

    if key in ('START', 'END') and op in ('REPLACE_FILE_RANGE', 'PREVIEW'):
        return [
            'COMPAT:',
            '- START/END is clear intent. Forge normalises START + END into LINES when both are present.',
            '- If normalisation did not happen, use LINES directly.',
            'EXAMPLE:',
            op + ' path/to/file.py',
            'LINES: 10-20',
            'NEXT:',
            '- Prefer LINES: start-end for explicit line ranges.',
            '- Run HELP ' + op + '.',
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

    if key == 'FILES' and op == 'BRANCH':
        return [
            'COMPAT:',
            '- BRANCH does not use FILES:.',
            '- Put the files or folders to snapshot inside BEGIN_BODY / END_BODY.',
            'EXAMPLE:',
            'BRANCH create before_change',
            'BEGIN_BODY',
            'forge/compat_hints.py',
            'forge/compat_normalizer.py',
            'END_BODY',
            'NEXT:',
            '- Move FILES: entries into the body.',
            '- Run HELP BRANCH.',
        ]

    if key == 'SKIP_IF_EXISTS' and op == 'CREATE_FILE':
        return [
            'COMPAT:',
            '- CREATE_FILE does not support SKIP_IF_EXISTS.',
            '- CREATE_FILE is intentionally strict and fails if the file already exists.',
            'EXAMPLE:',
            'PREVIEW scratch/example.py',
            '',
            'REPLACE_FILE scratch/example.py',
            'BEGIN_BODY',
            'print("replacement")',
            'END_BODY',
            'NEXT:',
            '- Use PREVIEW first if unsure whether the file exists.',
            '- Use REPLACE_FILE for a deliberate overwrite.',
            '- Run HELP CREATE_FILE.',
        ]

    if key in ('OUT', '$OUT') and op == 'URL':
        return [
            'COMPAT:',
            '- URL does not use OUT: as a directive.',
            '- $OUT is a conceptual result field in packet/context output, not bundle syntax.',
            'EXAMPLE:',
            'URL https://example.com',
            'MODE: fetch',
            'NEXT:',
            '- Remove OUT: from the bundle.',
            '- Read the URL result from the run packet.',
            '- Run HELP URL.',
        ]

    return []

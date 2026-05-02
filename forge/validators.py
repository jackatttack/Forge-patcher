# -*- coding: utf-8 -*-
"""
validators.py
=============
Validation helpers for parsed ops.

This layer validates parsed op shape against OP_SPECS. It deliberately
does not execute or normalise ops; it reports clear, actionable diagnostics
when syntax is close but not valid.
"""

from forge.registry import OP_SPECS


def _fmt_directives(values):
    """Return stable printable directive list."""
    if values is None:
        return ['<any>']
    try:
        items = sorted(values)
    except Exception:
        items = list(values or [])
    return items


def _lines(title, items):
    """Format a titled bullet list for diagnostics."""
    out = [title + ':']
    if not items:
        out.append('- none')
    else:
        for item in items:
            out.append('- ' + str(item))
    return out


def _compat_hint(op_name, bad_key):
    """Return op-specific compatibility guidance for common LLM near-misses."""
    try:
        from forge.compat_hints import hint_for_invalid_directive
        return hint_for_invalid_directive(op_name, bad_key)
    except Exception:
        return []


def _invalid_directive_error(op_name, bad_key, spec):
    """Build a rich diagnostic for an unsupported directive."""
    allowed = _fmt_directives(spec.get('allowed_directives', set()))
    required = _fmt_directives(spec.get('required_directives', set()))
    body_mode = spec.get('body_mode', 'forbidden')

    lines = [
        'Directive not allowed for %s: %s' % (op_name, bad_key),
        'OP: %s' % op_name,
        'INVALID DIRECTIVE: %s' % bad_key,
    ]
    lines.extend(_lines('ALLOWED DIRECTIVES', allowed))
    lines.extend(_lines('REQUIRED DIRECTIVES', required))
    lines.append('BODY MODE: ' + str(body_mode))

    hint = _compat_hint(op_name, bad_key)
    if hint:
        lines.extend(hint)

    lines.extend([
        'NEXT:',
        '- Check HELP ' + str(op_name),
        '- Replace the unsupported directive with one of the allowed directives above.',
    ])
    return '\n'.join(lines)


def _missing_directive_error(op_name, missing_key, spec):
    """Build a richer diagnostic for a missing required directive."""
    allowed = _fmt_directives(spec.get('allowed_directives', set()))
    required = _fmt_directives(spec.get('required_directives', set()))

    lines = [
        'Missing required directive for %s: %s' % (op_name, missing_key),
        'OP: %s' % op_name,
        'MISSING DIRECTIVE: %s' % missing_key,
    ]
    lines.extend(_lines('REQUIRED DIRECTIVES', required))
    lines.extend(_lines('ALLOWED DIRECTIVES', allowed))

    if missing_key in ('ANCHOR_START', 'ANCHOR_END'):
        lines.extend([
            'EXAMPLE:',
            op_name + ' target',
            'ANCHOR_START: exact first line',
            'ANCHOR_END: exact last line',
            'BEGIN_BODY',
            'replacement',
            'END_BODY',
        ])

    lines.extend([
        'NEXT:',
        '- Add ' + str(missing_key) + ': <value>',
        '- Use HELP ' + str(op_name) + ' for the exact syntax.',
    ])
    return '\n'.join(lines)


def validate_op_shape(op_name, directives, body):
    """Check parsed op has required fields and no disallowed directives. Returns errors."""
    spec = OP_SPECS.get(op_name)
    if spec is None:
        return ['Unknown op: ' + str(op_name)]

    errors = []

    allowed = spec.get('allowed_directives', set())
    required = spec.get('required_directives', set())
    body_mode = spec.get('body_mode', 'forbidden')

    # Global safety directives are accepted by the parser for all ops.
    # They may be interpreted later by the engine or guards.
    global_allowed = set(['CONFIRM'])

    # None means allow any directives (e.g. proxy ops like PIXEL)
    if allowed is not None:
        for key in directives.keys():
            if key in global_allowed:
                continue
            if key not in allowed:
                errors.append(_invalid_directive_error(op_name, key, spec))

    for key in required:
        if key not in directives:
            errors.append(_missing_directive_error(op_name, key, spec))

    has_body = bool(body)

    if body_mode == 'required' and not has_body:
        errors.append('Body required for ' + op_name)
    elif body_mode == 'forbidden' and has_body:
        errors.append('Body not allowed for ' + op_name)

    return errors

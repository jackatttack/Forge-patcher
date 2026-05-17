# -*- coding: utf-8 -*-
"""
Small failure hint renderer for Forge.

Ops may define:

HINTS = {
    '_max_hints': 1,
    'some substring': 'Short hint text',
    'other substring': {
        'message': 'User-facing message.',
        'why': 'Reason.',
        'example': ['OP thing', 'DIRECTIVE: value'],
        'next': ['Do this', 'Then this'],
    },
}

Hints are matched against failed result status/message/preview text.
"""

def _as_lines(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def _render_hint(key, hint):
    lines = []

    if isinstance(hint, dict):
        message = hint.get('message') or str(key)
        lines.append('HINT: ' + str(message))

        why = hint.get('why')
        if why:
            lines.append('WHY: ' + str(why))

        example = _as_lines(hint.get('example'))
        if example:
            lines.append('EXAMPLE:')
            lines.extend(example)

        next_steps = _as_lines(hint.get('next'))
        if next_steps:
            lines.append('NEXT:')
            for step in next_steps:
                lines.append('- ' + str(step))

        see = hint.get('see')
        if see:
            lines.append('See: ' + str(see))

        return '\n'.join(lines)

    return 'HINT: ' + str(hint)


def render_hints_for_result(op_module, result):
    hints = getattr(op_module, 'HINTS', {}) or {}
    if not hints:
        return ''

    status = str((result or {}).get('status') or '')
    if status == 'APPLIED':
        return ''

    haystack = '\n'.join([
        str((result or {}).get('op') or ''),
        str((result or {}).get('status') or ''),
        str((result or {}).get('message') or ''),
        str((result or {}).get('preview') or ''),
    ]).lower()

    max_hints = hints.get('_max_hints', 1)
    try:
        max_hints = int(max_hints)
    except Exception:
        max_hints = 1

    rendered = []
    seen = set()

    for key, hint in hints.items():
        if str(key).startswith('_'):
            continue

        needle = str(key).lower()
        if needle and needle in haystack and needle not in seen:
            rendered.append(_render_hint(key, hint))
            seen.add(needle)

        if len(rendered) >= max_hints:
            break

    return '\n\n'.join(rendered).strip()

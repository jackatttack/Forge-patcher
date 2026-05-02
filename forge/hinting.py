# -*- coding: utf-8 -*-
"""
forge.hinting
==============

Shared failure-hint rendering for Forge entry points.

HINTS remains backwards compatible:

    HINTS = {
        'body': 'Wrap content in BEGIN_BODY / END_BODY',
    }

Richer hints are also supported:

    HINTS = {
        '_max_hints': 1,
        'body': {
            'message': 'This op needs body content.',
            'why': 'The op writes or snapshots explicit content.',
            'priority': 10,
            'example': [
                'OP target',
                'BEGIN_BODY',
                '...',
                'END_BODY',
            ],
            'next': ['HELP OP'],
        },
    }

Private keys beginning with "_" configure rendering and are not matched.
"""


def _as_lines(value):
    """Return value as a list of display lines."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value]
    return [str(value)]


def _hint_priority(hint):
    """Return numeric priority for a hint. Higher renders first."""
    if isinstance(hint, dict):
        try:
            return int(hint.get('priority', 0))
        except Exception:
            return 0
    return 0


def _max_hints(hints_dict):
    """Return max hints to render for a match set."""
    try:
        return int(hints_dict.get('_max_hints', 2))
    except Exception:
        return 2


def _render_rich_hint(hint):
    """Render a string or dict hint to a compact failure-help block."""
    if isinstance(hint, str):
        return 'Hint: ' + hint

    if not isinstance(hint, dict):
        return 'Hint: ' + str(hint)

    lines = []

    message = hint.get('message') or hint.get('hint') or hint.get('summary')
    if message:
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
            lines.append('- ' + step)

    if not lines:
        lines.append('Hint: ' + str(hint))

    return '\n'.join(lines)


def render_hints_for_errors(mod, errors):
    """Match error strings against an op module's HINTS dict and render hints."""
    hints_dict = getattr(mod, 'HINTS', {})
    if not hints_dict:
        return ''

    matched = []
    seen_blocks = set()
    order = 0

    for error in errors:
        error_lower = str(error).lower()
        for key, hint in hints_dict.items():
            key_text = str(key)
            if key_text.startswith('_'):
                continue
            if key_text.lower() in error_lower:
                block = _render_rich_hint(hint)
                if block not in seen_blocks:
                    seen_blocks.add(block)
                    matched.append((_hint_priority(hint), len(key_text), order, block))
                    order += 1

    if not matched:
        return ''

    # Sort by:
    # 1. explicit priority, highest first
    # 2. key specificity, longest matching key first
    # 3. original order, stable fallback
    matched.sort(key=lambda item: (-item[0], -item[1], item[2]))

    limit = _max_hints(hints_dict)
    if limit > 0:
        matched = matched[:limit]

    return '\n'.join(item[3] for item in matched)

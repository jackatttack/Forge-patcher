# -*- coding: utf-8 -*-
"""
anchor_tools.py
===============
Small anchor-matching helpers for AST/text range replacement.
"""

def _normalize(s):
    """Collapse whitespace runs to single spaces and strip ends."""
    return ' '.join((s or '').strip().split())


def find_anchor_line_indexes(lines, anchor, match_mode='exact'):
    """
    Return 0-based indexes of matching lines.
    """
    out = []
    needle = anchor or ''
    for idx, line in enumerate(lines):
        if match_mode == 'fuzzy':
            if _normalize(needle) == _normalize(line):
                out.append(idx)
        else:
            if needle in line:
                out.append(idx)
    return out


def resolve_single_anchor(lines, anchor, match_mode='exact', occurrence=1, expect=1):
    """Find a single anchor match in lines. Returns (rel_idx, error_str)."""
    matches = find_anchor_line_indexes(lines, anchor, match_mode=match_mode)

    if expect is not None and len(matches) != expect:
        msg = 'Anchor matched %d times, expected %d' % (len(matches), expect)
        if len(matches) > 1:
            candidates = []
            for idx in matches:
                preview = lines[idx].strip()
                if len(preview) > 60:
                    preview = preview[:57] + '...'
                candidates.append('  line %d: %s' % (idx + 1, preview))
            msg += '\nCandidates:\n' + '\n'.join(candidates)
        return None, msg

    occ = max(1, int(occurrence or 1))
    if occ > len(matches):
        return None, 'Occurrence %d out of range for %d matches' % (occ, len(matches))

    return matches[occ - 1], None

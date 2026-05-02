# -*- coding: utf-8 -*-
"""
source_ops.py
=============
Small source-text helpers for forge write ops.
"""

import textwrap


def get_line_indent(line):
    """Return leading whitespace of a line as a string."""
    s = line or ''
    return s[:len(s) - len(s.lstrip(' \t'))]


def replace_line_range(source_text, start_line, end_line, new_body):
    """
    Replace 1-based inclusive line range with new_body text.
    """
    lines = source_text.splitlines(True)
    if not lines:
        return (new_body or '').strip('\n') + '\n'

    if start_line < 1 or end_line < start_line or end_line > len(lines):
        raise ValueError('Invalid line range %d..%d for %d-line source' % (
            start_line, end_line, len(lines)
        ))

    before = lines[:start_line - 1]
    after = lines[end_line:]

    indent = get_line_indent(lines[start_line - 1])
    replacement_block = textwrap.dedent((new_body or '').strip('\n'))

    new_lines = []
    for line in replacement_block.splitlines():
        if line.strip():
            new_lines.append(indent + line + '\n')
        else:
            new_lines.append('\n')

    if after and after[0].strip():
        new_lines.append('\n')

    return ''.join(before) + ''.join(new_lines) + ''.join(after)


def insert_after_lines(source_text, line_no, insert_block, indent, tight=False):
    """
    Insert after line_no (1-based).
    tight=True suppresses auto blank lines before/after the inserted block.
    """
    src_lines = source_text.splitlines(True)

    if line_no < 0 or line_no > len(src_lines):
        raise ValueError('Invalid insert position after line %d in %d-line source' % (
            line_no, len(src_lines)
        ))

    insert_block = textwrap.dedent((insert_block or '').strip('\n'))

    ins_lines = []
    for line in insert_block.splitlines():
        if line.strip():
            ins_lines.append(indent + line + '\n')
        else:
            ins_lines.append('\n')

    before = src_lines[:line_no]
    after = src_lines[line_no:]

    if not tight:
        if before and before[-1].strip():
            ins_lines.insert(0, '\n')
        if after and after[0].strip():
            ins_lines.append('\n')

    if src_lines and not src_lines[-1].endswith('\n'):
        src_lines[-1] = src_lines[-1] + '\n'

    return ''.join(before) + ''.join(ins_lines) + ''.join(after)

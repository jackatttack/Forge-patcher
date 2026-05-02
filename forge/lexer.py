# -*- coding: utf-8 -*-
"""
lexer.py
========
First-pass structural scanning for Forge bundles.

Keep this tiny and strict.
"""


def is_known_op_header(line):
    s = (line or '').strip()
    try:
        from forge.registry import OP_SPECS
        op_names = OP_SPECS.keys()
    except Exception:
        return False
    for op_name in op_names:
        if s.startswith(op_name + ' ') or s == op_name:
            return True
    return False


def is_phase1_op_header(line):
    # Backward-compatible alias while parser_main still uses this name.
    return is_known_op_header(line)


def is_exact_begin_body(line):
    return line.rstrip() == 'BEGIN_BODY'

def is_exact_end_body(line):
    return line.rstrip() == 'END_BODY'

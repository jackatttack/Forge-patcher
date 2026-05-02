# -*- coding: utf-8 -*-
"""
target_resolver.py
==================
AST target parsing and resolution for forge.

Parses target strings like 'file.py::Class.method' into components,
then resolves them against the filesystem and AST to find exact line
ranges. Used by all AST patch ops before they touch any file.
"""

import os

from forge.ast_bridge import resolve_target_range


def parse_target_ref(target_ref, default_file=None):
    """Parse 'file.py::Class.method' into {file_ref, class_name, target_name} or None."""
    raw = (target_ref or '').strip()
    if '::' in raw:
        file_ref, rhs = raw.split('::', 1)
    else:
        file_ref, rhs = default_file, raw

    if not file_ref:
        return None

    file_ref = file_ref.strip()
    rhs = (rhs or '').strip()

    class_name = None
    target_name = rhs

    if '.' in rhs:
        lhs, tail = rhs.split('.', 1)
        if tail:
            class_name = lhs.strip()
            target_name = tail.strip()

    return {
        'file_ref': file_ref,
        'class_name': class_name,
        'target_name': target_name,
    }


def resolve_ast_target(project_root, target_ref, default_file=None):
    """Resolve a target string to file path, line range, and source text. Returns dict with ok flag."""
    parsed = parse_target_ref(target_ref, default_file=default_file)
    if not parsed:
        return None

    file_ref = parsed['file_ref']
    if os.path.isabs(file_ref):
        file_abs = os.path.abspath(file_ref)
    else:
        file_abs = os.path.abspath(os.path.join(project_root, file_ref))

    if not os.path.isfile(file_abs):
        return {
            'ok': False,
            'error': 'File not found: ' + str(file_ref),
        }

    with open(file_abs, 'r', encoding='utf-8', errors='replace') as f:

        src = f.read()

    start, end, kind = resolve_target_range(
        src,
        parsed['class_name'],
        parsed['target_name'],
    )

    if not start or not end:
        return {
            'ok': False,
            'error': 'Target not found: ' + str(target_ref),
        }

    return {
        'ok': True,
        'file_abs': file_abs,
        'file_ref': file_ref,
        'class_name': parsed['class_name'],
        'target_name': parsed['target_name'],
        'kind': kind,
        'start': start,
        'end': end,
        'source_text': src,
    }

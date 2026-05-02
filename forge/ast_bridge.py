# -*- coding: utf-8 -*-
"""
ast_bridge.py
=============
AST helpers for forge. Now self-contained - no dependency on forge1.
"""

from forge.ast_finder import (
    supports_end_lineno,
    find_method_range,
    find_class_range,
    find_function_range,
    find_global_assign_range,
    find_class_assign_range,
)


def ast_capabilities():
    """Return dict of AST feature flags for the current Python version."""
    return {
        'supports_end_lineno': supports_end_lineno(),
    }


def _normalize_range(rng):
    """Expand single-line AST node range to include decorators and trailing lines."""
    if not rng:
        return None
    if isinstance(rng, tuple) and len(rng) == 2 and rng[0] == 'AMBIGUOUS':
        return None
    return rng


def resolve_target_range(source_text, class_name, target_name):
    """Dispatch to the correct ast_finder function based on target kind."""
    """
    Returns:
      (start_lineno, end_lineno, kind)
    or
      (None, None, None)
    """
    if class_name and target_name:
        if target_name.startswith('@'):
            rng = _normalize_range(find_class_assign_range(source_text, class_name, target_name[1:]))
            if rng:
                return rng[0], rng[1], 'class_assign'

        if target_name == '*':
            rng = _normalize_range(find_class_range(source_text, class_name))
            if rng:
                return rng[0], rng[1], 'class'

        rng = _normalize_range(find_method_range(source_text, class_name, target_name))
        if rng:
            return rng[0], rng[1], 'method'

    if (not class_name) and target_name:
        if target_name.startswith('@'):
            rng = _normalize_range(find_global_assign_range(source_text, target_name[1:]))
            if rng:
                return rng[0], rng[1], 'global_assign'

        rng = _normalize_range(find_function_range(source_text, target_name))
        if rng:
            return rng[0], rng[1], 'function'

    return None, None, None

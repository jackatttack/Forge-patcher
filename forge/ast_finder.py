# -*- coding: utf-8 -*-
"""
forge.ast_finder
=================
AST-based range locators. Pure stdlib, no internal deps.
Copied from forge/ast_finder.py - forge is now self-contained.
All finders return (start_line, end_line) 1-based inclusive,
None if not found, or ("AMBIGUOUS", matches) if multiple hits.
"""

import ast


def supports_end_lineno():
    """Return True if this Python version's AST nodes carry end_lineno."""
    src = "def f():\n    return 1\n"
    t = ast.parse(src)
    fn = t.body[0]
    return hasattr(fn, "end_lineno") and fn.end_lineno is not None


def find_method_range(source, class_name, method_name):
    """Find line range of a named method inside a named class. Returns (start, end) or None."""
    tree = ast.parse(source)
    matches = []
    for node in tree.body:
        if not (isinstance(node, ast.ClassDef) and node.name == class_name):
            continue
        items = [it for it in node.body if getattr(it, "lineno", None) is not None]
        for idx, it in enumerate(items):
            if not isinstance(it, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if it.name != method_name:
                continue
            start_line = it.lineno
            for d in getattr(it, "decorator_list", []) or []:
                dl = getattr(d, "lineno", None)
                if dl is not None:
                    start_line = min(start_line, dl)
            end_line = getattr(it, "end_lineno", None)
            if idx + 1 < len(items):
                next_it = items[idx + 1]
                next_line = getattr(next_it, "lineno", None)
                if next_line is not None and next_line > start_line:
                    end_line = next_line - 1
            if end_line is None:
                raise RuntimeError("end_lineno not available; cannot locate method end reliably.")
            matches.append((start_line, end_line))
    if not matches:
        return None
    if len(matches) > 1:
        return ("AMBIGUOUS", matches)
    return matches[0]


def find_class_range(source, class_name):
    """Find line range of a named class in the AST. Returns (start, end) or None."""
    tree = ast.parse(source)
    matches = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            if getattr(node, "lineno", None) is None:
                continue
            if getattr(node, "end_lineno", None) is None:
                raise RuntimeError("end_lineno not available; cannot locate class end reliably.")
            matches.append((node.lineno, node.end_lineno))
    if not matches:
        return None
    if len(matches) > 1:
        return ("AMBIGUOUS", matches)
    return matches[0]


def find_function_range(source, func_name):
    """Find line range of a top-level named function. Returns (start, end) or None."""
    tree = ast.parse(source)
    matches = []
    items = [n for n in tree.body if getattr(n, "lineno", None) is not None]
    for idx, node in enumerate(items):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != func_name:
            continue
        start_line = node.lineno
        for d in getattr(node, "decorator_list", []) or []:
            dl = getattr(d, "lineno", None)
            if dl is not None:
                start_line = min(start_line, dl)
        end_line = getattr(node, "end_lineno", None)
        if idx + 1 < len(items):
            next_node = items[idx + 1]
            next_line = getattr(next_node, "lineno", None)
            if next_line is not None and next_line > start_line:
                end_line = next_line - 1
        if end_line is None:
            raise RuntimeError("end_lineno not available; cannot locate function end reliably.")
        matches.append((start_line, end_line))
    if not matches:
        return None
    if len(matches) > 1:
        return ("AMBIGUOUS", matches)
    return matches[0]


def find_inner_function_range(source, class_name, method_name, inner_name):
    """Find line range of a named inner function inside an outer function. Returns (start, end) or None."""
    tree = ast.parse(source)
    outer = None
    if class_name is not None:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                        outer = item
                        break
                if outer:
                    break
    else:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:
                outer = node
                break
    if outer is None:
        return None
    items = [n for n in outer.body if getattr(n, "lineno", None) is not None]
    matches = []
    for idx, node in enumerate(items):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != inner_name:
            continue
        start_line = node.lineno
        for d in getattr(node, "decorator_list", []) or []:
            dl = getattr(d, "lineno", None)
            if dl is not None:
                start_line = min(start_line, dl)
        end_line = getattr(node, "end_lineno", None)
        if idx + 1 < len(items):
            next_node = items[idx + 1]
            next_line = getattr(next_node, "lineno", None)
            if next_line is not None and next_line > start_line:
                end_line = next_line - 1
        if end_line is None:
            raise RuntimeError("end_lineno not available for inner function %r" % inner_name)
        matches.append((start_line, end_line))
    if not matches:
        return None
    if len(matches) > 1:
        return ("AMBIGUOUS", matches)
    return matches[0]


def find_global_assign_range(source, var_name):
    """Find line range of a module-level assignment by name. Returns (start, end) or None."""
    tree = ast.parse(source)
    matches = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in (node.targets or []):
                if isinstance(t, ast.Name) and t.id == var_name:
                    if getattr(node, "lineno", None) is None:
                        continue
                    end_line = getattr(node, "end_lineno", None)
                    if end_line is None:
                        raise RuntimeError("end_lineno not available; cannot locate assignment end reliably.")
                    matches.append((node.lineno, end_line))
                    break
        elif isinstance(node, ast.AnnAssign):
            t = getattr(node, "target", None)
            if isinstance(t, ast.Name) and t.id == var_name:
                if getattr(node, "lineno", None) is None:
                    continue
                end_line = getattr(node, "end_lineno", None)
                if end_line is None:
                    raise RuntimeError("end_lineno not available; cannot locate assignment end reliably.")
                matches.append((node.lineno, end_line))
    if not matches:
        return None
    if len(matches) > 1:
        return ("AMBIGUOUS", matches)
    return matches[0]


def find_class_assign_range(source, class_name, var_name):
    """Find line range of a class-level assignment by name. Returns (start, end) or None."""
    tree = ast.parse(source)
    matches = []
    for node in tree.body:
        if not (isinstance(node, ast.ClassDef) and node.name == class_name):
            continue
        for item in (node.body or []):
            if isinstance(item, ast.Assign):
                for t in (item.targets or []):
                    if isinstance(t, ast.Name) and t.id == var_name:
                        if getattr(item, "lineno", None) is None:
                            continue
                        end_line = getattr(item, "end_lineno", None)
                        if end_line is None:
                            raise RuntimeError("end_lineno not available; cannot locate assignment end reliably.")
                        matches.append((item.lineno, end_line))
                        break
            elif isinstance(item, ast.AnnAssign):
                t = getattr(item, "target", None)
                if isinstance(t, ast.Name) and t.id == var_name:
                    if getattr(item, "lineno", None) is None:
                        continue
                    end_line = getattr(item, "end_lineno", None)
                    if end_line is None:
                        raise RuntimeError("end_lineno not available; cannot locate assignment end reliably.")
                    matches.append((item.lineno, end_line))
    if not matches:
        return None
    if len(matches) > 1:
        return ("AMBIGUOUS", matches)
    return matches[0]

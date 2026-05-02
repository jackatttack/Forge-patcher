# -*- coding: utf-8 -*-
"""
file_ops.py
===========
Shared filesystem helpers for parser-lab file management ops.
"""

import os


def resolve_under_root(project_root, target):
    target = (target or '').strip()
    if os.path.isabs(target):
        path = os.path.abspath(target)
    else:
        path = os.path.abspath(os.path.join(project_root, target))
    return path


def in_root(project_root, path):
    root = os.path.realpath(project_root)
    real = os.path.realpath(path)
    return real.startswith(root)


def ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)


def rel_from_root(project_root, path):
    try:
        return os.path.relpath(path, project_root)
    except Exception:
        return path

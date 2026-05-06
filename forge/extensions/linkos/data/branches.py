# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.data.branches
=====================================

Self-contained branch reader for public/minimal LinkOS.
"""

import json
import os

try:
    from forge.runtime.paths import project_root
    _PROJECT_ROOT = project_root()
except Exception:
    _PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


BRANCHES_DIR = os.path.join(_PROJECT_ROOT, 'artifacts', 'branches')


def _safe_listdir(path):
    try:
        return os.listdir(path)
    except Exception:
        return []


def list_branches(limit=200):
    """Return branch dicts newest first."""
    if not os.path.isdir(BRANCHES_DIR):
        return []

    rows = []
    for name in _safe_listdir(BRANCHES_DIR):
        if name.startswith('.'):
            continue
        path = os.path.join(BRANCHES_DIR, name)
        if not os.path.isdir(path):
            continue
        try:
            mtime = os.path.getmtime(path)
        except Exception:
            mtime = 0
        rows.append({'name': name, 'mtime': mtime, 'path': path})

    rows.sort(key=lambda r: r.get('mtime', 0), reverse=True)
    return rows[:int(limit or 200)]


def load_manifest(name):
    """Return manifest dict for a branch name, or {}."""
    path = os.path.join(BRANCHES_DIR, str(name), 'manifest.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def scope_summary(name):
    """Return short human scope summary for a branch."""
    manifest = load_manifest(name)
    files = manifest.get('files') or []

    if not files:
        return 'snapshot'
    if len(files) == 1:
        return str(files[0])

    prefixes = set()
    for f in files:
        parts = str(f).split('/', 1)
        prefixes.add(parts[0] if len(parts) > 1 else '')

    if len(prefixes) == 1 and '' not in prefixes:
        return '%d files in %s/' % (len(files), prefixes.pop())

    return '%d files' % len(files)


def relative_time(mtime):
    """Return compact relative time."""
    import time
    if not mtime:
        return ''
    delta = int(time.time() - float(mtime))
    if delta < 30:
        return 'just now'
    if delta < 60:
        return '%d sec ago' % delta
    mins = delta // 60
    if mins < 60:
        return '%d min ago' % mins
    hrs = mins // 60
    if hrs < 24:
        return '%d hr ago' % hrs
    days = hrs // 24
    if days < 30:
        return '%d days ago' % days
    return '%d mo ago' % (days // 30)

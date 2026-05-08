# -*- coding: utf-8 -*-
"""
forge.runtime.paths
====================

Import/path bootstrap helpers for Pythonista projects.

Purpose
-------
Pythonista code often starts by adding ~/Documents to sys.path. That works
while every importable package lives at root, but it becomes brittle when
the project root is cleaned up into containers such as systems/, apps/,
workspaces/, experiments/, etc.

This module keeps import names stable while allowing physical folders to
move later.

Example
-------
    from forge.runtime.paths import boot_paths
    boot_paths()

Then imports such as `import forge_ui` or `from forge_notes import store`
can continue to work if those packages live under a known container.
"""

import os
import sys


# These names are treated as stable import surfaces. They may live directly
# under ~/Documents today and can move into containers later.
DEFAULT_PACKAGES = [
    'forge',
]
# Candidate parent folders to add to sys.path. Keep this list small and
# intentional; do not walk the whole Documents tree on every launch.
DEFAULT_CONTAINERS = [
    '',
    'forge',
    'library',
    'systems',
    'apps',
    'projects',
    'workspaces',
    'tools',
    'experiments',
    'runtime',
]


def project_root():
    """Return the installed minimal Forge project root.

    Public Forge is portable: it may live under ~/Documents/Forge,
    workspaces/, iCloud folders, or another container. The project root is
    the folder containing both forge_entry.py and the forge/ package.

    Root-router launches set FORGE_INSTALL_ROOT. Prefer that first so
    tappable Pythonista root links do not accidentally resolve to
    ~/Documents and then look for docs under lowercase ~/Documents/forge.
    """
    def valid_root(path):
        try:
            path = os.path.abspath(os.path.expanduser(path or ''))
            return (
                os.path.isfile(os.path.join(path, 'forge_entry.py')) and
                os.path.isdir(os.path.join(path, 'forge'))
            )
        except Exception:
            return False

    env_root = os.environ.get('FORGE_INSTALL_ROOT') or ''
    if valid_root(env_root):
        return os.path.abspath(os.path.expanduser(env_root))

    here = os.path.abspath(os.path.dirname(__file__))

    # forge/runtime/paths.py -> forge/ -> project root
    candidate = os.path.abspath(os.path.join(here, '..', '..'))
    if valid_root(candidate):
        return candidate

    # Fallback for unusual development layouts.
    docs = os.path.abspath(os.path.expanduser('~/Documents'))
    forge_install = os.path.join(docs, 'Forge')
    if valid_root(forge_install):
        return forge_install

    return docs
def _norm(path):
    return os.path.abspath(os.path.expanduser(path))


def _add_path(path, front=True):
    """Add path to sys.path if it exists and is not already present."""
    path = _norm(path)
    if not os.path.isdir(path):
        return False

    existing = set(_norm(p) for p in sys.path if p)
    if path in existing:
        return False

    if front:
        sys.path.insert(0, path)
    else:
        sys.path.append(path)
    return True


def candidate_containers(root=None):
    """Return absolute candidate import container paths."""
    root = _norm(root or project_root())
    out = []
    for rel in DEFAULT_CONTAINERS:
        out.append(root if not rel else os.path.join(root, rel))
    return out


def package_markers(package_name, root=None):
    """Return possible package paths for a stable import name."""
    root = _norm(root or project_root())
    out = []
    for container in candidate_containers(root):
        out.append(os.path.join(container, package_name))
    return out


def is_package_dir(path):
    """Return True when path looks like an importable package directory.

    Accept both classic packages with __init__.py and Python 3 namespace-style
    package directories. Several Pythonista project folders currently import
    successfully without __init__.py, so treating plain directories as valid
    keeps this helper aligned with runtime behaviour.
    """
    path = _norm(path)
    if not os.path.isdir(path):
        return False

    if os.path.isfile(os.path.join(path, '__init__.py')):
        return True

    # Namespace/package-like project folder. Avoid accepting empty directories;
    # require at least one useful Python/project marker.
    try:
        names = set(os.listdir(path))
    except Exception:
        return False

    if any(name.endswith('.py') for name in names):
        return True

    marker_dirs = {
        'apps',
        'components',
        'engine',
        'app',
        'entries',
        'pdf_app',
        'flashcards',
        'demos',
        'docs',
    }
    return bool(names & marker_dirs)

def find_package(package_name, root=None):
    """Find the package directory for a stable import name, or return None."""
    for path in package_markers(package_name, root):
        if is_package_dir(path):
            return _norm(path)
    return None


def find_package_parent(package_name, root=None):
    """Find the parent directory that should be on sys.path for package_name."""
    found = find_package(package_name, root)
    if not found:
        return None
    return os.path.dirname(found)


def boot_paths(packages=None, containers=None, root=None, front=True, verbose=False):
    """Add project and discovered package-parent paths to sys.path.

    Parameters
    ----------
    packages:
        Stable package names to look for. Defaults to DEFAULT_PACKAGES.
    containers:
        Optional container relpaths. If supplied, temporarily overrides the
        default container list for this call.
    root:
        Project root. Defaults to ~/Documents.
    front:
        Insert paths at the front of sys.path by default.
    verbose:
        If True, print a small report.

    Returns
    -------
    dict with added, already, missing and root keys.
    """
    root = _norm(root or project_root())
    packages = list(packages or DEFAULT_PACKAGES)

    if containers is None:
        container_paths = candidate_containers(root)
    else:
        container_paths = []
        for rel in containers:
            rel = rel or ''
            container_paths.append(root if not rel else os.path.join(root, rel))

    added = []
    already = []
    missing = []

    # Always keep Documents itself available for current root-level packages
    # and legacy launchers.
    if _add_path(root, front=front):
        added.append(root)
    else:
        already.append(root)

    existing = set(_norm(p) for p in sys.path if p)

    for package in packages:
        parent = None
        for container in container_paths:
            candidate = os.path.join(container, package)
            if is_package_dir(candidate):
                parent = _norm(container)
                break

        if not parent:
            missing.append(package)
            continue

        if parent in existing:
            already.append(parent)
            continue

        if _add_path(parent, front=front):
            added.append(parent)
            existing.add(parent)
        else:
            already.append(parent)

    # Preserve order, remove duplicates.
    def unique(seq):
        seen = set()
        out = []
        for item in seq:
            key = _norm(item) if '/' in str(item) else item
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    report = {
        'root': root,
        'added': unique(added),
        'already': unique(already),
        'missing': unique(missing),
    }

    if verbose:
        print_report(report)

    return report


def print_report(report=None):
    """Print a human-readable path bootstrap report."""
    report = report or boot_paths()
    print('=== FORGE PATH BOOT ===')
    print('root:', report.get('root'))
    print('added:', len(report.get('added') or []))
    for path in report.get('added') or []:
        print('  +', path)
    print('already:', len(report.get('already') or []))
    for path in report.get('already') or []:
        print('  =', path)
    print('missing packages:', len(report.get('missing') or []))
    for name in report.get('missing') or []:
        print('  -', name)


def main(argv=None):
    """CLI probe: python forge/runtime/paths.py."""
    boot_paths(verbose=True)
    print('')
    print('PACKAGE LOCATIONS:')
    for name in DEFAULT_PACKAGES:
        found = find_package(name)
        print('%-12s %s' % (name, found or 'missing'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

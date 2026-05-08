# -*- coding: utf-8 -*-
"""
internal/docs_resolution_smoke.py
=================================

Public LinkOS docs resolution smoke test.

This catches the fresh-install/root-router bug where project_root()
incorrectly resolves to ~/Documents, causing docs.py to look under
~/Documents/forge/guides instead of the installed public Forge root.
"""

from __future__ import print_function

import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT in sys.path:
    try:
        sys.path.remove(ROOT)
    except Exception:
        pass
sys.path.insert(0, ROOT)

os.environ['FORGE_INSTALL_ROOT'] = ROOT


def main():
    print('=== LINKOS DOCS RESOLUTION SMOKE ===')
    print('Expected root:', ROOT)

    from forge.runtime.paths import project_root
    actual_root = os.path.abspath(project_root())
    print('project_root():', actual_root)

    ok = True

    if actual_root != ROOT:
        print('FAIL  project_root resolved wrong root')
        ok = False
    else:
        print('OK    project_root resolved install root')

    from forge.extensions.linkos.data import docs as d

    data_root = os.path.abspath(getattr(d, '_PROJECT_ROOT', ''))
    print('_PROJECT_ROOT:', data_root)

    if data_root != ROOT:
        print('FAIL  docs data root is wrong')
        ok = False
    else:
        print('OK    docs data root resolved install root')

    checks = [
        'onboarding',
        'tutorial',
        'tutorial-files',
        'tutorial-loop',
        'first-run',
        'run-packet',
        'safe-patch',
    ]

    print('')
    print('Doc slugs:')
    for slug in checks:
        status, payload = d.resolve(slug)
        if status == 'hit':
            path = payload.get('path') or ''
            print('OK    %-18s %s' % (slug, os.path.relpath(path, ROOT)))
        else:
            print('MISS  %-18s %s' % (slug, payload))
            ok = False

    print('')
    print('Result:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

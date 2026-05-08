# -*- coding: utf-8 -*-
"""
forge_public_smoke.py
=====================

Public Forge install smoke test.

Run this after install or update. It checks important public files exist and
that the core public scripts/modules compile.

This script is intentionally safe:
- no file writes
- no installs
- no network access
- no Forge bundle execution
"""

from __future__ import print_function

import os
import py_compile


ROOT = os.path.abspath(os.path.dirname(__file__))


REQUIRED_FILES = [
    'README.md',
    'AI_FIRST_BOOT.txt',
    'docs/AI_FIRST_BOOT.txt',
    'docs/MINIMAL_BOOT_BUNDLE.txt',
    'forge_entry.py',
    'linkos.py',
    'start_here.py',
    'install_health.py',
    'install_forge.py',
    'install_root_router.py',
    'forge_public_smoke.py',
    'internal/linkos_route_smoke.py',
    'internal/help_smoke.py',
    'forge/entry.py',
    'forge/op_help.py',
    'forge/ops/core/help_op.py',
    'forge/extensions/linkos/router.py',
    'forge/extensions/linkos/render/footer.py',
    'forge/extensions/linkos/render/primitives.py',
    'forge/extensions/linkos/actions/start.py',
    'forge/extensions/linkos/actions/run_forge.py',
    'forge/extensions/linkos/pages/home.py',
    'forge/extensions/linkos/pages/help.py',
    'forge/extensions/linkos/pages/docs.py',
    'forge/extensions/linkos/pages/unknown.py',
    'forge/extensions/linkos/pages/start_here.py',
    'forge/extensions/linkos/pages/install_health.py',
]


COMPILE = [
    'forge_entry.py',
    'linkos.py',
    'start_here.py',
    'install_health.py',
    'install_forge.py',
    'install_root_router.py',
    'forge_public_smoke.py',
    'internal/linkos_route_smoke.py',
    'internal/help_smoke.py',
    'forge/entry.py',
    'forge/op_help.py',
    'forge/ops/core/help_op.py',
    'forge/extensions/linkos/router.py',
    'forge/extensions/linkos/render/footer.py',
    'forge/extensions/linkos/render/primitives.py',
    'forge/extensions/linkos/render/pills.py',
    'forge/extensions/linkos/actions/start.py',
    'forge/extensions/linkos/actions/run_forge.py',
    'forge/extensions/linkos/pages/home.py',
    'forge/extensions/linkos/pages/help.py',
    'forge/extensions/linkos/pages/docs.py',
    'forge/extensions/linkos/pages/unknown.py',
    'forge/extensions/linkos/pages/start_here.py',
    'forge/extensions/linkos/pages/install_health.py',
]


def _exists(rel):
    return os.path.exists(os.path.join(ROOT, rel))


def _compile(rel):
    path = os.path.join(ROOT, rel)
    try:
        py_compile.compile(path, doraise=True)
        return True, ''
    except Exception as e:
        return False, type(e).__name__ + ': ' + str(e)


def main():
    print('=== FORGE PUBLIC SMOKE TEST ===')
    print('Root:', ROOT)
    print('')

    ok = True

    print('Files:')
    for rel in REQUIRED_FILES:
        exists = _exists(rel)
        print(('OK    ' if exists else 'MISS  ') + rel)
        ok = ok and exists

    print('')
    print('Compile:')
    for rel in COMPILE:
        good, err = _compile(rel)
        print(('OK    ' if good else 'FAIL  ') + rel + ('' if good else ' :: ' + err))
        ok = ok and good

    print('')
    print('Result:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""
forge_public_smoke.py
=====================

Small public Forge install smoke test.
Run manually from Pythonista after installing or updating Forge.
"""

from __future__ import print_function

import os
import py_compile


REQUIRED_FILES = [
    'README.md',
    'docs/AI_FIRST_BOOT.txt',
    'docs/MINIMAL_BOOT_BUNDLE.txt',
    'forge_entry.py',
    'linkos.py',
    'install_forge.py',
    'install_root_router.py',
    'forge/entry.py',
    'forge/op_help.py',
    'forge/extensions/linkos/router.py',
    'forge/extensions/linkos/render/primitives.py',
    'forge/extensions/linkos/actions/start.py',
]


COMPILE_FILES = [
    'forge_entry.py',
    'linkos.py',
    'install_forge.py',
    'install_root_router.py',
    'forge_public_smoke.py',
    'forge/entry.py',
    'forge/op_help.py',
    'forge/extensions/linkos/router.py',
    'forge/extensions/linkos/render/primitives.py',
    'forge/extensions/linkos/render/pills.py',
    'forge/extensions/linkos/actions/start.py',
    'forge/extensions/linkos/actions/run_forge.py',
]


def _root():
    return os.path.abspath(os.path.dirname(__file__))


def _check_files(root):
    print('Files:')
    ok = True
    for rel in REQUIRED_FILES:
        path = os.path.join(root, rel)
        exists = os.path.exists(path)
        print('%-5s %s' % ('OK' if exists else 'MISS', rel))
        if not exists:
            ok = False
    return ok


def _compile_files(root):
    print('')
    print('Compile:')
    ok = True
    for rel in COMPILE_FILES:
        path = os.path.join(root, rel)
        try:
            py_compile.compile(path, doraise=True)
            print('OK   %s' % rel)
        except Exception as e:
            print('FAIL %s — %s: %s' % (rel, type(e).__name__, e))
            ok = False
    return ok


def main():
    root = _root()
    print('=== FORGE PUBLIC SMOKE TEST ===')
    print('Root: %s' % root)
    print('')

    files_ok = _check_files(root)
    compile_ok = _compile_files(root)

    print('')
    if files_ok and compile_ok:
        print('Result: PASS')
        return 0

    print('Result: FAIL')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

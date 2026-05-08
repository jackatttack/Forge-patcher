# -*- coding: utf-8 -*-
"""
forge_public_smoke.py
=====================

Public Forge install smoke test.

Run this after install or update. It checks important public files exist,
that the core public scripts/modules compile, and that LinkOS docs resolve
from the installed project root.

Pythonista note:
- iOS does not support subprocess.
- Internal smoke scripts are executed in-process with runpy.
"""

from __future__ import print_function

import contextlib
import io
import os
import py_compile
import runpy
import sys


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
    'internal/linkos_single_arg_smoke.py',
    'internal/docs_resolution_smoke.py',
    'internal/help_smoke.py',

    'forge/entry.py',
    'forge/op_help.py',
    'forge/runtime/paths.py',
    'forge/ops/core/help_op.py',

    'forge/guides/onboarding.txt',
    'forge/guides/tutorial.txt',
    'forge/guides/tutorial_files.txt',
    'forge/guides/tutorial_loop.txt',
    'forge/guides/first_run.txt',
    'forge/guides/run_packet.txt',
    'forge/guides/safe_patch.txt',

    'forge/extensions/linkos/router.py',
    'forge/extensions/linkos/state.py',
    'forge/extensions/linkos/data/docs.py',
    'forge/extensions/linkos/data/runs.py',
    'forge/extensions/linkos/data/branches.py',
    'forge/extensions/linkos/data/doc_log.py',

    'forge/extensions/linkos/render/cards.py',
    'forge/extensions/linkos/render/console_code.py',
    'forge/extensions/linkos/render/docpage.py',
    'forge/extensions/linkos/render/footer.py',
    'forge/extensions/linkos/render/hero.py',
    'forge/extensions/linkos/render/pills.py',
    'forge/extensions/linkos/render/primitives.py',

    'forge/extensions/linkos/actions/doc_ops.py',
    'forge/extensions/linkos/actions/file_ops.py',
    'forge/extensions/linkos/actions/open_in_pythonista.py',
    'forge/extensions/linkos/actions/run_forge.py',
    'forge/extensions/linkos/actions/run_ops.py',
    'forge/extensions/linkos/actions/safety_ops.py',
    'forge/extensions/linkos/actions/start.py',

    'forge/extensions/linkos/pages/coming_soon.py',
    'forge/extensions/linkos/pages/doc.py',
    'forge/extensions/linkos/pages/doc_missing.py',
    'forge/extensions/linkos/pages/docs.py',
    'forge/extensions/linkos/pages/files.py',
    'forge/extensions/linkos/pages/help.py',
    'forge/extensions/linkos/pages/home.py',
    'forge/extensions/linkos/pages/install_health.py',
    'forge/extensions/linkos/pages/run.py',
    'forge/extensions/linkos/pages/runs.py',
    'forge/extensions/linkos/pages/safety.py',
    'forge/extensions/linkos/pages/start_here.py',
    'forge/extensions/linkos/pages/unknown.py',
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
    'internal/linkos_single_arg_smoke.py',
    'internal/docs_resolution_smoke.py',
    'internal/help_smoke.py',

    'forge/entry.py',
    'forge/op_help.py',
    'forge/runtime/paths.py',
    'forge/ops/core/help_op.py',

    'forge/extensions/linkos/router.py',
    'forge/extensions/linkos/state.py',
    'forge/extensions/linkos/data/docs.py',
    'forge/extensions/linkos/data/runs.py',
    'forge/extensions/linkos/data/branches.py',
    'forge/extensions/linkos/data/doc_log.py',

    'forge/extensions/linkos/render/cards.py',
    'forge/extensions/linkos/render/console_code.py',
    'forge/extensions/linkos/render/docpage.py',
    'forge/extensions/linkos/render/footer.py',
    'forge/extensions/linkos/render/hero.py',
    'forge/extensions/linkos/render/pills.py',
    'forge/extensions/linkos/render/primitives.py',

    'forge/extensions/linkos/actions/doc_ops.py',
    'forge/extensions/linkos/actions/file_ops.py',
    'forge/extensions/linkos/actions/open_in_pythonista.py',
    'forge/extensions/linkos/actions/run_forge.py',
    'forge/extensions/linkos/actions/run_ops.py',
    'forge/extensions/linkos/actions/safety_ops.py',
    'forge/extensions/linkos/actions/start.py',

    'forge/extensions/linkos/pages/coming_soon.py',
    'forge/extensions/linkos/pages/doc.py',
    'forge/extensions/linkos/pages/doc_missing.py',
    'forge/extensions/linkos/pages/docs.py',
    'forge/extensions/linkos/pages/files.py',
    'forge/extensions/linkos/pages/help.py',
    'forge/extensions/linkos/pages/home.py',
    'forge/extensions/linkos/pages/install_health.py',
    'forge/extensions/linkos/pages/run.py',
    'forge/extensions/linkos/pages/runs.py',
    'forge/extensions/linkos/pages/safety.py',
    'forge/extensions/linkos/pages/start_here.py',
    'forge/extensions/linkos/pages/unknown.py',
]


INTERNAL_CHECKS = [
    'internal/docs_resolution_smoke.py',
    'internal/linkos_single_arg_smoke.py',
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


def _evict_forge_modules():
    """Make in-process smoke checks deterministic after path/root edits."""
    for name in list(sys.modules.keys()):
        if name == 'forge' or name.startswith('forge.'):
            try:
                del sys.modules[name]
            except Exception:
                pass


def _run_internal_smoke(rel):
    """Run an internal smoke script without subprocess.

    Pythonista iOS does not support subprocess, so use runpy and capture stdout.
    Treat SystemExit(0) or no SystemExit as success.
    """
    path = os.path.join(ROOT, rel)
    old_argv = list(sys.argv)
    old_path = list(sys.path)
    old_env = os.environ.get('FORGE_INSTALL_ROOT')

    buf = io.StringIO()

    try:
        if ROOT in sys.path:
            while ROOT in sys.path:
                sys.path.remove(ROOT)
        sys.path.insert(0, ROOT)
        os.environ['FORGE_INSTALL_ROOT'] = ROOT
        sys.argv = [path]

        _evict_forge_modules()

        with contextlib.redirect_stdout(buf):
            try:
                runpy.run_path(path, run_name='__main__')
                code = 0
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 0

        return code == 0, buf.getvalue(), ''

    except Exception as e:
        return False, buf.getvalue(), type(e).__name__ + ': ' + str(e)

    finally:
        sys.argv = old_argv
        sys.path[:] = old_path
        if old_env is None:
            try:
                del os.environ['FORGE_INSTALL_ROOT']
            except Exception:
                pass
        else:
            os.environ['FORGE_INSTALL_ROOT'] = old_env
        _evict_forge_modules()


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
    print('Internal checks:')
    for rel in INTERNAL_CHECKS:
        good, out, err = _run_internal_smoke(rel)
        print(('OK    ' if good else 'FAIL  ') + rel)
        if not good:
            if out:
                print(out)
            if err:
                print(err)
        ok = ok and good

    print('')
    print('Result:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

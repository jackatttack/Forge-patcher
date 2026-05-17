# -*- coding: utf-8 -*-
"""
Public surface smoke test for Forge.

This checks that the local forge/ folder can render the user-facing run surface
without relying on the development workspace path.
"""

from __future__ import print_function

import os
import sys
import io
import contextlib


HERE = os.path.dirname(os.path.abspath(__file__))

if HERE not in sys.path:
    sys.path.insert(0, HERE)

os.environ['FORGE_HOME'] = HERE


from entry import run_from_text
from forge_core.surface.page_stack import build_run_page_stack
from forge_core.surface.page_runtime import render_landing, render_stack_page


def check(name, condition):
    if condition:
        print('PASS: ' + name)
    else:
        print('FAIL: ' + name)
        raise AssertionError(name)


def capture(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args)
    return buf.getvalue()


def main():
    bundle = '\n'.join([
        'HELP SURFACE',
        '',
    ])

    run = run_from_text(bundle, project_root=HERE, mode='dev', store=True)
    check('run applied', run.get('status') == 'APPLIED')
    check('artifact dir under forge home', os.path.realpath(run.get('artifact_dir') or '').startswith(os.path.realpath(HERE) + os.sep))

    stack = build_run_page_stack(run, registry={})
    pages = stack.get('pages') or []
    page_ids = [p.get('id') for p in pages]

    check('has run.home', 'run.home' in page_ids)
    check('has op.list', 'op.list' in page_ids)
    check('has run.audit', 'run.audit' in page_ids)
    check('has packet.raw', 'packet.raw' in page_ids)

    landing = capture(render_landing, stack)

    check('landing has rich run clean hero', 'R U N   C L E A N' in landing)
    check('landing has outcome graph', 'Outcome' in landing and 'applied' in landing)
    check('landing has run controls', 'RUN CONTROLS' in landing)
    check('landing has ops navigation', 'Ops' in landing or 'OPS' in landing)
    check('landing has runs navigation', 'Runs' in landing or 'RUNS' in landing)
    check('landing has raw navigation', 'Raw' in landing or 'RAW' in landing)
    check('landing has no runtime failure', 'runtime surface failed' not in landing.lower())
    check('landing has no legacy fallback warning', 'legacy surface failed' not in landing.lower())

    detail = capture(render_stack_page, stack, 'op.detail.0')
    detail_compact = detail.replace(' ', '').replace('\n', '').upper()
    check('detail route renders HELP op', 'HELPSURFACE' in detail_compact or 'HELPFORSURFACE' in detail_compact)
    check('detail route not missing', 'Page not found' not in detail)

    print('')
    print('FORGE PUBLIC SURFACE SMOKE PASSED')
    print('forge_home: ' + HERE)
    print('artifact_dir: ' + str(run.get('artifact_dir') or ''))


if __name__ == '__main__':
    main()
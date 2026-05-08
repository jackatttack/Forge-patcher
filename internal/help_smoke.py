# -*- coding: utf-8 -*-
"""
Probe public minimal Forge HELP behaviour without relying on the outer Forge.
"""

from __future__ import print_function

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from forge.entry import run_from_text


TESTS = [
    ('bare help', 'HELP'),
    ('help help', 'HELP HELP'),
    ('install topic', 'HELP install'),
    ('run missing topic', 'HELP run-missing'),
    ('module not found topic', 'HELP module-not-found'),
    ('buttons topic', 'HELP buttons'),
    ('root topic', 'HELP root'),
]


def _failed_results(result):
    ctx = result.get('context')
    rows = ctx.results if ctx else []
    return [
        r for r in rows
        if str(r.get('status') or '').upper().startswith('FAILED')
    ]


def main():
    print('=== PUBLIC HELP PROBE ===')
    failed = False

    for label, bundle in TESTS:
        print('')
        print('--- ' + label + ' ---')
        result = run_from_text(bundle, project_root=ROOT)
        packet = result.get('packet') or ''
        print(packet[:1200])

        bad = _failed_results(result)
        if bad:
            failed = True
            print('PROBE FAIL: failed result status found')
            for row in bad:
                print('- %s :: %s' % (row.get('status'), row.get('message')))

    print('')
    print('Result:', 'FAIL' if failed else 'PASS')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())

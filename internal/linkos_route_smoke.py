# -*- coding: utf-8 -*-
"""
Probe public LinkOS routes without requiring tappable Pythonista links.
"""

from __future__ import print_function

import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
LINKOS = os.path.join(ROOT, 'linkos.py')

ROUTES = [
    [],
    ['home'],
    ['help', 'install'],
    ['help', 'run-missing'],
    ['help', 'module-not-found'],
    ['help', 'buttons'],
    ['help', 'root'],
    ['install-health'],
    ['docs', 'onboarding'],
    ['unknown_route_test'],
]


def main():
    print('=== LINKOS ROUTE PROBE ===')
    ok = True

    for route in ROUTES:
        label = ' '.join(route) if route else '(direct)'
        print('')
        print('--- ' + label + ' ---')

        # Pythonista's RUN_FILE already executes this script under Python.
        # Use in-process execution so this stays Pythonista-compatible.
        old_argv = sys.argv[:]
        try:
            sys.argv = [LINKOS] + route
            ns = {'__name__': '__main__', '__file__': LINKOS}
            code = open(LINKOS, 'r', encoding='utf-8', errors='replace').read()
            exec(compile(code, LINKOS, 'exec'), ns, ns)
        except SystemExit:
            pass
        except Exception as e:
            ok = False
            print('ROUTE FAIL:', label, type(e).__name__ + ': ' + str(e))
        finally:
            sys.argv = old_argv

    print('')
    print('Result:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

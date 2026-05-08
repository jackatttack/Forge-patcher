# -*- coding: utf-8 -*-
"""
Smoke-test LinkOS routes as Pythonista URL launches often deliver them:
one argv item containing spaces, e.g. ['docs onboarding'].
"""

import os
import sys
import io
import contextlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from forge.extensions.linkos.router import dispatch


ROUTES = [
    'docs onboarding',
    'docs ops',
    'docs tutorials',
    'docs safety',
    'docs extension',
    'docs all',
]


def main():
    print('=== LINKOS SINGLE-ARG ROUTE PROBE ===')
    failed = 0

    for route in ROUTES:
        print('')
        print('--- %s ---' % route)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                dispatch([route])
            text = buf.getvalue()
            if 'UNKNOWN ROUTE' in text or 'did not recognise this route' in text:
                failed += 1
                print('FAIL: unknown route')
                print(text[:800])
            else:
                print('OK')
                # Print a tiny proof slice so packets stay readable.
                lines = [l for l in text.splitlines() if l.strip()]
                for line in lines[:8]:
                    print(line)
        except Exception as e:
            failed += 1
            print('FAIL: %s: %s' % (type(e).__name__, e))

    print('')
    if failed:
        print('Result: FAIL (%d)' % failed)
        return 1

    print('Result: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

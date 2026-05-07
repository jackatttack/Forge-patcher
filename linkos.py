# -*- coding: utf-8 -*-
"""
linkos.py
=========

Standalone LinkOS launcher for public Forge.

Safe behaviour:
- Running this file directly opens Start Here.
- Passing a route dispatches that route.
- It does not run a Forge bundle.
- It should remain a safe file for new users to tap by accident.

Examples:
    pythonista3://linkos.py?action=run
    pythonista3://linkos.py?action=run&argv=start-here
    pythonista3://linkos.py?action=run&argv=help%20install
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def main(argv=None):
    """Dispatch to minimal Forge LinkOS with stale modules evicted."""
    stale = [
        name for name in list(sys.modules.keys())
        if name == 'forge.extensions'
        or name == 'forge.extensions.linkos'
        or name.startswith('forge.extensions.linkos.')
    ]
    for name in stale:
        try:
            del sys.modules[name]
        except Exception:
            pass

    from forge.extensions.linkos.router import dispatch

    # Direct-run should be a lifeboat, not a generic dashboard.
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        argv = ['start-here']

    dispatch(argv)


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
Local launcher for minimal Forge LinkOS.

This file lives beside forge_entry.py so Pythonista URL links from this
minimal install route back into this install, not the user's root/main
Forge launcher.
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
    dispatch(sys.argv[1:] if argv is None else argv)


if __name__ == '__main__':
    main()

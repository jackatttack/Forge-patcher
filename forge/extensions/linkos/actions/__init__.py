# -*- coding: utf-8 -*-
"""LinkOS action handlers.

Each function in this package performs a side effect (write to
clipboard, open Quick Look, run a script, etc.) and then renders a
confirmation page. Actions are dispatched from
:mod:`forge.extensions.linkos.router` based on the route name.

Modules:
    file_ops   File-level actions: copy path, quicklook, open-in, run.
    run_ops    Forge run actions (built later: copy packet, branch, etc.).
"""

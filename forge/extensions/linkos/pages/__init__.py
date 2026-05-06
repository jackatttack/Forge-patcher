# -*- coding: utf-8 -*-
"""LinkOS page renderers.

Each module owns the rendering of one route. Pages compose primitives
from :mod:`forge.extensions.linkos.render` and read data via
:mod:`forge.extensions.linkos.data`. They never call other pages
directly — navigation always goes through the dispatcher.

Modules:
    home     The top-level menu.
    files    Directory browser and file detail view.
    page     Generic placeholder page (used for ad-hoc routes).
    bank     Saved console states (placeholder).
    command  Free-text command palette.
    echo     Argument round-trip view.
    unknown  Recovery view for unrecognised commands.
    run      Run-packet view (built later, replaces ``router.run_panel``).
"""

# -*- coding: utf-8 -*-
"""LinkOS rendering primitives.

Pure print-functions that produce console output. No knowledge of routes,
state, or page composition. Pages and actions import from here; nothing
in here imports from pages or actions.

Modules:
    primitives  Theme, colour, basic text helpers, URL builder.
    hero        Branded section opener + big section labels.
    cards       Boxed panel and action-card primitives.
    pills       Dense tappable links and rows.
    footer      Bottom navigation rail.
"""

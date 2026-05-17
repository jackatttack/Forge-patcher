# -*- coding: utf-8 -*-
"""
forge_core.surface.render
=========================

Render helper package for the Forge LinkOS-style surface.

Compatibility note:
The old plain-text surface renderer used to live at
``forge_core.surface.render`` as a module file. That file has been moved to
``forge_core.surface.legacy_render`` so this directory can behave as a real
Python package and expose submodules such as:

    forge_core.surface.render.hero
    forge_core.surface.render.tile_dock
    forge_core.surface.render.docpage

For now, ``format_surface`` is re-exported here so older reboot code that does
``from forge_core.surface.render import format_surface`` keeps working during
the migration.
"""

try:
    from forge_core.surface.legacy_render import format_surface
except Exception:
    def format_surface(run):
        run = run or {}
        return run.get('packet') or run.get('surface_text') or ''

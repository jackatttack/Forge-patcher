# -*- coding: utf-8 -*-
"""
forge.config
=============
Constants for forge runtime.
"""

RUNS_DIRNAME = 'artifacts/runs'

# Op layers loaded by the registry.
#
# Local/full Forge normally loads both:
# - core: required inspect/edit/run/recover/share surface
# - custom: personal workflow ops and optional integrations
#
# A shareable/minimal Forge can set this to ['core'].
LOAD_OP_LAYERS = ['core']

KEEP_RUNS = 20

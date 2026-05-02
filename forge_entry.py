# -*- coding: utf-8 -*-
"""
forge_entry.py
=================

Self-contained iOS Shortcut entrypoint for minimal Forge.

Expected folder shape:

minimal_forge/
  forge_entry.py
  forge/

The iOS Shortcut can run this file directly. It does not need to live at
Pythonista Documents root.
"""

import os
import sys
import clipboard

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from forge.entry import run_from_text


def run():
    """Read a Forge bundle from clipboard, execute it, and write output back."""
    bundle_text = clipboard.get() or ''
    result = run_from_text(bundle_text, project_root=HERE)
    packet = result.get('packet', '')

    ctx = result.get('context')
    results = ctx.results if ctx else []
    clip_result = next((r.get('clip_result') for r in results if r.get('clip_result')), None)

    clipboard.set(clip_result or packet)

    try:
        print(clip_result or packet)
    except Exception:
        pass

    return result


if __name__ == '__main__':
    run()

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

Run order:

1. Read the Forge bundle from clipboard.
2. Run it against this folder as project root.
3. Copy the clean packet, or explicit clip_result, back to clipboard.
4. Print the clean packet.
5. Render LinkOS run view as the final user-facing console surface.

The packet remains the model-facing source of truth. LinkOS is the
human-facing post-run surface.
"""

import os
import sys
import clipboard

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from forge.entry import run_from_text


def _coerce_clip_text(value):
    """Return clipboard-safe text for packet or explicit clip_result."""
    if value is None:
        return ''
    if isinstance(value, bytes):
        return value.decode('utf-8', 'replace')
    if isinstance(value, str):
        return value
    return str(value)


def _print_fallback_footer(results, stamp=None):
    """Small defensive footer if LinkOS cannot render."""
    applied = sum(1 for r in results if r.get('status') == 'APPLIED')
    failed = sum(1 for r in results if (r.get('status') or '').startswith('FAILED'))
    skipped = len(results) - applied - failed

    print('')
    print('')
    print('=== FORGE LOCAL SUMMARY ===')
    print('applied: %s' % applied)
    print('skipped: %s' % skipped)
    print('failed: %s' % failed)
    if stamp:
        print('run: %s' % stamp)
    print('')
    print('LinkOS did not render. The run packet above is still valid.')


def _render_linkos_run(stamp=None):
    """Render the LinkOS run page after the packet has printed."""
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
    dispatch(['run', stamp] if stamp else ['run', 'latest'])


def run():
    """Read a Forge bundle from clipboard, execute it, and render output."""
    bundle_text = clipboard.get() or ''
    result = run_from_text(bundle_text, project_root=HERE)

    packet = _coerce_clip_text(result.get('packet'))
    ctx = result.get('context')
    results = ctx.results if ctx else []

    clip_result = None
    for r in results:
        if r.get('clip_result') is not None:
            clip_result = r.get('clip_result')
            break

    clipboard.set(_coerce_clip_text(clip_result) if clip_result is not None else packet)

    try:
        print(packet)
    except Exception:
        pass

    stamp = result.get('stamp') or result.get('run_stamp')

    try:
        _render_linkos_run(stamp)
    except Exception as e:
        print('[forge_entry] LinkOS render failed: %s' % e)
        try:
            _print_fallback_footer(results, stamp)
        except Exception as inner:
            print('[forge_entry] fallback footer failed: %s' % inner)

    return result


if __name__ == '__main__':
    run()

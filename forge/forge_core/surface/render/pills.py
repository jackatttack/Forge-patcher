# -*- coding: utf-8 -*-
"""
forge_core.surface.render.pills
================================

Dense tappable link primitives for the reboot live surface.

Pills are the workhorse tappable: the full label is the link, with no
``tap ↗`` suffix and no boxed border. Use these for action grids,
file lists, navigation chips — anywhere a long list of compact
tappables is needed.

The capture-detection logic here is what lets live rendering and
packet rendering share one renderer. In a live Pythonista console
``pill_link`` prints a tappable link; under ``RUN_FILE`` capture it
falls back to plain coloured text so the run packet stays readable.
"""

import sys

try:
    import console as _console
except Exception:
    _console = None

from forge_core.surface.render.primitives import (
    colour, reset, url,
)


def pill_link(label, *args, **kwargs):
    """Print a single pill — the visible label is the tap target."""
    tone = kwargs.get('tone', 'accent')
    icon = kwargs.get('icon', '')
    href = url(*args)

    label_text = str(label)
    if label_text.endswith('/'):
        label_text = label_text[:-1]

    text = (str(icon) if icon else '') + label_text

    captured = hasattr(sys.stdout, 'getvalue')

    if not captured and _console and hasattr(_console, 'write_link'):
        try:
            colour(tone)
            _console.write_link(text, href)
            reset()
            return
        except Exception:
            reset()

    colour(tone)
    print(text, end='')
    reset()


def pill_rows(items, cols=2):
    """Render a grid of pills, ``cols`` per row.

    Each item is a 4-tuple ``(label, args_tuple, tone, icon)``.
    """
    if not items:
        return

    for i, item in enumerate(items):
        label, args, tone, icon = item
        pill_link(label, *args, tone=tone, icon=icon)
        if (i + 1) % cols == 0:
            print('')
        else:
            print('   ', end='')
    if len(items) % cols:
        print('')

# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.render.pills
=====================================

Dense tappable link primitives for LinkOS.

Pills are the workhorse tappable: the full label is the link, with no
``tap ↗`` suffix and no boxed border. Use these for action grids,
file lists, navigation chips — anywhere a long list of compact
tappables is needed.
"""

import sys

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.render.primitives import (
    colour, reset, url,
)


def pill_link(label, *args, **kwargs):
    """Print a single pill — the visible label is the tap target.

    In live Pythonista console output, ``console.write_link`` renders the
    label as a tappable link. During Forge ``RUN_FILE`` capture, however,
    write_link text is not preserved in stdout. Detect captured stdout and
    print a plain label instead so run packets remain readable.
    """
    tone = kwargs.get('tone', 'accent')
    icon = kwargs.get('icon', '')
    href = url(*args)

    label_text = str(label)
    if label_text.endswith('/'):
        label_text = label_text[:-1]

    text = (str(icon) if icon else '') + label_text

    # Forge RUN_FILE capture usually swaps stdout for a StringIO-like
    # object. In that mode console.write_link is invisible to the packet,
    # so preserve the label as plain text.
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

    Each item is a 4-tuple ``(label, args_tuple, tone, icon)``. Items
    are emitted left-to-right with a 3-space gap between columns and
    a newline at the end of each row.
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

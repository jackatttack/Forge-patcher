# -*- coding: utf-8 -*-
"""
forge_core.surface.render.cards
================================

Boxed and badged card primitives.

* ``panel`` — quiet labelled box for grouping prose lines.
* ``badge`` — short uppercase tag, inline.
* ``action_link`` — fully-boxed tappable card, used for high-weight
  one-of-a-kind actions. Prefer ``pill_link`` for dense lists.
"""

try:
    import console as _console
except Exception:
    _console = None

from forge_core.surface.render.primitives import (
    colour, reset, say, spacer, url,
)


def panel(title_text, lines=None, icon='▣', tone='surface_2'):
    """Print a labelled prose panel with a soft trailing rule."""
    spacer()
    colour(tone)
    print('▌ %s  %s' % (icon, title_text))
    reset()
    if lines:
        for line in lines:
            say('  ' + str(line), 'muted')
    say('  ' + '━' * 28, 'surface_2')


def badge(text, tone='surface_2'):
    """Print an uppercase ``[TAG]`` badge inline (no newline)."""
    colour(tone)
    print('  [%s]' % str(text).upper(), end='')
    reset()


def action_link(label, *args, **kwargs):
    """Print a fully-boxed tappable action card.

    Heavy visual weight — reserve for one or two top-of-page actions
    per page. For dense action grids use
    :func:`forge_core.surface.render.pills.pill_link`.
    """
    icon = kwargs.get('icon', '🔗')
    tone = kwargs.get('tone', 'accent')
    note = kwargs.get('note', '')
    tag = kwargs.get('tag', '')
    index = kwargs.get('index', '')
    href = url(*args)
    button = '_' + str(label).upper() + '_'

    spacer()

    colour('surface_2')
    print('╭' + '─' * 38)
    reset()

    prefix = ('%02d' % index) if isinstance(index, int) else str(index or '»')

    colour(tone)
    print('│ %s  %s  %s' % (prefix, icon, str(label)), end='')
    reset()

    if tag:
        print('   ', end='')
        colour(tone)
        print('[%s]' % str(tag).upper())
        reset()
    else:
        print('')

    if note:
        say('│     ' + str(note), 'muted')

    colour('border')
    print('│  ↳  ', end='')
    reset()

    if _console and hasattr(_console, 'write_link'):
        try:
            colour('border')
            _console.write_link(button, href)
            reset()
        except Exception:
            say(button, 'border')
    else:
        say(button, 'border')

    colour('surface_2')
    print('╰' + '─' * 22)
    reset()

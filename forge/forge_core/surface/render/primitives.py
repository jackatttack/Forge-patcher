# -*- coding: utf-8 -*-
"""
forge_core.surface.primitives
==============================

Theme, colour, low-level text helpers, and URL building for the reboot
LinkOS-style live surface.

This is the foundation module — everything else in ``surface/`` that
draws live console output imports from here. It owns:

* The ``HEX`` palette and resolved ``PALETTE`` (RGB triples).
* The ``colour`` / ``reset`` / ``font`` console helpers.
* Plain text helpers: ``say``, ``spacer``, ``band``, ``soft``,
  ``thin_rule``, ``small_note``, ``kv``, ``write_tap``.
* Section labels: ``section_label``.
* One-line status rows: ``status_line``.
* The ``url()`` builder that produces ``pythonista3://`` links pointed
  at the reboot launcher script.

The Pythonista ``console`` module is imported defensively so this code
also runs cleanly when imported outside Pythonista (e.g. for testing).
"""

import os

try:
    import console
except Exception:
    console = None

try:
    from urllib.parse import quote
except Exception:
    from urllib import quote


# -- launcher script --------------------------------------------------------
#
# Name of the root-level Python file Pythonista invokes for reboot URLs.
# Every tappable surface link points back at this script with an ``argv``
# query string. If the launcher is renamed, change this constant.
SCRIPT = 'forge_entry.py'


# -- theme roles -------------------------------------------------------------

try:
    from forge_core.surface.theme import resolve_tone
except Exception:
    def resolve_tone(name, default='text'):
        return str(name or default).strip() or default


# -- palette ----------------------------------------------------------------

def _hex_to_rgb(value):
    """Convert a ``#RRGGBB`` string to an RGB float triple in 0..1."""
    value = str(value).strip().lstrip('#')
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# Forge sunset palette. Add new tones here, never inline RGB values in
# render code — the palette is the single source of theme truth.
HEX = {
    'accent':     '#5AA9FF',
    'background': '#08001E',
    'border':     '#E91E63',
    'danger':     '#FF5A5F',
    'muted':      '#9FB4C9',
    'panel':      '#101D2B',
    'success':    '#4CD964',
    'surface':    '#29173D',
    'surface_2':  '#501A3E',
    'text':       '#EEF6FF',
    'warning':    '#FFD166',
    'orange':     '#FF9F43',
    'cyan':       '#5DEBFF',
}

PALETTE = dict((k, _hex_to_rgb(v)) for k, v in HEX.items())


# -- console helpers --------------------------------------------------------

def colour(name):
    """Set the console foreground colour by palette name or semantic role.

    Semantic roles are resolved through ``forge_core.surface.theme`` before
    hitting the concrete palette. Existing raw tones such as ``success`` and
    ``warning`` continue to work unchanged.
    """
    if not console:
        return
    try:
        tone = resolve_tone(name)
        console.set_color(*PALETTE.get(tone, PALETTE['text']))
    except Exception:
        pass


def reset():
    """Restore the foreground colour to the body text tone."""
    colour('text')


def font(name='Menlo', size=15):
    """Set the console font, falling back to defaults if unsupported."""
    if not console:
        return
    try:
        console.set_font(name, size)
    except Exception:
        try:
            console.set_font()
        except Exception:
            pass


# -- url construction -------------------------------------------------------

def q(text):
    """URL-quote a single value with no safe characters."""
    return quote(str(text or ''), safe='')


def url(*args):
    """Build a Pythonista launch URL for the reboot dispatcher.

    Positional ``args`` are joined into a single ``argv`` string. Empty
    args are dropped. Returns a URL of the form
    ``pythonista3://forge_entry.py?action=run&argv=<route>``.
    """
    arg_text = ' '.join(str(a) for a in args if str(a) != '')
    if arg_text:
        return 'pythonista3://%s?action=run&argv=%s' % (SCRIPT, q(arg_text))
    return 'pythonista3://%s?action=run' % SCRIPT


# -- text rows --------------------------------------------------------------

def say(text='', tone=None):
    """Print one line, optionally wrapped in a colour tone."""
    if tone:
        colour(tone)
    print(str(text))
    if tone:
        reset()


def spacer(n=1):
    """Print ``n`` blank lines."""
    for _ in range(n):
        print('')


def band(char='━', width=46, tone='border'):
    """Print a heavy horizontal rule. Used for page hero borders."""
    say(char * width, tone)


def soft(width=34, tone='muted', char='─'):
    """Print a softer/narrower rule. Used for inline separators."""
    say(char * width, tone)


def thin_rule(width=46, tone='surface_2', char='─'):
    """Print a single quiet rule line — no spacers, no colour reset gap.

    Designed for the run-panel hero where the rule frames content
    without the visual weight of ``band``.
    """
    say(char * width, tone)


def small_note(text, icon='•', tone='muted'):
    """Print a single note line: ``icon  text`` in the given tone."""
    say('%s  %s' % (icon, text), tone)


def kv(label, value, icon='•', tone='accent'):
    """Print a key/value row with an arrow separator.

    Format: ``icon  label  →  value`` — icon and label use ``tone``,
    arrow is muted, value is body text.
    """
    colour(tone)
    print('%s  %s' % (icon, label), end='')
    colour('muted')
    print('  →  ', end='')
    colour('text')
    print(value)
    reset()


def section_label(text, icon=None, tone='muted'):
    """Print a single-line section header with no underline.

    Lighter than a hero band — for lists where each item already
    carries its own visual weight.
    """
    if icon:
        say('%s  %s' % (icon, str(text).upper()), tone)
    else:
        say(str(text).upper(), tone)


def status_line(emoji, *parts, **kwargs):
    """Print a one-line status row: ``emoji  part1  part2  …``.

    ``parts`` is a sequence of ``(text, tone)`` pairs or plain strings.
    Plain strings render in the default body tone. The leading emoji is
    always rendered uncoloured so its native colour shows through.
    """
    sep = kwargs.get('sep', '  ')
    print(str(emoji), end='  ')
    for i, p in enumerate(parts):
        if i > 0:
            colour('muted')
            print(sep, end='')
            reset()
        if isinstance(p, tuple) and len(p) == 2:
            text, tone = p
            colour(tone)
            print(str(text), end='')
            reset()
        else:
            colour('text')
            print(str(p), end='')
            reset()
    print('')


def write_tap(label, href, tone='border'):
    """Print a visible label followed by a tappable ``tap ↗`` link.

    Used when the visible label needs to read in captured Forge stdout
    (where ``console.write_link`` text is not preserved). Prefer
    ``pill_link`` from ``surface.pills`` when the full label can be
    the link.
    """
    colour(tone)
    print(label)
    reset()

    if console and hasattr(console, 'write_link'):
        try:
            console.write_link('      tap ↗', href)
            return
        except Exception:
            pass

    say('      ' + href, tone)

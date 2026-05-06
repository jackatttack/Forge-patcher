# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.run_forge
========================================

Launch the normal minimal Forge entry loop from LinkOS.
"""

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.render.docpage import (
    doc_actions, doc_footer, doc_hero, doc_text,
)


FORGE_URL = 'pythonista3://forge_entry.py?action=run'


def _open_url(url):
    if _console and hasattr(_console, 'open_url'):
        try:
            _console.open_url(url)
            return True
        except Exception:
            pass

    try:
        import webbrowser
        webbrowser.open(url)
        return True
    except Exception:
        return False


def run_forge():
    """Launch forge_entry.py through the normal Pythonista URL route."""
    ok = _open_url(FORGE_URL)

    if _console:
        try:
            _console.hud_alert(
                'Running Forge' if ok else 'Launch failed',
                'success' if ok else 'error',
                0.9,
            )
        except Exception:
            pass

    doc_hero('Run Forge', 'launch clipboard loop')

    if ok:
        doc_text('Forge has been launched. If a bundle is on the clipboard, it will run through the normal Forge loop.')
        doc_text('After the run completes, return to LinkOS and inspect the latest run.')
    else:
        doc_text('Could not launch Forge automatically.', tone='muted')
        doc_text('Run forge_entry.py manually, then return to LinkOS.', tone='muted')

    doc_actions([
        ('Home', ('home',), 'success', '🏠 '),
        ('Docs', ('docs',), 'accent', '📖 '),
        ('Start', ('start',), 'warning', '🏁 '),
    ])
    doc_footer()

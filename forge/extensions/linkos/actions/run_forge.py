# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.run_forge
========================================

Launch the normal minimal Forge entry loop from LinkOS.

Contained mode:
    LinkOS renders, but the user should run forge_entry.py manually.

Root-router mode:
    LinkOS can open pythonista3://forge_entry.py?action=run because a
    deliberate root launcher exists at Pythonista Documents root.
"""

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.render.docpage import (
    doc_actions, doc_footer, doc_hero, doc_text,
)
from forge.extensions.linkos.render.primitives import (
    root_router_installed,
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
    """Launch forge_entry.py when root-router links are active."""
    links_active = root_router_installed()
    ok = _open_url(FORGE_URL) if links_active else False

    if _console:
        try:
            _console.hud_alert(
                'Running Forge' if ok else 'Manual launch needed',
                'success' if ok else 'error',
                0.9,
            )
        except Exception:
            pass

    doc_hero('Run Forge', 'clipboard loop')

    if ok:
        doc_text('Forge has been launched. If a bundle is on the clipboard, it will run through the normal Forge loop.')
        doc_text('After the run completes, return to LinkOS and inspect the latest run.')
    else:
        doc_text('LinkOS is currently in contained/display-only mode.')
        doc_text('Run forge_entry.py manually from Pythonista to execute the clipboard bundle.')
        doc_text('To enable tappable LinkOS buttons and wider workspace access, install the optional root router. This is convenient, but it gives Forge broader access, so only enable it deliberately.', tone='muted')

    doc_actions([
        ('Home', ('home',), 'success', '🏠 '),
        ('Docs', ('docs',), 'accent', '📖 '),
        ('Start', ('start',), 'warning', '🏁 '),
        ('Root mode', ('doc', 'root-launcher-mode'), 'orange', '🧭 '),
    ])
    doc_footer()

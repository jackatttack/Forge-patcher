# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.open_in_pythonista
===================================================

Open any project file directly in the Pythonista editor.

Same one-tap pattern as :mod:`forge.extensions.linkos.actions.scratch`:
no confirmation page, render LinkOS home so the console persists when
the user swipes back from the editor, then fire the
``pythonista3://...?action=open`` URL via :mod:`webbrowser`.
"""

import os

try:
    import console as _console
except Exception:
    _console = None

try:
    from forge.runtime.paths import project_root
    _PROJECT_ROOT = project_root()
except Exception:
    _PROJECT_ROOT = os.path.expanduser('~/Documents')


def _flash_hud(message):
    """Show a Pythonista HUD alert if available; silent otherwise."""
    if _console:
        try:
            _console.hud_alert(message, 'success', 0.8)
        except Exception:
            pass


def open_in_pythonista(rel):
    """Open ``rel`` in the Pythonista editor.

    ``rel`` is a project-relative file path. The file is not modified;
    Pythonista will create it on first save if it doesn't exist yet.

    Renders LinkOS home before firing the URL so the user has a useful
    place to land when they swipe back from the editor.
    """
    import webbrowser
    from forge.extensions.linkos.pages.home import home

    rel = str(rel or '').strip().lstrip('/')
    if not rel:
        _flash_hud('No file')
        return

    abs_path = os.path.join(_PROJECT_ROOT, rel)
    if not os.path.exists(abs_path):
        _flash_hud('File missing')
    else:
        _flash_hud('Opening')

    # Render home first so the console has something to show when the
    # user returns from the editor.
    try:
        home()
    except Exception:
        pass

    url = 'pythonista3://%s?action=open' % rel
    try:
        webbrowser.open(url)
    except Exception:
        from forge.extensions.linkos.render.docpage import (
            doc_footer, doc_hero, doc_text,
        )
        doc_hero('Open failed', rel)
        doc_text('Could not auto-open in Pythonista.', tone='danger')
        doc_text('URL: %s' % url, tone='muted')
        doc_footer()

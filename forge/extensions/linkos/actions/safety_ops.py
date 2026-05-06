# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.safety_ops
==========================================

Public/minimal safety bundle generators.
"""

try:
    import clipboard as _clipboard
except Exception:
    _clipboard = None

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.data import runs as _runs


def _flash_hud(message, kind='success'):
    if _console:
        try:
            _console.hud_alert(message, kind, 1.0)
        except Exception:
            pass


def _set_clipboard(text):
    if _clipboard is None:
        return False
    try:
        _clipboard.set(str(text))
        return True
    except Exception:
        return False


def _render_home():
    try:
        from forge.extensions.linkos.pages.home import home
        home()
    except Exception:
        pass


def revert_run(stamp=None):
    """Copy REVERT_RUN bundle to clipboard."""
    if not stamp or stamp == 'latest':
        stamp = _runs.latest_stamp()

    if not stamp:
        _flash_hud('No run to revert', 'error')
        _render_home()
        return

    bundle = 'REVERT_RUN %s\n' % stamp
    _flash_hud('Revert bundle copied' if _set_clipboard(bundle) else 'Clipboard failed',
               'success' if _clipboard else 'error')
    _render_home()


def restore_branch(name):
    """Copy BRANCH restore bundle to clipboard."""
    name = str(name or '').strip()
    if not name:
        _flash_hud('No branch named', 'error')
        _render_home()
        return

    bundle = 'BRANCH restore %s\n' % name
    _flash_hud('Restore bundle copied' if _set_clipboard(bundle) else 'Clipboard failed',
               'success' if _clipboard else 'error')
    _render_home()

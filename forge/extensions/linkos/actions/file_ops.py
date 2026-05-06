# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.file_ops
=========================================

File-level action handlers for LinkOS.

Each function performs a side effect on a single file path and then
renders either a confirmation page (clipboard copy, run completion)
or delegates to :func:`forge.extensions.linkos.pages.files.file_detail`
(quicklook, open-in — where the side effect itself surfaces a UI).

All paths are sanitised through
:func:`forge.extensions.linkos.pages.files.safe_rel` so unsafe inputs
fail closed to the project root.
"""

import os

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.pages.files import (
    abs_for_rel, file_detail, file_icon, safe_rel,
)
from forge.extensions.linkos.render.cards import panel
from forge.extensions.linkos.render.footer import footer
from forge.extensions.linkos.render.hero import big_section, hero
from forge.extensions.linkos.render.pills import pill_rows
from forge.extensions.linkos.render.primitives import band, small_note


def copy_path(rel):
    """Copy a relative path to the clipboard and render a confirmation page.

    Shows a HUD alert when running in Pythonista. Failures are silent —
    the confirmation page still renders so the user has a clear next
    move via the action grid.
    """
    rel = safe_rel(rel)
    try:
        import clipboard
        clipboard.set(rel)
        if _console:
            _console.hud_alert('Path copied', 'success', 1.0)
    except Exception:
        pass

    hero('Copied path', '⧉', rel)
    panel('Clipboard', ['Copied relative path:', rel], icon='⧉', tone='border')
    big_section('Next', '→', 'accent')
    pill_rows([
        ('FILE', ('files', rel), 'warning', file_icon(rel)),
        ('HOME', ('home',), 'success', '🏠'),
    ], cols=2)
    footer()


def quicklook_file(rel):
    """Open the iOS Quick Look preview for a file, then re-render its detail page.

    If Quick Look raises (unsupported file, etc.), renders an error
    page and returns. Otherwise the detail page renders after the
    user dismisses the preview.
    """
    rel = safe_rel(rel)
    abs_path = abs_for_rel(rel)

    if _console:
        try:
            _console.quicklook(abs_path)
        except Exception as e:
            hero('QuickLook failed', '⚠️', rel)
            panel('Error', [str(e)], icon='⚠️', tone='danger')
            footer()
            return

    file_detail(rel, abs_path)


def open_in_file(rel):
    """Open a file via the iOS share sheet (``open in...``)."""
    rel = safe_rel(rel)
    abs_path = abs_for_rel(rel)

    if _console:
        try:
            _console.open_in(abs_path)
        except Exception as e:
            hero('Open In failed', '⚠️', rel)
            panel('Error', [str(e)], icon='⚠️', tone='danger')
            footer()
            return

    file_detail(rel, abs_path)


def run_py_file(rel):
    """Run a Python file with confirmation, then render an after-run page.

    Refuses non-``.py`` paths. In Pythonista, prompts via
    ``console.alert`` before executing — cancelling falls back to the
    file detail page. Captures ``SystemExit`` and other exceptions and
    renders them as inline notes rather than crashing LinkOS.
    """
    rel = safe_rel(rel)
    abs_path = abs_for_rel(rel)

    if not rel.lower().endswith('.py'):
        hero('Run blocked', '⚠️', rel)
        panel('Not a Python file', ['Only .py files can be run from LinkOS.'], icon='⚠️', tone='danger')
        footer()
        return

    if _console:
        try:
            choice = _console.alert(
                'Run Python file?',
                rel,
                'Run',
                'Cancel',
                hide_cancel_button=True,
            )
            if choice != 1:
                file_detail(rel, abs_path)
                return
        except Exception:
            pass

    hero('Running file', '▶️', rel)
    band('━', 46, 'danger')
    try:
        import runpy
        runpy.run_path(abs_path, run_name='__main__')
    except SystemExit as e:
        small_note('SystemExit: %s' % e, icon='⚠️', tone='warning')
    except Exception as e:
        small_note('Run failed: %s' % e, icon='⚠️', tone='danger')
    band('━', 46, 'danger')

    big_section('After run', '→', 'accent')
    pill_rows([
        ('FILE', ('files', rel), 'warning', file_icon(rel)),
        ('FOLDER', ('files', os.path.dirname(rel) or '.'), 'orange', '⬅️'),
        ('HOME', ('home',), 'success', '🏠'),
    ], cols=2)
    footer()

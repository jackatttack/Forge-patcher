# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.start
======================================

First-time Start action for LinkOS.

Copies the starter Forge bundle that a new user can paste into an LLM.
The LLM then guides them through the onboarding/tutorial docs.
"""

try:
    import clipboard as _clipboard
except Exception:
    _clipboard = None

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.render.docpage import (
    doc_actions, doc_footer, doc_hero, doc_text,
)


STARTER_BUNDLE = """DOCS
OPEN: llm-first-time-guide, onboarding
SUGGEST: concepts, the-loop, run-packet, tutorial, tutorial-loop
"""


def start():
    """Copy the first-time LLM starter bundle and render instructions."""
    ok = False
    if _clipboard is not None:
        try:
            _clipboard.set(STARTER_BUNDLE)
            ok = True
        except Exception:
            ok = False

    if _console:
        try:
            if ok:
                _console.hud_alert('Starter copied', 'success', 0.9)
            else:
                _console.hud_alert('Copy failed', 'error', 1.0)
        except Exception:
            pass

    doc_hero('Start Forge', 'new user handoff')

    if ok:
        doc_text('The first-time Forge starter bundle is now on your clipboard.')
        doc_text('Paste it into an LLM of your choice. It will use the Forge docs to guide you through onboarding and the first tutorials.')
        doc_text('After that, run the bundle through Forge and paste the run packet back to the LLM.')
    else:
        doc_text('Could not copy the starter bundle automatically.', tone='muted')
        doc_text('Open onboarding or llm-first-time-guide and copy the starter bundle manually.', tone='muted')

    doc_actions([
        ('Onboarding', ('doc', 'onboarding'), 'success', '🏁 '),
        ('LLM guide', ('doc', 'llm-first-time-guide'), 'accent', '🤖 '),
        ('Tutorials', ('doc', 'tutorial'), 'warning', '🎓 '),
        ('Home', ('home',), 'border', '🏠 '),
    ])
    doc_footer()

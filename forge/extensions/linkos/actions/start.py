# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.start
======================================

First-time Start action for LinkOS.

Copies the LLM first-boot guide, not a raw Forge bundle.

That distinction matters:

- A raw Forge bundle is for forge_entry.py.
- The first Start handoff is for an LLM.
- The LLM guide teaches the assistant what Forge is, what a runnable
  bundle looks like, and what it should output first.
"""

import os

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

try:
    from forge.runtime.paths import project_root as _project_root
except Exception:
    _project_root = None


GUIDE_PATH = 'docs/AI_FIRST_BOOT.txt'


FALLBACK_LLM_GUIDE = """Forge AI First Boot

You are working with Forge, a clipboard-based patching harness for Pythonista on iOS.

The user will copy one of your Forge bundles to the clipboard, run forge_entry.py in Pythonista, and paste the returned run packet back to you.

The run packet is the source of truth.

Your first response should output the minimal boot bundle from docs/MINIMAL_BOOT_BUNDLE.txt inside a plain code block.
"""


def _root():
    """Return the current Forge project root."""
    if _project_root is not None:
        try:
            return _project_root()
        except Exception:
            pass

    here = os.path.abspath(os.path.dirname(__file__))
    # start.py -> actions -> linkos -> extensions -> forge -> project root
    return os.path.abspath(os.path.join(here, '..', '..', '..', '..', '..'))


def _read_guide_text():
    """Read the LLM first-boot guide from disk, with a tiny fallback."""
    path = os.path.join(_root(), GUIDE_PATH)
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read().strip()
        if text:
            return text + '\n'
    except Exception:
        pass
    return FALLBACK_LLM_GUIDE


def start():
    """Copy the first-time LLM guide and render instructions."""
    copied_text = _read_guide_text()

    ok = False
    if _clipboard is not None:
        try:
            _clipboard.set(copied_text)
            ok = True
        except Exception:
            ok = False

    if _console:
        try:
            if ok:
                _console.hud_alert('LLM guide copied', 'success', 0.9)
            else:
                _console.hud_alert('Copy failed', 'error', 1.0)
        except Exception:
            pass

    doc_hero('Start Forge', 'LLM handoff')

    if ok:
        doc_text('The LLM first-boot guide is now on your clipboard.')
        doc_text('Paste it into an LLM. It explains Forge, shows what a runnable bundle looks like, and tells the LLM what to output first.')
        doc_text('The LLM should then give you a small runnable Forge bundle in a code block. Copy that bundle, run forge_entry.py, and paste the packet back.')
    else:
        doc_text('Could not copy the LLM guide automatically.', tone='muted')
        doc_text('Open llm-first-time-guide or docs/AI_FIRST_BOOT.txt and copy the guide manually.', tone='muted')

    doc_actions([
        ('LLM guide', ('doc', 'llm-first-time-guide'), 'accent', '🤖 '),
        ('Onboarding', ('doc', 'onboarding'), 'success', '🏁 '),
        ('Tutorials', ('doc', 'tutorial'), 'warning', '🎓 '),
        ('Home', ('home',), 'border', '🏠 '),
    ])
    doc_footer()

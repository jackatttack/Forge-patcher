# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.start
=====================================

Copy the real AI first-boot guide for a fresh assistant.

The Start action is the main handoff from LinkOS to an LLM. It should copy the
full AI_FIRST_BOOT.txt document, not a tiny placeholder.
"""

import os

import clipboard


FALLBACK_GUIDE = '''Forge AI First Boot
===================

You are helping a user work with Forge.

Forge is a local, clipboard-based patching and automation harness for Pythonista on iOS.

The user will copy Forge bundles from you, run forge_entry.py, and paste the returned run packet back.

The run packet is the source of truth.

A Forge bundle is plain text made of ops like:

    LIST_FILES .
    DEPTH: 2
    FILES: yes

    LIST_OPS

    HELP

    HELP HELP

    RUN_FILE start_here.py

Only put runnable Forge syntax inside the bundle. Do not include comments or markdown headings inside runnable bundles.

Your first response should give this orientation bundle:

    LIST_FILES .
    DEPTH: 2
    FILES: yes

    LIST_OPS

    HELP

    HELP HELP

    DOCS
    OPEN: onboarding
    SUGGEST: concepts, the-loop, run-packet, inspect-first, safe-patch

    RUN_FILE start_here.py

Tell the user to copy the bundle, run forge_entry.py in Pythonista, and paste the packet back.

After every packet, read it carefully. Do not claim files changed, tests passed, or uploads happened unless the packet proves it.
'''


def _project_root():
    """Return the public Forge install root."""
    try:
        from forge.runtime.paths import project_root
        root = project_root()
        if root:
            return os.path.abspath(root)
    except Exception:
        pass

    try:
        here = os.path.abspath(os.path.dirname(__file__))
        return os.path.abspath(os.path.join(here, '..', '..', '..', '..'))
    except Exception:
        return os.path.abspath(os.path.expanduser('~/Documents/Forge'))


def _read_guide():
    """Read the best available AI first-boot guide."""
    root = _project_root()
    candidates = [
        os.path.join(root, 'AI_FIRST_BOOT.txt'),
        os.path.join(root, 'docs', 'AI_FIRST_BOOT.txt'),
    ]

    for path in candidates:
        try:
            if os.path.isfile(path):
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    text = f.read().strip()
                if text:
                    return text
        except Exception:
            pass

    return FALLBACK_GUIDE.strip()


def start():
    """Copy the AI first-boot guide to the clipboard and print a short status."""
    text = _read_guide()
    clipboard.set(text)

    print('')
    print('=== FORGE START ===')
    print('')
    print('Copied AI_FIRST_BOOT.txt to the clipboard.')
    print('')
    print('Paste it into a fresh LLM chat.')
    print('The assistant should return the first safe Forge bundle.')
    print('')
    print('chars: %s' % len(text))
    print('')
    return text


if __name__ == '__main__':
    start()

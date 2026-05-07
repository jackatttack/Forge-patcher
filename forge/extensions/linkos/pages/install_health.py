# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.install_health
============================================

Human-facing install-health page for LinkOS.

This is intentionally explanatory. The standalone install_health.py script is
the dependency-light checker to run when LinkOS itself is not trustworthy.
"""

import os

from forge.extensions.linkos.render.docpage import (
    doc_actions, doc_footer, doc_hero, doc_section, doc_text,
)


MARKER = 'FORGE_ROOT_ROUTER'


def _documents_root():
    return os.path.abspath(os.path.expanduser('~/Documents'))


def _project_root():
    try:
        from forge.runtime.paths import project_root
        return os.path.abspath(project_root())
    except Exception:
        return os.path.abspath(os.path.expanduser('~/Documents'))


def _contains(path, needle):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return needle in f.read(5000)
    except Exception:
        return False


def install_health_page():
    """Render a friendly install state page."""
    docs = _documents_root()
    root = _project_root()
    root_entry = os.path.join(docs, 'forge_entry.py')
    root_linkos = os.path.join(docs, 'linkos.py')
    root_router = _contains(root_entry, MARKER) or _contains(root_linkos, MARKER)
    shadow = os.path.isdir(os.path.join(docs, 'forge'))

    doc_hero('Install Health', 'where am I?')

    doc_section('quick status')
    doc_text('Active root: ' + root)
    doc_text('Documents root: ' + docs)
    doc_text('Root router: ' + ('installed' if root_router else 'not detected'))
    doc_text('Lowercase root forge/ shadow: ' + ('yes' if shadow else 'no'))

    doc_section('what this means')
    if root_router:
        doc_text('Root router mode appears active. Tappable LinkOS buttons should be more reliable, and Forge may see the wider Pythonista Documents workspace.')
    else:
        doc_text('Contained/display-only mode may be active. That is a valid and safe first-user setup.')
        doc_text('If buttons do not tap, run forge_entry.py manually.')

    if shadow:
        doc_text('A lowercase Documents/forge folder exists. This can shadow a public Forge install and cause import errors.', tone='danger')
        doc_text('If you see ModuleNotFoundError, fully restart Pythonista and inspect this folder before continuing.', tone='warning')

    doc_section('safe next steps')
    doc_text('Run start_here.py if you are unsure what to do.')
    doc_text('Run install_health.py for a dependency-light plain-text check.')
    doc_text('Run forge_public_smoke.py after install/update.')
    doc_text('Only run install_root_router.py when you deliberately want root/tappable-link mode.')

    doc_actions([
        ('Start Here', ('start-here',), 'success', '🧭 '),
        ('Root mode', ('doc', 'root-launcher-mode'), 'orange', '🧭 '),
        ('Docs', ('docs',), 'accent', '📖 '),
        ('Home', ('home',), 'success', '🏠 '),
    ])

    doc_footer()

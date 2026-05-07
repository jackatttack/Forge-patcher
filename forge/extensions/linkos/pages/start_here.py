# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.start_here
========================================

Rendered Start Here lifeboat for LinkOS.

This page mirrors the standalone root start_here.py script but uses the LinkOS
DocPage visual language. It is the safest default page for new users, stale
routes, direct linkos.py runs, and failed orientation states.
"""

from forge.extensions.linkos.render.docpage import (
    doc_actions, doc_footer, doc_hero, doc_section, doc_text,
)


def start_here_page():
    """Render the public Forge Start Here page."""
    doc_hero('Start Here', 'safe orientation')

    doc_section('what Forge is')
    doc_text('Forge is a local Pythonista harness for working with an LLM.')
    doc_text('The LLM gives you a plain-text Forge bundle. You choose when to run it.')
    doc_text('Forge runs the bundle locally and returns a run packet.')
    doc_text('The run packet is the source of truth.')

    doc_section('first safe path')
    doc_text('1. Run forge_entry.py once.')
    doc_text('2. Open AI_FIRST_BOOT.txt at the root of this project and paste it into an LLM.')
    doc_text('3. Copy the small Forge bundle the LLM gives you.')
    doc_text('4. Run forge_entry.py again and paste the packet back.')

    doc_section('if something looks wrong')
    doc_text('Buttons do not tap: contained mode may be active. Run forge_entry.py manually.')
    doc_text('RUN MISSING: the visual run page could not find saved details; the packet above may still be valid.')
    doc_text('Failed parse: your clipboard probably did not contain a valid Forge bundle.')
    doc_text('ModuleNotFoundError: restart Pythonista, then run install_health.py.')
    doc_text('Cannot see your wider files: root launcher mode is optional.')

    doc_section('useful files')
    doc_text('AI_FIRST_BOOT.txt — paste this into an LLM.')
    doc_text('forge_entry.py — runs the Forge clipboard loop.')
    doc_text('start_here.py — standalone orientation lifeboat.')
    doc_text('install_health.py — read-only install checker.')
    doc_text('install_root_router.py — optional root/tappable-link mode.')
    doc_text('forge_public_smoke.py — sanity check.')

    doc_actions([
        ('Start', ('start',), 'success', '🏁 '),
        ('Health', ('install-health',), 'warning', '🩺 '),
        ('Docs', ('docs',), 'accent', '📖 '),
        ('Root mode', ('help', 'root'), 'orange', '🧭 '),
    ])

    doc_footer()

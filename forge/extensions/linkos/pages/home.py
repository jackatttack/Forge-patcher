# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.home
===================================

The top-level LinkOS launcher.

Home is a friendly command centre. Start Here is the lifeboat. Home should
make the safe path obvious while still giving experienced users fast routes
to runs, docs, files, health, and the Forge loop.
"""

from forge.extensions.linkos.data import runs as _runs
from forge.extensions.linkos.render.docpage import (
    doc_footer, doc_hero, doc_inline, doc_run_card, doc_section, doc_text,
    doc_tile_grid,
)


def home():
    """Render the LinkOS home route."""
    doc_hero('LinkOS Home', 'forge command surface')

    doc_inline(
        'New here or something weird happened? Open [[onboarding]], tap Start Here, '
        'or run install_health.py. LinkOS is the human-facing layer: it should '
        'help you understand where you are before you do anything risky.',
        source='home:intro',
    )

    doc_tile_grid('safe first', [
        ('🧭 ', 'Start Here', 'orientation', ('start-here',), 'success'),
        ('🩺 ', 'Health', 'install check', ('install-health',), 'warning'),
        ('🏁 ', 'Start', 'copy LLM guide', ('start',), 'success'),
        ('▶️ ', 'Run Forge', 'clipboard loop', ('run_forge',), 'orange'),
    ])

    doc_section('latest run')
    latest_stamp = _runs.latest_stamp()
    if latest_stamp:
        run = _runs.load_run(latest_stamp)
        doc_run_card(run, route=('run', latest_stamp))
    else:
        doc_text('No Forge runs yet. Run forge_entry.py once, then come back here.', tone='muted')

    doc_tile_grid('workbench', [
        ('📖 ', 'Docs', 'learn Forge', ('docs',), 'accent'),
        ('❔ ', 'Help', 'human help', ('help', 'HELP'), 'border'),
        ('📁 ', 'Files', 'browse project', ('files', '.'), 'cyan'),
        ('◎ ', 'Runs', 'history', ('runs',), 'success'),
        ('🛟 ', 'Safety', 'restore + revert', ('safety',), 'border'),
        ('🧭 ', 'Root Mode', 'optional power', ('doc', 'root-launcher-mode'), 'orange'),
        ('🎓 ', 'Tutorials', 'learn by doing', ('docs', 'tutorials'), 'warning'),
        ('⚙ ', 'Ops Help', 'commands', ('docs', 'ops'), 'accent'),
    ])

    doc_footer()

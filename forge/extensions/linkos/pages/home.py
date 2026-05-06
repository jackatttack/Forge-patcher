# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.home
===================================

The top-level LinkOS launcher.

Three sections, top to bottom in console scroll order:

1. Hero + intro paragraph — orientation for new users.
2. Latest run card — the run panel is LinkOS's primary surface, so
   "what just happened" is always one tap away from home.
3. Workbench tile grid — six destinations covering files, runs, docs,
   shortcuts, scratch, and bank.

Home is for going somewhere. The run page is for acting on something.
Home deliberately has no action grid — actions live on the pages you
navigate into.
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
        'New here? Tap Start to copy the first-time LLM guide. '
        'Paste that guide into an LLM first; it will explain Forge and give you the first runnable bundle. '
        'You can also read [[onboarding]] or jump into [[tutorial]].',
        source='home:intro',
    )

    # Latest run — the most likely thing you wanted when you tapped LinkOS.
    doc_section('latest run')
    latest_stamp = _runs.latest_stamp()
    if latest_stamp:
        run = _runs.load_run(latest_stamp)
        doc_run_card(run, route=('run', latest_stamp))
    else:
        doc_text('No Forge runs yet. Run a bundle and check back here.', tone='muted')

    doc_tile_grid('workbench', [
        ('🏁 ', 'Start',     'copy LLM guide',  ('start',),                  'success'),
        ('📖 ', 'Docs',      'learn Forge',     ('docs',),                   'accent'),
        ('📁 ', 'Files',     'browse project',  ('files', '.'),              'cyan'),
        ('◎ ',  'Runs',      'history',         ('runs',),                   'success'),
        ('🛟 ', 'Safety',    'restore + revert',('safety',),                 'border'),
        ('🎓 ', 'Tutorials', 'learn by doing',  ('docs', 'tutorials'),       'warning'),
        ('❔ ', 'Help',      'op reference',    ('help', 'HELP'),            'border'),
        ('▶️ ', 'Run Forge', 'clipboard loop',  ('run_forge',),              'orange'),
    ])
    doc_footer()

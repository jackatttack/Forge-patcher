# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.docs
===================================

Docs Hub for LinkOS.

This is the navigation surface for learning and onboarding. It is not a
search page yet. The first version is a curated set of category grids that
send the user to the right kind of doc quickly.
"""

from forge.extensions.linkos.render.docpage import (
    doc_footer, doc_header_nav, doc_hero, doc_section, doc_text,
    doc_tile_grid,
)


CATEGORIES = [
    ('🚪 ', 'Onboarding', 'start here', ('docs', 'onboarding'), 'success'),
    ('🎓 ', 'Tutorials', 'learn by doing', ('docs', 'tutorials'), 'warning'),
    ('⚙ ', 'Ops Help', 'commands', ('docs', 'ops'), 'accent'),
    ('🛟 ', 'Safety', 'patch + recover', ('docs', 'safety'), 'border'),
    ('🧩 ', 'Extension', 'custom ops', ('docs', 'extension'), 'cyan'),
    ('📚 ', 'All Docs', 'curated index', ('docs', 'all'), 'muted'),
]


DOC_GROUPS = {
    'onboarding': [
        ('🧭 ', 'start_here', 'safe orientation', ('start-here',), 'success'),
        ('🚪 ', 'onboarding', 'start here', ('doc', 'onboarding'), 'success'),
        ('🧠 ', 'llm_first_time_guide', 'AI guide', ('doc', 'llm-first-time-guide'), 'warning'),
        ('🌱 ', 'first_boot', 'AI first boot', ('doc', 'first-boot'), 'success'),
        ('✅ ', 'first_run', 'after packet', ('doc', 'first-run'), 'accent'),
        ('🧭 ', 'root_launcher_mode', 'project scope', ('doc', 'root-launcher-mode'), 'orange'),
        ('🔁 ', 'the_loop', 'clipboard loop', ('doc', 'the-loop'), 'accent'),
        ('🧩 ', 'concepts', 'vocabulary', ('doc', 'concepts'), 'cyan'),
        ('📦 ', 'run_packet', 'packet truth', ('doc', 'run-packet'), 'border'),
    ],
    'safety': [
        ('🩺 ', 'install_health', 'check install', ('install-health',), 'warning'),
        ('🛟 ', 'safe_patch', 'patch safely', ('doc', 'safe-patch'), 'success'),
        ('🔒 ', 'core_edit', 'core guard', ('doc', 'core-edit'), 'warning'),
        ('🧯 ', 'tutorial_recovery', 'undo + restore', ('doc', 'tutorial-recovery'), 'orange'),
        ('❌ ', 'failure_reading', 'bad packets', ('doc', 'tutorial-failure-reading'), 'danger'),
        ('🧭 ', 'inspect_first', 'orient first', ('doc', 'inspect-first'), 'border'),
    ],
    'ops': [
        ('❔ ', 'HELP', 'op reference', ('help', 'HELP'), 'accent'),
        ('📖 ', 'DOCS', 'living docs', ('help', 'DOCS'), 'warning'),
        ('🔗 ', 'LINKOS', 'surface', ('help', 'LINKOS'), 'cyan'),
        ('📁 ', 'LIST_FILES', 'tree view', ('help', 'LIST_FILES'), 'accent'),
        ('👁 ', 'PREVIEW', 'read source', ('help', 'PREVIEW'), 'border'),
        ('🔎 ', 'GREP', 'search', ('help', 'GREP'), 'cyan'),
        ('▶️ ', 'RUN_FILE', 'execute', ('help', 'RUN_FILE'), 'warning'),
        ('🌿 ', 'BRANCH', 'checkpoint', ('help', 'BRANCH'), 'success'),
        ('✍️ ', 'REPLACE', 'AST edit', ('help', 'REPLACE'), 'orange'),
        ('🌐 ', 'URL', 'HTTP client', ('help', 'URL'), 'cyan'),
        ('📦 ', 'PIP', 'packages', ('help', 'PIP'), 'success'),
    ],
    'tutorials': [
        ('🎓 ', 'tutorial', 'learning hub', ('doc', 'tutorial'), 'warning'),
        ('🔁 ', 'tutorial_loop', 'first loop', ('doc', 'tutorial-loop'), 'success'),
        ('📄 ', 'tutorial_files', 'file ops', ('doc', 'tutorial-files'), 'accent'),
        ('🔎 ', 'tutorial_search', 'inspect first', ('doc', 'tutorial-search'), 'cyan'),
        ('🛟 ', 'tutorial_patching', 'safe edits', ('doc', 'tutorial-patching'), 'border'),
        ('🧯 ', 'tutorial_recovery', 'undo + restore', ('doc', 'tutorial-recovery'), 'orange'),
        ('❌ ', 'tutorial_failure', 'read failures', ('doc', 'tutorial-failure-reading'), 'danger'),
        ('⚙ ', 'tutorial_ops', 'op map', ('doc', 'tutorial-ops'), 'accent'),
        ('🌐 ', 'tutorial_url', 'HTTP client', ('doc', 'tutorial-url'), 'cyan'),
        ('📦 ', 'tutorial_pip', 'packages', ('doc', 'tutorial-pip'), 'success'),
    ],
    'extension': [
        ('🧾 ', 'docs_authoring', 'write docs', ('doc', 'docs-authoring'), 'warning'),
        ('📖 ', 'docs_vs_guide', 'doc types', ('doc', 'docs-vs-guide'), 'border'),
        ('🧾 ', 'tutorial_docs', 'living docs', ('doc', 'tutorial-docs-authoring'), 'warning'),
        ('🧩 ', 'tutorial_custom', 'make an op', ('doc', 'tutorial-custom-op'), 'accent'),
        ('🛠 ', 'tutorial_extend', 'grow Forge', ('doc', 'tutorial-extension'), 'orange'),
        ('🧩 ', 'add_custom_op', 'new op', ('doc', 'add-custom-op'), 'accent'),
        ('⚙ ', 'custom_ops', 'op layer', ('doc', 'custom-ops'), 'accent'),
        ('🔒 ', 'tutorial_core', 'core edits', ('doc', 'tutorial-core-edit'), 'danger'),
    ],
    'all': [
        ('🧭 ', 'start_here', 'safe orientation', ('start-here',), 'success'),
        ('🩺 ', 'install_health', 'check install', ('install-health',), 'warning'),
        ('🚪 ', 'onboarding', 'start here', ('doc', 'onboarding'), 'success'),
        ('🧠 ', 'llm_first_time_guide', 'AI guide', ('doc', 'llm-first-time-guide'), 'warning'),
        ('✅ ', 'first_run', 'after packet', ('doc', 'first-run'), 'accent'),
        ('🧭 ', 'root_launcher_mode', 'project scope', ('doc', 'root-launcher-mode'), 'orange'),
        ('🔁 ', 'the_loop', 'clipboard loop', ('doc', 'the-loop'), 'accent'),
        ('🧩 ', 'concepts', 'vocabulary', ('doc', 'concepts'), 'cyan'),
        ('📦 ', 'run_packet', 'packet truth', ('doc', 'run-packet'), 'border'),
        ('🎓 ', 'tutorial', 'guided intro', ('doc', 'tutorial'), 'warning'),
        ('🛟 ', 'safe_patch', 'patch safely', ('doc', 'safe-patch'), 'success'),
        ('🧯 ', 'tutorial_recovery', 'recover', ('doc', 'tutorial-recovery'), 'orange'),
        ('📖 ', 'docs_authoring', 'living docs', ('doc', 'docs-authoring'), 'warning'),
        ('🧩 ', 'add_custom_op', 'new op', ('doc', 'add-custom-op'), 'accent'),
        ('📋 ', 'minimal_release', 'release plan', ('doc', 'minimal-public-release-plan'), 'muted'),
    ],
}


CATEGORY_TITLES = {
    'onboarding': ('Docs Onboarding', 'start here'),
    'safety': ('Docs Safety', 'safe patching'),
    'ops': ('Docs Ops Help', 'commands'),
    'tutorials': ('Docs Tutorials', 'worked examples'),
    'extension': ('Docs Extension', 'build Forge'),
    'all': ('Docs Index', 'curated list'),
}


def docs_page(category=''):
    """Render the Docs Hub or one docs category."""
    category = str(category or '').strip().lower()

    doc_header_nav()

    if not category:
        doc_hero('Docs', 'learn forge')
        doc_text(
            'Choose the kind of help you need. This is the front door for '
            'Forge onboarding, safety, ops, tutorials, and extension work.'
        )
        doc_tile_grid('docs hub', CATEGORIES)
        doc_footer()
        return

    if category not in DOC_GROUPS:
        doc_hero('Docs', 'unknown category')
        doc_text('No docs category exists for: %s' % category, tone='muted')
        doc_section('categories')
        doc_tile_grid('docs hub', CATEGORIES)
        doc_footer()
        return

    title, subtitle = CATEGORY_TITLES.get(category, ('Docs', category))
    doc_hero(title, subtitle)
    doc_tile_grid(category, DOC_GROUPS.get(category) or [])
    doc_footer()

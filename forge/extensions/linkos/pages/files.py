# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.files
====================================

Directory browser and file detail view, rendered in DocPage grammar.

Two responsibilities live here because they are tightly coupled:

* :func:`files_panel` lists folders and files at a path. If the path
  resolves to a single file, it delegates to :func:`file_detail`.
* :func:`file_detail` renders a per-file action page with a tappable
  breadcrumb, single-line metadata, and an action grid keyed off the
  file type (Python files get Run; non-text files get Quick Look;
  every file gets Open in Pythonista).

Helper functions (:func:`safe_rel`, :func:`join_rel`, :func:`file_icon`,
:func:`abs_for_rel`) stay in this module so the page is fully
self-contained.
"""

import os

try:
    from forge.runtime.paths import project_root
    PROJECT_ROOT = project_root()
except Exception:
    PROJECT_ROOT = os.path.expanduser('~/Documents')

from forge.extensions.linkos.render.docpage import (
    doc_breadcrumb, doc_footer, doc_hero, doc_section, doc_size,
    doc_text, doc_tile_grid,
)
from forge.extensions.linkos.render.pills import pill_link
from forge.extensions.linkos.render.primitives import (
    colour, reset, say, spacer,
)


# Quick Look is offered for binary/preview-friendly file types where
# the Pythonista editor is not the right surface. Editable formats
# (.py, .md, .txt, .json, .html, .css, .js) get Pythonista editor
# instead and skip Quick Look entirely.
_QUICKLOOK_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.heic', '.pdf', '.svg')

# Item display caps. Bumped from previous values — we'd rather scroll
# than hide useful entries.
_FOLDER_CAP = 40
_FILE_CAP = 60


# -- path helpers -----------------------------------------------------------

def safe_rel(path):
    """Sanitise a relative path argument to project-root-safe form.

    Rejects absolute paths, parent-escapes, and empty values. Returns
    ``'.'`` for any unsafe input so callers always have a valid root
    fallback.
    """
    path = (path or '.').strip()
    path = path.replace('\\', '/')
    if not path or path == '.':
        return '.'
    norm = os.path.normpath(path).replace('\\', '/')
    if norm.startswith('../') or norm == '..' or os.path.isabs(norm):
        return '.'
    return norm


def join_rel(base, name):
    """Join a child name onto a base relative path, re-sanitising the result."""
    base = safe_rel(base)
    if base == '.':
        return safe_rel(name)
    return safe_rel(base + '/' + name)


def file_icon(path, is_dir=False):
    """Return an emoji icon based on file extension or directory flag."""
    if is_dir:
        return '📁'
    lower = path.lower()
    if lower.endswith('.py'):
        return '🐍'
    if lower.endswith(('.md', '.txt')):
        return '📄'
    if lower.endswith('.json'):
        return '🧩'
    if lower.endswith(('.html', '.css', '.js')):
        return '🌐'
    if lower.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        return '🖼️'
    if lower.endswith('.pdf'):
        return '📕'
    return '▪'


def abs_for_rel(rel):
    """Resolve a sanitised relative path to an absolute filesystem path."""
    rel = safe_rel(rel)
    return PROJECT_ROOT if rel == '.' else os.path.join(PROJECT_ROOT, rel)


def _file_type_label(rel):
    """Return a human label for a file's apparent type."""
    lower = str(rel or '').lower()
    if lower.endswith('.py'):
        return 'python script'
    if lower.endswith('.md'):
        return 'markdown'
    if lower.endswith('.txt'):
        return 'text'
    if lower.endswith('.json'):
        return 'json'
    if lower.endswith(('.html', '.css', '.js')):
        return 'web'
    if lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.heic', '.svg')):
        return 'image'
    if lower.endswith('.pdf'):
        return 'pdf'
    return 'file'


def _wants_quicklook(rel):
    """Return True if this file type benefits from Quick Look."""
    return str(rel or '').lower().endswith(_QUICKLOOK_EXTS)


# -- file detail page ------------------------------------------------------

def file_detail(rel, abs_path):
    """Render the per-file detail page in DocPage grammar.

    Layout:

        * Hero — spaced filename title + file-type subtitle
        * Metadata line — name · size · type
        * Breadcrumb path bar (tappable parent segments)
        * OPEN section — tile grid keyed off file type
        * PATH section — relative path + copy action
    """
    try:
        size = os.path.getsize(abs_path)
    except Exception:
        size = 0

    parent = os.path.dirname(rel) or '.'
    name = os.path.basename(rel)
    is_py = rel.lower().endswith('.py')
    type_label = _file_type_label(rel)

    doc_hero(name, type_label)

    # Single-line metadata row.
    doc_text('%s · %s · %s' % (name, doc_size(size), type_label), tone='muted')

    # Breadcrumb (only if this file isn't at project root).
    if parent and parent != '.':
        doc_section('path')
        doc_breadcrumb(parent)

    # Action tile grid keyed off file type.
    tiles = []
    tiles.append(('🐍 ', 'Pythonista', 'editor', ('open_pythonista', rel), 'success'))

    if is_py:
        tiles.append(('▶️ ', 'Run', 'with confirm', ('run_py', rel), 'danger'))

    tiles.append(('↗ ', 'Open In', 'share sheet', ('open_in', rel), 'accent'))
    tiles.append(('📂 ', 'Folder', parent if parent != '.' else 'root', ('files', parent), 'orange'))

    if _wants_quicklook(rel):
        tiles.append(('👁️ ', 'Quick Look', 'preview', ('quicklook', rel), 'cyan'))

    doc_tile_grid('open', tiles)

    # Path + copy action.
    doc_section('copy')
    print(' ' * 3, end='')
    pill_link('Copy path', 'copy_path', rel, tone='warning', icon='📋 ')
    print('')
    say(' ' * 3 + rel, 'muted')

    doc_footer()


# -- file browser page ----------------------------------------------------

def _list_dir(abs_path):
    """Return ``(dirs, files)`` for a path, filtering hidden entries.

    ``.forge_secrets`` is shown despite its leading dot because it's a
    real Forge directory; other dotfiles are filtered.
    """
    try:
        names = os.listdir(abs_path)
    except Exception:
        return None, None

    dirs = []
    files = []
    for name in names:
        if name.startswith('.') and name not in ('.forge_secrets',):
            continue
        child = os.path.join(abs_path, name)
        if os.path.isdir(child):
            dirs.append(name)
        else:
            files.append(name)

    dirs.sort(key=lambda x: x.lower())
    files.sort(key=lambda x: x.lower())
    return dirs, files


def files_panel(path='.'):
    """Render the file/folder browser at ``path`` in DocPage grammar.

    Behaviour:

    * If the path doesn't exist → renders a recovery page.
    * If the path is a file → delegates to :func:`file_detail`.
    * If the path is a directory → renders breadcrumb + folder list +
      file list with sizes. No quick-controls block (the bottom rail
      and breadcrumb cover navigation).
    """
    rel = safe_rel(path)
    abs_path = abs_for_rel(rel)

    # Missing path recovery.
    if not os.path.exists(abs_path):
        doc_hero('Files', 'missing path')
        doc_text(rel, tone='danger')
        doc_text('Bad file links should fail into useful navigation.', tone='muted')
        doc_section('recovery')
        print(' ' * 3, end='')
        pill_link('Project root', 'files', '.', tone='success', icon='📁 ')
        print('')
        doc_footer()
        return

    # File path → delegate.
    if os.path.isfile(abs_path):
        file_detail(rel, abs_path)
        return

    # Directory listing.
    dirs, files = _list_dir(abs_path)
    if dirs is None:
        doc_hero('Files', 'blocked')
        doc_text('Cannot read folder: %s' % rel, tone='danger')
        doc_footer()
        return

    total = len(dirs) + len(files)
    title_subtitle = rel if rel != '.' else 'project root'

    doc_hero('Files', title_subtitle)

    doc_text(
        '%d folders · %d files · %d total' % (len(dirs), len(files), total),
        tone='muted',
    )

    # Breadcrumb only at non-root.
    if rel != '.':
        doc_section('path')
        doc_breadcrumb(rel)

    # Folders.
    if dirs:
        doc_section('folders')
        spacer()
        shown_dirs = dirs[:_FOLDER_CAP]
        for name in shown_dirs:
            child_rel = join_rel(rel, name)
            print(' ' * 3, end='')
            pill_link(name, 'files', child_rel, tone='accent', icon='📁 ')
            print('')
        if len(dirs) > _FOLDER_CAP:
            spacer()
            say(
                ' ' * 3 + '... %d more folder(s) hidden' % (len(dirs) - _FOLDER_CAP),
                'muted',
            )

    # Files with sizes.
    if files:
        doc_section('files')
        spacer()
        shown_files = files[:_FILE_CAP]
        for name in shown_files:
            child_rel = join_rel(rel, name)
            try:
                size = os.path.getsize(os.path.join(abs_path, name))
            except Exception:
                size = 0

            print(' ' * 3, end='')
            pill_link(name, 'files', child_rel, tone='warning', icon=file_icon(name) + ' ')
            # Size right-padded — keeps the size column visually anchored.
            colour('muted')
            print('   ' + doc_size(size))
            reset()
        if len(files) > _FILE_CAP:
            spacer()
            say(
                ' ' * 3 + '... %d more file(s) hidden' % (len(files) - _FILE_CAP),
                'muted',
            )

    if not dirs and not files:
        doc_section('empty')
        doc_text('No items in this folder.', tone='muted')

    doc_footer()

# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.data.docs
==================================

Doc registry and parser for the LinkOS docs system.

A "doc" is a structured ``.txt`` file under one of the registered doc
roots. The format is loose markdown-ish:

    # slug                       ← title line, optional. Defaults to filename.

    ## SECTION NAME              ← uppercase section header

    Prose paragraphs.

    1. Numbered lists
    2. Render verbatim

    - Bullet lists

        Indented blocks render as code.

    [[other_slug]]               ← inline link to another doc
    [[OP_NAME]]                  ← inline link to op HELP page

    ## RELATED                   ← optional, special-cased section
    - other_slug — short note
    - another_slug — another note

This module exposes:

* :func:`list_docs`       — every doc currently on disk, newest first.
* :func:`load_doc(slug)`  — return a parsed doc dict, or ``None``.
* :func:`resolve(slug)`   — return ``('hit', doc)`` or ``('miss', slug)``.
* :func:`parse(text)`     — pure parse, returns the structured dict.

Doc roots are declared in :data:`DOC_ROOTS`. New roots can be added
without changing parsing or rendering.

The on-disk format is deliberately tolerant. Missing title, missing
sections, weird formatting — all render. The renderer is dumb; the
parser does the work.
"""

import os
import re

try:
    from forge.runtime.paths import project_root
    _PROJECT_ROOT = project_root()
except Exception:
    _PROJECT_ROOT = os.path.expanduser('~/Documents')


# Folders to scan for docs. The first existing entry takes precedence
# if the same slug is found in two roots, but in practice slugs are
# unique. Add new roots here as the corpus grows beyond Forge guides.
DOC_ROOTS = [
    'forge/guides',
]


# -- slug + path helpers --------------------------------------------------

def _abs_root(rel_root):
    """Return absolute path for a registered root."""
    return os.path.join(_PROJECT_ROOT, rel_root)


def _slug_for_filename(name):
    """Return the slug for a doc filename. ``safe_patch.txt`` -> ``safe_patch``."""
    base = os.path.basename(str(name or ''))
    if '.' in base:
        base = base.rsplit('.', 1)[0]
    return base.strip()


def _path_for_slug(slug):
    """Return the absolute file path for ``slug`` if it exists, else ``''``.

    Accept both hyphen and underscore forms so user-facing doc links can
    use natural slugs like ``first-run`` while files can remain named
    ``first_run.txt``.
    """
    raw = str(slug or '').strip()
    if not raw:
        return ''

    candidates = []
    for value in (
        raw,
        raw.replace('-', '_'),
        raw.replace('_', '-'),
    ):
        if value and value not in candidates:
            candidates.append(value)

    for root in DOC_ROOTS:
        abs_root = _abs_root(root)
        for candidate_slug in candidates:
            candidate = os.path.join(abs_root, candidate_slug + '.txt')
            if os.path.isfile(candidate):
                return candidate

    return ''

_SECTION_RE = re.compile(r'^(#{2,})\s+(.+)\s*$')

# Title lines are a single ``#`` then a slug-shape word.
_TITLE_RE = re.compile(r'^#\s+([\w\-:]+)\s*$')


def _classify_line(raw):
    """Return a structural classification for a line.

    Output kinds:
        ``'blank'``     — whitespace-only line
        ``'title'``     — single-hash title line
        ``'section'``   — multi-hash section header
        ``'numbered'``  — ``N.`` list item
        ``'bulleted'``  — ``-`` or ``*`` list item
        ``'code'``      — line starts with 4+ spaces or a tab
        ``'prose'``     — anything else
    """
    if not raw.strip():
        return 'blank'

    # Code lines preserve their indentation as a signal.
    if raw.startswith('    ') or raw.startswith('\t'):
        return 'code'

    stripped = raw.strip()
    if _TITLE_RE.match(raw):
        return 'title'
    if _SECTION_RE.match(raw):
        return 'section'
    if re.match(r'^\d+\.\s', stripped):
        return 'numbered'
    if stripped.startswith('- ') or stripped.startswith('* '):
        return 'bulleted'
    return 'prose'


def _parse_related_block(block_lines):
    """Return a list of ``(slug, note)`` pairs from a RELATED section.

    Each line is expected to be ``- slug — note`` or ``- slug``. The
    em-dash separator is preferred but ``--`` and ``-`` are tolerated.
    Empty lines are skipped.
    """
    rows = []
    for line in block_lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith(('- ', '* ')):
            s = s[2:].strip()

        slug = s
        note = ''
        for sep in (' — ', ' -- ', ' - '):
            if sep in s:
                slug, note = s.split(sep, 1)
                slug = slug.strip()
                note = note.strip()
                break

        # Defensive: drop anything that doesn't look slug-shaped.
        if slug and re.match(r'^[\w\-:]+$', slug):
            rows.append((slug, note))
    return rows


def _is_related_section(name):
    """Return True if a section name is the special RELATED section."""
    return str(name or '').strip().upper().startswith('RELATED')


def parse(text, fallback_title=''):
    """Parse a doc's raw text into a structured dict.

    Returns a dict with keys:
        ``title``    — the title line slug, or ``fallback_title``.
        ``sections`` — list of ``{'name', 'lines'}`` in document order.
        ``related``  — list of ``(slug, note)`` pairs from RELATED.

    Title lines are metadata and are always consumed. They should never
    leak into the intro body, even when the title is already known from
    the filename fallback.
    """
    title = str(fallback_title or '').strip()
    sections = []
    related = []

    raw_lines = str(text or '').splitlines()

    current_name = None
    current_lines = []

    def _flush():
        if current_name is None and not current_lines:
            return

        name = current_name or 'intro'

        # RELATED is parsed and consumed, not stored as a regular section.
        if _is_related_section(name):
            related.extend(_parse_related_block(current_lines))
            return

        # Trim trailing blank lines for clean rendering.
        cleaned = list(current_lines)
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()

        if cleaned or current_name:
            sections.append({'name': name, 'lines': cleaned})

    for line in raw_lines:
        kind = _classify_line(line)

        if kind == 'title':
            if not title:
                m = _TITLE_RE.match(line)
                if m:
                    title = m.group(1).strip()
            continue

        if kind == 'section':
            _flush()
            m = _SECTION_RE.match(line)
            current_name = m.group(2).strip() if m else 'untitled'
            current_lines = []
            continue

        current_lines.append(line)

    _flush()

    return {
        'title': title,
        'sections': sections,
        'related': related,
    }

def list_docs():
    """Return all docs across all registered roots.

    Each entry: ``{'slug', 'path', 'mtime', 'root'}``. Sorted by mtime
    desc — newest first.
    """
    rows = []
    for root in DOC_ROOTS:
        abs_root = _abs_root(root)
        if not os.path.isdir(abs_root):
            continue
        try:
            for name in os.listdir(abs_root):
                if not name.endswith('.txt'):
                    continue
                if name.startswith('.'):
                    continue
                path = os.path.join(abs_root, name)
                try:
                    mtime = os.path.getmtime(path)
                except Exception:
                    mtime = 0
                rows.append({
                    'slug': _slug_for_filename(name),
                    'path': path,
                    'mtime': mtime,
                    'root': root,
                })
        except Exception:
            continue

    rows.sort(key=lambda r: r['mtime'], reverse=True)
    return rows


def load_doc(slug):
    """Load and parse a doc by slug. Returns ``None`` if not found.

    Returned dict adds ``'slug'`` and ``'path'`` to the parse result.
    """
    path = _path_for_slug(slug)
    if not path:
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception:
        return None

    parsed = parse(text, fallback_title=slug)
    parsed['slug'] = slug
    parsed['path'] = path
    return parsed


def resolve(slug):
    """Resolve a slug to ``('hit', doc)`` or ``('miss', slug)``.

    The dispatcher and renderer use this so missing slugs never raise —
    they route to the missing-doc page instead.
    """
    doc = load_doc(slug)
    if doc is not None:
        return 'hit', doc
    return 'miss', str(slug or '')


def relative_time(mtime):
    """Return a short relative-time string for a unix mtime."""
    import time
    if not mtime:
        return ''
    delta = int(time.time() - float(mtime))
    if delta < 30:
        return 'just now'
    if delta < 60:
        return '%d sec ago' % delta
    mins = delta // 60
    if mins < 60:
        return '%d min ago' % mins
    hrs = mins // 60
    if hrs < 24:
        return '%d hr ago' % hrs
    days = hrs // 24
    if days < 30:
        return '%d days ago' % days
    return '%d mo ago' % (days // 30)

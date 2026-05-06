# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.doc
==================================

Universal doc renderer.

Loads a doc by slug, parses it, renders sections through DocPage
primitives. Inline ``[[]]`` links resolve through the doc registry
and log every resolution attempt.

Section rendering rules:

* ``## RELATED``     — special-cased into a tile grid at page bottom.
* ``## SUMMARY``     — rendered as muted prose under the hero.
* ``## WHEN TO USE`` — rendered as a small framed callout.
* All other sections — rendered as a doc_section with body lines
  classified per-line (prose / numbered / bulleted / code) and
  emitted through the matching DocPage primitive.

Inline ``[[]]`` markup is expanded in every prose line by routing
through :func:`forge.extensions.linkos.render.docpage.doc_inline`.
"""

import re

from forge.extensions.linkos.data import docs as _docs
from forge.extensions.linkos.render.docpage import (
    doc_actions, doc_bullets, doc_bundle, doc_code, doc_footer,
    doc_header_nav, doc_hero, doc_inline, doc_section, doc_text,
    doc_tile_grid,
)
from forge.extensions.linkos.render.pills import pill_link
from forge.extensions.linkos.render.primitives import (
    colour, reset, say, spacer,
)


def _classify_line_for_render(raw):
    """Match the parser's classification, repeated here for the renderer."""
    if not raw.strip():
        return 'blank'
    if raw.startswith('    ') or raw.startswith('\t'):
        return 'code'
    stripped = raw.strip()
    if re.match(r'^\d+\.\s', stripped):
        return 'numbered'
    if stripped.startswith('- ') or stripped.startswith('* '):
        return 'bulleted'
    return 'prose'


def _strip_list_marker(line):
    """Strip leading ``- ``, ``* ``, or ``N. `` from a list line."""
    s = line.strip()
    if s.startswith(('- ', '* ')):
        return s[2:]
    m = re.match(r'^(\d+)\.\s+(.*)$', s)
    if m:
        return m.group(2)
    return s


def _numbered_parts(line):
    """Return ``(number, text)`` for a numbered list line."""
    s = str(line or '').strip()
    m = re.match(r'^(\d+)\.\s+(.*)$', s)
    if not m:
        return '', s
    return m.group(1), m.group(2)


def _render_numbered_items(lines, source=''):
    """Render numbered lists as aligned numbered rows."""
    for line in lines or []:
        num, body = _numbered_parts(line)
        if not body:
            continue

        # Prefix is part of the first line only; doc_inline reserves the
        # same width on continuations so wrapped text stays aligned.
        doc_inline(body, source=source, indent=3, first_prefix='%s.  ' % (num or '•'))

def _render_section_body(lines, source=''):
    """Render a section body through DocPage primitives.

    Supports Forge-native copyable bundle blocks:

        @forge-bundle optional-label
        LIST_FILES .
        DEPTH: 2
        @end-forge-bundle

    These render as code plus a Copy bundle action. The copied text is
    handled by actions.doc_ops so page rendering stays side-effect free.
    """
    if not lines:
        return

    slug = ''
    if str(source or '').startswith('doc:'):
        slug = str(source)[4:]

    def _next_bundle_index():
        idx = getattr(_render_section_body, '_bundle_index', 0)
        setattr(_render_section_body, '_bundle_index', idx + 1)
        return idx

    def _render_plain(chunk):
        if not chunk:
            return

        runs = []
        for line in chunk:
            kind = _classify_line_for_render(line)

            if kind == 'blank':
                if runs and runs[-1][0] != 'blank':
                    runs.append(('blank', []))
                continue

            if not runs or runs[-1][0] != kind:
                runs.append((kind, []))

            runs[-1][1].append(line)

        for kind, run in runs:
            if kind == 'blank':
                spacer()
                continue

            if kind == 'code':
                stripped = []
                for line in run:
                    if line.startswith('    '):
                        stripped.append(line[4:])
                    elif line.startswith('\t'):
                        stripped.append(line[1:])
                    else:
                        stripped.append(line)
                doc_code(stripped)
                continue

            if kind == 'numbered':
                _render_numbered_items(run, source=source)
                continue

            if kind == 'bulleted':
                items = [_strip_list_marker(line) for line in run]
                doc_bullets(items)
                continue

            paragraph = ' '.join(line.strip() for line in run if line.strip())
            if paragraph:
                doc_inline(paragraph, source=source)

    plain = []
    rows = list(lines or [])
    i = 0

    while i < len(rows):
        line = rows[i]
        stripped = str(line or '').strip()

        if stripped.startswith('@forge-bundle'):
            _render_plain(plain)
            plain = []

            bundle_lines = []
            i += 1
            while i < len(rows):
                inner = rows[i]
                if str(inner or '').strip() == '@end-forge-bundle':
                    break

                if inner.startswith('    '):
                    bundle_lines.append(inner[4:])
                elif inner.startswith('\t'):
                    bundle_lines.append(inner[1:])
                else:
                    bundle_lines.append(inner)
                i += 1
            if slug:
                bundle_idx = _next_bundle_index()
                from forge.extensions.linkos.render.pills import pill_link
                print('       ', end='')
                pill_link('Copy bundle', 'copy_doc_bundle', slug, str(bundle_idx), tone='warning', icon='📋 ')
                print(':')
            doc_bundle(bundle_lines)

            if i < len(rows) and str(rows[i] or '').strip() == '@end-forge-bundle':
                i += 1
            continue

        plain.append(line)
        i += 1

    _render_plain(plain)

def _render_summary(section, source):
    """Render SUMMARY as muted prose under the hero."""
    paragraph = ' '.join(
        line.strip() for line in section.get('lines') or [] if line.strip()
    )
    if paragraph:
        doc_inline(paragraph, source=source)


def _render_when_to_use(section, source):
    """Render WHEN TO USE as a small framed callout under the summary.

    Uses a simple structural treatment for now: muted heading line +
    inline-link prose. Once we have a proper doc_callout primitive
    this gets richer.
    """
    say('   when to use', 'muted')
    paragraph = ' '.join(
        line.strip() for line in section.get('lines') or [] if line.strip()
    )
    if paragraph:
        doc_inline(paragraph, source=source)


def _render_related(related, source):
    """Render the RELATED block as a tile grid at the page bottom."""
    if not related:
        return

    # Build tiles as ``(icon, label, subtitle, args, tone)``. The
    # ``doc`` route resolves through the same registry, so missing
    # related slugs still route — to the missing page in that case.
    tiles = []
    for slug, note in related:
        from forge.extensions.linkos.data import docs as _d
        status, _ = _d.resolve(slug)
        tone = 'accent' if status == 'hit' else 'muted'
        subtitle = (note or '')[:17]
        tiles.append(('📖 ', slug, subtitle, ('doc', slug), tone))

    doc_tile_grid('related', tiles)


def doc_page(slug):
    """Render a doc by slug. Routes to missing page on slug miss."""
    slug = str(slug or '').strip()
    if not slug:
        from forge.extensions.linkos.pages.coming_soon import coming_soon_page
        coming_soon_page('docs')
        return

    status, payload = _docs.resolve(slug)
    if status != 'hit':
        from forge.extensions.linkos.pages.doc_missing import doc_missing_page
        doc_missing_page(slug, source='doc_route')
        return

    doc = payload
    title = doc.get('title') or slug
    sections = doc.get('sections') or []
    related = doc.get('related') or []

    source = 'doc:' + slug
    subtitle = 'guide'

    # Top frame: navigation first, then hero.
    doc_header_nav()
    doc_hero(title, subtitle)
    doc_actions([
        ('Copy doc', ('copy_doc', slug), 'warning', '📋 '),
        ('Docs hub', ('docs',), 'accent', '📖 '),
    ])

    # Summary + when-to-use get rendered first if present.
    summary_section = None
    when_section = None
    body_sections = []
    for idx, section in enumerate(sections):
        name_upper = str(section.get('name', '')).upper()
        if name_upper == 'SUMMARY':
            summary_section = (idx, section)
        elif name_upper == 'WHEN TO USE':
            when_section = (idx, section)
        else:
            body_sections.append((idx, section))

    if summary_section:
        _idx, section = summary_section
        _render_summary(section, source)

    if when_section:
        _idx, section = when_section
        spacer()
        _render_when_to_use(section, source)

    # Body sections.
    setattr(_render_section_body, '_bundle_index', 0)
    for idx, section in body_sections:
        name = section.get('name') or 'section'
        if name == 'intro':
            _render_section_body(section.get('lines') or [], source=source)
        else:
            doc_section(name)
            _render_section_body(section.get('lines') or [], source=source)

    # Related block at the bottom.
    if related:
        _render_related(related, source)

    # Closing frame: repeat the hero before the bottom rail so docs feel
    # deliberately bounded when the console lands at the bottom.
    doc_actions([
        ('Copy doc', ('copy_doc', slug), 'warning', '📋 '),
        ('Docs hub', ('docs',), 'accent', '📖 '),
    ])
    doc_hero(title, subtitle)
    doc_footer()

# -*- coding: utf-8 -*-
"""
Docs Surface for Forge.
"""

import re

from forge_core import docs as doc_data


CATEGORIES = [
    ('🚪 ', 'Start', 'first moves', ('doc', 'start_here'), 'success'),
    ('🔁 ', 'Loop', 'how Forge works', ('doc', 'the_loop'), 'accent'),
    ('🛟 ', 'Safety', 'patch safely', ('doc', 'safe_patch'), 'warning'),
    ('◎ ', 'Runs', 'history surface', ('doc', 'run_history'), 'accent'),
    ('🖼 ', 'Surface', 'user pages', ('doc', 'surface_model'), 'success'),
    ('🤖 ', 'LLM guide', 'agent rules', ('doc', 'llm_guidance'), 'warning'),
    ('✍️ ', 'Author docs', 'write guides', ('doc', 'docs_authoring'), 'accent'),
]


def _helpers():
    try:
        from forge_core.surface.render.docpage import doc_hero, doc_text
    except Exception:
        doc_hero = None
        doc_text = None

    try:
        from forge_core.surface.render.tile_dock import render_tile_dock
    except Exception:
        render_tile_dock = None

    return doc_hero, doc_text, render_tile_dock


def _hero(title, subtitle=''):
    doc_hero, _doc_text, _render_tile_dock = _helpers()
    if doc_hero:
        doc_hero(title, subtitle)
    else:
        print('')
        print('=== %s ===' % title)
        if subtitle:
            print(subtitle)
        print('')


def _text(text, tone='text'):
    _doc_hero, doc_text, _render_tile_dock = _helpers()
    if doc_text:
        doc_text(text, tone=tone)
    else:
        print('   ' + str(text or ''))


def _section(title):
    print('')
    print('  ' + '═' * 37)
    print(('  ' + str(title or '').upper()).center(41))
    print('  ' + '═' * 37)
    print('')


def _tiles(title, tiles, cols=2):
    _doc_hero, _doc_text, render_tile_dock = _helpers()
    if render_tile_dock:
        render_tile_dock(title, tiles, cols=cols, col_width=18, leading_space=1, trailing_space=2)
        return

    print('')
    print('-- %s --' % title)
    for _icon, label, subtitle, route, _tone in tiles:
        print('  %s — %s [%s]' % (label, subtitle, ' '.join(route)))


def render_docs(project_root, category=''):
    _hero('Docs', 'Forge guidance')

    _text('Guides, patterns, and copyable bundles for using Forge safely and quickly.', tone='muted')

    _tiles('Docs launcher', CATEGORIES)

    docs = doc_data.list_docs(project_root)
    if docs:
        recent = []
        for row in docs[:8]:
            slug = row.get('slug') or ''
            recent.append(('📖 ', slug, doc_data.relative_time(row.get('mtime')), ('doc', slug), 'accent'))
        _tiles('Available docs', recent)

    _tiles('Footer controls', [
        ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
        ('▶ ', 'Latest', 'run', ('run', 'latest'), 'success'),
    ])

    return True


def _strip_marker(line):
    s = str(line or '').strip()
    if s.startswith(('- ', '* ')):
        return s[2:].strip()
    m = re.match(r'^\d+\.\s+(.*)$', s)
    if m:
        return m.group(1).strip()
    return s


def _render_bundle(lines, slug, index):
    print('       ' + '─' * 28)
    for line in lines:
        print('       ' + str(line))
    print('       ' + '─' * 28)

    _tiles('Bundle action', [
        ('📋 ', 'Copy bundle', 'to clipboard', ('copy_doc_bundle', slug, str(index)), 'warning'),
    ], cols=1)


def _render_lines(lines, slug):
    bundle_index = 0
    i = 0
    paragraph = []

    def flush_para():
        if paragraph:
            _text(' '.join(paragraph))
            while paragraph:
                paragraph.pop()

    while i < len(lines):
        line = lines[i]
        stripped = str(line or '').strip()

        if stripped.startswith('@forge-bundle'):
            flush_para()
            bundle = []
            i += 1
            while i < len(lines):
                inner = lines[i]
                if str(inner or '').strip() == '@end-forge-bundle':
                    break
                if inner.startswith('    '):
                    bundle.append(inner[4:])
                elif inner.startswith('\t'):
                    bundle.append(inner[1:])
                else:
                    bundle.append(inner)
                i += 1
            _render_bundle(bundle, slug, bundle_index)
            bundle_index += 1
            if i < len(lines) and str(lines[i] or '').strip() == '@end-forge-bundle':
                i += 1
            continue

        if not stripped:
            flush_para()
            print('')
            i += 1
            continue

        if line.startswith('    ') or line.startswith('\t'):
            flush_para()
            print('       ' + line.strip())
            i += 1
            continue

        if stripped.startswith(('- ', '* ')) or re.match(r'^\d+\.\s+', stripped):
            flush_para()
            _text('• ' + _strip_marker(stripped))
            i += 1
            continue

        paragraph.append(stripped)
        i += 1

    flush_para()


def render_doc(project_root, slug):
    slug = str(slug or '').strip()
    if not slug:
        return render_docs(project_root)

    status, payload = doc_data.resolve(project_root, slug)
    if status != 'hit':
        _hero(slug or 'doc', 'not yet written')
        _text('This doc slug was requested but does not exist yet.', tone='muted')
        _tiles('Actions', [
            ('📖 ', 'Docs hub', 'guides', ('docs',), 'accent'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ])
        return True

    doc = payload
    title = doc.get('title') or slug
    sections = doc.get('sections') or []
    related = doc.get('related') or []

    _hero(title, 'guide')
    _tiles('Actions', [
        ('📋 ', 'Copy doc', 'raw text', ('copy_doc', slug), 'warning'),
        ('📖 ', 'Docs hub', 'guides', ('docs',), 'accent'),
    ])

    summary = None
    when = None
    body = []

    for section in sections:
        name = str(section.get('name') or '')
        upper = name.upper()
        if upper == 'SUMMARY':
            summary = section
        elif upper == 'WHEN TO USE':
            when = section
        else:
            body.append(section)

    if summary:
        _render_lines(summary.get('lines') or [], slug)

    if when:
        _section('When to use')
        _render_lines(when.get('lines') or [], slug)

    for section in body:
        name = section.get('name') or 'section'
        if name != 'intro':
            _section(name)
        _render_lines(section.get('lines') or [], slug)

    if related:
        tiles = []
        for rel_slug, note in related:
            tiles.append(('📖 ', rel_slug, note or 'related', ('doc', rel_slug), 'accent'))
        _tiles('Related', tiles)

    _tiles('Footer controls', [
        ('📋 ', 'Copy doc', 'raw text', ('copy_doc', slug), 'warning'),
        ('📖 ', 'Docs hub', 'guides', ('docs',), 'accent'),
        ('◎ ', 'Runs', 'history', ('runs',), 'accent'),
        ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
    ])

    return True


def _set_clipboard(text):
    try:
        import clipboard
        clipboard.set(text or '')
        try:
            import console
            console.hud_alert('Copied', 'success', 0.8)
        except Exception:
            pass
        return True
    except Exception:
        return False


def copy_doc(project_root, slug):
    status, payload = doc_data.resolve(project_root, slug)
    text = ''
    if status == 'hit':
        text = payload.get('raw') or ''
    ok = _set_clipboard(text) if text else False

    _hero('Copied doc' if ok else 'Copy failed', slug)
    if ok:
        _text('%d characters copied.' % len(text), tone='muted')
    else:
        _text('Could not copy this doc.', tone='muted')

    _tiles('Return', [
        ('📖 ', 'Back to doc', slug, ('doc', slug), 'accent'),
        ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
    ])
    return True


def copy_doc_bundle(project_root, slug, index):
    text = doc_data.bundle_text(project_root, slug, index)
    ok = _set_clipboard(text) if text else False

    if not ok:
        _hero('Copy failed', slug)
        _text('Could not copy bundle %s from %s.' % (index, slug), tone='muted')
        _tiles('Return', [
            ('📖 ', 'Back to doc', slug, ('doc', slug), 'accent'),
            ('🏠 ', 'Home', 'workbench', ('home',), 'success'),
        ])
        return True

    return render_doc(project_root, slug)
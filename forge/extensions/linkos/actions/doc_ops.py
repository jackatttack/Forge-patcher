# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.actions.doc_ops
=======================================

Clipboard actions for LinkOS docs.

These actions keep doc rendering pure: pages render buttons, router
dispatches actions, and this module performs clipboard side effects.
"""

try:
    import clipboard as _clipboard
except Exception:
    _clipboard = None

try:
    import console as _console
except Exception:
    _console = None

from forge.extensions.linkos.data import docs as _docs
from forge.extensions.linkos.render.docpage import (
    doc_actions, doc_footer, doc_hero, doc_text,
)


def _set_clipboard(text):
    """Write text to the clipboard. Returns True on success."""
    if _clipboard is None:
        return False
    try:
        _clipboard.set(text or '')
        if _console:
            try:
                _console.hud_alert('Copied doc', 'success', 0.8)
            except Exception:
                pass
        return True
    except Exception:
        return False


def _raw_doc_text(slug):
    """Return raw on-disk doc text for slug, or an empty string."""
    status, payload = _docs.resolve(slug)
    if status != 'hit':
        return ''
    path = payload.get('path') or ''
    if not path:
        return ''
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().rstrip() + '\n'
    except Exception:
        return ''


def _section_text(slug, section_index):
    """Return one doc section as copyable raw text.

    ``section_index`` is zero-based over the parsed doc sections.
    The copied text includes the doc title and section heading so it
    still makes sense when pasted into an LLM chat.
    """
    status, payload = _docs.resolve(slug)
    if status != 'hit':
        return ''

    sections = payload.get('sections') or []
    try:
        idx = int(section_index)
    except Exception:
        idx = -1

    if idx < 0 or idx >= len(sections):
        return ''

    section = sections[idx]
    title = payload.get('title') or slug
    name = section.get('name') or 'section'
    lines = section.get('lines') or []

    out = [
        '# %s' % title,
        '',
        '## %s' % name,
    ]
    out.extend(lines)
    return '\n'.join(out).rstrip() + '\n'

def _bundle_blocks(slug):
    """Return all @forge-bundle blocks from a raw doc.

    V1 uses Forge-native doc notation instead of markdown fences because
    triple backticks collide with chat markdown, mobile copy/paste, and
    Forge bundle bodies.

    Syntax:

        @forge-bundle optional-label
        LIST_FILES .
        DEPTH: 2
        @end-forge-bundle

    Only explicit @forge-bundle blocks are treated as runnable bundles.
    Other code/examples remain normal docs content.
    """
    raw = _raw_doc_text(slug)
    if not raw:
        return []

    blocks = []
    in_bundle = False
    current = []

    for line in raw.splitlines():
        stripped = line.strip()

        if not in_bundle and stripped.startswith('@forge-bundle'):
            in_bundle = True
            current = []
            continue

        if in_bundle and stripped == '@end-forge-bundle':
            blocks.append('\n'.join(current).rstrip() + '\n')
            in_bundle = False
            current = []
            continue

        if in_bundle:
            # Docs may indent bundle blocks for readability/parser safety.
            if line.startswith('    '):
                current.append(line[4:])
            elif line.startswith('\t'):
                current.append(line[1:])
            else:
                current.append(line)

    return blocks

def _bundle_text(slug, bundle_index):
    """Return one forge-bundle block by zero-based index."""
    blocks = _bundle_blocks(slug)
    try:
        idx = int(bundle_index)
    except Exception:
        idx = -1

    if idx < 0 or idx >= len(blocks):
        return ''

    return blocks[idx]

def copy_doc(slug):
    """Copy a whole doc to clipboard and render a confirmation page."""
    slug = str(slug or '').strip()
    text = _raw_doc_text(slug)
    ok = _set_clipboard(text) if text else False

    doc_hero('Copied doc' if ok else 'Copy failed', slug or 'doc')
    if ok:
        doc_text('The raw doc text is now on the clipboard.')
        doc_text('%d characters copied.' % len(text), tone='muted')
    else:
        doc_text('Could not copy this doc. It may be missing or unreadable.', tone='muted')

    doc_actions([
        ('Back to doc', ('doc', slug), 'accent', '📖 '),
        ('Home', ('home',), 'success', '🏠 '),
    ])
    doc_footer()

def copy_doc_section(slug, section_index):
    """Copy one doc section to clipboard and render a confirmation page."""
    slug = str(slug or '').strip()
    section_index = str(section_index or '').strip()
    text = _section_text(slug, section_index)
    ok = _set_clipboard(text) if text else False

    label = '%s section %s' % (slug or 'doc', section_index or '?')
    doc_hero('Copied section' if ok else 'Copy failed', label)

    if ok:
        doc_text('That section is now on the clipboard.')
        doc_text('%d characters copied.' % len(text), tone='muted')
    else:
        doc_text('Could not copy this section. It may be missing or unreadable.', tone='muted')

    doc_actions([
        ('Back to doc', ('doc', slug), 'accent', '📖 '),
        ('Home', ('home',), 'success', '🏠 '),
    ])
    doc_footer()

def copy_doc_bundle(slug, bundle_index):
    """Copy one embedded forge-bundle block to clipboard.

    This is an inline page action: it should feel like tapping a copy
    button beside code. After copying, re-render the same doc so the
    LinkOS screen is not left blank after the route fires.
    """
    slug = str(slug or '').strip()
    bundle_index = str(bundle_index or '').strip()
    text = _bundle_text(slug, bundle_index)

    ok = False
    if text and _clipboard is not None:
        try:
            _clipboard.set(text)
            ok = True
        except Exception:
            ok = False

    if _console:
        try:
            if ok:
                _console.hud_alert('Bundle copied', 'success', 0.8)
            else:
                _console.hud_alert('Copy failed', 'error', 1.0)
        except Exception:
            pass

    # Re-render the source doc after the side effect. This keeps the
    # copy action lightweight while avoiding a blank console after a
    # Pythonista URL route invocation.
    try:
        from forge.extensions.linkos.pages.doc import doc_page
        doc_page(slug)
    except Exception:
        pass

    # Intentionally render no page. The user should stay visually in the
    # doc they were reading.

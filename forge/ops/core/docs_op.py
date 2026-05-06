# -*- coding: utf-8 -*-
"""
docs_op.py
==========

Forge DOCS op.

Surface, suggest, and request documentation slugs from a bundle.

Three independent directives, all optional:

    DOCS
    OPEN: slug, slug              ← render these into the run packet now
    SUGGEST: slug, slug           ← surface as tappable links in Docs section
    REQUEST: slug, slug           ← log only, signals what should exist

OPEN renders each doc inline as part of this op's stdout. The user
sees the doc rendered in the run packet without any navigation. Misses
render the not-yet content so request counts grow naturally.

SUGGEST writes structured data the LinkOS run panel reads in
``_doc_links_for_run`` to populate the Docs section. Each slug is
resolved against the doc registry; hits route to the doc page,
misses route to the doc_missing page.

REQUEST is fire-and-forget — slugs are logged to the doc_log
immediately as misses, with source ``request:bundle``. They do not
surface on the run packet. They exist purely as backlog signal:
"this doc would be useful if it existed."

This op is the structured replacement for scanning bundle text for
inline ``[[]]`` markup. Bundle text scanning was too eager — it
caught literal ``[[slug]]`` examples in docstrings and comments.
DOCS is intent-explicit: every slug here is a deliberate reference.
"""

import io
import sys


SPEC = {
    'name': 'DOCS',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': {'OPEN', 'SUGGEST', 'REQUEST'},
    'required_directives': set(),
}

HELP = {
    'summary': 'Open, suggest, request, and surface living docs from inside a Forge bundle.',
    'subject': ['No subject. Use OPEN / SUGGEST / REQUEST directives.'],
    'common_failures': [
        'Empty DOCS op (no directives) — at least one of OPEN, SUGGEST, REQUEST is required for the op to do anything.',
        'Slug not found — opens the not-yet page instead. Not an error.',
        'Slug list contains invalid characters — non-slug entries are silently dropped.',
        'Using markdown triple-backtick fences for Forge bundles inside docs can collide with chat and bundle parsing.',
    ],
    'safe_usage': [
        'Use OPEN to render a doc inline in the run packet — best for "here is the answer" responses.',
        'Use SUGGEST to surface tappable links in the Docs section — best for "you might want to read these" hints.',
        'Use REQUEST when you want to flag a doc that should exist but does not — feeds the backlog.',
        'Docs can link to other docs with [[doc-slug]] inline markup.',
        'Docs can include copyable Forge bundles with @forge-bundle name / @end-forge-bundle blocks.',
        'Prefer @forge-bundle blocks over markdown fences for runnable examples.',
        'Keep embedded bundles small, safe, labelled, and followed by expected packet output.',
        'Use DOCS SUGGEST liberally at the end of useful bundles.',
        'Use DOCS OPEN sparingly when the user should read the doc immediately.',
        'All three directives are optional and can appear together.',
        'Slug lists are comma-separated. Whitespace is tolerated.',
    ],
    'minimal_example': [
        'DOCS',
        'OPEN: onboarding',
        '',
        'DOCS',
        'SUGGEST: the-loop, safe-patch',
        '',
        'DOCS',
        'OPEN: boot',
        'SUGGEST: the-loop, run-packet',
        'REQUEST: parse-errors',
        '',
        'Inside docs, use inline links:',
        'Read [[first-run]] before [[safe-patch]].',
        '',
        'Inside docs, use copyable bundle blocks:',
        '@forge-bundle read-only-start',
        'LIST_FILES .',
        'DEPTH: 2',
        'FILES: no',
        '@end-forge-bundle',
    ],
    'related_ops': ['HELP', 'GUIDE', 'LINKOS'],
}

HINTS = {
    'empty': 'DOCS op with no directives does nothing. Add OPEN, SUGGEST, or REQUEST.',
    'open': 'Use OPEN: slug, slug to render docs inline in the run packet.',
    'suggest': 'Use SUGGEST: slug, slug to surface docs as tappable links.',
}


def _parse_slug_list(raw):
    """Parse a comma-separated slug list directive into a clean list.

    Whitespace is stripped. Empty entries are dropped. Slug-shape
    validation is intentionally permissive — the doc resolver handles
    misses gracefully via the not-yet page.
    """
    if not raw:
        return []
    parts = [p.strip() for p in str(raw).split(',')]
    return [p for p in parts if p]


def validate(parsed_op):
    """Confirm at least one of OPEN, SUGGEST, REQUEST is present."""
    open_raw    = (parsed_op.directives.get('OPEN') or '').strip()
    suggest_raw = (parsed_op.directives.get('SUGGEST') or '').strip()
    request_raw = (parsed_op.directives.get('REQUEST') or '').strip()

    if not (open_raw or suggest_raw or request_raw):
        return ['DOCS requires at least one of OPEN, SUGGEST, REQUEST.']

    return []


def _render_open_to_string(slugs):
    """Render the given slugs through the DocPage renderer to a string.

    Captures stdout from ``pages.doc.doc_page`` so the rendered output
    matches exactly what ``LINKOS doc <slug>`` would show. Multiple
    slugs are rendered in sequence with a divider between them.

    Returns ``(text, hits, misses)``:
        text   — the captured render output as a single string
        hits   — list of slugs that resolved
        misses — list of slugs that did not
    """
    from forge.extensions.linkos.data import docs as _docs
    from forge.extensions.linkos.pages.doc import doc_page
    from forge.extensions.linkos.pages.doc_missing import doc_missing_page

    hits = []
    misses = []
    chunks = []

    for i, slug in enumerate(slugs):
        if i > 0:
            chunks.append('\n\n' + ('─' * 40) + '\n\n')

        # Resolve to know whether to render the doc or the not-yet page.
        status, _ = _docs.resolve(slug)

        # Capture stdout from the renderer. DocPage primitives use
        # print() so a stdout swap captures everything.
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            if status == 'hit':
                doc_page(slug)
                hits.append(slug)
            else:
                doc_missing_page(slug, source='docs_op_open')
                misses.append(slug)
        finally:
            sys.stdout = old

        chunks.append(buf.getvalue())

    return ''.join(chunks), hits, misses


def _build_suggested_data(slugs):
    """Resolve SUGGEST slugs and log each. Returns structured data
    the run packet's ``_doc_links_for_run`` will read.

    Each entry: ``{'slug': str, 'status': 'hit'|'miss'}``.
    """
    from forge.extensions.linkos.data import docs as _docs
    from forge.extensions.linkos.data import doc_log as _log

    rows = []
    for slug in slugs:
        status, _ = _docs.resolve(slug)
        try:
            _log.record(slug, status, source='suggest:bundle')
        except Exception:
            pass
        rows.append({'slug': slug, 'status': status})
    return rows


def _build_requested_data(slugs):
    """Log REQUEST slugs as misses. Returns structured data
    (purely for the run packet to display the count, not for routing).
    """
    from forge.extensions.linkos.data import doc_log as _log

    rows = []
    for slug in slugs:
        try:
            _log.record(slug, 'miss', source='request:bundle')
        except Exception:
            pass
        rows.append({'slug': slug})
    return rows


def execute(ctx, parsed_op, result):
    """Run DOCS: render OPEN docs, log SUGGEST/REQUEST, write structured
    data into the result dict for the run packet to surface.
    """
    open_slugs    = _parse_slug_list(parsed_op.directives.get('OPEN'))
    suggest_slugs = _parse_slug_list(parsed_op.directives.get('SUGGEST'))
    request_slugs = _parse_slug_list(parsed_op.directives.get('REQUEST'))

    stdout_text = ''
    open_hits = []
    open_misses = []
    if open_slugs:
        try:
            stdout_text, open_hits, open_misses = _render_open_to_string(open_slugs)
        except Exception as e:
            stdout_text = '(DOCS OPEN render failed: %s)' % e

    suggested = _build_suggested_data(suggest_slugs) if suggest_slugs else []
    requested = _build_requested_data(request_slugs) if request_slugs else []

    parts = []
    if open_slugs:
        parts.append('opened %d' % len(open_slugs))
    if suggest_slugs:
        parts.append('suggested %d' % len(suggest_slugs))
    if request_slugs:
        parts.append('requested %d' % len(request_slugs))
    summary = ', '.join(parts) if parts else 'no-op'

    result['status']    = 'APPLIED'
    result['message']   = summary
    result['out']       = {'stdout': stdout_text}
    result['suggested'] = suggested
    result['requested'] = requested

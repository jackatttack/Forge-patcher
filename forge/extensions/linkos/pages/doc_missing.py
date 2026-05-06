# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.pages.doc_missing
==========================================

Renderer for missing doc slugs.

When a ``[[slug]]`` link references a doc that doesn't exist on disk,
the link routes here. The page acts as a soft landing rather than an
error: it shows the slug, the request count from the doc log, and a
list of recent sources that asked for this slug.

This is the input signal for the doc backlog: the more often a slug
appears here, the more it deserves to be written. ``compat_audit``
will eventually surface a sorted list of these slugs as "docs to
write next".
"""

from forge.extensions.linkos.data import doc_log as _log
from forge.extensions.linkos.render.docpage import (
    doc_footer, doc_hero, doc_section, doc_text,
)
from forge.extensions.linkos.render.primitives import say, spacer


def doc_missing_page(slug, source=''):
    """Render the not-yet page for a missing doc slug."""
    slug = str(slug or '').strip() or 'unknown'

    # Record the visit itself (not just the inline link miss). Lets
    # the doc_log capture taps from existing pages too.
    try:
        _log.record(slug, 'miss', source=source or 'doc_missing_view')
    except Exception:
        pass

    count = _log.count_for(slug)
    sources = _log.sources_for(slug, limit=8)

    doc_hero(slug, 'not yet written')

    doc_text(
        'This doc has been requested but not yet written. The '
        'request count and recent sources help decide which docs '
        'to author next.',
        tone='muted',
    )

    doc_section('requests')
    if count > 0:
        say('   %d total request(s) logged' % count, 'accent')
    else:
        say('   no requests logged yet', 'muted')

    if sources:
        doc_section('referenced from')
        spacer()
        for src in sources:
            say('   ' + str(src), 'muted')
    spacer()

    doc_footer()

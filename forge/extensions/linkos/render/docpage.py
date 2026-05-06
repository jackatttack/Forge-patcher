# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.render.docpage
=======================================

Reusable rendered-document primitives for LinkOS pages.

DOC PAGE VISUAL SPEC
--------------------
LinkOS doc pages are text-native rendered pages for HELP, GUIDE, op
details, and future rich console surfaces.

Grammar:
    1. Hero
       - heavy border
       - centred spaced title
       - muted subtitle/type

    2. Intro/body
       - wrapped white text
       - readable indent
       - no unnecessary chrome

    3. Sections
       - purple structural bars
       - white section title
       - consistent calculated divider width

    4. Content blocks
       - body text: white
       - key labels: warning/accent where useful
       - secondary notes: muted
       - code/examples: white monospace with indent

    5. Actions
       - compact link rows
       - structural bars above/below
       - links carry colour, not body text

Principle:
    Purple is structure. White is content. Colour marks actions/status.
"""

from forge.extensions.linkos.render.footer import footer
from forge.extensions.linkos.render.pills import pill_rows
from forge.extensions.linkos.render.primitives import (
    band, colour, reset, say, spacer,
)


WIDTH = 41
SIDE_PAD = 2
INNER = WIDTH - (SIDE_PAD * 2)
BODY_INDENT = 3
SECTION_TEXT_PAD = 2


def spaced_title(text):
    """Return a spaced uppercase title for document heroes."""
    return ' '.join(str(text or '').upper())


def center(text, width=WIDTH):
    """Center text for console display."""
    text = str(text or '')
    if len(text) >= width:
        return text
    left = (width - len(text)) // 2
    return (' ' * left) + text


def side_prefix():
    """Return the standard structural left inset."""
    return ' ' * SIDE_PAD

def centered_rule(length=34, char='━'):
    """Return a centred structural rule string."""
    return center(char * int(length), WIDTH)

def wrap_words(text, width=INNER):
    """Simple dependency-free word wrap."""
    words = str(text or '').split()
    if not words:
        return ['']

    lines = []
    cur = ''
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += ' ' + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _section_rule_parts(title, width=INNER):
    """Return left/right rule lengths for a centred section title."""
    title = str(title or '').upper()
    title_block = (' ' * SECTION_TEXT_PAD) + title + (' ' * SECTION_TEXT_PAD)
    remaining = max(2, width - len(title_block))
    left = remaining // 2
    right = remaining - left
    return left, title_block, right


def doc_hero(title, subtitle=''):
    """Render a strong document-style hero."""
    spacer()
    band('═', WIDTH, 'border')
    spacer()

    colour('text')
    print(center(spaced_title(title)))
    reset()

    if subtitle:
        spacer()
        colour('muted')
        print(center(str(subtitle)))
        reset()

    spacer()
    band('═', WIDTH, 'border')
    spacer()


def doc_header_nav():
    """Render a compact top navigation rail for document pages.

    Mirrors the bottom rail without timestamp/label. Used at the top of
    long docs so the page feels framed rather than ending-only.
    """
    from forge.extensions.linkos.render.footer import bottom_action

    spacer()
    bottom_action('Back', ('back',), icon='⬅️', tone='orange')
    bottom_action('Home', ('home',), icon='🏠', tone='success')
    bottom_action('Files', ('files', '.'), icon='📁', tone='accent')
    bottom_action('Runs', ('runs',), icon='◎', tone='border')
    bottom_action('Docs', ('doc', 'boot'), icon='📖', tone='warning')
    print('')
    spacer()

def doc_text(text, tone='text', indent=BODY_INDENT):
    """Render wrapped body text.

    Width is calculated after indentation so Pythonista does not perform
    its own edge-wrap. This keeps continuation lines aligned with the
    first line of the paragraph.
    """
    prefix = ' ' * indent
    available = max(12, WIDTH - indent - 1)
    for line in wrap_words(text, available):
        say(prefix + line, tone)


def doc_size(num_bytes):
    """Return a human-friendly size string for a byte count.

    Examples:
        47       -> '47 B'
        1234     -> '1.2 KB'
        12716    -> '12.4 KB'
        2400000  -> '2.4 MB'
    """
    try:
        n = float(num_bytes or 0)
    except Exception:
        return '? B'
    if n < 1024:
        return '%d B' % int(n)
    if n < 1024 * 1024:
        return '%.1f KB' % (n / 1024.0)
    if n < 1024 * 1024 * 1024:
        return '%.1f MB' % (n / (1024.0 * 1024.0))
    return '%.1f GB' % (n / (1024.0 * 1024.0 * 1024.0))


def doc_breadcrumb(rel):
    """Render a tappable breadcrumb path bar.

    ``rel`` is a project-relative path like ``'forge/extensions/linkos'``.
    Each segment is rendered as a pill_link to the directory at that
    level, separated by muted ``/`` glyphs. Renders nothing for the
    project root.
    """
    from forge.extensions.linkos.render.pills import pill_link

    rel = str(rel or '').strip().strip('/')
    if not rel or rel == '.':
        return

    parts = rel.split('/')

    print(' ' * BODY_INDENT, end='')
    accumulated = ''
    for i, part in enumerate(parts):
        accumulated = part if not accumulated else (accumulated + '/' + part)

        if i > 0:
            colour('muted')
            print('  /  ', end='')
            reset()

        # Folder icon + segment name as a single tap target.
        pill_link(part, 'files', accumulated, tone='accent', icon='📁 ')
    print('')


# -- doc link primitives ---------------------------------------------------

# Inline ``[[slug]]`` markup. Slugs match word characters, hyphens, and
# colons (for namespaces like ``keyboard:layout``). Op slugs are
# detected by being all-uppercase plus underscores.
_DOC_LINK_RE = __import__('re').compile(r'\[\[([\w\-:]+)\]\]')


def _is_op_slug(slug):
    """Return True if ``slug`` looks like a Forge op name (all caps)."""
    s = str(slug or '')
    if not s:
        return False
    return s == s.upper() and any(c.isalpha() for c in s)


def doc_link(slug, source=''):
    """Render a single tappable link to a doc.

    Resolves ``slug`` against the doc registry and logs the attempt.
    Hits render as a normal pill_link to the doc page. Misses render
    as a muted pill linking to the ``doc_missing`` page so the user
    can still tap and see what was requested.

    ``source`` is recorded in the doc link log so we can later see
    which surfaces drove the most requests for a missing slug.

    Op-shaped slugs (``REPLACE``, ``LIST_TARGETS``) route to the
    Forge HELP page instead of the doc registry.
    """
    from forge.extensions.linkos.render.pills import pill_link
    from forge.extensions.linkos.data import doc_log
    from forge.extensions.linkos.data import docs as _docs

    slug = str(slug or '').strip()
    if not slug:
        return

    # Op references go to HELP, not the doc registry.
    if _is_op_slug(slug):
        try:
            doc_log.record(slug, 'hit', source=source or 'inline')
        except Exception:
            pass
        pill_link(slug, 'help', slug, tone='accent', icon='⚙ ')
        return

    status, _payload = _docs.resolve(slug)
    try:
        doc_log.record(slug, status, source=source or 'inline')
    except Exception:
        pass

    if status == 'hit':
        pill_link(slug, 'doc', slug, tone='accent', icon='📖 ')
    else:
        # Missing: still tappable, but muted so the user can see at a
        # glance that the doc isn't written yet.
        pill_link(slug, 'doc_missing', slug, tone='muted', icon='📖 ')


def doc_inline(text, source='', indent=BODY_INDENT, first_prefix=''):
    """Render prose text with inline ``[[slug]]`` markup expanded.

    Unlike the first version, this wraps safely inside the DocPage width.
    Link pills stay inline where possible, and wrapped continuation lines
    align with the body text rather than falling to the console edge.

    ``first_prefix`` is useful for numbered rows, e.g. ``'1.  '``.
    Continuation lines reserve the same prefix width so list bodies align.
    """
    s = str(text or '')
    if not s:
        return

    # Fast path: no links, no prefix, use the normal wrapped text renderer.
    if '[[' not in s and not first_prefix:
        doc_text(s, indent=indent)
        return

    # Tokenise into text words and doc-link slugs.
    tokens = []
    last_end = 0
    for m in _DOC_LINK_RE.finditer(s):
        before = s[last_end:m.start()]
        for word in before.split():
            tokens.append(('text', word))
        tokens.append(('slug', m.group(1)))
        last_end = m.end()

    after = s[last_end:]
    for word in after.split():
        tokens.append(('text', word))

    if not tokens:
        return

    base_indent = int(indent or 0)
    first_prefix = str(first_prefix or '')
    continuation_prefix = ' ' * len(first_prefix)

    def _token_width(kind, value):
        value = str(value or '')
        if kind == 'slug':
            # Approximate visible pill width: icon + space + slug.
            return len(value) + 2
        return len(value)

    def _line_start(prefix):
        print((' ' * base_indent) + prefix, end='')
        return base_indent + len(prefix)

    available = max(12, WIDTH - 1)
    line_len = _line_start(first_prefix)
    first_on_line = True

    for kind, value in tokens:
        value = str(value or '')
        if not value:
            continue

        sep = 0 if first_on_line else 1
        token_w = _token_width(kind, value)

        if not first_on_line and line_len + sep + token_w > available:
            print('')
            line_len = _line_start(continuation_prefix)
            first_on_line = True
            sep = 0

        if sep:
            colour('text')
            print(' ', end='')
            reset()
            line_len += 1

        if kind == 'slug':
            doc_link(value, source=source)
        else:
            colour('text')
            print(value, end='')
            reset()

        line_len += token_w
        first_on_line = False

    print('')

def doc_section(title, copy_args=None):
    """Render a boxed section title band.

    If ``copy_args`` is supplied, a small copy pill is rendered directly
    under the section title. This keeps section-level copy available
    without turning every paragraph into an action surface.
    """
    spacer()
    colour('surface_2')
    print(side_prefix() + '═' * INNER)
    reset()

    colour('text')
    print(center(str(title or '').upper(), WIDTH))
    reset()

    colour('surface_2')
    print(side_prefix() + '═' * INNER)
    reset()

    if copy_args:
        from forge.extensions.linkos.render.pills import pill_link
        print(' ' * BODY_INDENT, end='')
        pill_link('Copy', *copy_args, tone='warning', icon='📋 ')
        print('')

    spacer()

def doc_bullets(items, tone='text'):
    """Render simple wrapped text lines."""
    for item in items or []:
        doc_text(str(item), tone=tone, indent=BODY_INDENT)


def doc_kv(rows):
    """Render key/value rows for arguments and options.

    Long values wrap under the value column rather than spilling to the
    console edge.
    """
    key_width = 9
    key_indent = BODY_INDENT
    value_indent = key_indent + key_width
    value_width = max(12, WIDTH - value_indent - 1)

    for key, value in rows or []:
        colour('warning')
        print((' ' * key_indent) + ('%-9s' % str(key)), end='')
        reset()

        wrapped = wrap_words(str(value), value_width)
        if not wrapped:
            print('')
            continue

        colour('text')
        print(wrapped[0])
        reset()

        for line in wrapped[1:]:
            colour('text')
            print((' ' * value_indent) + line)
            reset()

def doc_code(lines):
    """Render a small monospace code/example block."""
    for line in lines or []:
        colour('text')
        print('       ' + str(line))
        reset()


def doc_bundle(lines, tone='warning'):
    """Render a copyable Forge bundle block as a distinct doc object.

    Used for @forge-bundle blocks. Keeps bundles visually separate from
    ordinary examples/code so users recognise them as runnable objects.
    """
    colour('surface_2')
    print('       ' + '─' * 28)
    reset()

    for line in lines or []:
        colour(tone)
        print('       ' + str(line))
        reset()

    colour('surface_2')
    print('       ' + '─' * 28)
    reset()

def doc_output(lines, tone='text', max_lines=120):
    """Render preformatted output/code without prose indentation or wrapping.

    Use for PREVIEW, stdout, stderr, run packets, tracebacks, and code-like
    output. Unlike doc_text/doc_code, this preserves line starts so numbered
    code previews stay readable in the console.
    """
    rows = list(lines or [])
    if max_lines is not None:
        rows = rows[:int(max_lines)]
    for line in rows:
        say(str(line), tone)

def doc_actions(items):
    """Render final page actions using the boxed-section visual language.

    ``items`` is a list of ``(label, args, tone, icon)`` tuples. Pills
    are laid out two per row using the standard body indent.
    """
    spacer()
    colour('surface_2')
    print(side_prefix() + '═' * INNER)
    reset()

    colour('text')
    print(center('ACTIONS', WIDTH))
    reset()

    colour('surface_2')
    print(side_prefix() + '═' * INNER)
    reset()
    spacer()

    items = list(items or [])
    for i in range(0, len(items), 2):
        print(' ' * BODY_INDENT, end='')
        row = items[i:i + 2]
        for j, item in enumerate(row):
            label, args, tone, icon = item
            from forge.extensions.linkos.render.pills import pill_link
            pill_link(label, *args, tone=tone, icon=icon)
            if j == 0 and len(row) > 1:
                print('   ', end='')
        print('')

    spacer()
    colour('surface_2')
    print(side_prefix() + '═' * INNER)
    reset()


def doc_tile_grid(title, tiles):
    """Render a tile grid as a boxed section with subtitles per tile.

    ``title`` is the section header (e.g. ``'workbench'``). ``tiles`` is
    a list of ``(icon, label, subtitle, args, tone)`` tuples. Pills are
    laid out two per row with a fixed column width so the subtitle row
    below aligns under each pill consistently regardless of label
    length.

    Use ``doc_actions`` for verbs (Copy, Open, Continue); use this for
    destinations (Files, Runs, Docs).
    """
    spacer()
    colour('surface_2')
    print(side_prefix() + '═' * INNER)
    reset()

    colour('text')
    print(center(str(title or '').upper(), WIDTH))
    reset()

    colour('surface_2')
    print(side_prefix() + '═' * INNER)
    reset()
    spacer()

    # Fixed column width keeps subtitles aligned under their pills.
    col_width = 18
    gap = '   '

    items = list(tiles or [])
    for i in range(0, len(items), 2):
        row = items[i:i + 2]

        # Pill row: each pill in a fixed-width column, padded with
        # spaces after the link so the next column starts at the
        # same horizontal position regardless of label length.
        print(' ' * BODY_INDENT, end='')
        for j, item in enumerate(row):
            icon, label, _subtitle, args, tone = item
            from forge.extensions.linkos.render.pills import pill_link
            pill_link(label, *args, tone=tone, icon=icon)

            # Pad to column width. The pill itself is a write_link with
            # variable visible width; we approximate by counting icon +
            # label characters and padding to col_width.
            visible = len(str(icon)) + len(str(label))
            pad = max(1, col_width - visible)
            print(' ' * pad, end='')

            if j == 0 and len(row) > 1:
                print(gap, end='')
        print('')

        # Subtitle row: muted, in matching fixed-width columns.
        print(' ' * BODY_INDENT, end='')
        for j, item in enumerate(row):
            _icon, _label, subtitle, _args, _tone = item
            colour('muted')
            cell = ('%-' + str(col_width) + 's') % (str(subtitle or '')[:col_width])
            print(cell, end='')
            reset()
            if j == 0 and len(row) > 1:
                print(gap, end='')
        print('')
        spacer()

def doc_run_card(run, route=None):
    """Render a compact summary of a Forge run.

    Layout (4 lines):
        ✅  20260505_151744
            Clean run
            6 applied · 0 skipped · 0 failed
            🧠 Summary enough

    Phrase and counts split onto separate lines so neither has to
    wrap at console width on iPhone. The whole stamp is tappable as
    a single pill_link if ``route`` is provided. ``run`` is the
    structured run dict from
    :func:`forge.extensions.linkos.data.runs.load_run`.
    """
    from forge.extensions.linkos.render.pills import pill_link
    from forge.extensions.linkos.data import runs as _runs

    if not run or run.get('missing'):
        say(' ' * BODY_INDENT + 'No run available yet.', 'muted')
        return

    counts = run.get('counts') or {}
    applied = counts.get('applied', 0)
    skipped = counts.get('skipped', 0)
    failed = counts.get('failed', 0)
    stamp = run.get('stamp') or '(unknown)'

    if failed:
        status_emoji = '❌'
    elif skipped:
        status_emoji = '⚠️'
    elif applied:
        status_emoji = '✅'
    else:
        status_emoji = '•'

    phrase = _runs.status_phrase(run)
    rec_emoji, rec_label = _runs.recommendation(run)

    counts_text = '%d applied · %d skipped · %d failed' % (applied, skipped, failed)

    # Stamp row — tappable into full run view if route provided.
    print(' ' * BODY_INDENT + status_emoji + '  ', end='')
    if route:
        pill_link(stamp, *route, tone='accent')
    else:
        colour('text')
        print(stamp, end='')
        reset()
    print('')

    # Phrase on its own line.
    say(' ' * (BODY_INDENT + 4) + phrase, 'muted')

    # Counts on their own line so neither line has to wrap.
    say(' ' * (BODY_INDENT + 4) + counts_text, 'muted')

    # Recommendation row.
    rec_tone = {
        '🧠': 'success',
        '📋': 'warning',
        '❌': 'danger',
        '⚠️': 'warning',
    }.get(rec_emoji, 'muted')
    say(' ' * (BODY_INDENT + 4) + rec_emoji + '  ' + rec_label, rec_tone)

def doc_footer():
    """Render standard LinkOS footer."""
    footer()

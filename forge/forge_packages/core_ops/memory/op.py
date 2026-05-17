# -*- coding: utf-8 -*-
"""
MEMORY reboot op.

Public, portable memory/journal layer.

This first implementation uses the historical library/journal backend when
available, so old entries remain usable without migration.
"""

import os
import shlex
import sys
from datetime import datetime, timedelta


SPEC = {
    'name': 'MEMORY',
    'target_kind': 'none',
    'body_mode': 'optional',
    'allowed_directives': set(['ARGS', 'TAGS', 'LIMIT', 'CONFIRM']),
    'required_directives': set(),
}


HELP = {
    'summary': 'Read, search, and write durable memory entries using the journal-compatible backend.',
    'minimal_example': [
        'MEMORY start',
        '',
        'MEMORY code last 7',
        '',
        'MEMORY personal all',
        '',
        'MEMORY search forge docs',
        '',
        'MEMORY show 20260424_084459_agxm',
        '',
        'MEMORY delete 20260424_084459_agxm',
        'CONFIRM: yes',
        '',
        'MEMORY add code --tags forge progress',
        'BEGIN_BODY',
        'What changed and what should happen next.',
        'END_BODY',
    ],
}


HINTS = {
    '_max_hints': 1,
    'usage': {
        'message': 'MEMORY supports start, search, show, add, and kind views.',
        'why': 'Memory is the portable context layer for project and personal continuity.',
        'example': [
            'MEMORY start',
            '',
            'MEMORY code last 7',
            '',
            'MEMORY search forge docs',
        ],
        'next': [
            'Use MEMORY start at boot.',
            'Use MEMORY search <query> for targeted recall.',
            'Use MEMORY add <kind> --tags ... with BEGIN_BODY for durable notes.',
        ],
    },
}


def _documents_root():
    here = os.path.abspath(os.path.dirname(__file__))
    cur = here
    for _ in range(12):
        if os.path.isdir(os.path.join(cur, 'library', 'journal')):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(os.getcwd())


def _ensure_journal_path():
    root = _documents_root()
    library = os.path.join(root, 'library')
    if library not in sys.path:
        sys.path.insert(0, library)
    return root


def _split_args(parsed_op):
    directives = parsed_op.get('directives') or {}
    raw = directives.get('ARGS') or parsed_op.get('target') or ''
    try:
        return shlex.split(str(raw or ''))
    except Exception:
        return str(raw or '').split()


def _confirmed(value):
    return str(value or '').strip().lower() in ('1', 'yes', 'y', 'true', 'on')


def _as_int(value, default):
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _entry_key(entry):
    return entry.get('ts') or entry.get('date') or ''


def _preview_text(entry, max_chars=220):
    text = entry.get('body') or entry.get('preview') or entry.get('snippet') or ''
    return ' '.join(str(text).split())[:max_chars]


def _fmt_entry(entry, full=False):
    tags = entry.get('tags') or []
    tag_text = ' [' + ', '.join(tags) + ']' if tags else ''
    head = '%s  %s  %s%s' % (
        entry.get('id', ''),
        (entry.get('ts') or entry.get('date') or '')[:19],
        entry.get('kind', ''),
        tag_text,
    )
    if full:
        return head + '\n' + str(entry.get('body') or entry.get('preview') or '').rstrip()
    preview = _preview_text(entry)
    if preview:
        return head + '\n  ' + preview
    return head


def _fmt_entries(title, entries, limit=10, full=False):
    lines = [title]
    entries = sorted(entries or [], key=_entry_key, reverse=True)
    shown = entries[:limit]
    lines.append('count: %d%s' % (len(entries), '' if len(entries) <= limit else ' showing %d' % limit))
    lines.append('')
    if not shown:
        lines.append('(no entries)')
        return '\n'.join(lines).rstrip()
    for entry in shown:
        lines.append(_fmt_entry(entry, full=full))
        lines.append('')
    return '\n'.join(lines).rstrip()


def _recent_entries(days=7, kind=None):
    from journal.query import recent
    return recent(days=days, kind=kind)


def _all_entries(kind=None):
    from journal.query import all_entries
    entries = all_entries()
    if kind:
        entries = [e for e in entries if e.get('kind') == kind]
    return entries


def _cmd_start(result):
    lines = []
    lines.append('MEMORY START')
    lines.append('Purpose: compact context. Retrieve more once the task is clear.')
    lines.append('')

    today = _recent_entries(days=1)
    lines.append(_fmt_entries('TODAY', today, limit=6))
    lines.append('')

    reflections = [
        e for e in _recent_entries(days=7, kind='personal')
        if 'llm-reflect' in (e.get('tags') or [])
    ]
    lines.append(_fmt_entries('LATEST LLM REFLECTIONS', reflections, limit=3))
    lines.append('')

    summaries = [
        e for e in _recent_entries(days=7, kind='code')
        if set(e.get('tags') or []) & set(['summary', 'progress', 'next-session', 'milestone', 'continuity'])
    ]
    lines.append(_fmt_entries('LATEST PROJECT SUMMARIES', summaries, limit=4))
    lines.append('')
    lines.append('NEXT')
    lines.append('- MEMORY search <query>')
    lines.append('- MEMORY code last 7')
    lines.append('- MEMORY show <id>')

    result['status'] = 'APPLIED'
    result['message'] = 'memory start'
    result['preview'] = '\n'.join(lines).rstrip()
    result['data'] = {'mode': 'start'}


def _cmd_show(result, parts):
    if len(parts) < 2:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'MEMORY show requires an entry id'
        return
    from journal.query import full_entry
    entry = full_entry(parts[1])
    if entry is None:
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'Memory entry not found: ' + parts[1]
        return
    result['status'] = 'APPLIED'
    result['message'] = 'Memory entry: ' + parts[1]
    result['preview'] = _fmt_entry(entry, full=True)
    result['data'] = {'mode': 'show', 'entry': entry}


def _cmd_search(result, parts):
    query = ' '.join(parts[1:]).strip()
    if not query:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'MEMORY search requires a query'
        return
    from journal.memory_search import search
    hits = search(query, top=10)
    lines = ['MEMORY SEARCH %r' % query, 'results: %d' % len(hits), '']
    if not hits:
        lines.append('(no results)')
    for hit in hits:
        score = hit.get('score')
        suffix = '  score=%.3f' % score if isinstance(score, float) else ''
        lines.append('%s  %s  %s%s' % (hit.get('id', ''), (hit.get('ts') or '')[:10], hit.get('kind', ''), suffix))
        tags = hit.get('tags') or []
        if tags:
            lines.append('  tags: ' + ', '.join(tags))
        snippet = hit.get('snippet') or ''
        if snippet:
            lines.append('  ' + ' '.join(snippet.split())[:180])
        lines.append('')
    result['status'] = 'APPLIED'
    result['message'] = '%d memory result(s)' % len(hits)
    result['preview'] = '\n'.join(lines).rstrip()
    result['data'] = {'mode': 'search', 'query': query, 'hits': hits}



def _cmd_delete(result, parts, directives):
    if len(parts) < 2:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'MEMORY delete requires an entry id'
        return
    if not _confirmed(directives.get('CONFIRM')):
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'MEMORY delete requires CONFIRM: yes'
        return
    from journal.store import delete_entry
    entry_id = parts[1]
    ok = delete_entry(entry_id)
    if not ok:
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'Memory entry not found: ' + entry_id
        return
    result['status'] = 'APPLIED'
    result['message'] = 'Deleted memory: ' + entry_id
    result['preview'] = 'MEMORY DELETED\n' + entry_id
    result['data'] = {'mode': 'delete', 'entry_id': entry_id}


def _cmd_add(result, parts, body, directives):
    if len(parts) < 2:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'MEMORY add requires a kind'
        return
    kind = parts[1]
    rest = parts[2:]
    tags = []
    if '--tags' in rest:
        idx = rest.index('--tags')
        tags = rest[idx + 1:]
        rest = rest[:idx]
    if directives.get('TAGS'):
        tags.extend([x.strip() for x in str(directives.get('TAGS')).split(',') if x.strip()])
    text = str(body or '').strip()
    if not text:
        text = ' '.join(rest).strip()
    if not text:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'MEMORY add requires body text or BEGIN_BODY'
        return
    from journal.store import add_entry
    entry = add_entry(text, kind=kind, tags=tags)
    result['status'] = 'APPLIED'
    result['message'] = 'Added memory: ' + entry.get('id', '')
    result['preview'] = 'MEMORY ADDED\n' + _fmt_entry(entry, full=True)
    result['data'] = {'mode': 'add', 'entry': entry}


def _cmd_kind_view(result, parts, directives):
    kind = parts[0]
    limit = _as_int(directives.get('LIMIT'), 10)
    mode = parts[1] if len(parts) > 1 else 'last'
    n = _as_int(parts[2], limit) if len(parts) > 2 else limit

    if mode == 'all':
        entries = _all_entries(kind=kind)
        limit = _as_int(directives.get('LIMIT'), 80)
        title = 'MEMORY %s all' % kind
    elif mode == 'last':
        entries = _all_entries(kind=kind)
        limit = n
        title = 'MEMORY %s last %d' % (kind, limit)
    else:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'Unknown MEMORY kind view: ' + ' '.join(parts)
        return

    result['status'] = 'APPLIED'
    result['message'] = '%d %s entr%s' % (len(entries), kind, 'y' if len(entries) == 1 else 'ies')
    result['preview'] = _fmt_entries(title, entries, limit=limit)
    result['data'] = {'mode': 'kind', 'kind': kind, 'entries': entries[:limit], 'count': len(entries)}


def validate(parsed_op):
    parts = _split_args(parsed_op)
    body = parsed_op.get('body') or ''
    if body.strip() and (not parts or parts[0] != 'add'):
        return ['MEMORY body is only supported with MEMORY add <kind>']
    return []


def execute(ctx, parsed_op, result):
    try:
        _ensure_journal_path()
        parts = _split_args(parsed_op)
        directives = parsed_op.get('directives') or {}
        body = parsed_op.get('body') or ''

        if not parts:
            parts = ['start']

        cmd = parts[0]
        if cmd in ('start', 'boot'):
            _cmd_start(result)
            return
        if cmd == 'today':
            entries = _recent_entries(days=1)
            result['status'] = 'APPLIED'
            result['message'] = '%d memory entr%s today' % (len(entries), 'y' if len(entries) == 1 else 'ies')
            result['preview'] = _fmt_entries('MEMORY today', entries, limit=_as_int(directives.get('LIMIT'), 12))
            result['data'] = {'mode': 'today', 'entries': entries}
            return
        if cmd == 'search':
            _cmd_search(result, parts)
            return
        if cmd == 'show':
            _cmd_show(result, parts)
            return
        if cmd == 'delete':
            _cmd_delete(result, parts, directives)
            return
        if cmd == 'add':
            _cmd_add(result, parts, body, directives)
            return
        _cmd_kind_view(result, parts, directives)
    except Exception as e:
        result['status'] = 'FAILED_RUNTIME'
        result['message'] = 'MEMORY failed: %s: %s' % (type(e).__name__, e)

# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.data.doc_log
=====================================

Append-only log of doc link resolution attempts.

Every time a ``[[slug]]`` link is rendered — whether it resolves to a
real doc or a missing one — a small record is appended to the log.
This serves two purposes:

1. **Missing-doc visibility.** The "Coming soon: <slug>" page can show
   how many times that slug has been requested, and from where. That
   tells the user (and the author) which docs are most-needed.

2. **Audit input.** ``compat_audit`` (or any other tool) can read this
   log to surface a doc backlog — slugs that were requested but never
   written. The most-requested misses become the highest-priority
   docs to author next.

The log is JSON-lines (one entry per line) for cheap append. Read with
:func:`load_entries`. Failures are silent — logging must never break
rendering.
"""

import json
import os
import time

try:
    from forge.runtime.paths import project_root
    _PROJECT_ROOT = project_root()
except Exception:
    _PROJECT_ROOT = os.path.expanduser('~/Documents')


LOG_PATH = os.path.join(
    _PROJECT_ROOT, 'forge', 'artifacts', 'doc_link_log.json',
)

# Keep the log bounded. When it grows past this many entries, the
# oldest entries are pruned on the next write. Generous enough that
# we'll keep months of history; small enough to read fast.
_MAX_ENTRIES = 5000


def _ensure_dir():
    """Create the log's containing folder if it doesn't exist."""
    try:
        folder = os.path.dirname(LOG_PATH)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
    except Exception:
        pass


def record(slug, status, source=''):
    """Append one resolution attempt to the log.

    ``slug`` is the raw slug requested. ``status`` is ``'hit'`` or
    ``'miss'``. ``source`` is an optional short hint about where the
    request came from (``'run_panel'``, ``'home'``, ``'guide:boot'``).

    All failures are silent — this function never raises.
    """
    try:
        _ensure_dir()
        entry = {
            't': int(time.time()),
            'slug': str(slug or ''),
            'status': str(status or ''),
            'source': str(source or ''),
        }
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, sort_keys=True) + '\n')
    except Exception:
        pass


def load_entries(limit=None):
    """Return all log entries, oldest first. Empty list on any failure.

    ``limit`` caps the number returned (most recent first when limited).
    """
    try:
        if not os.path.exists(LOG_PATH):
            return []
        rows = []
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        if limit is not None:
            return rows[-int(limit):]
        return rows
    except Exception:
        return []


def count_for(slug):
    """Return the total number of times ``slug`` has been requested."""
    target = str(slug or '')
    if not target:
        return 0
    try:
        n = 0
        for entry in load_entries():
            if entry.get('slug') == target:
                n += 1
        return n
    except Exception:
        return 0


def sources_for(slug, limit=10):
    """Return up to ``limit`` distinct sources that requested ``slug``.

    Most recent unique sources first.
    """
    target = str(slug or '')
    if not target:
        return []
    try:
        seen = []
        for entry in reversed(load_entries()):
            if entry.get('slug') != target:
                continue
            src = entry.get('source') or ''
            if src and src not in seen:
                seen.append(src)
            if len(seen) >= limit:
                break
        return seen
    except Exception:
        return []


def missing_summary(top_n=20):
    """Return the most-requested missing slugs.

    Each entry: ``{'slug', 'count', 'last_t'}``. Sorted by count desc.
    Used by the doc backlog audit and the missing-doc page.
    """
    try:
        agg = {}
        for entry in load_entries():
            if entry.get('status') != 'miss':
                continue
            slug = entry.get('slug') or ''
            if not slug:
                continue
            row = agg.setdefault(slug, {'slug': slug, 'count': 0, 'last_t': 0})
            row['count'] += 1
            t = int(entry.get('t') or 0)
            if t > row['last_t']:
                row['last_t'] = t

        rows = sorted(agg.values(), key=lambda r: r['count'], reverse=True)
        return rows[:int(top_n)]
    except Exception:
        return []


def prune_if_large():
    """Trim the log if it has grown past ``_MAX_ENTRIES``.

    Keeps the most recent entries. Failures are silent.
    """
    try:
        rows = load_entries()
        if len(rows) <= _MAX_ENTRIES:
            return
        keep = rows[-_MAX_ENTRIES:]
        _ensure_dir()
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            for entry in keep:
                f.write(json.dumps(entry, sort_keys=True) + '\n')
    except Exception:
        pass

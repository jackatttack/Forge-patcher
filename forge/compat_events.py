# -*- coding: utf-8 -*-
"""
compat_events.py
================

Persistent Forge behavioural event log.

Stores small, long-term summaries of run outcomes so Forge can learn from
actual model usage without keeping full run packets forever.
"""

import json
import os
import re
from datetime import datetime


EVENTS_FILE = 'forge/artifacts/compat_events.jsonl'

MAX_MESSAGE = 700


def _events_path(project_root):
    return os.path.join(project_root, EVENTS_FILE)


def _short(text, limit=MAX_MESSAGE):
    text = (text or '').strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + '…'


def _extract_invalid_directives(text):
    out = []
    for m in re.finditer(r'Directive not allowed for ([A-Z_][A-Z0-9_]*): ([A-Z_][A-Z0-9_]*)', text or ''):
        out.append({'op': m.group(1), 'directive': m.group(2)})
    return out


def _extract_missing_directives(text):
    out = []
    for m in re.finditer(r'Missing required directive for ([A-Z_][A-Z0-9_]*): ([A-Z_][A-Z0-9_]*)', text or ''):
        out.append({'op': m.group(1), 'directive': m.group(2)})
    return out


def _extract_learn_lines(text):
    notes = []
    lines = (text or '').splitlines()
    for i, line in enumerate(lines):
        if line.strip() == 'LEARN:':
            j = i + 1
            while j < len(lines) and lines[j].startswith('- '):
                notes.append(lines[j][2:].strip())
                j += 1
    return notes


def _result_event(result):
    status = result.get('status') or 'UNKNOWN'
    op = result.get('op') or '?'
    target = result.get('target') or '?'
    msg = result.get('message') or ''

    return {
        'status': status,
        'op': op,
        'target': target,
        'message': _short(msg),
        'invalid_directives': _extract_invalid_directives(msg),
        'missing_directives': _extract_missing_directives(msg),
        'learn': _extract_learn_lines(msg),
    }


def build_run_event(stamp=None, results=None, normalise_notes=None, source='run'):
    """Build a compact event summary for one Forge run."""
    results = results or []
    normalise_notes = normalise_notes or []

    failures = []
    skipped = []
    core_guard_hits = 0
    invalid_directives = []
    missing_directives = []
    learn = []

    for r in results:
        status = r.get('status') or ''
        if status.startswith('FAILED'):
            event = _result_event(r)
            failures.append(event)
            invalid_directives.extend(event.get('invalid_directives', []))
            missing_directives.extend(event.get('missing_directives', []))
            learn.extend(event.get('learn', []))
            if status == 'FAILED_CORE_GUARD':
                core_guard_hits += 1
        elif status.startswith('SKIPPED'):
            skipped.append(_result_event(r))

    return {
        'ts': datetime.now().isoformat(timespec='seconds'),
        'run': stamp or '',
        'source': source,
        'normalised': list(normalise_notes),
        'failed_count': len(failures),
        'skipped_count': len(skipped),
        'core_guard_hits': core_guard_hits,
        'failures': failures,
        'skipped': skipped,
        'invalid_directives': invalid_directives,
        'missing_directives': missing_directives,
        'learn': learn,
    }


def append_event(project_root, event):
    """Append one JSONL event. Best-effort; raises to caller if filesystem fails."""
    path = _events_path(project_root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + '\n')


def record_run(project_root, stamp=None, results=None, normalise_notes=None, source='run'):
    """Record one run summary. Best-effort wrapper used by bridge."""
    event = build_run_event(
        stamp=stamp,
        results=results or [],
        normalise_notes=normalise_notes or [],
        source=source,
    )

    # Do not spam empty successful runs with no behavioural signal.
    if (
        not event['normalised']
        and not event['failed_count']
        and not event['skipped_count']
        and not event['core_guard_hits']
    ):
        return None

    append_event(project_root, event)
    return event


def load_events(project_root, limit=None):
    """Load recent persisted compat events."""
    path = _events_path(project_root)
    if not os.path.isfile(path):
        return []

    events = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue

    if limit:
        return events[-int(limit):]
    return events

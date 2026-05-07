# -*- coding: utf-8 -*-
"""
forge.extensions.linkos.data.runs
=================================

Self-contained run reader for public/minimal LinkOS.

Reads minimal Forge artifacts directly from:

    artifacts/runs/<stamp>/

No dependency on forge_ui.
"""

import datetime
import json
import os


try:
    from forge.runtime.paths import project_root
    _CANDIDATE_ROOT = os.path.abspath(project_root())
except Exception:
    _CANDIDATE_ROOT = ''

_FALLBACK_ROOT = os.environ.get('FORGE_INSTALL_ROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if _CANDIDATE_ROOT and os.path.isdir(os.path.join(_CANDIDATE_ROOT, 'artifacts', 'runs')):
    _PROJECT_ROOT = _CANDIDATE_ROOT
else:
    _PROJECT_ROOT = os.path.abspath(_FALLBACK_ROOT)

RUNS_DIR = os.path.join(_PROJECT_ROOT, 'artifacts', 'runs')
PATCH_OPS = set([
    'CREATE_FILE', 'REPLACE_FILE', 'REPLACE_FILE_LINES', 'REPLACE_FILE_RANGE',
    'INSERT_FILE_LINE', 'COPY_FILE', 'MOVE_FILE', 'MOVE_DIR', 'DELETE_FILE',
    'DELETE_DIR', 'REPLACE', 'REPLACE_LINES', 'REPLACE_LINE',
    'INSERT_AFTER', 'INSERT_BEFORE', 'INSERT_INTO', 'APPEND_INTO',
    'PREPEND_INTO', 'REPLACE_BLOCK',
])

INSPECT_OPS = set([
    'PREVIEW', 'READ_FILE', 'LIST_FILES', 'LIST_TARGETS', 'GREP',
    'HELP', 'GUIDE', 'DOCS',
])

RUN_OPS = set([
    'RUN_FILE', 'SHORTCUT', 'URL', 'PIP',
])

SYNC_OPS = set([
    'PACK', 'CLIPBOARD',
])


def _read_text(path, max_bytes=900000):
    if not path or not os.path.exists(path):
        return ''
    try:
        if os.path.getsize(path) > max_bytes:
            with open(path, 'rb') as f:
                raw = f.read(max_bytes)
            return raw.decode('utf-8', 'replace') + '\n\n... truncated ...'
    except Exception:
        pass

    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception:
        return ''


def _load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def list_stamps(limit=80):
    """Return recent run stamps, newest first."""
    if not os.path.isdir(RUNS_DIR):
        return []

    rows = []
    try:
        for name in os.listdir(RUNS_DIR):
            path = os.path.join(RUNS_DIR, name)
            if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'manifest.json')):
                rows.append(name)
    except Exception:
        return []

    rows.sort(reverse=True)
    return rows[:int(limit or 80)]


def latest_stamp():
    """Return most recent run stamp, or empty string."""
    rows = list_stamps(1)
    return rows[0] if rows else ''


def _run_dir(stamp):
    return os.path.join(RUNS_DIR, str(stamp or ''))


def load_manifest(stamp=None):
    """Load a run manifest, defaulting to latest."""
    stamp = stamp or latest_stamp()
    if not stamp:
        return {
            'stamp': '',
            'root': _PROJECT_ROOT,
            'results': [],
            'touched': [],
            'missing': True,
        }

    path = os.path.join(_run_dir(stamp), 'manifest.json')
    data = _load_json(path)
    if not data:
        return {
            'stamp': stamp,
            'root': _PROJECT_ROOT,
            'results': [],
            'touched': [],
            'missing': True,
        }

    data.setdefault('stamp', stamp)
    data.setdefault('root', _PROJECT_ROOT)
    data.setdefault('results', [])
    data.setdefault('touched', [])
    return data


def bundle_text(stamp=None):
    """Return original bundle text for a run."""
    stamp = latest_stamp() if not stamp or stamp == 'latest' else stamp
    if not stamp:
        return ''
    return _read_text(os.path.join(_run_dir(stamp), 'bundle.txt'))


def _status_emoji(status):
    status = str(status or '').upper()
    if status == 'APPLIED':
        return '✅'
    if status.startswith('SKIPPED'):
        return '⚠️'
    if status.startswith('FAILED'):
        return '❌'
    return '•'


def _op_emoji(op):
    op = str(op or '').upper()
    if op == 'PARSE':
        return '🧩'
    if op in PATCH_OPS:
        return '🛠️'
    if op in INSPECT_OPS:
        return '🔎'
    if op in RUN_OPS:
        return '🧪'
    if op in SYNC_OPS:
        return '📦'
    if op in ('REVERT_RUN', 'BRANCH'):
        return '↩️'
    return '📄'


def _kind_for_op(op):
    op = str(op or '').upper()
    if op == 'PARSE':
        return 'parse'
    if op in PATCH_OPS:
        return 'patch'
    if op in INSPECT_OPS:
        return 'inspect'
    if op in RUN_OPS:
        return 'run'
    if op in SYNC_OPS:
        return 'sync'
    return 'other'


def _short(text, limit=120):
    text = str(text or '').strip().replace('\n', ' ')
    if len(text) > limit:
        return text[:max(0, limit - 1)] + '...'
    return text


def structure_result(raw, index=0):
    raw = dict(raw or {})
    status = str(raw.get('status') or '').upper()
    op = str(raw.get('op') or '')
    target = str(raw.get('target') or '')
    message = str(raw.get('message') or '')
    preview = str(raw.get('preview') or '')

    stdout_top = raw.get('stdout')
    if stdout_top is None or stdout_top == '':
        out_obj = raw.get('out') or {}
        stdout_top = out_obj.get('stdout') if isinstance(out_obj, dict) else ''

    suggested = raw.get('suggested') or []
    if not isinstance(suggested, list):
        suggested = []

    requested = raw.get('requested') or []
    if not isinstance(requested, list):
        requested = []

    return {
        'index': index,
        'status': status,
        'status_emoji': _status_emoji(status),
        'op': op,
        'op_emoji': _op_emoji(op),
        'kind': _kind_for_op(op),
        'target': target,
        'message': message,
        'message_short': _short(message, 140),
        'preview': preview,
        'preview_short': _short(preview, 180),
        'file': str(raw.get('file') or ''),
        'stdout': str(stdout_top or ''),
        'stderr': str(raw.get('stderr') or ''),
        'suggested': suggested,
        'requested': requested,
        'raw': raw,
    }


def structure_manifest(manifest):
    """Return LinkOS-ready run dict."""
    manifest = dict(manifest or {})
    results = [structure_result(r, i) for i, r in enumerate(manifest.get('results') or [])]

    counts = {'applied': 0, 'skipped': 0, 'failed': 0, 'other': 0}
    for r in results:
        st = r.get('status') or ''
        if st == 'APPLIED':
            counts['applied'] += 1
        elif st.startswith('SKIPPED'):
            counts['skipped'] += 1
        elif st.startswith('FAILED'):
            counts['failed'] += 1
        else:
            counts['other'] += 1

    touched = list(manifest.get('touched') or [])
    touched_files = []
    seen = set()

    for row in touched:
        rel = row.get('rel') or row.get('file') or '' if isinstance(row, dict) else str(row or '')
        if rel and rel not in seen:
            seen.add(rel)
            touched_files.append(rel)

    for r in results:
        rel = r.get('file') or ''
        if rel and rel not in seen:
            seen.add(rel)
            touched_files.append(rel)

    return {
        'stamp': manifest.get('stamp') or '',
        'root': manifest.get('root') or _PROJECT_ROOT,
        'bundle_sha': manifest.get('bundle_sha') or '',
        'results': results,
        'counts': counts,
        'touched': touched,
        'touched_files': touched_files,
        'preview_count': len([r for r in results if r.get('preview')]),
        'failed_results': [r for r in results if (r.get('status') or '').startswith('FAILED')],
        'skipped_results': [r for r in results if (r.get('status') or '').startswith('SKIPPED')],
        'inspect_count': len([r for r in results if r.get('kind') == 'inspect']),
        'missing': bool(manifest.get('missing')),
        'manifest': manifest,
    }


def load_run(stamp=None):
    """Load structured run dict, defaulting to latest."""
    stamp = latest_stamp() if not stamp or stamp == 'latest' else stamp
    run = structure_manifest(load_manifest(stamp))
    run['bundle'] = bundle_text(run.get('stamp')) if run.get('stamp') else ''
    return run


def list_stamps_for_ui(limit=80):
    return list_stamps(limit)


def neighbours(stamp):
    stamps = list_stamps(500)
    if not stamps or stamp not in stamps:
        return '', ''
    idx = stamps.index(stamp)
    newer = stamps[idx - 1] if idx > 0 else ''
    older = stamps[idx + 1] if idx + 1 < len(stamps) else ''
    return older, newer


def relative_time(stamp):
    s = str(stamp or '').strip()
    if len(s) < 15 or s[8] != '_':
        return s
    try:
        when = datetime.datetime.strptime(s[:15], '%Y%m%d_%H%M%S')
    except Exception:
        return s

    delta = datetime.datetime.now() - when
    secs = int(delta.total_seconds())
    if secs < 30:
        return 'just now'
    if secs < 60:
        return '%d sec ago' % secs
    mins = secs // 60
    if mins < 60:
        return '%d min ago' % mins
    hrs = mins // 60
    if hrs < 24:
        return '%d hr ago' % hrs
    days = hrs // 24
    if days < 30:
        return '%d days ago' % days
    return when.strftime('%d %b')


def recommendation(run):
    counts = run.get('counts') or {}
    if counts.get('failed', 0):
        return '❌', 'Send failure detail'
    if counts.get('skipped', 0):
        return '⚠️', 'Full packet useful'
    if run.get('inspect_count', 0) >= 2 or run.get('preview_count', 0) >= 3:
        return '📋', 'Full packet useful'
    return '🧠', 'Summary enough'


def status_phrase(run):
    counts = run.get('counts') or {}
    if run.get('missing'):
        return 'No run manifest found'
    if counts.get('failed', 0):
        return 'Needs attention: %s failed' % counts.get('failed', 0)
    if counts.get('skipped', 0):
        return 'Partial success: %s skipped' % counts.get('skipped', 0)
    if counts.get('applied', 0):
        return 'Clean run'
    return 'No applied ops'


def ai_summary(run):
    counts = run.get('counts') or {}
    stamp = run.get('stamp') or '(unknown run)'
    rec_emoji, rec_label = recommendation(run)

    lines = [
        'Run %s: %s' % (stamp, status_phrase(run)),
        '',
        '✅ APPLIED: %s' % counts.get('applied', 0),
        '⚠️ SKIPPED: %s' % counts.get('skipped', 0),
        '❌ FAILED: %s' % counts.get('failed', 0),
        '%s Recommendation: %s' % (rec_emoji, rec_label),
    ]

    failures = run.get('failed_results') or []
    if failures:
        lines.append('')
        lines.append('Failures:')
        for r in failures[:6]:
            lines.append('- %s %s: %s' % (
                r.get('op') or '',
                r.get('target') or '',
                (r.get('message') or '').replace('\n', ' / '),
            ))

    touched = run.get('touched_files') or []
    if touched:
        lines.append('')
        lines.append('Changed/touched files:')
        for rel in touched[:8]:
            lines.append('- %s' % rel)

    return '\n'.join(lines).rstrip() + '\n'


def full_packet(run):
    counts = run.get('counts') or {}
    lines = [
        '=== FORGE RUN ===',
        'Run: %s' % (run.get('stamp') or ''),
        '',
        'Ops:',
    ]

    for r in run.get('results') or []:
        lines.append('- %s | %s | %s :: %s' % (
            r.get('status') or '',
            r.get('op') or '',
            r.get('target') or '?',
            (r.get('message') or '').replace('\n', '\n  '),
        ))

    lines.append('')
    lines.append('APPLIED=%s  SKIPPED=%s  FAILED=%s' % (
        counts.get('applied', 0),
        counts.get('skipped', 0),
        counts.get('failed', 0),
    ))

    previews = [r for r in run.get('results') or [] if r.get('preview')]
    if previews:
        lines.append('')
        lines.append('=== PREVIEW ===')
        for r in previews:
            lines.append(r.get('preview') or '')

    return '\n'.join(lines).rstrip() + '\n'

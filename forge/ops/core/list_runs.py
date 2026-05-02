# -*- coding: utf-8 -*-
"""
ops.list_runs
=============
List recent forge runs with a readable summary.

Usage:
    LIST_RUNS
    LIST_RUNS 10
"""

import os
import json

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'LIST_RUNS',
    'target_kind': 'file',
    'body_mode': 'none',
    'allowed_directives': set(),
    'required_directives': set(),
    "summary": 'List recent forge runs with their IDs, timestamps, and op summaries.',
}


def validate(parsed_op):
    """No validation required — all directives optional. Returns empty list."""
    return []


def execute(ctx, parsed_op, result):
    """List recent forge runs with timestamps, op summaries, and file counts."""
    from forge.run_storage import runs_root, list_runs

    limit_raw = (parsed_op.target or '').strip()
    try:
        limit = int(limit_raw)
    except Exception:
        limit = 50

    runs = list_runs(ctx.project_root)[:limit]

    if not runs:
        result['status'] = 'APPLIED'
        result['message'] = 'No runs found'
        result['preview'] = 'LIST_RUNS [0 runs]'
        return

    rr = runs_root(ctx.project_root)
    write_runs = []
    for stamp in runs:
        mp = os.path.join(rr, stamp, 'manifest.json')
        if not os.path.isfile(mp):
            continue
        try:
            with open(mp, 'r', encoding='utf-8') as f:
                m = json.load(f)
            if m.get('touched'):
                write_runs.append(stamp)
        except Exception:
            pass

    if not write_runs:
        result['status'] = 'APPLIED'
        result['message'] = 'No runs with file changes found'
        result['preview'] = 'LIST_RUNS [0 runs]'
        return

    lines = ['LIST_RUNS [%d runs]\n' % len(write_runs)]
    for stamp in write_runs:

        manifest_path = os.path.join(rr, stamp, 'manifest.json')
        if not os.path.isfile(manifest_path):
            lines.append('%s  (no manifest)' % stamp)
            continue
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception:
            lines.append('%s  (unreadable)' % stamp)
            continue

        touched = manifest.get('touched') or []
        results_data = manifest.get('results') or []

        applied = sum(1 for r in results_data if r.get('status') == 'APPLIED')
        failed = sum(1 for r in results_data if (r.get('status') or '').startswith('FAILED'))
        skipped = len(results_data) - applied - failed

        ops_summary = []
        seen_ops = {}
        for r in results_data:
            op = r.get('op') or '?'
            st = r.get('status') or '?'
            key = op + '/' + st
            seen_ops[key] = seen_ops.get(key, 0) + 1

        for key, count in seen_ops.items():
            op, st = key.split('/', 1)
            if count > 1:
                ops_summary.append('%s x%d' % (op, count))
            else:
                ops_summary.append(op)

        files = [t.get('rel', '?') for t in touched[:3]]
        files_str = ', '.join(files)
        if len(touched) > 3:
            files_str += ' (+%d more)' % (len(touched) - 3)

        status_str = 'A:%d' % applied
        if skipped:
            status_str += ' S:%d' % skipped
        if failed:
            status_str += ' F:%d' % failed

        line = '%s  [%s]  %s' % (
            stamp,
            status_str,
            files_str or '(no files touched)',
        )
        lines.append(line)

    result['status'] = 'APPLIED'
    result['message'] = '%d runs' % len(runs)
    result['preview'] = '\n'.join(lines)

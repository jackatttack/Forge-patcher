# -*- coding: utf-8 -*-
"""
ops.diff
========
Show changed lines between before and after snapshots for a run.

Usage:
    DIFF 20260324_203520   - diff a specific run
    DIFF                   - diff the most recent run
"""

import os
import json

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'DIFF',
    'target_kind': 'file',
    'body_mode': 'none',
    'allowed_directives': set(),
    'required_directives': set(),
    "summary": 'Show changes between a run\'s file snapshots and current disk state.',
}


def validate(parsed_op):
    """No validation required — run ID is optional. Returns empty list."""
    return []


def _diff_lines(before, after, context=1):
    """Compute unified diff between before/after text, return formatted lines."""
    before_lines = (before or '').splitlines()
    after_lines = (after or '').splitlines()
    max_len = max(len(before_lines), len(after_lines))
    changed = []

    for i in range(max_len):
        b = before_lines[i] if i < len(before_lines) else None
        a = after_lines[i] if i < len(after_lines) else None
        if b != a:
            changed.append(i)

    if not changed:
        return []

    out = []
    emitted = set()
    for idx in changed:
        start = max(0, idx - context)
        end = min(max_len - 1, idx + context)
        for i in range(start, end + 1):
            if i in emitted:
                continue
            emitted.add(i)
            b = before_lines[i] if i < len(before_lines) else None
            a = after_lines[i] if i < len(after_lines) else None
            lineno = i + 1
            if b != a:
                if b is not None:
                    out.append('  line %d:  - %s' % (lineno, b))
                if a is not None:
                    out.append('           + %s' % a)
            else:
                out.append('  line %d:    %s' % (lineno, b or ''))

    return out


def execute(ctx, parsed_op, result):
    """Load run snapshots and emit a unified diff for each touched file."""
    from forge.run_storage import runs_root, list_runs

    stamp = (parsed_op.target or '').strip()

    if not stamp:
        runs = list_runs(ctx.project_root)
        if not runs:
            result['status'] = 'APPLIED'
            result['message'] = 'No runs found'
            result['preview'] = 'DIFF [no runs]'
            return
        stamp = runs[0]

    rr = runs_root(ctx.project_root)
    manifest_path = os.path.join(rr, stamp, 'manifest.json')

    if not os.path.isfile(manifest_path):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Run not found: ' + stamp
        return

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = 'Manifest unreadable: ' + str(e)
        return

    touched = manifest.get('touched') or []
    snap_dir = os.path.join(rr, stamp, 'snapshots')
    lines = ['DIFF %s [%d file(s)]\n' % (stamp, len(touched))]

    for t in touched:
        rel = t.get('rel', '?')
        snap_path = os.path.join(snap_dir, rel)
        current_path = os.path.join(ctx.project_root, rel)

        try:
            with open(snap_path, 'r', encoding='utf-8', errors='replace') as f:
                before = f.read()
        except Exception:
            before = ''

        try:
            with open(current_path, 'r', encoding='utf-8', errors='replace') as f:
                after = f.read()
        except Exception:
            after = ''

        diff = _diff_lines(before, after)
        lines.append(rel)
        if diff:
            lines.extend(diff)
        else:
            lines.append('  (no changes - already reverted or overwritten)')
        lines.append('')

    result['status'] = 'APPLIED'
    result['message'] = '%d file(s) diffed' % len(touched)
    result['preview'] = '\n'.join(lines).rstrip()

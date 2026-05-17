# -*- coding: utf-8 -*-
"""
DIFF reboot op.

Shows the stored change for a run, then shows current disk drift when the file
has changed again since the run was stored.

Recovery model:
    before-run -> after-run -> current-disk
"""

import os


SPEC = {
    'name': 'DIFF',
    'target_kind': 'none',
    'body_mode': 'forbidden',
    'allowed_directives': set(['ARGS']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Show stored before/after file changes for a run, plus current disk drift.',
    'minimal_example': [
        'DIFF current',
        'DIFF latest',
        'DIFF 20260511_120000',
    ],
}


HINTS = {
    '_max_hints': 1,
    'run': {
        'message': 'DIFF needs a stored run id.',
        'why': 'Diff compares a run snapshot against the current disk state.',
        'example': [
            'RUNS latest',
            '',
            'DIFF 20260511_120000',
        ],
        'next': [
            'Run RUNS latest or RUNS list.',
            'Copy the stamp exactly into DIFF.',
        ],
    },
}

def validate(parsed_op):
    return []


def _args(parsed_op):
    return ((parsed_op.get('directives') or {}).get('ARGS') or parsed_op.get('target') or '').strip()


def _diff_lines(before, after):
    before_lines = (before or '').splitlines()
    after_lines = (after or '').splitlines()
    max_len = max(len(before_lines), len(after_lines))
    out = []

    for i in range(max_len):
        b = before_lines[i] if i < len(before_lines) else None
        a = after_lines[i] if i < len(after_lines) else None
        if b == a:
            continue
        if b is not None:
            out.append('  line %d -%s' % (i + 1, b))
        if a is not None:
            out.append('  line %d +%s' % (i + 1, a))

    return out


def _read_current(root, rel):
    path = os.path.join(root, rel)
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read(), True
    except Exception:
        return '', False


def _collect_current_touched(run):
    touched = []

    for item in run.get('touched_files') or []:
        if isinstance(item, dict):
            touched.append(dict(item))

    for res in run.get('results') or []:
        for item in res.get('touched') or []:
            if isinstance(item, dict):
                touched.append(dict(item))

    out = []
    seen = set()
    for item in touched:
        rel = str(item.get('rel') or item.get('file') or '').strip()
        if not rel or rel in seen:
            continue
        seen.add(rel)

        out.append({
            'rel': rel,
            'kind': item.get('kind') or 'file',
            'existed_before': bool(item.get('existed_before')),
            'before': item.get('before') if item.get('before') is not None else '',
            'after': item.get('after') if item.get('after') is not None else '',
        })

    return out


def _render_touched(root, label, touched):
    lines = ['DIFF %s' % label]

    if not touched:
        lines.append('(no touched files)')
        return lines

    for item in touched:
        rel = item.get('rel') or '?'
        existed_before = bool(item.get('existed_before'))
        before = item.get('before') or ''
        after = item.get('after') or ''
        current, current_exists = _read_current(root, rel)

        lines.append('')
        lines.append(rel)

        if existed_before:
            lines.append('  stored change: before -> after')
        else:
            lines.append('  stored change: created by run')

        stored_diff = _diff_lines(before, after)
        if stored_diff:
            lines.extend(stored_diff)
        else:
            lines.append('  (no stored content change)')

        if current_exists:
            if current != after:
                lines.append('  current disk drift:')
                drift = _diff_lines(after, current)
                if drift:
                    lines.extend(drift)
                else:
                    lines.append('  (current differs, but no line diff emitted)')
        else:
            if after:
                lines.append('  current disk drift:')
                lines.append('  file missing on disk')

    return lines


def execute(ctx, parsed_op, result):
    from forge_core.run_storage import list_runs, read_manifest

    root = ctx.get('project_root') or os.getcwd()
    stamp = _args(parsed_op)

    if stamp == 'current':
        touched = _collect_current_touched(ctx.get('run') or {})
        lines = _render_touched(root, 'current', touched)
        result['status'] = 'APPLIED'
        result['message'] = '%d current file(s) diffed' % len(touched)
        result['preview'] = '\n'.join(lines).rstrip()
        result['data'] = {'mode': 'current', 'touched': touched}
        return

    if not stamp or stamp == 'latest':
        runs = list_runs(root, limit=1)
        if not runs:
            result['status'] = 'APPLIED'
            result['message'] = 'No runs found'
            result['preview'] = 'DIFF [no runs]'
            return
        stamp = runs[0]

    manifest, err = read_manifest(root, stamp)
    if err:
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = err
        return

    touched = manifest.get('touched') or []
    lines = _render_touched(root, stamp, touched)

    result['status'] = 'APPLIED'
    result['message'] = '%d file(s) diffed' % len(touched)
    result['preview'] = '\n'.join(lines).rstrip()
    result['data'] = {'mode': 'stored', 'stamp': stamp, 'touched': touched}

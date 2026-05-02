# -*- coding: utf-8 -*-
"""
forge.run_storage
==================
Run persistence, pruning, and revert for forge.
Self-contained - no forge1 imports.
"""

import os
import json
import hashlib
import datetime


def _sha256(text):
    """Return SHA-256 hex digest of a byte string."""
    return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


def _read(path):
    """Read a file from disk and return its text content."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def _write(path, text):
    """Write text content to a file, creating parent dirs if needed."""
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def ensure_dir(path):
    """Create a directory and any missing parents."""
    if path and not os.path.isdir(path):
        os.makedirs(path)


def now_stamp():
    """Return current datetime as a sortable timestamp string."""
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def runs_root(project_root):
    """Return absolute path to the forge_runs directory."""
    from forge.config import RUNS_DIRNAME
    return os.path.join(project_root, RUNS_DIRNAME)


def list_runs(project_root):
    """Return list of run stamp strings sorted newest-first."""
    rr = runs_root(project_root)
    if not os.path.isdir(rr):
        return []
    items = [n for n in os.listdir(rr)
             if os.path.isdir(os.path.join(rr, n))]
    items.sort(reverse=True)
    return items


def prune_runs(project_root):
    """Delete oldest runs beyond the keep limit to cap disk usage."""
    from forge.config import KEEP_RUNS
    rr = runs_root(project_root)
    if not os.path.isdir(rr):
        return
    runs = list_runs(project_root)
    if len(runs) <= KEEP_RUNS:
        return
    for name in runs[KEEP_RUNS:]:
        p = os.path.join(rr, name)
        try:
            for root, dirs, files in os.walk(p, topdown=False):
                for fn in files:
                    try:
                        os.remove(os.path.join(root, fn))
                    except Exception:
                        pass
                for dn in dirs:
                    try:
                        os.rmdir(os.path.join(root, dn))
                    except Exception:
                        pass
            os.rmdir(p)
        except Exception:
            pass


def write_run_artifacts(project_root, stamp, bundle_text, results, touched_files):
    """Persist run packet, op results, and before/after file snapshots to disk."""
    rr = runs_root(project_root)
    run_dir = os.path.join(rr, stamp)
    snap_dir = os.path.join(run_dir, 'snapshots')
    log_dir = os.path.join(run_dir, 'logs')
    ensure_dir(snap_dir)
    ensure_dir(log_dir)

    _write(os.path.join(run_dir, 'bundle.txt'), (bundle_text or '').strip() + '\n')

    touched_list = []
    for file_abs, meta in touched_files.items():
        rel = os.path.relpath(file_abs, project_root)
        snap_path = os.path.join(snap_dir, rel)
        _write(snap_path, meta.get('before') or '')
        touched_list.append({
            'rel': rel,
            'snapshot_rel': os.path.relpath(snap_path, run_dir),
            'before_sha': _sha256(meta.get('before') or ''),
            'after_sha': _sha256(meta.get('after') or ''),
        })

    manifest = {
        'stamp': stamp,
        'root': os.path.abspath(project_root),
        'bundle_sha': _sha256(bundle_text or ''),
        'results': results,

        'results': results,

        'touched': touched_list,
    }
    _write(os.path.join(run_dir, 'manifest.json'),
           json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    summary_lines = ['Run: ' + stamp, '']
    for r in results:
        st = r.get('status') or 'UNKNOWN'
        line = ('%-22s %-16s %s  %s' % (
            st, r.get('op', '?'), r.get('target', '?'), r.get('message', '')
        )).rstrip()
        summary_lines.append(line)
    _write(os.path.join(log_dir, 'run_summary.txt'),
           '\n'.join(summary_lines) + '\n')

    with open(os.path.join(log_dir, 'run_log.jsonl'), 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def revert_run(project_root, run_stamp):
    """Restore files to their pre-run state using snapshots from a run directory."""
    run_dir = os.path.join(runs_root(project_root), run_stamp)
    manifest_path = os.path.join(run_dir, 'manifest.json')

    if not os.path.isfile(manifest_path):
        return False, 'Manifest not found for run: ' + run_stamp

    try:
        manifest = json.loads(_read(manifest_path))
    except Exception as e:
        return False, 'Manifest unreadable: ' + type(e).__name__ + ': ' + str(e)

    touched = manifest.get('touched') or []
    snap_dir = os.path.join(run_dir, 'snapshots')

    if not os.path.isdir(snap_dir):
        return False, 'Snapshots folder missing for run: ' + run_stamp

    restored = 0
    failed = 0
    errors = []

    for t in touched:
        rel = t.get('rel')
        if not rel:
            continue
        snap_path = os.path.join(snap_dir, rel)
        target_path = os.path.abspath(os.path.join(project_root, rel))
        try:
            src = _read(snap_path)
            _write(target_path, src)
            restored += 1
        except Exception as e:
            failed += 1
            errors.append('%s: %s: %s' % (rel, type(e).__name__, str(e)))

    if failed:
        msg = 'Revert completed with errors. Restored %d, failed %d.' % (restored, failed)
        if errors:
            msg += ' ' + '; '.join(errors[:3])
        return False, msg

    return True, 'Reverted run %s (%d file(s) restored).' % (run_stamp, restored)

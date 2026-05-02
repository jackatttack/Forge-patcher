# -*- coding: utf-8 -*-
"""
forge/emergency_revert.py
==========================
Standalone emergency revert tool. No forge imports.
Run directly in Pythonista when forge itself is broken.

Usage:
  1. Copy a bundle to clipboard, then run this script:

       Revert a run:
           REVERT_RUN 20260418_135735

       Restore a branch:
           BRANCH restore my_branch_name

  2. Or run with no clipboard / invalid clipboard to see
     recent runs, saved branches, and syntax help.
"""

import os
import sys
import json
import shutil

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RUNS_DIR     = os.path.join(PROJECT_ROOT, 'forge', 'artifacts', 'runs')
BRANCHES_DIR = os.path.join(PROJECT_ROOT, 'forge', 'artifacts', 'branches')


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------

def _read_clipboard():
    try:
        import clipboard
        return (clipboard.get() or '').strip()
    except Exception:
        return ''


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def _write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


# ---------------------------------------------------------------------------
# Run revert
# ---------------------------------------------------------------------------

def _list_runs(limit=10):
    if not os.path.isdir(RUNS_DIR):
        return []
    items = [n for n in os.listdir(RUNS_DIR)
             if os.path.isdir(os.path.join(RUNS_DIR, n))]
    items.sort(reverse=True)
    result = []
    for stamp in items:
        if len(result) >= limit:
            break
        manifest = _load_run_manifest(stamp)
        if manifest and manifest.get('touched'):
            result.append(stamp)
    return result

def _load_run_manifest(stamp):
    path = os.path.join(RUNS_DIR, stamp, 'manifest.json')
    if not os.path.isfile(path):
        return None
    try:
        return json.loads(_read(path))
    except Exception:
        return None

def _revert_run(stamp):
    run_dir  = os.path.join(RUNS_DIR, stamp)
    snap_dir = os.path.join(run_dir, 'snapshots')
    manifest = _load_run_manifest(stamp)

    if manifest is None:
        print('ERROR: Manifest not found for run: ' + stamp)
        return False

    if not os.path.isdir(snap_dir):
        print('ERROR: Snapshots folder missing for run: ' + stamp)
        return False

    touched  = manifest.get('touched') or []
    restored = 0
    errors   = []

    for t in touched:
        rel = t.get('rel')
        if not rel:
            continue
        snap_path   = os.path.join(snap_dir, rel)
        target_path = os.path.abspath(os.path.join(PROJECT_ROOT, rel))
        try:
            src = _read(snap_path)
            _write(target_path, src)
            restored += 1
            print('  restored: ' + rel)
        except Exception as e:
            errors.append('%s: %s' % (rel, e))
            print('  FAILED:   ' + rel + ' — ' + str(e))

    if errors:
        print('\nRevert completed with %d error(s). Restored %d file(s).' % (len(errors), restored))
        return False

    print('\nReverted run %s — %d file(s) restored.' % (stamp, restored))
    return True


# ---------------------------------------------------------------------------
# Branch restore
# ---------------------------------------------------------------------------

def _list_branches():
    if not os.path.isdir(BRANCHES_DIR):
        return []
    entries = []
    for name in sorted(os.listdir(BRANCHES_DIR)):
        mpath = os.path.join(BRANCHES_DIR, name, 'manifest.json')
        if not os.path.isfile(mpath):
            continue
        try:
            manifest = json.loads(_read(mpath))
            mtime = os.path.getmtime(mpath)
            import datetime
            ts = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            entries.append((name, ts, len(manifest.get('files', []))))
        except Exception:
            entries.append((name, '?', 0))
    return entries

def _restore_branch(name):
    branch_dir = os.path.join(BRANCHES_DIR, name)
    mpath = os.path.join(branch_dir, 'manifest.json')

    if not os.path.isfile(mpath):
        print('ERROR: No branch found: ' + name)
        return False

    try:
        manifest = json.loads(_read(mpath))
    except Exception as e:
        print('ERROR: Could not read manifest: ' + str(e))
        return False

    restored = 0
    errors = []
    for rel in manifest.get('files', []):
        src = os.path.join(branch_dir, rel)
        dst = os.path.abspath(os.path.join(PROJECT_ROOT, rel))
        if not os.path.isfile(src):
            errors.append(rel + ' (missing from branch)')
            print('  MISSING:  ' + rel)
            continue
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            restored += 1
            print('  restored: ' + rel)
        except Exception as e:
            errors.append('%s: %s' % (rel, e))
            print('  FAILED:   ' + rel + ' — ' + str(e))

    if errors:
        print('\nRestore completed with %d error(s). Restored %d file(s).' % (len(errors), restored))
        return False

    print('\nBranch %r restored — %d file(s).' % (name, restored))
    return True


# ---------------------------------------------------------------------------
# Clipboard parsers
# ---------------------------------------------------------------------------

def _parse_revert_stamp(text):
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith('REVERT_RUN'):
            parts = line.split()
            if len(parts) == 2:
                return parts[1].strip()
    return None

def _parse_branch_name(text):
    for line in text.splitlines():
        line = line.strip()
        parts = line.split()
        if (len(parts) == 3
                and parts[0].upper() == 'BRANCH'
                and parts[1].lower() == 'restore'):
            return parts[2].strip()
    return None


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def _show_runs():
    runs = _list_runs(limit=10)
    if not runs:
        print('No runs found in: ' + RUNS_DIR)
        return

    print('Recent runs (newest first):\n')
    for stamp in runs:
        manifest = _load_run_manifest(stamp)
        if manifest is None:
            print('  %s  (unreadable manifest)' % stamp)
            continue

        touched   = manifest.get('touched') or []
        results   = manifest.get('results') or []
        applied   = sum(1 for r in results if r.get('status') == 'APPLIED')
        failed    = sum(1 for r in results if (r.get('status') or '').startswith('FAILED'))
        files     = [t.get('rel', '?') for t in touched[:3]]
        files_str = ', '.join(files)
        if len(touched) > 3:
            files_str += ' (+%d more)' % (len(touched) - 3)
        status_str = 'A:%d' % applied
        if failed:
            status_str += ' F:%d' % failed
        print('  %s  [%s]  %s' % (stamp, status_str, files_str or '(no files touched)'))
    print()

def _show_branches():
    branches = _list_branches()
    if not branches:
        print('No branches saved.')
        return

    print('Saved branches:\n')
    for name, ts, count in branches:
        print('  %-30s %s  (%d files)' % (name, ts, count))
    print()

def _show_help():
    print("""
emergency_revert.py — forge independent recovery tool
=======================================================

Copy one of the following to clipboard, then re-run this script:

  Revert a specific run:
      REVERT_RUN 20260418_135735

  Restore a saved branch:
      BRANCH restore my_branch_name

This script requires NO forge imports and can run even when
forge itself is broken.
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('=== EMERGENCY REVERT ===\n')

    clip = _read_clipboard()

    stamp = _parse_revert_stamp(clip) if clip else None
    branch = _parse_branch_name(clip) if clip else None

    if stamp:
        print('Clipboard: REVERT_RUN detected.')
        print('Reverting run: %s\n' % stamp)
        _revert_run(stamp)
    elif branch:
        print('Clipboard: BRANCH restore detected.')
        print('Restoring branch: %s\n' % branch)
        _restore_branch(branch)
    else:
        if clip:
            print('Clipboard not recognised as a REVERT_RUN or BRANCH restore bundle.\n')
        else:
            print('No clipboard content found.\n')
        _show_runs()
        _show_branches()
        _show_help()

if __name__ == '__main__':
    main()

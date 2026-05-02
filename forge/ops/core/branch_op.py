# -*- coding: utf-8 -*-
"""
ops.branch
==========
Named filesystem checkpoints. Save and restore sets of files by name.

Useful for experimenting safely — especially when working on forge itself.

Usage:
    BRANCH create <name>
    BEGIN_BODY
    forge/
    journal/prompts/forge.md
    END_BODY

    BRANCH restore <name>

    BRANCH list

    BRANCH delete <name>

Branches are stored in forge/artifacts/branches/<name>/ with a manifest.json tracking
original paths. Restore uses the manifest to put files back exactly.
"""

import os
import json
import shutil

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'BRANCH',
    'target_kind': 'none',
    'body_mode': 'optional',
    'allowed_directives': set(['ARGS']),
    'required_directives': set(),
    'summary': 'Named filesystem checkpoints. Save and restore files by name.',
}

# HELP doc block — surfaces via HELP BRANCH.
HELP = {
    'summary': 'Named filesystem checkpoints. Save and restore files by name.',
    'subject': [
        'Subcommand and name: create <name>, restore <name>, delete <name>, list',
    ],
    'common_failures': [
        'Missing subcommand.',
        'Branch name not found for restore or delete.',
        'No paths in body for create.',
        'Path not found under project root.',
    ],
    'safe_usage': [
        'Use before any risky patch session, especially on forge/ itself.',
        'Branch name should be short and descriptive.',
        'restore puts files back exactly as they were — use with care.',
        'list shows all saved branches with timestamps.',
        'create also writes forge/artifacts/branches/<name>/restore_branch.py, a standalone restore script that does not import forge.',

    ],
    'minimal_example': [
        'BRANCH create before_help_refactor',
        'BEGIN_BODY',
        'forge/',
        'journal/prompts/forge.md',
        'END_BODY',
        '',
        'BRANCH restore before_help_refactor',
        '',
        'BRANCH list',
        '',
        'BRANCH delete before_help_refactor',
    ],
    'related_ops': ['REVERT_RUN', 'COPY_FILE', 'DIFF'],
}

HINTS = {
    '_max_hints': 1,
    'subcommand': {
        'message': 'BRANCH needs a subcommand.',
        'why': 'Branches can create, restore, list, or delete named filesystem checkpoints.',
        'priority': 100,
        'example': [
            'BRANCH list',
            '',
            'BRANCH create before_change',
            'BEGIN_BODY',
            'forge/ops/core/file.py',
            'END_BODY',
        ],
        'next': ['HELP BRANCH'],
    },
    'create': {
        'message': 'BRANCH create requires a body listing files or directories to snapshot.',
        'why': 'Forge needs to know exactly which paths should be saved in the branch.',
        'priority': 100,
        'example': [
            'BRANCH create before_change',
            'BEGIN_BODY',
            'forge/ops/core/file.py',
            'docs/important_note.txt',
            'END_BODY',
        ],
        'next': ['HELP BRANCH', 'LIST_FILES .'],
    },
    'body': {
        'message': 'Add paths inside BEGIN_BODY / END_BODY, one path per line.',
        'why': 'The branch snapshot is built from the body path list.',
        'priority': 50,
        'example': [
            'BRANCH create before_change',
            'BEGIN_BODY',
            'forge/',
            'journal/prompts/forge.md',
            'END_BODY',
        ],
        'next': ['HELP BRANCH'],
    },
    'not found': {
        'message': 'That branch name was not found.',
        'why': 'Restore and delete only work on branches that already exist.',
        'priority': 100,
        'example': [
            'BRANCH list',
            '',
            'BRANCH restore before_change',
        ],
        'next': ['BRANCH list', 'HELP BRANCH'],
    },
    'path not found': {
        'message': 'One of the requested snapshot paths does not exist under project root.',
        'why': 'BRANCH create only snapshots real files or directories.',
        'priority': 100,
        'example': [
            'LIST_FILES forge/ops/core',
            '',
            'BRANCH create before_change',
            'BEGIN_BODY',
            'forge/ops/core/branch_op.py',
            'END_BODY',
        ],
        'next': ['LIST_FILES .', 'HELP BRANCH'],
    },
}


def validate(parsed_op):
    """Check command and branch name are present. Returns list of error strings."""
    errors = []

    args = (parsed_op.directives.get('ARGS') or '').strip()
    if not args:
        errors.append('BRANCH requires a subcommand: create <name>, restore <name>, delete <name>, or list')
    return errors


def _branches_dir(root):
    """Return absolute path to the Forge branch artifact storage directory."""
    return os.path.join(root, 'forge', 'artifacts', 'branches')

def _branch_dir(root, name):
    """Return absolute path to a named branch directory."""
    return os.path.join(_branches_dir(root), name)


def _manifest_path(root, name):
    """Return absolute path to the manifest JSON for a named branch."""
    return os.path.join(_branch_dir(root, name), 'manifest.json')


def _restore_script_path(root, name):
    """Return absolute path to the standalone restore script for a branch."""
    return os.path.join(_branch_dir(root, name), 'restore_branch.py')


def _write_restore_script(root, name):
    """Write a standalone, forge-independent restore script into the branch."""
    script = r'''# -*- coding: utf-8 -*-
"""
Standalone branch restore script.

Run this file directly in Pythonista to restore this branch without importing
forge. Useful if Forge itself is broken.
"""
import os
import json
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BRANCH_NAME = os.path.basename(SCRIPT_DIR)
BRANCHES_DIR = os.path.dirname(SCRIPT_DIR)
ARTIFACTS_DIR = os.path.dirname(BRANCHES_DIR)
FORGE_DIR = os.path.dirname(ARTIFACTS_DIR)
PROJECT_ROOT = os.path.dirname(FORGE_DIR)
MANIFEST = os.path.join(SCRIPT_DIR, 'manifest.json')


def _find_project_root():
    """Find the Pythonista project root from the restore script location."""
    candidates = [
        PROJECT_ROOT,
        os.path.dirname(SCRIPT_DIR),
        os.path.dirname(os.path.dirname(SCRIPT_DIR)),
        os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))),
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))),
    ]
    for path in candidates:
        if os.path.isdir(os.path.join(path, 'forge')) or os.path.isfile(os.path.join(path, 'forge_entry.py')):
            return path
    return PROJECT_ROOT


def main():
    project_root = _find_project_root()

    if not os.path.isfile(MANIFEST):
        print('ERROR: manifest.json not found next to restore script')
        return

    with open(MANIFEST, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    restored = 0
    failed = []

    print('Restoring branch: %s' % manifest.get('name', BRANCH_NAME))
    print('Project root: %s' % project_root)
    print('')

    for rel in manifest.get('files', []):
        src = os.path.join(SCRIPT_DIR, rel)
        dst = os.path.abspath(os.path.join(project_root, rel))

        if not os.path.isfile(src):
            failed.append(rel + ' (missing from branch)')
            print('MISSING:  ' + rel)
            continue

        try:
            parent = os.path.dirname(dst)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
            shutil.copy2(src, dst)
            restored += 1
            print('restored: ' + rel)
        except Exception as e:
            failed.append('%s: %s' % (rel, e))
            print('FAILED:   ' + rel + ' — ' + str(e))

    print('')
    if failed:
        print('Restore completed with %d error(s). Restored %d file(s).' % (len(failed), restored))
        for item in failed:
            print('  - ' + item)
    else:
        print('Branch %r restored — %d file(s).' % (manifest.get('name', BRANCH_NAME), restored))


if __name__ == '__main__':
    main()
'''
    path = _restore_script_path(root, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(script)
    return path

def _collect_files(root, include_paths):
    """Walk project root and return list of relative file paths to snapshot."""
    collected = []
    for path in include_paths:
        path = path.strip()
        if not path:
            continue
        abs_path = os.path.join(root, path)
        if os.path.isdir(abs_path):
            for dirpath, dirnames, filenames in os.walk(abs_path):
                dirnames[:] = sorted(
                    x for x in dirnames
                    if not x.startswith('.') and x != '__pycache__'
                )
                for fn in sorted(filenames):
                    if fn.startswith('.'):
                        continue
                    file_abs = os.path.join(dirpath, fn)
                    rel = os.path.relpath(file_abs, root)
                    collected.append(rel)
        elif os.path.isfile(abs_path):
            rel = os.path.relpath(abs_path, root)
            collected.append(rel)
        else:
            collected.append(('MISSING', path))
    return collected


def _cmd_create(ctx, name, body, result):
    """Snapshot current project files into a named branch."""
    root = ctx.project_root
    include_paths = [l.strip() for l in (body or '').splitlines() if l.strip()]
    if not include_paths:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'BRANCH create requires paths in body'
        return

    collected = _collect_files(root, include_paths)
    missing = [p for p in collected if isinstance(p, tuple)]
    collected = [p for p in collected if not isinstance(p, tuple)]

    if not collected:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'No files found to branch — check your paths'
        return

    branch_dir = _branch_dir(root, name)
    if os.path.exists(branch_dir):
        shutil.rmtree(branch_dir)
    os.makedirs(branch_dir)

    saved = []
    for rel in collected:
        src = os.path.join(root, rel)
        dst = os.path.join(branch_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        saved.append(rel)

    manifest = {'name': name, 'files': saved}
    with open(_manifest_path(root, name), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    restore_script = _write_restore_script(root, name)
    restore_rel = os.path.relpath(restore_script, root)

    msg = 'Branch %r created — %d files; standalone restore: %s' % (name, len(saved), restore_rel)
    if missing:
        msg += ' (%d missing: %s)' % (len(missing), ', '.join(p for _, p in missing))
    result['status'] = 'APPLIED'
    result['message'] = msg

def _cmd_restore(ctx, name, result):
    """Restore project files from a named branch snapshot."""
    root = ctx.project_root
    mpath = _manifest_path(root, name)
    if not os.path.isfile(mpath):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'No branch found: ' + name
        return

    with open(mpath, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    branch_dir = _branch_dir(root, name)
    restored = []
    failed = []
    for rel in manifest.get('files', []):
        src = os.path.join(branch_dir, rel)
        dst = os.path.join(root, rel)
        if not os.path.isfile(src):
            failed.append(rel)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        restored.append(rel)

    msg = 'Branch %r restored — %d files' % (name, len(restored))
    if failed:
        msg += ' (%d missing in branch: %s)' % (len(failed), ', '.join(failed))
    result['status'] = 'APPLIED'
    result['message'] = msg


def _cmd_list(ctx, result):
    """List all saved branches with timestamps and file counts."""
    root = ctx.project_root
    bdir = _branches_dir(root)
    if not os.path.isdir(bdir):
        result['status'] = 'APPLIED'
        result['message'] = 'No branches saved yet'
        result['preview'] = 'No branches saved yet.\n'
        return

    entries = []
    for name in sorted(os.listdir(bdir)):
        mpath = os.path.join(bdir, name, 'manifest.json')
        if not os.path.isfile(mpath):
            continue
        try:
            with open(mpath, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            mtime = os.path.getmtime(mpath)
            import datetime
            ts = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            entries.append('  %-30s %s  (%d files)' % (name, ts, len(manifest.get('files', []))))
        except Exception:
            entries.append('  ' + name + '  (unreadable manifest)')

    if not entries:
        preview = 'No branches saved yet.\n'
    else:
        preview = '=== BRANCHES ===\n\n' + '\n'.join(entries) + '\n'

    result['status'] = 'APPLIED'
    result['message'] = '%d branch(es)' % len(entries)
    result['preview'] = preview


def _cmd_delete(ctx, name, result):
    """Delete a named branch and its snapshot files."""
    root = ctx.project_root
    branch_dir = _branch_dir(root, name)
    if not os.path.isdir(branch_dir):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = 'No branch found: ' + name
        return

    shutil.rmtree(branch_dir)
    result['status'] = 'APPLIED'
    result['message'] = 'Branch %r deleted' % name


def execute(ctx, parsed_op, result):
    """Dispatch BRANCH command to create, restore, list, or delete handler."""
    args = (parsed_op.directives.get('ARGS') or '').strip().split(None, 1)
    subcommand = args[0].lower() if args else ''
    name = args[1].strip() if len(args) > 1 else ''

    if subcommand == 'create':
        if not name:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'BRANCH create requires a name'
            return
        _cmd_create(ctx, name, parsed_op.body, result)
    elif subcommand == 'restore':
        if not name:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'BRANCH restore requires a name'
            return
        _cmd_restore(ctx, name, result)
    elif subcommand == 'list':
        _cmd_list(ctx, result)
    elif subcommand == 'delete':
        if not name:
            result['status'] = 'FAILED_PARSE'
            result['message'] = 'BRANCH delete requires a name'
            return
        _cmd_delete(ctx, name, result)
    else:
        result['status'] = 'FAILED_PARSE'
        result['message'] = 'Unknown subcommand: %r — use create, restore, list, or delete' % subcommand

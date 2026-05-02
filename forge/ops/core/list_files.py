# -*- coding: utf-8 -*-
"""
ops.list_files
==============
Directory listing op.
"""

import os

from forge.file_ops import resolve_under_root, in_root, rel_from_root

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'LIST_FILES',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['FILTER', 'DEPTH', 'FILES', 'ALL', 'DOCS']),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP LIST_FILES.
HELP = {
    'summary': 'List directory contents as a tree. Auto-excludes noisy system folders. Shows README.md summaries and module docstrings inline.',
    'subject': ['Relative directory path inside project root. Defaults to . if omitted.'],
    'directives': {
        'DEPTH': 'How many levels deep to recurse (default 1, use 2+ for tree view)',
        'FILES': 'Show files in output — yes or no (default yes)',
        'FILTER': 'Only include files with this suffix e.g. .py',
        'ALL': 'Set to yes to disable auto-exclusions and show everything (default no)',
        'DOCS': 'Set to yes to show module docstring summaries for .py files (default no)',
    },
    'common_failures': [
        'Directory not found.',
        'Target escapes project root.',
        'Using a file path where a directory is expected.',
    ],
    'safe_usage': [
        'Use DEPTH: 2 FILES: no for a clean project overview at session start.',
        'Auto-excludes .Trash, site-packages, stash, script_snapshots, Examples, Templates.',
        'Use ALL: yes to override exclusions when you need the full listing.',
        'README.md first lines are shown as · summaries under each directory.',
        'Use DOCS: yes to surface module docstrings — great for codebase orientation.',
        'DOCS: yes on a directory shows what every file does at a glance.',
    ],
    'minimal_example': [
        'LIST_FILES .',
        'DEPTH: 2',
        'FILES: no',
        '',
        'LIST_FILES forge/ops/core',
        'DOCS: yes',
    ],
    'related_ops': ['READ_FILE', 'PREVIEW', 'GREP', 'LIST_TARGETS'],
}


def validate(parsed_op):
    """No validation required — target defaults to project root. Returns empty list."""
    return []

# Directory names skipped during recursive file walks.

# Directory names skipped during recursive file walks.
_EXCLUDED = {
    '.Trash',
    'site-packages', 'site-packages-2', 'site-packages-3',
    'stash', 'stash_extensions',
    'script_snapshots',
    'Examples', 'Templates',
}

def execute(ctx, parsed_op, result):
    """Walk a directory tree and emit a structured file listing with optional doc summaries."""
    target = (parsed_op.target or '.').strip() or '.'
    dir_abs = resolve_under_root(ctx.project_root, target)

    if not in_root(ctx.project_root, dir_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isdir(dir_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Directory not found: ' + target
        return

    ext_filter = (parsed_op.directives.get('FILTER') or '').strip()
    show_files = (parsed_op.directives.get('FILES') or 'yes').strip().lower() != 'no'
    show_all   = (parsed_op.directives.get('ALL') or 'no').strip().lower() == 'yes'
    show_docs  = (parsed_op.directives.get('DOCS') or 'no').strip().lower() == 'yes'

    try:
        max_depth = int((parsed_op.directives.get('DEPTH') or '1').strip())
    except ValueError:
        max_depth = 1

    lines = []

    def _readme_summary(dir_path):
        """Return first non-heading line of README.md in dir_path, or None."""
        readme = os.path.join(dir_path, 'README.md')
        if not os.path.isfile(readme):
            return None
        try:
            with open(readme, encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        continue
                    return stripped
        except OSError:
            pass
        return None

    def _module_doc(file_path):
        """Return first descriptive line of a Python file's module docstring, or None."""
        try:
            import ast
            with open(file_path, encoding='utf-8', errors='replace') as f:
                src = f.read()
            tree = ast.parse(src)
            raw = ast.get_docstring(tree) or ''
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Skip underline decorators e.g. '==============='
                if set(line) <= set('=-'):
                    continue
                # Skip bare module path / name lines — descriptions always contain a space
                if ' ' not in line:
                    continue
                return line
        except Exception:
            pass
        return None
        return None
        return None

    def _walk(abs_path, depth):
        """Recursively walk directory, appending formatted lines to outer list."""
        try:
            entries = sorted(os.listdir(abs_path))
        except OSError:
            return
        for name in entries:
            full = os.path.join(abs_path, name)
            is_dir = os.path.isdir(full)
            indent = '  ' * depth
            if is_dir:
                if not show_all and name in _EXCLUDED:
                    continue
                lines.append(indent + name + '/')
                summary = _readme_summary(full)
                if summary:
                    lines.append(indent + '  · ' + summary)
                if depth + 1 < max_depth:
                    _walk(full, depth + 1)
            else:
                if ext_filter and not name.endswith(ext_filter):
                    continue
                if not show_files:
                    continue
                try:
                    size = os.path.getsize(full)
                    line = indent + '%s (%d bytes)' % (name, size)
                except OSError:
                    line = indent + name
                lines.append(line)
                if show_docs and name.endswith('.py'):
                    doc = _module_doc(full)
                    if doc:
                        lines.append(indent + '  · ' + doc)

    _walk(dir_abs, 0)

    rel = rel_from_root(ctx.project_root, dir_abs)
    result['file'] = rel
    result['status'] = 'APPLIED'
    result['message'] = '%d entries' % len(lines)
    result['preview'] = 'LIST_FILES %s [%d entries]\n' % (rel, len(lines)) + '\n'.join(lines)

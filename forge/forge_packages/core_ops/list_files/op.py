# -*- coding: utf-8 -*-
"""
LIST_FILES reboot op.

This ports the useful shape of Forge2 LIST_FILES into the reboot:
- README-aware orientation tree
- depth control
- optional file display
- optional docstring surfacing
- structured result data for Surface pages
"""

import ast
import os


SPEC = {
    'name': 'LIST_FILES',
    'target_kind': 'path',
    'body_mode': 'forbidden',
    'allowed_directives': set(['DEPTH', 'FILES', 'ALL', 'DOCS', 'README', 'FILTER']),
    'required_directives': set(),
}

HELP = {
    'summary': 'List directory contents as an orientation tree with README summaries and optional module docstrings.',
    'subject': [
        'Relative directory path inside project root. Defaults to . if omitted.',
        'Use this to understand project shape before editing.',
    ],
    'directives': {
        'DEPTH': 'How many levels deep to recurse. Default: 1.',
        'FILES': 'Show files in output — yes/no. Default: yes.',
        'ALL': 'yes disables noisy/system folder exclusions.',
        'DOCS': 'yes shows first useful module docstring line for .py files.',
        'README': 'yes/no controls directory README summaries. Default: yes.',
        'FILTER': 'Only include files with this suffix, e.g. .py or .txt.',
    },
    'minimal_example': [
        'LIST_FILES forge',
        'DEPTH: 2',
        'FILES: yes',
    ],
    'related_ops': ['HELP', 'RUNS', 'LIST_OPS'],
}


_EXCLUDED = {
    '.Trash',
    '.git',
    '.mypy_cache',
    '.pytest_cache',
    '__pycache__',
    'site-packages',
    'site-packages-2',
    'site-packages-3',
    'stash',
    'stash_extensions',
    'script_snapshots',
}
# Project-relative path suffixes skipped during ordinary tree views.
# These are generated operational artifacts, not user project content.
_SKIP_PATH_SUFFIXES = (
    ('artifacts', 'branches'),
    ('artifacts', 'runs'),
    ('artifacts', 'packed'),
)


_README_NAMES = (
    'README.md',
    'README.txt',
    'README.rst',
    'readme.md',
    'readme.txt',
)


HINTS = {
    '_max_hints': 1,
    'not found': {
        'message': 'LIST_FILES could not find that directory.',
        'why': 'The target path may be misspelled, a file instead of a directory, or outside the project root.',
        'example': [
            'LIST_FILES forge',
            'DEPTH: 2',
        ],
        'next': [
            'List a parent directory first.',
            'Use SEARCH if you are looking for a file by content.',
        ],
    },
}

def validate(parsed_op):
    return []


def _as_int(value, default):
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _flag(value, default=False):
    text = str(value if value is not None else '').strip().lower()
    if not text:
        return bool(default)
    return text in ('yes', 'true', '1', 'on')


def _read_text(path, limit_chars=6000):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read(limit_chars)
    except Exception:
        return ''


def _clean(line):
    return str(line or '').strip()


def _is_rule(line):
    s = _clean(line)
    return bool(s) and set(s) <= set('=-_*`~')


def _readme_summary(dir_path):
    """Return the first useful descriptive line from README.* in dir_path."""
    base_name = os.path.basename(os.path.abspath(dir_path)).strip().lower()

    def _is_heading(line, next_line=''):
        s = _clean(line)
        n = _clean(next_line)

        if not s:
            return True
        if s.startswith('#'):
            return True
        if _is_rule(s):
            return True
        if n and _is_rule(n):
            return True

        low = s.lower().rstrip(':')
        if low in set([
            base_name,
            'purpose',
            'overview',
            'summary',
            'current state',
            'current shape',
            'what belongs here',
            'main areas',
            'important locations',
            'usage',
            'workflow',
        ]):
            return True

        return False

    for name in _README_NAMES:
        readme = os.path.join(dir_path, name)
        if not os.path.isfile(readme):
            continue

        try:
            with open(readme, encoding='utf-8', errors='replace') as f:
                raw_lines = f.readlines()
        except OSError:
            continue

        lines = [_clean(x) for x in raw_lines]
        for i, line in enumerate(lines):
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if _is_heading(line, next_line):
                continue
            if line.startswith(('```', '---')):
                continue
            if len(line) > 140:
                return line[:139].rstrip() + '…'
            return line

    return None


def _module_doc(file_path):
    """Return first descriptive line of a Python module docstring."""
    try:
        src = _read_text(file_path, limit_chars=30000)
        tree = ast.parse(src)
        raw = ast.get_docstring(tree) or ''
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if set(line) <= set('=-'):
                continue
            if ' ' not in line:
                continue
            return line
    except Exception:
        pass
    return None


def _file_line(name, full):
    try:
        size = os.path.getsize(full)
        return '%s (%d bytes)' % (name, size)
    except OSError:
        return name


def _should_skip_dir(root, dirpath, name, show_all):
    if show_all:
        return False
    if name in _EXCLUDED or name.startswith('.'):
        return True

    full = os.path.join(dirpath, name)
    try:
        rel = os.path.relpath(full, root)
    except ValueError:
        return False

    if rel == '.':
        return False

    parts = tuple(rel.replace('\\', '/').split('/'))
    for suffix in _SKIP_PATH_SUFFIXES:
        if len(parts) >= len(suffix) and parts[-len(suffix):] == suffix:
            return True

    return False


def _sorted_entries(abs_path):
    try:
        names = sorted(os.listdir(abs_path))
    except OSError:
        return []

    dirs = []
    files = []
    for name in names:
        full = os.path.join(abs_path, name)
        if os.path.isdir(full):
            dirs.append(name)
        else:
            files.append(name)
    return dirs + files


def _rel(root, path):
    try:
        rel = os.path.relpath(path, root)
        return '.' if rel == '.' else rel.replace(os.sep, '/')
    except Exception:
        return path


def execute(ctx, parsed_op, result):
    root = ctx.get('project_root') or os.getcwd()
    target = (parsed_op.get('target') or '.').strip() or '.'
    directives = parsed_op.get('directives') or {}

    base = os.path.abspath(os.path.join(root, target))
    root_abs = os.path.abspath(root)

    if not (base == root_abs or base.startswith(root_abs + os.sep)):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isdir(base):
        result['status'] = 'FAILED_IO'
        result['message'] = 'Directory not found: ' + target
        return

    depth = _as_int(directives.get('DEPTH'), 1)
    if depth < 1:
        depth = 1

    show_files = _flag(directives.get('FILES'), default=True)
    show_all = _flag(directives.get('ALL'), default=False)
    show_docs = _flag(directives.get('DOCS'), default=False)
    show_readme = _flag(directives.get('README'), default=True)
    ext_filter = (directives.get('FILTER') or '').strip()

    lines = []
    tree = []
    seen_dirs = 0
    seen_files = 0

    root_summary = _readme_summary(base) if show_readme else None
    if root_summary:
        lines.append('· ' + root_summary)

    def add_node(kind, name, path, level, summary=None, doc=None, size=None):
        node = {
            'kind': kind,
            'name': name,
            'path': _rel(root_abs, path),
            'level': level,
        }
        if summary:
            node['summary'] = summary
        if doc:
            node['doc'] = doc
        if size is not None:
            node['size'] = size
        tree.append(node)

    def walk(path, level):
        nonlocal seen_dirs, seen_files

        if level >= depth:
            return

        for name in _sorted_entries(path):
            full = os.path.join(path, name)
            is_dir = os.path.isdir(full)
            indent = '  ' * level

            if is_dir:
                if _should_skip_dir(root_abs, path, name, show_all):
                    continue

                seen_dirs += 1
                lines.append(indent + name + '/')

                summary = _readme_summary(full) if show_readme else None
                add_node('dir', name, full, level, summary=summary)

                if summary:
                    lines.append(indent + '  · ' + summary)

                walk(full, level + 1)
                continue

            if not show_files:
                continue
            if ext_filter and not name.endswith(ext_filter):
                continue
            if not show_all and name.startswith('.'):
                continue

            seen_files += 1
            lines.append(indent + _file_line(name, full))

            doc = _module_doc(full) if show_docs and name.endswith('.py') else None
            size = None
            try:
                size = os.path.getsize(full)
            except OSError:
                pass

            add_node('file', name, full, level, doc=doc, size=size)

            if doc:
                lines.append(indent + '  · ' + doc)

    walk(base, 0)

    rel = _rel(root_abs, base)
    header = 'LIST_FILES %s [%d entries]' % (rel, len(lines))
    meta = 'dirs=%d files=%d depth=%d readme=%s docs=%s' % (
        seen_dirs,
        seen_files,
        depth,
        'yes' if show_readme else 'no',
        'yes' if show_docs else 'no',
    )

    result['file'] = rel
    result['status'] = 'APPLIED'
    result['message'] = '%d entries' % len(lines)
    result['preview'] = header + '\n' + meta + '\n' + '\n'.join(lines).rstrip() + '\n'
    result['data'] = {
        'path': rel,
        'target': target,
        'lines': lines,
        'tree': tree,
        'meta': {
            'dirs': seen_dirs,
            'files': seen_files,
            'depth': depth,
            'readme': show_readme,
            'docs': show_docs,
            'entries': len(lines),
        },
    }

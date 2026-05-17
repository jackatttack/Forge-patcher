# -*- coding: utf-8 -*-
"""
PREVIEW reboot op.

Read-only source inspection with line numbers.

Compatibility rule:
Match current Forge PREVIEW syntax first:
- LINES: start-end
- ANCHOR: text
- CONTEXT: N
- MATCH: fuzzy

Do not support LIMIT as a public directive. A private default display cap may
exist internally, but user-facing syntax should stay aligned with Forge2.
"""

import os


SPEC = {
    'name': 'PREVIEW',
    'target_kind': 'path',
    'body_mode': 'forbidden',
    'allowed_directives': set(['LINES', 'ANCHOR', 'CONTEXT', 'MATCH']),
    'required_directives': set(),
}

HELP = {
    'summary': 'Preview a project-relative file or AST target with numbered source lines.',
    'minimal_example': [
        'PREVIEW forge/forge_core/engine.py',
        'LINES: 1-80',
        '',
        'PREVIEW forge/smoke.py::main',
        '',
        'PREVIEW forge/smoke.py',
        'ANCHOR: def main',
        'CONTEXT: 6',
    ],
}


HINTS = {
    '_max_hints': 1,
    'target': {
        'message': 'PREVIEW needs a file path or AST target.',
        'why': 'Preview is the inspect-first step before editing.',
        'example': [
            'PREVIEW forge/smoke.py',
            'LINES: 1-80',
            '',
            'PREVIEW forge/smoke.py::main',
        ],
        'next': [
            'Use LIST_FILES to find paths.',
            'Use LIST_TARGETS for AST target names.',
        ],
    },
}

def validate(parsed_op):
    errors = []
    if not (parsed_op.get('target') or '').strip():
        errors.append('PREVIEW requires a target path or AST target')
    return errors


def _in_root(root, path):
    root_real = os.path.realpath(os.path.abspath(root))
    path_real = os.path.realpath(os.path.abspath(path))
    return path_real == root_real or path_real.startswith(root_real + os.sep)


def _as_int(value, default):
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _parse_lines(raw, total, default_limit):
    text = str(raw or '').strip()

    if not text:
        return 1, min(total, default_limit)

    if '-' in text:
        left, _sep, right = text.partition('-')
        try:
            start = int(left.strip())
            end = int(right.strip())
        except Exception:
            start = 1
            end = min(total, default_limit)
    else:
        try:
            start = int(text)
            end = start
        except Exception:
            start = 1
            end = min(total, default_limit)

    if start < 1:
        start = 1
    if end < start:
        end = start
    if end > total:
        end = total

    return start, end


def _normalise_for_match(text):
    return ' '.join(str(text or '').strip().split())


def _anchor_range(lines, anchor, context, match_mode):
    anchor = str(anchor or '')
    if not anchor:
        return None

    fuzzy = str(match_mode or '').strip().lower() == 'fuzzy'
    wanted = _normalise_for_match(anchor) if fuzzy else anchor

    matches = []
    for idx, line in enumerate(lines):
        hay = _normalise_for_match(line) if fuzzy else line
        if wanted in hay:
            matches.append(idx + 1)

    if not matches:
        return None

    line_no = matches[0]
    start = max(1, line_no - context)
    end = min(len(lines), line_no + context)
    return start, end


def _format_preview(title, lines, start, end):
    selected = lines[start - 1:end]
    width = max(4, len(str(end)))

    out = []
    out.append('%s [lines %d-%d of %d]' % (title, start, end, len(lines)))

    for offset, line in enumerate(selected):
        n = start + offset
        out.append(('%0' + str(width) + 'd: %s') % (n, line))

    return out


def _preview_file(root, target, directives):
    abs_path = os.path.abspath(os.path.join(root, target))

    if not _in_root(root, abs_path):
        return None, 'FAILED_IO', 'Path escapes project root'

    if not os.path.isfile(abs_path):
        return None, 'FAILED_NOT_FOUND', 'File not found: ' + target

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            src = f.read()
    except Exception as e:
        return None, 'FAILED_IO', 'Could not read file: %s: %s' % (type(e).__name__, e)

    lines = src.splitlines()
    total = len(lines)
    default_limit = 120

    if directives.get('ANCHOR'):
        context = _as_int(directives.get('CONTEXT'), 10)
        found = _anchor_range(lines, directives.get('ANCHOR'), context, directives.get('MATCH'))
        if not found:
            return None, 'FAILED_NOT_FOUND', 'ANCHOR matched 0 times'
        start, end = found
    else:
        start, end = _parse_lines(directives.get('LINES'), total, default_limit)

    return {
        'title': target,
        'path': target,
        'start': start,
        'end': end,
        'total': total,
        'lines': lines[start - 1:end],
        'preview_lines': _format_preview(target, lines, start, end),
    }, None, None


def _preview_ast(root, target, directives):
    try:
        from forge_core.ast_tools import resolve_ast_target
    except Exception as e:
        return None, 'FAILED_RUNTIME', 'AST tools unavailable: %s: %s' % (type(e).__name__, e)

    resolved = resolve_ast_target(root, target)
    if not resolved.get('ok'):
        return None, 'FAILED_NOT_FOUND', resolved.get('error') or 'AST target not found'

    src = resolved.get('source_text') or ''
    lines = src.splitlines()
    start = int(resolved.get('start') or 1)
    end = int(resolved.get('end') or start)

    file_ref = resolved.get('file_ref') or target
    title = target

    return {
        'title': title,
        'path': file_ref,
        'ast_target': target,
        'kind': resolved.get('kind') or '',
        'start': start,
        'end': end,
        'total': len(lines),
        'lines': lines[start - 1:end],
        'preview_lines': _format_preview(title, lines, start, end),
    }, None, None


def execute(ctx, parsed_op, result):
    root = os.path.abspath(ctx.get('project_root') or os.getcwd())
    target = (parsed_op.get('target') or '').strip()
    directives = parsed_op.get('directives') or {}

    if '::' in target:
        data, status, message = _preview_ast(root, target, directives)
    else:
        data, status, message = _preview_file(root, target, directives)

    if status:
        result['status'] = status
        result['message'] = message
        return

    result['status'] = 'APPLIED'
    result['message'] = 'Lines %d-%d' % (data.get('start'), data.get('end'))
    result['preview'] = '\n'.join(data.get('preview_lines') or []).rstrip()
    result['file'] = data.get('path') or target
    result['data'] = {
        'path': data.get('path') or target,
        'ast_target': data.get('ast_target') or '',
        'kind': data.get('kind') or '',
        'start': data.get('start'),
        'end': data.get('end'),
        'total': data.get('total'),
        'lines': data.get('lines') or [],
    }

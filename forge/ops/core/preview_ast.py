# -*- coding: utf-8 -*-
"""
forge.ops.core.preview_ast
===========================
PREVIEW op — unified code and file preview.

Detects mode from subject syntax:
  file.py::Class.method   → AST mode — resolves target, shows its full line range
  file.py                 → file mode — shows whole file or a slice via LINES/ANCHOR
"""

import os

# Op identity, target kind, and directive contract.
SPEC = {
    'name': 'PREVIEW',
    'target_kind': 'any',
    'body_mode': 'forbidden',
    'allowed_directives': set(['LINES', 'ANCHOR', 'CONTEXT', 'MATCH']),
    'required_directives': set(),
}

# Human-readable help shown by HELP PREVIEW.
HELP = {
    'summary': 'Preview a resolved AST target or file slice with numbered source lines.',
    'subject': [
        'AST target (file.py::Class.method) — resolves and shows the full target.',
        'File path (file.py) — shows whole file, or a slice via LINES or ANCHOR.',
    ],
    'common_failures': [
        'Target does not resolve to a real AST target — check syntax with LIST_TARGETS.',
        'File not found — check path is relative to project root.',
        'ANCHOR matched 0 times — check spelling or use MATCH: fuzzy.',
        'ANCHOR matched multiple times — make it more specific.',
        'LINES must be in start-end format, e.g. LINES: 10-40.',
    ],
    'safe_usage': [
        'Use :: syntax to preview a named function, method, or class.',
        'Use file path alone to preview a full file or range.',
        'Use ANCHOR to jump to a known string without knowing the line number.',
        'Use LINES for exact line spans.',
        'Use CONTEXT to control how many lines either side of an anchor are shown.',
        'CONTEXT defaults to 10 lines either side of the anchor.',
        'Use MATCH: fuzzy if indentation or spacing might vary.',
        'Use LIST_TARGETS first if you do not know the exact AST target name.',
    ],
    'minimal_example': [
        'PREVIEW forge/ops/core/grep_ast.py::execute',
        '',
        'PREVIEW forge/ops/core/grep_ast.py',
        'LINES: 44-80',
        '',
        'PREVIEW journal/cli.py',
        'ANCHOR: def cmd_retag',
        'CONTEXT: 5',
    ],
    'related_ops': ['LIST_TARGETS', 'REPLACE', 'INSERT_INTO', 'REPLACE_FILE_RANGE'],
}

# Keyboard hint pills shown when PREVIEW is typed.
HINTS = {
    '_max_hints': 1,
    'requires a target': {
        'message': 'PREVIEW needs a file path or AST target.',
        'why': 'Forge needs to know what source to display.',
        'priority': 100,
        'example': [
            'PREVIEW forge/engine.py',
            'LINES: 1-80',
            '',
            'PREVIEW forge/engine.py::execute_ops',
        ],
        'next': ['Use LIST_FILES to find files', 'Use LIST_TARGETS to find AST targets'],
    },
    'target not found': {
        'message': 'AST target not found.',
        'why': 'The file may exist, but the function/class/method target name does not resolve.',
        'priority': 120,
        'example': [
            'LIST_TARGETS forge/engine.py',
            '',
            'PREVIEW forge/engine.py::execute_ops',
        ],
        'next': ['Run LIST_TARGETS on the file', 'Copy the exact target name'],
    },
    'file not found': {
        'message': 'File not found.',
        'why': 'PREVIEW can only display files that exist under project root.',
        'priority': 120,
        'example': [
            'LIST_FILES forge/ops/core',
            '',
            'PREVIEW forge/ops/core/branch_op.py',
        ],
        'next': ['Check the path with LIST_FILES'],
    },
    'anchor matched 0': {
        'message': 'PREVIEW anchor was not found.',
        'why': 'The anchor text does not appear in the file, or whitespace differs.',
        'priority': 120,
        'example': [
            'PREVIEW journal/cli.py',
            'ANCHOR: def cmd_today',
            'CONTEXT: 5',
        ],
        'next': ['Check spelling', 'Try MATCH: fuzzy if whitespace may differ'],
    },
    'anchor matched': {
        'message': 'PREVIEW anchor matched more than once.',
        'why': 'Forge needs a more specific anchor to choose the right location.',
        'priority': 100,
        'example': [
            'PREVIEW journal/cli.py',
            'ANCHOR: def cmd_today',
            'CONTEXT: 5',
        ],
        'next': ['Use a longer unique anchor', 'Use LINES if you know the range'],
    },
    'lines': {
        'message': 'PREVIEW LINES should be start-end.',
        'why': 'Line slices need an explicit inclusive range.',
        'priority': 90,
        'example': [
            'PREVIEW forge/engine.py',
            'LINES: 1-80',
        ],
        'next': ['Use LINES: start-end or use ANCHOR with CONTEXT'],
    },
}


def validate(parsed_op):
    """Check that a target is provided. Returns list of error strings."""
    errors = []
    if not (parsed_op.target or '').strip():
        errors.append('PREVIEW requires a target — file path or AST target (file.py::Target)')
    return errors


def execute(ctx, parsed_op, result):
    """Dispatch to AST or file preview based on whether subject contains '::'."""
    target = (parsed_op.target or '').strip()
    if '::' in target:
        _execute_ast(ctx, parsed_op, result)
    else:
        _execute_file(ctx, parsed_op, result)


def _execute_ast(ctx, parsed_op, result):
    """Resolve an AST target and emit its full source line range."""
    from forge.target_resolver import resolve_ast_target

    resolved = resolve_ast_target(
        ctx.project_root,
        parsed_op.target,
        default_file=parsed_op.default_file,
    )

    if not resolved.get('ok'):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = resolved.get('error') or 'Target not found'
        return

    src = resolved['source_text']
    lines = src.splitlines()
    start = resolved['start']
    end = resolved['end']

    snippet = ['%04d: %s' % (i, lines[i - 1]) for i in range(start, end + 1)]

    result['file'] = resolved['file_ref']
    result['status'] = 'APPLIED'
    result['message'] = '%s lines %d-%d' % (resolved['kind'], start, end)
    result['preview'] = (
        parsed_op.target + ' [%s lines %d-%d]\n' % (resolved['kind'], start, end)
        + '\n'.join(snippet)
    )


def _anchor_diagnostics(lines, anchor, match_mode, target_path, context=6):
    """Return candidate/near-match diagnostics for PREVIEW anchor failures."""
    fuzzy = (match_mode or '').strip().lower() == 'fuzzy'
    needle = ' '.join((anchor or '').split()) if fuzzy else (anchor or '')
    hits = []

    for idx, line in enumerate(lines):
        hay = ' '.join(line.split()) if fuzzy else line
        if needle and needle in hay:
            hits.append(idx)

    def _line_preview(i):
        text = (lines[i] or '').strip()
        if len(text) > 80:
            text = text[:77] + '...'
        return '  line %d: %s' % (i + 1, text)

    def _preview_block(i):
        start = max(1, i + 1 - context)
        end = min(len(lines), i + 1 + context)
        return '\n'.join([
            '  PREVIEW %s' % target_path,
            '  LINES: %d-%d' % (start, end),
        ])

    if len(hits) == 1:
        return hits, ''

    if len(hits) > 1:
        detail = 'Anchor matched %d times, expected 1' % len(hits)
        detail += '\nCandidates:\n' + '\n'.join(_line_preview(i) for i in hits[:8])
        if len(hits) > 8:
            detail += '\n  ... %d more' % (len(hits) - 8)
        detail += '\nSuggested previews:\n'
        detail += '\n\n'.join(_preview_block(i) for i in hits[:4])
        return hits, detail

    detail = 'Anchor matched 0 times, expected 1'

    suggestions = []
    norm_needle = ' '.join((anchor or '').split()).lower()
    if norm_needle:
        words = [w for w in norm_needle.split() if len(w) > 2]
        for idx, line in enumerate(lines):
            norm_line = ' '.join(line.split()).lower()
            if not norm_line:
                continue
            if norm_needle in norm_line or any(w in norm_line for w in words):
                suggestions.append(idx)
            if len(suggestions) >= 5:
                break

    if suggestions:
        detail += '\nNear matches:\n' + '\n'.join(_line_preview(i) for i in suggestions)
        detail += '\nSuggested previews:\n'
        detail += '\n\n'.join(_preview_block(i) for i in suggestions[:3])

    return hits, detail

def _execute_file(ctx, parsed_op, result):
    """Read a file and emit whole content or a slice via LINES or ANCHOR."""
    file_abs = ctx.resolve_file(parsed_op.target)
    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    if not os.path.isfile(file_abs):
        result['status'] = 'FAILED_IO'
        result['message'] = 'File not found: ' + parsed_op.target
        return

    with open(file_abs, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    lines = content.splitlines()
    lines_range = parsed_op.directives.get('LINES')
    anchor = (parsed_op.directives.get('ANCHOR') or '').strip()

    if anchor:
        fuzzy = (parsed_op.directives.get('MATCH') or '').strip().lower() == 'fuzzy'
        context = 10
        raw_ctx = (parsed_op.directives.get('CONTEXT') or '').strip()
        if raw_ctx.isdigit():
            context = int(raw_ctx)

        match_mode = 'fuzzy' if fuzzy else 'exact'
        hits_zero_based, detail = _anchor_diagnostics(
            lines, anchor, match_mode, parsed_op.target, context=max(1, min(context, 20))
        )

        if len(hits_zero_based) != 1:
            result['status'] = 'SKIPPED_ANCHOR_MISMATCH'
            result['message'] = "ANCHOR %r matched %d times, expected 1" % (
                anchor, len(hits_zero_based)
            )
            if detail:
                result['message'] += '\n' + detail
            return

        hit = hits_zero_based[0] + 1
        start = max(1, hit - context)
        end = min(len(lines), hit + context)
        numbered = ['%04d: %s' % (i, lines[i - 1]) for i in range(start, end + 1)]
        result['preview'] = '%s [anchor=%r context=%d lines %d-%d]\n%s' % (
            parsed_op.target, anchor, context, start, end, '\n'.join(numbered))
        result['status'] = 'APPLIED'
        result['message'] = 'Anchor line %d, context %d' % (hit, context)
        result['file'] = parsed_op.target
        return

    if lines_range:
        start, end = lines_range
        start = max(1, start)
        end = min(len(lines), end)
        numbered = ['%04d: %s' % (i, lines[i - 1]) for i in range(start, end + 1)]
        result['preview'] = parsed_op.target + ' [lines %d-%d]\n' % (start, end) + '\n'.join(numbered)
        result['status'] = 'APPLIED'
        result['message'] = 'Lines %d-%d' % (start, end)
        result['file'] = parsed_op.target
        return

    numbered = ['%04d: %s' % (i + 1, ln) for i, ln in enumerate(lines)]
    result['preview'] = parsed_op.target + ' [%d lines]\n' % len(numbered) + '\n'.join(numbered)
    result['status'] = 'APPLIED'
    result['message'] = '%d lines' % len(numbered)
    result['file'] = parsed_op.target

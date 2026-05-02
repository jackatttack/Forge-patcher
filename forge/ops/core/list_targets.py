# -*- coding: utf-8 -*-
"""
ops.list_targets
================
LIST_TARGETS op — enumerate all patchable AST targets in a Python file.

Parses the file and emits every class, method, function, and module-level
assignment with line ranges and docstrings. Use DOCS: yes (default) to
surface docstrings and flag missing ones with ∅. Use DOCS: no for a
compact list. Essential first step before any AST patch op.
"""



# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'LIST_TARGETS',
    'target_kind': 'file',
    'body_mode': 'forbidden',
    'allowed_directives': set(['DOCS']),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP LIST_TARGETS.
HELP = {
    'summary': 'List patchable AST targets found in a Python file.',
    'subject': ['Relative Python file path inside project root.'],
    'common_failures': [
        'File path is missing or invalid.',
        'Target escapes project root.',
        'Non-Python files may yield zero useful targets.',
    ],
    'safe_usage': [
        'Use this before PREVIEW or REPLACE when you do not know the exact target name.',
        'This is often the fastest way to discover class, method, function, and assignment targets.',
    ],
    'minimal_example': [
        'LIST_TARGETS forge_app_lab/forge_app_state.py',
    ],
    'related_ops': ['PREVIEW', 'REPLACE', 'INSERT_INTO'],
}

HINTS = {
    '_max_hints': 1,
    'file path': {
        'message': 'LIST_TARGETS needs a Python file path.',
        'why': 'Forge parses one .py file and lists its patchable AST targets.',
        'priority': 100,
        'example': [
            'LIST_TARGETS forge/engine.py',
            '',
            'LIST_TARGETS forge/engine.py',
            'DOCS: no',
        ],
        'next': ['Use LIST_FILES to find the file', 'Use PREVIEW or READ_FILE for non-Python files'],
    },
    'cannot read file': {
        'message': 'LIST_TARGETS could not read the file.',
        'why': 'The path may be wrong, missing, or not accessible under project root.',
        'priority': 120,
        'example': [
            'LIST_FILES forge/ops/core',
            '',
            'LIST_TARGETS forge/ops/core/branch_op.py',
        ],
        'next': ['Check the path with LIST_FILES'],
    },
    'syntaxerror': {
        'message': 'Python syntax error while parsing targets.',
        'why': 'LIST_TARGETS needs valid Python syntax before it can enumerate functions, classes, and assignments.',
        'priority': 120,
        'example': [
            'PREVIEW broken_file.py',
            '',
            'RUN_FILE broken_file.py',
        ],
        'next': ['Inspect the syntax error', 'Fix syntax before using AST patch ops'],
    },
    'escapes project root': {
        'message': 'Target path escapes project root.',
        'why': 'Forge only inspects files inside the Pythonista project root.',
        'priority': 120,
        'example': [
            'LIST_TARGETS forge/engine.py',
        ],
        'next': ['Use a relative path under project root'],
    },
}


def validate(parsed_op):
    """Check path is present and points to a .py file. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('LIST_TARGETS requires a file path')
    return errors


def execute(ctx, parsed_op, result):
    """Parse a Python file's AST and emit a structured target list with docs and line ranges."""
    import ast
    import os

    file_abs = ctx.resolve_file(parsed_op.target)
    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    try:
        with open(file_abs, 'r', encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        result['status'] = 'FAILED_IO'
        result['message'] = 'Cannot read file: %s' % e
        return

    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        result['status'] = 'FAILED'
        result['message'] = 'SyntaxError: %s' % e
        return

    try:
        rel = os.path.relpath(file_abs, ctx.project_root)
    except ValueError:
        rel = os.path.basename(file_abs)

    src_lines = src.splitlines()

    # DOCS directive: 'yes' = always show (∅ if missing), 'no' = never show,
    # default = yes
    docs_mode = (parsed_op.directives.get('DOCS') or '').strip().lower()
    if not docs_mode:
        docs_mode = 'yes'

    def first_doc(node):
        """Extract first non-empty line of a node's docstring."""
        try:
            raw = ast.get_docstring(node) or ''
            for line in raw.splitlines():
                line = line.strip()
                if line:
                    return line
        except Exception:
            pass
        return ''

    def preceding_comment(node):
        """Return inline # comment from the line immediately above an assignment node."""
        lineno = node.lineno - 2  # 0-indexed line above
        if 0 <= lineno < len(src_lines):
            stripped = src_lines[lineno].strip()
            if stripped.startswith('#'):
                return stripped.lstrip('#').strip()
        return ''

    def range_str(node):
        """Format AST node line range as [N] or [N-M]."""
        if node.lineno == node.end_lineno:
            return '[%d]' % node.lineno
        return '[%d-%d]' % (node.lineno, node.end_lineno)

    def fmt(target, rng, doc, indent=0):
        """Format a single target line with optional doc annotation."""
        pad = '  ' * indent
        line = '%-58s %s' % (pad + target, rng)
        if docs_mode == 'no':
            pass
        elif docs_mode == 'yes':
            marker = doc[:80] if doc else '∅'
            line += '  # ' + marker
        else:
            if doc:
                line += '  # ' + doc[:80]
        return line

    targets = []
    preview_lines = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            doc = first_doc(node)
            t = '%s::%s.*' % (rel, node.name)
            preview_lines.append(fmt(t, range_str(node), doc))
            targets.append(t)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    ft = '%s::%s.%s' % (rel, node.name, item.name)
                    preview_lines.append(fmt(ft, range_str(item), first_doc(item), indent=1))
                    targets.append(ft)
                elif isinstance(item, ast.Assign):
                    for t2 in (item.targets or []):
                        if isinstance(t2, ast.Name):
                            at = '%s::%s.@%s' % (rel, node.name, t2.id)
                            preview_lines.append(fmt(at, '[%d]' % item.lineno, preceding_comment(item), indent=1))
                            targets.append(at)
                elif isinstance(item, ast.AnnAssign):
                    t2 = getattr(item, 'target', None)
                    if isinstance(t2, ast.Name):
                        at = '%s::%s.@%s' % (rel, node.name, t2.id)
                        preview_lines.append(fmt(at, '[%d]' % item.lineno, preceding_comment(item), indent=1))
                        targets.append(at)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            t = '%s::%s' % (rel, node.name)
            preview_lines.append(fmt(t, range_str(node), first_doc(node)))
            targets.append(t)
        elif isinstance(node, ast.Assign):
            for t2 in (node.targets or []):
                if isinstance(t2, ast.Name):
                    t = '%s::@%s' % (rel, t2.id)
                    preview_lines.append(fmt(t, '[%d]' % node.lineno, preceding_comment(node)))
                    targets.append(t)
        elif isinstance(node, ast.AnnAssign):
            t2 = getattr(node, 'target', None)
            if isinstance(t2, ast.Name):
                t = '%s::@%s' % (rel, t2.id)
                preview_lines.append(fmt(t, '[%d]' % node.lineno, preceding_comment(node)))
                targets.append(t)

    header = 'LIST_TARGETS %s [%d targets]' % (rel, len(targets))
    result['status'] = 'APPLIED'
    result['message'] = '%d targets' % len(targets)
    result['preview'] = header + '\n' + '\n'.join(preview_lines)
    result['file'] = parsed_op.target

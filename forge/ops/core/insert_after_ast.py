# -*- coding: utf-8 -*-
"""
ops.insert_after_ast
====================
INSERT_AFTER op — insert a new method or function after an existing AST target.

Resolves the target and inserts the body block immediately after its
closing line. Skips automatically if the first def in the body already
exists in the file. Use for adding sibling methods or helper functions.
"""

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'INSERT_AFTER',
    'target_kind': 'ast',
    'body_mode': 'required',
    'allowed_directives': set(),
    'required_directives': set(),
    "summary": 'Insert a new method or function immediately after an existing AST target.',
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.

HELP = {
    'summary': 'Insert a new function or method immediately after an existing resolved AST target.',
    'subject': [
        'Required. Existing AST target to insert after.',
        'Example: app.py::Controller.render',
    ],
    'required_directives': [],
    'optional_directives': [],
    'body': [
        'Required. New function, method, class, or code block to insert.',
        'Use BEGIN_BODY / END_BODY.',
    ],
    'common_failures': [
        'Target missing or not found.',
        'Body missing.',
        'Inserted def already exists in the file.',
        'Wrong target level — use file.py::Class.method for class methods.',
    ],
    'safe_usage': [
        'Run LIST_TARGETS first to confirm the exact target.',
        'Use for adding sibling functions or methods.',
        'Do not use for injecting into the middle of a function — use INSERT_INTO instead.',
        'If replacing an existing function or method, use REPLACE.',
    ],
    'related_ops': ['LIST_TARGETS', 'PREVIEW', 'INSERT_BEFORE', 'INSERT_INTO', 'REPLACE'],
    'minimal_example': [
        'INSERT_AFTER app.py::old_helper',
        'BEGIN_BODY',
        'def new_helper():',
        '    return True',
        'END_BODY',
    ],
}

HINTS = {
    'body required': 'Provide the new method or function as the body',
    'not found': 'Target not found — run LIST_TARGETS on the file to see valid targets',
    'already present': 'A def with that name already exists in the file — use REPLACE instead',
    'ambiguous': 'Target name matched more than once — use file.py::ClassName.method_name to be specific',
}


def validate(parsed_op):
    """Check target and body are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('INSERT_AFTER requires a target')
    if not parsed_op.body:
        errors.append('INSERT_AFTER requires body content')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve AST target and insert body immediately after its closing line."""
    from forge.target_resolver import resolve_ast_target

    from forge.source_ops import insert_after_lines, get_line_indent

    resolved = resolve_ast_target(
        ctx.project_root,
        parsed_op.target,
        default_file=parsed_op.default_file,
    )

    if not resolved.get('ok'):
        result['status'] = 'FAILED_NOT_FOUND'
        result['message'] = resolved.get('error') or 'Target not found'
        return

    file_abs = resolved['file_abs']
    if not ctx.in_root(file_abs):
        result['status'] = 'FAILED_INVALID_PATH'
        result['message'] = 'Target escapes project root'
        return

    before = resolved['source_text']
    insert_line = resolved['end']
    ref_line = before.splitlines(True)[resolved['start'] - 1]
    indent = get_line_indent(ref_line)

    patched = insert_after_lines(
        before,
        insert_line,
        parsed_op.body,
        indent,
        tight=False,
    )

    with open(file_abs, 'w', encoding='utf-8') as f:

        f.write(patched)

    ctx.file_cache[file_abs] = patched
    ctx.touched_files[file_abs] = {
        'before': before,
        'after': patched,
    }

    result['file'] = resolved['file_ref']
    result['status'] = 'APPLIED'
    result['message'] = 'inserted after %s lines %d-%d' % (
        resolved['kind'],
        resolved['start'],
        resolved['end'],
    )

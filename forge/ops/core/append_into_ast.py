# -*- coding: utf-8 -*-
"""
ops.append_into_ast
===================
APPEND_INTO op — append code at the end of an AST target body.

Resolves the target and inserts the body block after the last line of
its body. No anchor needed — always appends to the very end. Use for
adding cleanup calls, return statements, or trailing logic to a function.
"""

# Op registration dict — name, target kind, body mode, directives.
SPEC = {
    'name': 'APPEND_INTO',
    'target_kind': 'ast',
    'body_mode': 'required',
    'allowed_directives': set(),
    'required_directives': set(),
}

# HELP doc block — surfaces via HELP APPEND_INTO.
HELP = {
    'summary': 'Append code at the end of a resolved AST target body.',
    'subject': [
        'AST target string, for example file.py::Class.method_name.',
        'Best for adding code near the end of a function, method, or class body.',
    ],
    'common_failures': [
        'Target does not resolve to a real AST target.',
        'Missing BEGIN_BODY / END_BODY.',
    ],
    'safe_usage': [
        'Use PREVIEW first if you are not sure where the body currently ends.',
        'Use this when a simple end-of-body insertion is cleaner than anchor matching.',
    ],
    'minimal_example': [
        'APPEND_INTO forge_app_lab/forge_app_state.py::build_starter_bundle',
        'BEGIN_BODY',
        "return '# done'",
        'END_BODY',
    ],
    'related_ops': ['PREVIEW', 'PREPEND_INTO', 'INSERT_INTO'],
}

# Runtime hint strings keyed by failure mode, surfaced by the hints engine.
HINTS = {
    'body required': 'Provide the code to append as the body',
    'not found': 'Target not found — run LIST_TARGETS on the file to see valid targets',
    'ambiguous': 'Target name matched more than once — use file.py::ClassName.method_name to be specific',
}


def validate(parsed_op):
    """Check that target is present. Returns list of error strings."""
    """Check target and body are present. Returns list of error strings."""
    errors = []

    if not (parsed_op.target or '').strip():
        errors.append('APPEND_INTO requires a target')
    if not parsed_op.body:
        errors.append('APPEND_INTO requires body content')
    return errors


def execute(ctx, parsed_op, result):
    """Resolve AST target and append body lines at the end of its block."""
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
    insert_line = resolved['end'] - 1
    ref_line = before.splitlines(True)[resolved['start'] - 1]
    indent = get_line_indent(ref_line) + '    '

    patched = insert_after_lines(
        before,
        insert_line,
        parsed_op.body,
        indent,
        tight=True,
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
    result['message'] = 'appended into %s lines %d-%d' % (
        resolved['kind'],
        resolved['start'],
        resolved['end'],
    )
